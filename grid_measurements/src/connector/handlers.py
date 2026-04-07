import logging
from grid_measurements.libs.ie3_iec_61850_lib import iec_61850_do

# Configure logger for this module
logger = logging.getLogger(__name__)

# Global dictionary to map DO types to their corresponding handler services
data_object_handlers = {}


def register_do_handler(do_type):
    """
    Decorator function to register a handler for a specific Data Object (DO) type.

    :param do_type: The type of the Data Object (e.g., DT_MV, DT_WYE)
    :return: Decorator that registers the handler function
    """
    def decorator(func):
        data_object_handlers[do_type] = func
        return func
    return decorator


# ----------- Handler Functions ----------- #

@register_do_handler("DT_MV")
def handle_mv(logical_node_name, data_object_name, data_object):
    """
    Handler for DO type 'DT_MV' (Measured Value). Maps to 'mag.f' path.

    :returns: Dictionary with reference key to data attributes
    """
    return {
        "mag": (logical_node_name, data_object_name, None, None, "mag", "f")
    }


@register_do_handler("DT_WYE")
def handle_wye(logical_node_name, data_object_name, data_object):
    """
    Handler for DO type 'DT_WYE' (Wye Connection).
    Maps each phase (phsA, phsB, phsC) to 'cVal.mag.f'.

    :returns: Dictionary mapping each phase to its measurement path
    """
    return {
        phase: (logical_node_name, data_object_name, phase, "cVal", "mag", "f")
        for phase in ["phsA", "phsB", "phsC"]
    }


@register_do_handler("DT_CMV")
@register_do_handler("DT_APC")
@register_do_handler("DT_SPS")
@register_do_handler("DT_INS")
@register_do_handler("DT_ASG")
@register_do_handler("DT_SPC")
@register_do_handler("DT_BCR")
@register_do_handler("DT_ING")
@register_do_handler("DT_ORG")
def handle_generic(logical_node_name, data_object_name, data_object):
    """
    Generic handler for various common DO types.
    Assumes a flat structure where each SDO might directly hold a 'f' DA.

    :returns: Dictionary mapping each SDO to its path ending in 'f'
    """
    return {
        da_name: (logical_node_name, data_object_name, None, None, da_name, "f")
        for da_name in data_object.SDO
        if isinstance(data_object.SDO[da_name], object)
    }


@register_do_handler("DT_SPG")
def handle_spg(logical_node_name, data_object_name, data_object):
    """
    Handler for 'DT_SPG' (Set Point Generic).
    Targets the 'setVal' parameter.

    :returns: Dictionary with reference to 'setVal'
    """
    return {
        "setVal": (logical_node_name, data_object_name, None, None, "setVal")
    }


@register_do_handler("DT_VSG")
def handle_vsg(logical_node_name, data_object_name, data_object):
    """
    Handler for 'DT_VSG' (Value Setting Generic).
    Targets the 'setVal' parameter.

    :returns: Dictionary with reference to 'setVal'
    """
    return {
        "setVal": (logical_node_name, data_object_name, None, None, "setVal")
    }


@register_do_handler("DT_TSG")
def handle_tsg(logical_node_name, data_object_name, data_object):
    """
    Handler for 'DT_TSG' (Time Setting Generic).
    Targets 'setTm' and 'setCal' fields.

    :returns: Dictionary with references to both parameters
    """
    return {
        "setTm": (logical_node_name, data_object_name, None, None, "setTm"),
        "setCal": (logical_node_name, data_object_name, None, None, "setCal")
    }


# ----------- Optional Fallback ----------- #

def default_handler(logical_node_name, data_object_name, data_object):
    """
    Fallback handler used when a specific DO type does not have a registered handler.
    Logs a warning and returns references for all available SDOs.

    :returns: Dictionary mapping each SDO to its reference path
    """
    logger.warning(f"Using default handler for {data_object.do_type}")
    return {
        da: (logical_node_name, data_object_name, None, None, da)
        for da in data_object.SDO
    }
