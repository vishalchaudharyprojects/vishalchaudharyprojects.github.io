from pymodbus.client import ModbusTcpClient
from pyModbusTCP.utils import decode_ieee, word_list_to_long
from grid_measurements.libs.ie3_iec_61850_lib.iec_61850_ln import *
from grid_measurements.libs.ie3_iec_61850_lib.iec_61850_do import *
from grid_measurements.libs.ie3_iec_61850_lib.iec_61850_sdo import *
from grid_measurements.libs.ie3_iec_61850_lib.iec_61850_da import *
from grid_measurements.libs.ie3_iec_61850_lib.iec_61850_enum import *
from grid_measurements.src.connector.scd_handling import extract_bay_name
from loguru import logger
import time
import pandas as pd
import xml.etree.ElementTree as et
import logging
from grid_measurements.src.connector.handlers import data_object_handlers, default_handler


NAMESPACES = {"scl": "http://www.iec.ch/61850/2003/SCL"}


def parse_modbus_addresses(scd_communication_df: pd.DataFrame):
    """
    Parses a DataFrame with the following columns

    columns=[
    "IED name", "LN name", "DOI", "SDI 1", "SDI 2", "SDI 3",
    "DAI", "Register type", "No. Registers", "Word-Order", "Datatype", "Unit"

    to create a mapping of logical nodes to their Modbus addresses.

    :param scd_communication_df: Pandas DataFrame containing Modbus address mappings.
    :returns reference_to_register_mapping:  Dictionary with key as
    (LN name, DOI, SDI 1, SDI 2, SDI 3, DAI) and value as Modbus register info.
    """
    reference_to_register_mapping = {}

    for _, row in scd_communication_df.iterrows():
        ln_name = row["LN name"].strip()
        doi = row["DOI"].strip()
        sdi1 = row["SDI 1"].strip() if pd.notna(row["SDI 1"]) else None
        sdi2 = row["SDI 2"].strip() if pd.notna(row["SDI 2"]) else None
        sdi3 = row["SDI 3"].strip() if pd.notna(row["SDI 3"]) else None
        dai = row["DAI"].strip()

        address = int(row["No. Registers"])
        register_type = row["Register type"]
        word_order = row["Word-Order"]
        data_type = row["Datatype"]

        if data_type.lower() in {"int32", "uint32", "float"}:
            no_registers = 2
        elif data_type.lower() in {"int16", "uint16", "int8", "uint8"}:
            no_registers = 1
        else:
            raise ValueError(
                f"Unknown datatype for ln {ln_name}, data object {doi}, "
                f"subdataobjects {sdi1}, {sdi2}, {sdi3} and data attribute {dai}"
            )

        key = (ln_name, doi, sdi1, sdi2, sdi3, dai)
        reference_to_register_mapping[key] = {
            "register_type": register_type,
            "address":       address,
            "word_order":    word_order,
            "data_type":     data_type,
            "no_registers":  no_registers,
            "unit":          row["Unit"]
        }

    return reference_to_register_mapping


def read_modbus_data_from_ieds(scd_communication_df: pd.DataFrame, bus: str, scd_tree_root: et.Element):
    """
    Reads the SCD file, dynamically instantiates Logical Nodes,
    and reads Modbus communication settings.

    :param scd_tree_root: Root of the ElementTree representing the SCD file
    :param scd_communication_df: DataFrame containing SCL communication and reporting settings
    :param bus: Bus name, read from config
    :returns logical_nodes: List of logical nodes with data attributes filled from Modbus
    """
    # Define the scd_file_name
    scd_file_name = f"autoconfig_{bus}.scd"

    # Extract the data integration node dynamically
    data_integration_ied_name = extract_bay_name(scd_tree_root, "Data integration")

    reference_register_mapping = parse_modbus_addresses(scd_communication_df)
    logger.info(f"Mapped data attribute references for all ieds successfully to modbus registers")

    # assign unit IDs to Modbus servers
    ied_to_modbus_mapping = map_ied_name_to_modbus_comm(scd_tree_root, scd_file_name)

    # initialize a modbus tcp client for every IED
    modbus_tcp_clients = {}
    for ied_name, modbus_info in ied_to_modbus_mapping.items():
        # skip data integration ied
        if "Data integration" in ied_name:
            continue
        modbus_ip = modbus_info["ip"]
        modbus_port = modbus_info["port"]
        modbus_tcp_clients[ied_name] = [ModbusTcpClient(modbus_ip, port=modbus_port), "connected"]
        if not modbus_tcp_clients[ied_name][0].connect():
            logger.warning(f"Modbus-TCP connection to {modbus_tcp_clients[ied_name]} failed")
            modbus_tcp_clients[ied_name][1] = "disconnected"


    # read_modbus_registers and fill the logical nodes
    logical_nodes = read_registers_to_logical_nodes(modbus_tcp_clients,
                                                    reference_register_mapping,
                                                    scd_tree_root,
                                                    ied_to_modbus_mapping,
                                                    data_integration_ied_name)

    return logical_nodes


