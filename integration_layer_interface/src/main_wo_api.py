"""
Digital Twin Application - Main Entry Point (Microservice Version)

Clean, absolute-path refactor for stability in container & IDE execution.
"""

import datetime
from pathlib import Path
import yaml
from loguru import logger
#from generate_aasx_from_datasheets.src.aas_og import process_all_equipment
from Cim_gen.src.Function_modules.InputData import get_data
from grid_measurements.src.connector.initialize_data import parse_config
from generate_aasx_from_datasheets.src.aas import process_all_equipment

# === 1. Set PROJECT_ROOT (two levels up from this file) ===
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# === 2. Logging configuration ===
LOGS_DIR = PROJECT_ROOT / 'integration_layer_interface' / 'logs'
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logger.add(
    LOGS_DIR / "digital_twin_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="7 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
)


def process_asset(config_data: dict) -> None:
    """
    Process AAS generation for a single asset or all assets based on config.
    """
    asset_config = config_data['Aas_gen']['application']['asset']

    if asset_config.get('process_all', False):
        logger.info("Processing all assets in the assets folder.")
    else:
        equipment = asset_config.get('equipment', '')
        if not equipment:
            logger.warning("No equipment specified, and process_all not set.")
            return
        logger.info(f"Processing single asset: {equipment}")

    process_all_equipment(config_data)
    logger.success("AAS generation completed successfully.")


def main():
    """
    Entry point for the Digital Twin Application.
    """
    try:
        logger.info("Starting Digital Twin Application...")

        config_path = PROJECT_ROOT / 'integration_layer_interface' / 'config_aas.yaml'
        logger.info(f"Loading configuration from: {config_path}")

        with open(config_path, 'r') as config_file:
            config_data = yaml.safe_load(config_file)

        module_type = config_data['Aas_gen']['module']['type']
        parser = config_data['Aas_gen']['module']['parser']
        logger.info(f"Module type: {module_type}, Parser: {parser}")

        if parser == "asset":
            logger.info("Initiating AAS generation workflow...")
            process_asset(config_data)

        elif parser == "cim_gen":
            logger.info("Initiating CIM generation workflow...")
            config_cim_path = PROJECT_ROOT / 'Cim_gen' / 'config_cim.yaml'
            logger.info(f"Loading CIM config from: {config_cim_path}")

            config_data_cim, grid_data, cim_results = get_data(str(config_cim_path))
            logger.success("CIM generation completed successfully.")

        elif parser == "grid_measurement":
            logger.info("Initiating grid measurement integration...")
            config_typhoon_path = PROJECT_ROOT / 'grid_measurements' / 'config_typhoon.yaml'
            logger.info(f"Loading Typhoon config from: {config_typhoon_path}")

            config = parse_config(str(config_typhoon_path))
            logger.success("Grid measurement integration initialized.")

        else:
            logger.error("No valid application parser specified in config!")
            raise ValueError("No valid application parser specified in config!")

    except Exception as e:
        logger.critical(f"Unexpected error during execution: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    main()
