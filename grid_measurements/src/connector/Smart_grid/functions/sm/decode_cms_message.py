import logging
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from asn1crypto import cms
from grid_measurements.src.connector.Smart_grid.functions.sm.x963_kdf import x963_kdf

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.keywrap import aes_key_unwrap


def decode_cms_message(cms_data: bytes, cms_parameters: dict):
    """
    This function decodes the CMS message using the CMS parameters.

    :param cms_data: The binary CMS message data.
    :param cms_parameters: A dictionary containing 'key_path' and 'cert_path'.
    :returns: The decrypted message as bytes.
    """
    # Set up logging for debugging
    logging.basicConfig(level=logging.DEBUG)

    # 2) Read in recipient private key
    with open(cms_parameters["key_path"], 'rb') as key_file: 
        private_key = serialization.load_pem_private_key(key_file.read(), password=None, backend=default_backend())

    # 3) Parse message
    logging.debug(f"Parsing CMS data: {cms_data}")
    cms_structure = cms.ContentInfo.load(cms_data)
    logging.debug(f'Parsed CMS structure: {cms_structure}')

    # 4) Check content type of the CMS structure
    content_type = getattr(cms_structure['content_type'], 'native', None)
    if content_type is None: 
        raise ValueError(f"Invalid content type: {cms_structure['content_type']}")
    logging.debug(f'Content type: {content_type}')

    if content_type == 'signed_data':
        signed_data = getattr(cms_structure['content'], 'native', None)
        logging.debug(f'Signed data content: {signed_data}')

        # Check if the content type is authenticated_enveloped_data
        content_type_value = signed_data['encap_content_info']['content_type']
        logging.debug(f'Encap content type: {content_type_value}')

        if content_type_value == 'authenticated_enveloped_data': 
            logging.debug("Processing authenticated_enveloped_data.")

            # Access auth_encrypted_content_info
            auth_encrypted_content = signed_data['encap_content_info']['content']
            logging.debug(f'Auth encrypted content info: {auth_encrypted_content}')

            recipient_info = auth_encrypted_content['recipient_infos'] 
            if not recipient_info:
                raise ValueError("No recipient info available.")

            # Assuming we have only one recipient for simplicity
            recipient = recipient_info[0]
            # obtain the public key of the sender
            public_key_sender = recipient["originator"]["public_key"]
            # Use the public key from the sender to create an EC public key object
            public_key = ec.EllipticCurvePublicKey.from_encoded_point(ec.BrainpoolP256R1(), public_key_sender)

            # Generate the shared secret:
            shared_secret = private_key.exchange(ec.ECDH(), public_key)
            ####################################################################################
            # obtain wrapped encrypted key
            key_length = 16  # As we use AES_GCM_128
            # Derive KEK using KDF
            kek = x963_kdf(shared_secret, key_length, shared_info=b"")
            # obtain recipient's encrypted key
            wrapped_key = recipient["recipient_encrypted_keys"][0]["encrypted_key"]


            # unwrap the key encryption
            unwrapped_key = aes_key_unwrap(kek, wrapped_key, backend=default_backend())
            ###################################################################################
            # obtain the initialization vector used 
            # for decrypting according to GCM method
            nonce = auth_encrypted_content["auth_encrypted_content_info"]["content_encryption_algorithm"]["parameters"]['0']
            tag_length = auth_encrypted_content["auth_encrypted_content_info"]["content_encryption_algorithm"]["parameters"]['1']  # acc. rfc 5084
            tag = auth_encrypted_content["mac"]
            encrypted_content = auth_encrypted_content["auth_encrypted_content_info"]["encrypted_content"]
            # decrypt the content with the unwrapped_key
            cipher = Cipher(algorithms.AES(unwrapped_key), modes.GCM(nonce, tag, min_tag_length=tag_length), backend=default_backend())
            decryptor = cipher.decryptor()
            decrypted_content = decryptor.update(encrypted_content) + decryptor.finalize()

            return decrypted_content
        else: 
            raise TypeError(
                "The content type of the signed data \
                is not authenticated_enveloped_data.")
    else:
        raise TypeError("The content type is not signed_data.")
