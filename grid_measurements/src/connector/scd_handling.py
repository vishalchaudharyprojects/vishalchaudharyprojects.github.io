from grid_measurements.src.connector.aas_interaction import read_scd_name_from_aas
import xml.etree.ElementTree as ET
import os
import pandas as pd
import requests
from dotenv import load_dotenv
from minio import Minio
from loguru import logger

# initialize a constant namespace
NAMESPACES = {"scl": "http://www.iec.ch/61850/2003/SCL"}
load_dotenv()
# load the variables
MINIO_IP = os.getenv("MINIO_IP")  # Should be something like 'http://minio:9000'
MINIO_PORT = os.getenv("MINIO_PORT")
MINIO_BUCKET_NAME = os.getenv("BUCKET_NAME")
API_URL = os.getenv("AAS_API_URL")

def extract_bay_name(root, name_segment):
    """
    This function extracts the name of a bay from the SCD tree
    that contains the input variable name_segment

    :param root: root of the element tree tree
    :param name_segment: Name segment that nees to be found
    :return name: Full name of the bay
    """
    name = None
    for bay in root.findall(".//scl:Bay", NAMESPACES):
        if name_segment in bay.get("name", ""):
            name = bay.get("name")
            break

    if name is None:
        logger.error(f"SCD file does not contain name with the segment {name_segment}")
        raise ValueError(f"Bay name segment '{name_segment}' not found in the SCD file.")
    return name