def map_ied_name_to_modbus_comm(scd_tree_root: et.Element, scd_file_name: str):
    """
    This function maps the IED name to the modbus information
    :param scd_tree_root: Root of the tree representing the SCD file
    :param scd_file_name: Name of the scd file including the information about IEDs and communication
    :returns ied_modbus_mapping: Dictionary mapping IED names to their Modbus information
    """
    # initialize output variables
    ied_modbus_mapping = {}
    # Iterate over all the IEDs in the Modbus-IP subnetwork
    for subnetwork in scd_tree_root.findall(".//scl:Communication/scl:SubNetwork[@type='Modbus-IP']", NAMESPACES):
        for connected_ap in subnetwork.findall("scl:ConnectedAP", NAMESPACES):
            ied_name = connected_ap.get("iedName")
            # initialize dictionary for this IED
            ied_modbus_mapping[ied_name] = {}
            # Data integration is not a modbus server, therefore don't proceed for that one.
            if "Data integration" in ied_name:
                continue
            # obtain the IP address and port of the Modbus server
            try:
                address = connected_ap.find("scl:Address", NAMESPACES)
                modbus_ip = address.find("scl:P[@type='tP_IP']", NAMESPACES).text
                modbus_port = int(address.find("scl:P[@type='PORT']", NAMESPACES).text)
                unit_id_element = address.find("scl:P[@type='Unit-ID']", NAMESPACES)
            except:
                raise FileNotFoundError(f"Modbus server not found in SCD file: {scd_file_name}")

            # parse unit it from elementtree element
            if unit_id_element is not None and unit_id_element.text is not None:
                modbus_unit_id = int(unit_id_element.text) if unit_id_element.text.isdigit() else None
            else:
                modbus_unit_id = None

            ied_modbus_mapping[ied_name]["unit-id"] = modbus_unit_id
            ied_modbus_mapping[ied_name]["ip"] = modbus_ip
            ied_modbus_mapping[ied_name]["port"] = modbus_port

    return ied_modbus_mapping


def read_registers_to_logical_nodes(modbus_tcp_clients,
                                    reference_register_mapping,
                                    scd_tree_root,
                                    ied_to_modbus_mapping,
                                    data_integration_ied_name):
    """
    This function iterates through all the IEDs that are reporting to data integration.
    Afterward, it initializes logical nodes for every LN in those IEDs and reads
    modbus registers for specific IEC 61850 common data classes

    :param modbus_tcp_clients: modbus tcp client instances for all IEDs
    :param reference_register_mapping: Mapping of IED -> LN -> DO -> SDO -> DA to registers
    :param scd_tree_root: Root of the tree representing the SCD file
    :param ied_to_modbus_mapping: Mapping of IED names to their Modbus information
    :param data_integration_ied_name: Name of the data integration IED

    :returns logical_nodes: List of logical nodes with data attributes filled from Modbus
    :returns read_data: Boolean indicating if data was read successfully
    """
    # todo: Only do the initialization ocne, think about if this is the best design?
    logical_nodes = {}
    read_data = False

    # iterate over all IEDs in order to obtain their values and map it to iec 61850
    for ied in scd_tree_root.findall(".//scl:IED", NAMESPACES):
        # reset/init logical_nodes for this IED
        logical_nodes_list = []
        ied_name = ied.get("name")
        # As Data integration is us, we have to skip it.
        if "Data integration" in ied_name:
            continue

        # Skip if IED is not in modbus_tcp_clients
        if ied_name not in modbus_tcp_clients:
            continue

        # if the server is not connected: Skip it for this run
        if modbus_tcp_clients[ied_name][1] == "disconnected":
            continue

        unit_id = ied_to_modbus_mapping[ied_name]["unit-id"]
        # Only iterate over IEDs that are already implemented
        if "iMSys" in ied_name or "dLSS bay" in ied_name or "EMS" in ied_name:
            if unit_id is not None:
                for rpt in ied.findall(".//scl:RptEnabled/scl:ClientLN", NAMESPACES):
                    if rpt.get("iedName") == data_integration_ied_name:
                        for ln in ied.findall(".//scl:LN", NAMESPACES):
                            ln_class = ln.get("lnClass")
                            ln_name = ln.get("prefix") + ln.get("lnClass")  # Logical Node instance name

                            # Dynamically instantiate the logical node class if it exists
                            ln_class_obj = globals().get(ln_class)
                            if ln_class_obj and isinstance(ln_class_obj, type):
                                logical_node = ln_class_obj()
                            else:
                                logical_node = LogicalNode(ln_id=ln.get("lnType"), ln_class=ln_class)

                            logical_node.ln_name = ln_name
                            logical_nodes_list.append(logical_node)

                            # Log the logical node details
                            logger.info(f"Appended logical Node: {ln_name} with class: {ln_class} to ied {ied_name}")

                            for do_name, do_obj in logical_node.DO.items():
                                # Log the data object details
                                logging.info(f"Data Object: {do_name} (Type: {do_obj.do_type})")

                                read_registers_to_data_attributes(ln_name,
                                                                  do_name,
                                                                  do_obj,
                                                                  reference_register_mapping,
                                                                  modbus_tcp_clients[ied_name][0],
                                                                  unit_id)
                                # indicates that data has been successfully read
                                read_data = True
        else:
            continue
        # füge dem IED alle LN hinzu
        logical_nodes[ied_name] = logical_nodes_list
        # close respective client connection
        modbus_tcp_clients[ied_name][0].close()
        # log the logical nodes for this IED
        logger.debug(f"Logical nodes for IED {ied_name} are {logical_nodes_list}")

    # return logical_nodes
    return logical_nodes, read_data

