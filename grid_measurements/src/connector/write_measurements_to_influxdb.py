from dotenv import load_dotenv
from loguru import logger
from influxdb_client import InfluxDBClient, WritePrecision, Point
from datetime import datetime
import os

# Load environment variables from .env file
load_dotenv()

# Retrieve InfluxDB configuration from environment variables
INFLUX_URL = os.getenv("INFLUXDB_URL")
INFLUX_TOKEN = os.getenv("INFLUXDB_TOKEN")
INFLUX_ORG = os.getenv("INFLUXDB_ORG")
INFLUX_BUCKET = os.getenv("INFLUXDB_BUCKET")


def init_influxdb_client():
    """
    Initializes the InfluxDB client using credentials from environment variables.

    :returns: Tuple of (InfluxDBClient, write_api) for data writing.
    :raises ValueError: If any required credentials are missing.
    """
    load_dotenv()

    # Ensure required environment variables are set
    if not INFLUX_URL or not INFLUX_TOKEN or not INFLUX_ORG or not INFLUX_BUCKET:
        logger.error("Missing InfluxDB credentials in environment variables.")
        raise ValueError("Missing InfluxDB credentials in environment variables.")

    logger.info("InfluxDB credentials loaded successfully.")

    # Initialize client with no SSL verification
    client = InfluxDBClient(
        url=INFLUX_URL,
        token=INFLUX_TOKEN,
        org=INFLUX_ORG,
        verify_ssl=False
    )

    logger.info("Initialized InfluxDB client successfully.")

    # Create write API for high-precision writes
    write_api = client.write_api(writeOptions=WritePrecision.NS)

    return client, write_api


def write_ln_to_influx_db(logical_nodes: dict, grid_name: str, bus: str, write_api):
    """
    Writes IEC 61850 logical node data into an InfluxDB bucket.

    :param logical_nodes: Dictionary mapping IED names to their logical nodes
    :param grid_name: Name of the grid (used as Influx tag)
    :param bus: Bus name where the logical nodes are located (used as Influx tag)
    :param write_api: Instance of InfluxDB write API for pushing data
    :return: None
    """
    data_point = None  # Initialize data point for reuse

    for ied_name, ied_ln in logical_nodes.items():
        for logical_node in ied_ln:
            for do_name, do_obj in logical_node.DO.items():
                # Create the base measurement with tags
                data_point = (
                    Point("Data_integration")
                    .tag("grid_name", grid_name)
                    .tag("node_name", bus)
                    .tag("ied_name", ied_name)
                    .tag("ln_name", logical_node.ln_name)
                    .tag("do_name", do_name)
                    .time(datetime.utcnow(), WritePrecision.NS)
                )

                value_written = False  # Tracks if any value has been added to the point

                # Handle DT_MV (Measured Value)
                if do_obj.do_type == "DT_MV":
                    try:
                        value = do_obj.SDO["mag"].DA.get("f")
                        validity = do_obj.SDO["q"].DA.get("validity", "Unknown")
                        quality = str(validity.value if hasattr(validity, "value") else validity)
                        unit = do_obj.SDO["units"].DA.get("SIUnit", "Unknown")
                        if hasattr(unit, "name"):
                            unit = unit.name

                        if value is not None:
                            data_point = data_point.field(f"{do_name}_mag_f", value)
                            data_point = data_point.field(f"{do_name}_quality", quality)
                            data_point = data_point.field(f"{do_name}_unit", unit)
                            value_written = True
                    except Exception as e:
                        logger.error(f"Error processing DT_MV: {e}")

                # Handle DT_WYE (3-phase vector data)
                elif do_obj.do_type == "DT_WYE":
                    for phase in ["phsA", "phsB", "phsC"]:
                        try:
                            if phase in do_obj.SDO and "cVal" in do_obj.SDO[phase].SDO:
                                cval = do_obj.SDO[phase].SDO["cVal"]
                                value = cval.SDO2["mag"].DA.get("f")
                                validity = do_obj.SDO[phase].SDO["q"].DA.get("validity", "Unknown")
                                quality = str(validity.value if hasattr(validity, "value") else validity)
                                unit = do_obj.SDO[phase].SDO["units"].DA.get("SIUnit", "Unknown")

                                if hasattr(unit, "name"):
                                    unit = unit.name

                                if value is not None:
                                    data_point = data_point.field(f"{do_name}_{phase}_mag_f", value)
                                    data_point = data_point.field(f"{do_name}_{phase}_quality", quality)
                                    data_point = data_point.field(f"{do_name}_{phase}_unit", unit)
                                    value_written = True
                        except Exception as e:
                            logger.error(f"Error processing DT_WYE for phase {phase}: {e}")

                # Handle generic data objects or other types (e.g., DT_APC, TCTR, etc.)
                else:
                    try:
                        for sdo_name, sdo in do_obj.SDO.items():
                            if hasattr(sdo, "DA") and "f" in sdo.DA:
                                value = sdo.DA.get("f")
                                quality = "GOOD"  # Default quality
                                unit = "Unknown"

                                # Attempt to extract quality and unit fields if available
                                try:
                                    q_val = do_obj.SDO.get("q", {}).DA.get("validity", "GOOD")
                                    quality = str(q_val.value if hasattr(q_val, "value") else q_val)
                                except Exception:
                                    pass
                                try:
                                    u_val = do_obj.SDO.get("units", {}).DA.get("SIUnit", "Unknown")
                                    unit = u_val.name if hasattr(u_val, "name") else u_val
                                except Exception:
                                    pass

                                if value is not None:
                                    data_point = data_point.field(f"{do_name}_{sdo_name}_f", value)
                                    data_point = data_point.field(f"{do_name}_{sdo_name}_quality", quality)
                                    data_point = data_point.field(f"{do_name}_{sdo_name}_unit", unit)
                                    value_written = True
                    except Exception as e:
                        logger.error(f"Error processing generic DO {do_name}: {e}")

                # Write the point to InfluxDB if a value was added
                if value_written:
                    write_api.write(bucket=INFLUX_BUCKET, record=data_point)
                    logger.debug(
                        f"Written to InfluxDB: {ied_name}, LN: {logical_node.ln_name}, DO: {do_name}, Value: {value}"
                    )
