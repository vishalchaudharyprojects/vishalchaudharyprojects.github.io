from grid_measurements.src.connector.write_measurements_to_influxdb import init_influxdb_client, write_ln_to_influx_db
from loguru import logger
from grid_measurements.src.connector.iec_61850_modbus_reading import *
import time
from multiprocessing import Process
from grid_measurements.src.connector.dlms_cosem_listener import start_dlms_listener


def data_integration(config, scl_communication_df, scl_dlms_df, root_scd_tree, scd_file_name):
    """
    Main loop to handle data integration for both Modbus and DLMS COSEM protocols.

    This function:
    - Initializes InfluxDB connection for data storage.
    - Spawns DLMS COSEM TLS listener(s) if DLMS devices are configured.
    - Continuously polls Modbus devices for data.
    - Writes IEC 61850 logical node data into InfluxDB for Grafana and analysis.

    Parameters:
    ----------
    config : dict
        Parsed YAML configuration containing DataIntegration parameters.
    scl_communication_df : pd.DataFrame
        DataFrame containing Modbus register configurations extracted from the SCD.
    scl_dlms_df : pd.DataFrame
        DataFrame containing DLMS COSEM listener configurations extracted from the SCD.
    root_scd_tree : xml.etree.ElementTree.Element
        Root of the parsed SCD XML tree for Modbus polling and context.
    scd_file_name : str
        Name of the SCD file, used to extract the bus identifier for Influx tagging.

    Returns:
    -------
    None
        This function runs indefinitely in a while-loop to maintain continuous ingestion.
    """

    # Extract runtime settings and tags from the config
    runtime_interval = config["DataIntegration"]["runtime_sec"]  # Polling interval in seconds
    grid_name = config["DataIntegration"]["grid"]["name"]        # Grid name for Influx tagging
    bus = scd_file_name.split("_")[-1].split(".")[0]            # Bus name extracted from SCD filename

    logger.info("Starting data integration process.")

    # Initialize the InfluxDB client and write API for efficient writes
    client, write_api = init_influxdb_client()

    # Check if there are DLMS COSEM configurations to set up TLS listeners
    if scl_dlms_df is not None and not scl_dlms_df.empty:
        logger.info("DLMS COSEM configurations found, starting DLMS listener.")

        # Spawn DLMS COSEM listener in a separate process for parallel ingestion
        dlms_process = Process(
            target=start_dlms_listener,
            args=(scl_dlms_df, grid_name, bus)  # Pass grid name and bus for Influx tagging
        )
        dlms_process.start()
    else:
        logger.info("No DLMS COSEM configurations found, skipping DLMS listener.")

    # Continuous ingestion loop for Modbus data collection
    while True:
        # Poll data from Modbus IEDs using the prepared configurations
        logical_nodes, read_data_status = read_modbus_data_from_ieds(
            scl_communication_df,
            bus,
            root_scd_tree
        )

        logger.info("Filled logical node data objects with data from Modbus TCP servers successfully.")

        # Warn if devices were unreachable but continue execution
        if not read_data_status:
            logger.warning("Modbus-TCP servers could not be reached. Program execution will continue.")

        # Write parsed logical node data (MMXU, TCTR) to InfluxDB for analysis
        write_ln_to_influx_db(logical_nodes, grid_name, bus, write_api)
        logger.info("Logical node data from IEDs written to InfluxDB successfully.")

        # Sleep for the specified runtime interval before polling again
        time.sleep(runtime_interval)