def parse_registers_from_scd(root):
    """
    Parses the SCD file to extract IED communication data for both Modbus and DLMS/COSEM protocols.
    Returns two DataFrames: one for Modbus registers and one for DLMS/COSEM connections.

    :param root: Root element of the SCD file XML tree
    :return: Tuple of (scd_communication_df, scd_dlms_df)
             - scd_communication_df: DataFrame with Modbus register information
             - scd_dlms_df: DataFrame with DLMS/COSEM connection information
    """
    # Initialize DataFrames for both protocols
    scd_communication_df = pd.DataFrame(
        columns=[
            "IED name", "LN name", "DOI", "SDI 1", "SDI 2", "SDI 3",
            "DAI", "Register type", "No. Registers", "Word-Order", "Datatype", "Unit"
        ]
    )

    scd_dlms_df = pd.DataFrame(
        columns=["IED name", "PORT", "Unit-ID", "AP Name", "SubNetwork"]
    )

    # Get the name of the data integration IED for reporting filtering
    data_integration_ied_name = extract_bay_name(root, "Data integration")

    # First parse all SubNetworks to identify protocol types
    for subnet in root.findall(".//scl:SubNetwork", NAMESPACES):
        subnet_type = subnet.get("type", "")
        subnet_name = subnet.get("name", "")

        for connected_ap in subnet.findall(".//scl:ConnectedAP", NAMESPACES):
            ied_name = connected_ap.get("iedName")
            ap_name = connected_ap.get("apName")

            address = connected_ap.find(".//scl:Address", NAMESPACES)
            ip = None
            port = None
            unit_id = "0"

            if address is not None:
                for p_elem in address.findall("scl:P", NAMESPACES):
                    p_type = p_elem.get("type", "")
                    if p_type == "tP_IP":
                        ip = p_elem.text
                    elif p_type == "PORT":
                        port = p_elem.text
                    elif p_type == "Unit-ID":
                        unit_id = p_elem.text

            # Handle Modbus-IP devices
            if subnet_type == "Modbus-IP" and ip:
                # Find the IED element for this connection
                ied = root.find(f'.//scl:IED[@name="{ied_name}"]', NAMESPACES)
                if ied is None:
                    continue

                # Check if this IED reports to our data integration IED
                reports_to_us = False
                for rpt in ied.findall(".//scl:RptEnabled/scl:ClientLN", NAMESPACES):
                    if rpt.get("iedName") in data_integration_ied_name:
                        reports_to_us = True
                        break

                if not reports_to_us:
                    continue

                # Parse Modbus registers for this IED
                for ln in ied.findall(".//scl:LN", NAMESPACES):
                    ln_name = ln.get("prefix", "") + ln.get("lnClass", "")

                    for doi in ln.findall(".//scl:DOI", NAMESPACES):
                        doi_name = doi.get("name")

                        # Parse units
                        unit = assign_si_unit(doi_name)  # Default
                        unit_sdi = doi.find('scl:SDI[@name="units"]', NAMESPACES)
                        if unit_sdi is not None:
                            si_unit_dai = unit_sdi.find('scl:DAI[@name="SIUnit"]/scl:Val', NAMESPACES)
                            multiplier_dai = unit_sdi.find('scl:DAI[@name="multiplier"]/scl:Val', NAMESPACES)
                            unit_parts = []
                            if si_unit_dai is not None:
                                unit_parts.append(si_unit_dai.text.strip())
                            if multiplier_dai is not None:
                                unit_parts.insert(0, multiplier_dai.text.strip())
                            unit = " ".join(unit_parts).strip()

                        # Parse register values
                        for sdi1 in doi.findall("scl:SDI", NAMESPACES):
                            sdi_chain = [sdi1.get("name")]
                            for sdi2 in sdi1.findall("scl:SDI", NAMESPACES):
                                sdi_chain.append(sdi2.get("name"))
                                for sdi3 in sdi2.findall("scl:SDI", NAMESPACES):
                                    sdi_chain.append(sdi3.get("name"))

                            if len(sdi_chain) == 1:
                                sdi_chain = [None, None, sdi_chain[0]]
                            elif len(sdi_chain) == 2:
                                sdi_chain = [None, sdi_chain[0], sdi_chain[1]]
                            elif len(sdi_chain) == 0:
                                sdi_chain = [None, None, None]

                            for dai in sdi1.findall(".//scl:DAI", NAMESPACES):
                                dai_name = dai.get("name")
                                saddr = dai.get("sAddr", "")

                                # Skip DAIs that are not tied to Modbus registers
                                if not saddr:
                                    continue

                                register_type = (
                                    "HoldingRegister" if "HoldingRegister" in saddr else "Unknown"
                                )
                                datatype = (
                                    saddr.split("T=")[-1].strip(")") if "T=" in saddr else "Unknown"
                                )
                                no_registers = (
                                    int(saddr.split("HoldingRegister=")[-1].split(";")[0])
                                    if "HoldingRegister=" in saddr else 0
                                )
                                word_order = "Little Endian" if "swap" in saddr else "Big Endian"

                                # Append to Modbus DataFrame
                                scd_communication_df = pd.concat(
                                    [scd_communication_df, pd.DataFrame([{
                                        "IED name": ied_name,
                                        "LN name": ln_name,
                                        "DOI": doi_name,
                                        "SDI 1": sdi_chain[0],
                                        "SDI 2": sdi_chain[1],
                                        "SDI 3": sdi_chain[2],
                                        "DAI": dai_name,
                                        "Register type": register_type,
                                        "No. Registers": no_registers,
                                        "Word-Order": word_order,
                                        "Datatype": datatype,
                                        "Unit": unit
                                    }])],
                                    ignore_index=True
                                )

            # Handle DLMS-COSEM devices
            elif subnet_type == "DLMS-COSEM" and port and not ip:
                scd_dlms_df = pd.concat([
                    scd_dlms_df,
                    pd.DataFrame([{
                        "IED name": ied_name,
                        "PORT": port,
                        "Unit-ID": unit_id,
                        "AP Name": ap_name,
                        "SubNetwork": subnet_name
                    }])
                ], ignore_index=True)

    if scd_communication_df.empty and scd_dlms_df.empty:
        logger.error("No communication data found in the SCD file.")
        raise ValueError("Communication segment of the SCD cannot be parsed. Abort execution.")

    return scd_communication_df, scd_dlms_df


def get_reference_from_asset():
    """
    # Todo: Document me!
    :return:
    """
    # HTTP-GET-Request an die URL senden
    response = requests.get(API_URL)

    # Überprüfen, ob der Request erfolgreich war
    if response.status_code == 200:
        # JSON-Daten aus der Antwort extrahieren
        data = response.json()

        # Werte aus dem JSON extrahieren
        param_url = data.get("Influxdb_Url")
        param_query = data.get("Influxdb_Query")
        param_token = data.get("Influxdb_Token")
        param_org = data.get("Influxdb_org")
        param_bucket = data.get("Influxdb_Bucket")
        param_scd = data.get("scd_file_name")

    return param_scd


