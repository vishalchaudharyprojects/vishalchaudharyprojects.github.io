import os
import ssl
import socket
from pathlib import Path
from multiprocessing import Process
from loguru import logger
from dotenv import load_dotenv
from grid_measurements.src.connector.write_measurements_to_influxdb import init_influxdb_client, write_ln_to_influx_db
from grid_measurements.src.connector.iec_61850_modbus_reading import MMXU, TCTR  # adjust if needed
from grid_measurements.src.connector.Smart_grid.functions.sm.sm_tls_server import recv_all, send_http_200_response, decode_cms_message, parse_http_post
from grid_measurements.src.connector.Smart_grid.functions.sm.cosem_to_iec61850_parsing import parse_taf10_to_iec61850_2

# Load environment variables from .env file
load_dotenv()


def start_dlms_listener(scl_dlms_df, grid_name, bus):
    """
    Starts DLMS COSEM TLS listeners for each IED specified in the SCD file DataFrame.

    Creates a separate process for each DLMS COSEM listener to handle concurrent connections.

    Args:
        scl_dlms_df (pd.DataFrame): DataFrame containing DLMS COSEM IED configurations from SCD file
                                    with columns: ["IED name", "PORT", "Unit-ID", "AP Name", "SubNetwork"]
        config (dict): Configuration dictionary from YAML file

    Returns:
        None: Runs indefinitely until interrupted
    """
    logger.info("Starting DLMS COSEM TLS listener(s) based on SCD...")

    processes = []
    for _, row in scl_dlms_df.iterrows():
        ied_name = row["IED name"]
        port = int(row["PORT"])

        logger.info(f"Launching DLMS TLS listener for IED: {ied_name} on Port: {port}")

        # Create a new process for each DLMS listener
        p = Process(
            target=run_tls_server_for_dlms,
            args=(ied_name, port,grid_name, bus)  # Pass grid name for Influx tagging
        )
        p.start()
        processes.append(p)

    # Wait for all processes to complete (though they run indefinitely)
    for p in processes:
        p.join()


def run_tls_server_for_dlms(ied_name, port, grid_name, bus):
    """
    Runs a TLS-secured DLMS COSEM server that listens for smart meter data,
    parses TAF10 payloads into IEC 61850 logical nodes (MMXU/TCTR),
    and writes measurements to InfluxDB.

    Args:
        ied_name (str): Name of the IED from SCD file
        port (int): Port number to listen on

    Returns:
        None: Runs indefinitely in a loop accepting connections
    """
    # Resolve paths for TLS certificates and keys
    PROJECT_ROOT = Path(os.getcwd())
    LIBS_PATH = PROJECT_ROOT / os.environ.get("DLMS_LIBS_PATH", "libs/pisa")

    def resolve_path(env_key):
        """
        Helper function to resolve file paths from environment variables.
        Handles both absolute and relative paths.

        Args:
            env_key (str): Environment variable name containing the path

        Returns:
            Path: Resolved absolute path

        Raises:
            EnvironmentError: If environment variable is not set
        """
        val = os.environ.get(env_key)
        if val is None:
            logger.error(f"{env_key} not set in .env")
            raise EnvironmentError(f"{env_key} not set in .env")
        p = Path(val)
        return p if p.is_absolute() else LIBS_PATH / p

    # TLS server configuration parameters
    CERTIFICATE_PARAMETERS = {
        "verify_client": os.environ.get("DLMS_VERIFY_CLIENT", "optional"),
        "server_certificate": str(resolve_path("DLMS_SERVER_CERT")),
        "server_key": str(resolve_path("DLMS_SERVER_KEY")),
        "client_certificate": str(resolve_path("DLMS_CLIENT_CERT")),
        "cipher_suite": os.environ.get("DLMS_CIPHER_SUITE", "ECDHE-ECDSA-AES128-GCM-SHA256"),
        "check_hostname": os.environ.get("DLMS_CHECK_HOSTNAME", "False") == "True",
        "elliptic_curve": os.environ.get("DLMS_ELLIPTIC_CURVE", "brainpoolP256r1"),
    }

    # CMS (Cryptographic Message Syntax) parameters for payload decryption
    CMS_PARAMETERS = {
        "key_path": str(resolve_path("DLMS_CMS_KEY")),
        "cert_path": str(resolve_path("DLMS_CMS_CERT")),
    }

    # Debug mode flag
    DEBUG = os.environ.get("DLMS_DEBUG", "False") == "True"

    # Configure TLS context for secure connections
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.check_hostname = CERTIFICATE_PARAMETERS["check_hostname"]

    # Set client certificate verification mode
    verify_client = CERTIFICATE_PARAMETERS["verify_client"]
    if verify_client == "optional":
        context.verify_mode = ssl.CERT_OPTIONAL
    elif verify_client == "required":
        context.verify_mode = ssl.CERT_REQUIRED
    else:
        context.verify_mode = ssl.CERT_NONE

    # Load certificates and configure TLS parameters
    context.load_verify_locations(cafile=CERTIFICATE_PARAMETERS["client_certificate"])
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(
        certfile=CERTIFICATE_PARAMETERS["server_certificate"],
        keyfile=CERTIFICATE_PARAMETERS["server_key"]
    )
    context.set_ciphers(CERTIFICATE_PARAMETERS["cipher_suite"])
    context.set_ecdh_curve(CERTIFICATE_PARAMETERS["elliptic_curve"])

    # Create and bind TCP socket
    bindsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    bindsocket.bind(("", port))  # Bind to all interfaces on specified port
    bindsocket.listen(5)  # Allow up to 5 pending connections

    logger.info(f"DLMS TLS Server for {ied_name} listening on Port {port}")

    # Initialize InfluxDB client once (reused for all connections)
    client, write_api = init_influxdb_client()

    # Main server loop - handles incoming connections
    while True:
        try:
            # Accept new connection
            newsocket, fromaddr = bindsocket.accept()
            logger.info(f"Connection from {fromaddr}")

            try:
                # Wrap socket with TLS
                conn = context.wrap_socket(newsocket, server_side=True)

                # Receive and process data
                data = recv_all(conn, debug=DEBUG)
                send_http_200_response(conn)  # Acknowledge receipt

                # Parse HTTP POST request
                headers, payload = parse_http_post(data)
                conn.close()  # Close connection after receiving data

                if payload:
                    # Decrypt CMS-encrypted payload
                    message = decode_cms_message(payload, CMS_PARAMETERS)
                    logger.info(f"Received DLMS COSEM payload for {ied_name}")

                    # Parse TAF10 message to IEC 61850 logical nodes
                    mmxu, tctr = parse_taf10_to_iec61850_2(message)

                    # Prepare logical nodes for InfluxDB write
                    logical_nodes = {
                        ied_name: [mmxu, tctr]
                    }

                    # Write measurements to InfluxDB
                    write_ln_to_influx_db(logical_nodes, grid_name, bus, write_api)
                    logger.info(f"DLMS COSEM data written to InfluxDB for {ied_name}")

            except Exception as e:
                logger.error(f"Error handling DLMS TLS connection: {e}")
                continue

        except Exception as e:
            logger.error(f"Server error: {e}")
            # Continue running server even if one connection fails
            continue