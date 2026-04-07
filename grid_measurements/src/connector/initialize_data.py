# Importing topology and operation data from csv files ##
from grid_measurements.src.connector.scd_handling import parse_registers_from_scd
from loguru import logger
import pandas as pd
import yaml



def parse_config(config_path):
    """
    This function parses the configuration file "GridCalcTool.yaml"
    and loads the SCD file from the local folder or s3 bucket

    :param config_path: Path for the configuration file
    :returns config_data: Configuration data loaded from the YAML file
    """
    # Load the YAML configuration file directly
    config_data = yaml.safe_load(open(config_path))
    logger.info(f"Configuration file {config_path} loaded successfully.")

    return config_data


def init_grid_data():
    """
    This function initializes grid_data as dictionary with
    dataframes for the grid model.

    :return: grid_data
    """
    # initialize required dataframes for grid parameters
    grid_data = {'gridConfig': pd.DataFrame(), 'busData': pd.DataFrame(), 'topology': pd.DataFrame(),
                 'lineTypes': pd.DataFrame(), 'loads': pd.DataFrame(), 'gens': pd.DataFrame(),
                 'measTopology': pd.DataFrame(), 'switches': pd.DataFrame}

    return grid_data


def parse_scd_communication(config, scd_tree_root):
    """
    Parses the SCD file to extract Modbus and DLMS COSEM configurations.

    Returns:
        scd_communication_df: Modbus DataFrame
        scd_dlms_df: DLMS COSEM DataFrame
    """
    protocol = config["DataIntegration"]["communication"]["input"]["protocol"]

    scd_communication_df, scd_dlms_df = parse_registers_from_scd(scd_tree_root)

    if protocol == "modbus" and scd_communication_df.empty:
        logger.error("No Modbus communication data found in the SCD file.")
        raise ValueError("No Modbus communication data found. Aborting.")

    if protocol == "dlms" and scd_dlms_df.empty:
        logger.error("No DLMS COSEM communication data found in the SCD file.")
        raise ValueError("No DLMS COSEM communication data found. Aborting.")

    return scd_communication_df, scd_dlms_df