def load_scd_tree(config):
    """
    This function reads a SCD file and extracts
    the ieds and their communication interfaces from them using the
    parse_scd function
    :param config: The configuration dictionary
    :returns scd_tree_root: Root of the element tree containing the parsed scd file
    :returns scd_file_name: Name of the scd file, either read from config or obtained by AAS server
    """
    # Build the path to the SCD file
    grid_name = config["DataIntegration"]["grid"]["name"]
    if config["DataIntegration"]["bus"]["information_source"] == "aas":
        logger.info("Data integration is started with AAS as source of information.")
        # get the AAS reference from the asset
        scd_file_name = read_scd_name_from_aas()
    elif config["DataIntegration"]["bus"]["information_source"] == "config":
        logger.info("Data integration is started with config as source of information.")
        bus = config["DataIntegration"]["bus"]["name"]
        scd_file_name = f"autoconfig_{bus}.scd"
    else:
        raise ValueError("Invalid information source for bus configuration.")

    # check if scd file name ends with xml and replace it by scd
    if scd_file_name.endswith(".xml"):
        scd_file_name = scd_file_name.replace(".xml", ".scd")

    # read the input configuration from the scd file
    if config["DataIntegration"]["grid"]["input_datasource"] == "s3":
        # get the scd file from s3 bucket
        logger.info(f"Load SCD file {scd_file_name} from S3 bucket")
        download_scd_file_from_s3(config, scd_file_name)

    # prepare parsing the SCD file
    scd_folder_path = os.path.join("grids", grid_name, "scd")
    scd_file_path = os.path.join(scd_folder_path, scd_file_name)

    # check if the scd file actually exists in the specified path
    if not os.path.exists(scd_file_path):
        raise FileNotFoundError(f"SCD file not found at {scd_file_path}")

    # parse the scd file
    scd_tree = ET.parse(scd_file_path)
    scd_tree_root = scd_tree.getroot()

    return scd_tree_root, scd_file_name


def download_scd_file_from_s3(config: dict, scd_file_name: str):
    """
    downloads the scd file from s3 bucket with specification of the given env file
    :param config: The configuration dictionary
    :param scd_file_name: The name of the SCD file to download
    :return: None
    """
    grid_name = config["DataIntegration"]["grid"]["name"]
    # Initialize the Minio client
    minio_client = Minio(
        endpoint=f"{MINIO_IP}:{MINIO_PORT}",
        access_key=os.getenv("ACCESS_KEY"),
        secret_key=os.getenv("SECRET_KEY"),
        secure=False
    )
    # specify the name of the object in the bucket
    remote_file_path = f"{grid_name}/{scd_file_name}"
    # specify the local path of the object
    local_file_path = os.path.join("grids", grid_name, "scd", scd_file_name)
    # create the directory for the scd file
    os.makedirs(os.path.join("grids", grid_name, "scd"), exist_ok=True)
    # List objects in the grid's folder
    objects = minio_client.list_objects(MINIO_BUCKET_NAME, prefix=grid_name, recursive=True)
    # initialize variable to see if an object has been found
    object_found = False
    # iterate through all the objects in objects
    for obj in objects:
        # if the correct object is found:
        if scd_file_name in obj.object_name:
            object_found = True
            # download the object
            minio_client.fget_object(bucket_name=MINIO_BUCKET_NAME,
                                     object_name=remote_file_path,
                                     file_path=local_file_path)
            break

    if object_found is False:
        raise FileNotFoundError(f"SCD file not found in S3 bucket {MINIO_BUCKET_NAME} under prefix {grid_name}")
    

def assign_si_unit(doi_name: str) -> str:
    """
    This is the function for assigning si units based on the data objects
    """
    si_unit = {
        'A': 'Ampere',
        'W': 'Watt',
        'PhV': 'Volt',
        'Var': 'Volt-Ampere Reactive',
        'TotVar': 'Volt-Ampere Reactive',
        'Hz': 'Hertz',
        'TotW': 'Watt',
    }
    
    return si_unit.get(doi_name, 'SI')

