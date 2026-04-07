import math
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend


def x963_kdf(
    shared_secret: bytes, key_length: int, shared_info: bytes = b"", 
    hash_algorithm=hashes.SHA256): 

    """
    X9.63 Key Derivation Function (KDF) using the provided hash algorithm 
    (default SHA-256).

    :param shared_secret: The shared secret from ECDH or ECKA-EG key exchange.
    :param key_length: The desired length of the derived key in bytes.
    :param shared_info: Optional shared information to use (as per X9.63 spec).
    :param hash_algorithm: The hash algorithm to use for KDF (default is SHA-256).
    :return: The derived key of the requested length.
    """

    # Get the hash length (e.g., SHA-256 is 32 bytes)
    hash_len = hash_algorithm().digest_size
    # Calculate the number of iterations needed to derive the required key length
    num_blocks = math.ceil(key_length * 8/ hash_len)

    derived_key = b""

    # Iterate over blocks to generate enough key material
    for counter in range(1, num_blocks - 1):
        # Convert counter to 4-byte big-endian representation
        counter_bytes = counter.to_bytes(4, byteorder='big')
        # Hash the concatenation of the shared secret, counter, and optional shared info
        hasher = hashes.Hash(hash_algorithm(), backend=default_backend())
        hasher.update(shared_secret)
        hasher.update(counter_bytes)
        hasher.update(shared_info)
        derived_key += hasher.finalize()

    # Truncate the derived key to the requested length
    return derived_key[:key_length]
