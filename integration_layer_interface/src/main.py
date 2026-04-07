"""
Digital Twin Application - Main Entry Point (Microservice Version)

This module serves as the main entry point for the Digital Twin application.
It coordinates between AAS generation (via API), CIM generation, and Typhoon HIL integration
based on configuration settings.
"""

import datetime
import os
import time
import requests
from pathlib import Path
from loguru import logger
import yaml

# Configure logger
logger.add(
    "logs/digital_twin_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="7 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
)

# Service endpoints (could also come from config or environment variables)
SERVICE_URLS = {
    "generate_aasx_from_datasheets": os.getenv("AAS_SERVICE_URL", "http://generate_aasx_from_datasheets:5002/generate"),
    "cim_generator": os.getenv("CIM_SERVICE_URL", "http://cim_generator:5003/generate"),
    "typhoon_integration": os.getenv("TYPHOON_SERVICE_URL", "http://typhoon_integration:5004/process")
}


def call_service(service_name: str, config: dict, timeout: int = 30):
    """
    Generic function to call microservices

    Args:
        service_name: Name of the service to call
        config: Configuration data to send
        timeout: Request timeout in seconds

    Returns:
        Response JSON if successful

    Raises:
        Exception: If service call fails
    """
    try:
        logger.info(f"Calling {service_name} service at {SERVICE_URLS[service_name]}")
        start_time = time.time()

        response = requests.post(
            SERVICE_URLS[service_name],
            json=config,
            timeout=timeout
        )

        duration = time.time() - start_time
        logger.debug(f"Service {service_name} responded in {duration:.2f}s")

        response.raise_for_status()
        return response.json()

    except requests.exceptions.Timeout:
        error_msg = f"Timeout calling {service_name} service after {timeout}s"
        logger.error(error_msg)
        raise Exception(error_msg)

    except requests.exceptions.RequestException as e:
        error_msg = f"Service communication error with {service_name}: {str(e)}"
        logger.error(error_msg)
        raise Exception(f"Service {service_name} unavailable: {str(e)}")


def run_app():
    """
    Main execution function for the Digital Twin application.
    Now uses microservices for all major components.
    """
    try:
        logger.info("Starting Digital Twin Application (Microservice Version)")

        # Get the directory where this script is located
        CONFIG_PATH = Path(__file__).resolve().parent.parent / 'config_aas.yaml'

        # Load the YAML configuration file
        logger.info(f"Loading configuration from {CONFIG_PATH}")
        with open(CONFIG_PATH, 'r') as config_file:
            config_data = yaml.safe_load(config_file)

        grid_name = config_data['Aas_gen']['grid']['name']
        server = {}

        # ICT-preprocessing
        if config_data['Aas_gen']['module']['type'] == "aasx":
            logger.info("AASX for the asset has already been developed")

        # Execute function based on config
        function = config_data['Aas_gen']['module']['parser']
        logger.info(f"Executing parser: {function}")

        if function == "asset":
            logger.info("Starting AAS generation process via API")
            call_service("generate_aasx_from_datasheets", config_data)
            logger.success("AAS generation completed successfully")

        elif function == "cim_gen":
            logger.info("Starting CIM generation process via API")
            # Assuming CIM generator is also containerized
            result = call_service("cim_generator", {
                "config_path": 'Digital_Twin_App/Cim_gen/config_cim.yaml'
            })
            logger.success("CIM generation completed successfully")
            grid_data = result.get('grid_data')
            cim_results = result.get('cim_results')

        elif function == "grid_measurement":
            logger.info("Starting grid measurement integration via API")
            # Assuming Typhoon integration is containerized
            result = call_service("typhoon_integration", {
                "config_path": 'Digital_Twin_App/Typhoon/config_typhoon.yaml',
                "timestamp": datetime.datetime.now().isoformat()
            })
            logger.success("Typhoon HIL integration completed successfully")

        else:
            error_msg = "No valid application found in the config file!"
            logger.error(error_msg)
            raise ValueError(error_msg)

    except yaml.YAMLError as e:
        logger.error(f"YAML configuration error: {e}")
        raise
    except FileNotFoundError as e:
        logger.error(f"File not found error: {e}")
        raise
    except Exception as e:
        logger.critical(f"Unexpected error during execution: {e}")
        raise
