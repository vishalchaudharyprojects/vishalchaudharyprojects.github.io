import re
import ssl
import socket
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from grid_measurements.src.connector.Smart_grid.functions.sm.parse_http_post import parse_http_post
from grid_measurements.src.connector.Smart_grid.functions.sm.send_http_200_response import send_http_200_response
from grid_measurements.src.connector.Smart_grid.functions.sm.decode_cms_message import decode_cms_message
from grid_measurements.src.connector.Smart_grid.functions.sm.cosem_to_iec61850_parsing import parse_taf10_to_iec61850
import time


def recv_all(conn, debug, buffer_size=4096):
    """
    Receives all data that is sent via a connection.
    However, the packet length must not be less than the buffer_size,
    otherwise the function will not work correctly

    :param conn: connection instance of the tls-server, socket
    :param debug: is the application running in debug mode?
    :param buffer_size: how many bytes are received at once

    :return: byte-string of the concatenated payload
    """
    # starte die Zeitmessung
    start_time = time.perf_counter()
    # initialisiere eine Liste für die Payload
    chunks = []
    # Empfange die Daten in Chunks bis die Payload nicht mehr
    # maximale Größe hat
    while True:
        chunk = conn.recv(buffer_size)
        # parse payload size from http header
        # füge die Payload der chunks hinzu
        chunks.append(chunk)
        # measure intermediate time to parse each chunk
        if debug:
            current_time = time.perf_counter()
            intermediate_elapsed_time = current_time - start_time
            print(f"Received {len(chunk)} bytes in {intermediate_elapsed_time} seconds.")
        # data is not filling buffer size anymore
        if len(chunks) > 1:
            if len(chunk) < len(chunks[-2]):
                break

    return b"".join(chunks)


def pisa_tls_server(certificate_parameters: dict, connection_parameters: dict, cms_parameters: dict, outputpath: str, outputfile: str, debug: bool = False):
    """
     def pisa_tls_server(certificate_parameters: dict, connection_parameters: 
        dict, cms_parameters: dict, debug: bool = False):
        Starts a TLS server with the given parameters and 
        handles incoming connections.
            certificate_parameters (dict): Dictionary 
            containing certificate-related parameters.
                - "check_hostname" (bool): Whether to check the 
                hostname in the certificate.
                - "verify_client" (bool or str): Client verification mode. 
                Can be True, False, or "optional".
                - "client_certificate" (str): Path to the client certificate file.
                - "server_certificate" (str): Path to the server certificate file.
                - "server_key" (str): Path to the server key file.
                - "cipher_suite" (str): Cipher suite to be used.
                - "elliptic_curve" (str): Elliptic curve to be used.
            connection_parameters (dict): Dictionary containing 
            connection-related parameters.
                - "ip_address" (str): IP address to bind the server to.
                - "port" (int): Port number to bind the server to.
            cms_parameters (dict): Dictionary containing CMS-related parameters.
                - Add relevant CMS parameters here.
            debug (bool, optional): If True, enables debug mode and 
            logs additional information. Defaults to False.
            outputfile (str): The name of the output file.
            outputpath (str): The path where the output should be saved.
        Raises:
            Exception: If there is an error in receiving or decoding the message.
    """

    # Ein SSL/TLS-Kontext wird erstellt
    # context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    # context.load_cert_chain(certfile=certfile, keyfile=keyfile)

    # Erstelle Kontextobjekt
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    # context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.check_hostname = certificate_parameters["check_hostname"]
    if not certificate_parameters["verify_client"]:
        print("Debug: Accepting connection without verifying")
        context.verify_mode = ssl.CERT_NONE
    elif certificate_parameters["verify_client"]:
        context.verify_mode = ssl.CERT_REQUIRED
    elif certificate_parameters["verify_client"] == "optional":
        context.verify_mode = ssl.CERT_OPTIONAL

    # verify the client certificate using concatenated sub_ca and root_ca certificate
    context.load_verify_locations(cafile=certificate_parameters["client_certificate"])

    context.minimum_version = ssl.TLSVersion.TLSv1_2

    # context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    # speficy tls 1.2
    # context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
    context.load_cert_chain(
        certfile=certificate_parameters["server_certificate"], 
        keyfile=certificate_parameters["server_key"])

    # Set the cipher suite
    # cipher_suite = (
    #    'ECDHE-ECDSA-AES128-GCM-SHA256:'
    #    'ECDHE-ECDSA-AES256-GCM-SHA384:'
    #    'AES128-GCM-SHA256:AES256-GCM-SHA384'
    # )
    # set cipher suite
    context.set_ciphers(certificate_parameters["cipher_suite"])

    # configure the eliptic curve
    context.set_ecdh_curve(certificate_parameters["elliptic_curve"])
    # context.set_ecdh_curve('brainpoolP256r1')
    # Erstellen eines TCP/IP-Sockets

    ip = connection_parameters["ip_address"]
    port = connection_parameters["port"]
    bindsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    bindsocket.bind((ip, port))
    bindsocket.listen(5)

    print(f"Server läuft und wartet auf Verbindungen auf {ip}:{port}...")
    while True:
        payload = ""
        # Erstellen eines SSL/TLS-Sockets, der den normalen Socket umwickelt
        newsocket, fromaddr = bindsocket.accept()
        print(f"Verbindung von {fromaddr}")
        try:
            conn = context.wrap_socket(newsocket, server_side=True)
            # Nachricht empfangen, buffer muss mindestens 17000 bytes 
            # groß sein! (payload length measured approx. 16xxx bytes)
            data = recv_all(conn, debug)
            send_http_200_response(conn)
            # decode http post

            if debug:
                with open("tls_payload2.txt", "wt") as file: 
                    for line in re.split(b'\r\n(?!0)', data): 
                        file.write(str(line) + '\n') 
            headers, payload = parse_http_post(data) 
            if debug:
                print(f"Header length is: [{len(headers)}] bytes")
                print(f"Payload length is: [{len(payload)}] bytes")
                with open("http_payload_binary.bin", "wb") as file: 
                    file.write(payload) 

            # Verbindung schließen
            print("Verbindung wird geschlossen")
            conn.close()
            try:
                if payload != "":
                    # decrypt the cms message and print it
                    message = decode_cms_message(payload, cms_parameters)
                    print(f"Empfangene Nachricht: {message}")
            except Exception as e:
                print(f"Fehler beim Dekodieren der Nachricht: {e}")

            # parse the message into iec 61850 objects
            parse_taf10_to_iec61850(message, outputpath, outputfile)

        except Exception as e:
            print(f"Fehler beim Empfangen der Nachricht: {e}")



