"""
This file is to define all loggers and handlers used in the toolchain
"""

import logging


def init_cim_import_logger():
    # create a logger
    cim_import_logger = logging.getLogger("CIM_import_logger")
    # set the level of the logger to debug to capture all kind of logging messages
    cim_import_logger.setLevel(logging.DEBUG)
    # create a console handler
    console_handler = logging.StreamHandler()
    # set level to INFO for console output
    console_handler.setLevel(logging.INFO)
    # create a file handler
    handler = logging.FileHandler("cim_import_logger.log")
    # set the level of the handler to Warning
    handler.setLevel(logging.WARNING)
    # Create a formatter and add it to the handler
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    # Add the handler to the logger
    cim_import_logger.addHandler(handler)
    cim_import_logger.addHandler(console_handler)

    return cim_import_logger


def bus_type_warning(value, cim_import_logger):
    bus_type = "unknown"
    # Set logging WARNING
    cim_import_logger.warning("The bus type of " + value.name + " is not specified")


def voltage_level_warning(value, cim_import_logger):
    busType = "unknown"
    # Set logging WARNING
    cim_import_logger.warning(
        "The bus type of "
        + value.name
        + " is not specified as it's voltage exceeds medium voltage."
    )


def coordinate_warning(ConfigData, cim_import_logger):
    # Set logging WARNING
    cim_import_logger.warning(
        "Invalid coordinate input format in "
        + next(iter(ConfigData.keys()))
        + ". Valid are 'GL', 'DL', or 'AI'."
    )