def read_registers_to_data_attributes(logical_node_name: str,
                                      data_object_name: str,
                                      data_object,
                                      iec_61850_ref_to_reg_map: dict,
                                      modbus_client,
                                      unit_id: int):
    """
    This function reads all the registers assigned to a given logical node reference and assigns them
    to the corresponding data attributes of the logical node.

    :param logical_node_name: Name of the logical node for which the registers are to be read
    :param data_object_name: Name of the data object for which the registers are to be read
    :param data_object: Data object instance from the ie3_iec61850_lib
    :param iec_61850_ref_to_reg_map: Mapping of IED -> LN -> DO -> SDO -> DA to registers
    :param modbus_client: Modbus TCP client instance for the IED
    :param unit_id: Unit ID of the Modbus server

    :returns dataobject: Data object instance with updated data attributes
    """

    handler = data_object_handlers.get(data_object.do_type, default_handler)
    reference_key = handler(logical_node_name, data_object_name, data_object)



    # iterate through all the values in reference key
    for key, value in reference_key.items():
        # get the modbus information for this register
        value_modbus_info = iec_61850_ref_to_reg_map.get(value)
        # if there is modbus information for this value:
        if value_modbus_info:
            value_address = value_modbus_info["address"]
            no_registers = value_modbus_info["no_registers"]
            unit = value_modbus_info.get("unit", "SI")
            # read the registers
            result = modbus_client.read_holding_registers(value_address,
                                                          count=no_registers,
                                                          slave=unit_id)

            if not result.isError():
                # Convert the register values to a floating-point number
                modbus_values = floating_value(result.registers)

                logger.info(
                    f"Read Modbus float Value for Logical Node {logical_node_name},"
                    f" Data Object {data_object_name} at register{value_address}: {modbus_values}")
                
                try:
                    if data_object.do_type == "DT_MV":
                        data_object.SDO["mag"].set_da("f", modbus_values)
                        data_object.SDO["q"].set_da("validity", Validity.GOOD)
                        data_object.SDO["units"].set_da("SIUnit", unit)

                    elif data_object.do_type == "DT_WYE":
                        data_object.SDO[key].SDO["cVal"].SDO2["mag"].set_da("f", modbus_values)
                        data_object.SDO[key].SDO["q"].set_da("validity", Validity.GOOD)
                        data_object.SDO[key].SDO["units"].set_da("SIUnit", unit)

                    else:
                        target = data_object.SDO[key]
                        if hasattr(target, "set_da"):
                            target.set_da("f", modbus_values)
                        else:
                            data_object.SDO[key] = modbus_values

                        if "q" in data_object.SDO:
                            data_object.SDO["q"].set_da("validity", Validity.GOOD)

                except Exception as e:
                    logger.error(f"Error setting DA for {value}: {e}")


            else:
                try:
                    if data_object.do_type == "DT_MV":
                        data_object.SDO["q"].set_da("validity", Validity.INVALID)
                    elif data_object.do_type == "DT_WYE":
                        data_object.SDO[key].SDO["q"].set_da("validity", Validity.INVALID)
                    elif "q" in data_object.SDO:
                        data_object.SDO["q"].set_da("validity", Validity.INVALID)
                except Exception as e:
                    logger.warning(f"Could not set INVALID status for {value}: {e}")

        else:
            logger.info(f"Modbus mapping of reference {value} to modbus-tcp-register not found")

    return


def floating_value(reg_amount):
    """
    Converts a list of register values into a floating-point number.

    This function takes a list of register values (`reg_amount`),
    processes each value using `word_list_to_long()`, and converts it
    into a floating-point number using `decode_ieee()`. The last
    converted value is returned.

    Args:
        reg_amount (list[int]): A list of register values.

    Returns:
        float: The floating-point representation of the last processed register value.
    """
    float_val = None
    for f in word_list_to_long(reg_amount):  # Convert register words to long integers
        float_val = decode_ieee(f)  # Decode the IEEE floating-point representation

    return float_val  # Return the last decoded floating-point value


