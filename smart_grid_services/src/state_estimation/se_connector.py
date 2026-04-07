# smart_grid_services/src/state_estimation/se_connector.py
from pathlib import Path
import xml.etree.ElementTree as ET
import pandas as pd
from typing import Dict, Any, List, Optional, Protocol
import logging
import sys

# --- New Imports ---
try:
    from influxdb_client import InfluxDBClient
    from influxdb_client.client.write_api import SYNCHRONOUS

    INFLUXDB_AVAILABLE = True
except ImportError:
    INFLUXDB_AVAILABLE = False

logger = logging.getLogger("se_connector")
logger.setLevel(logging.INFO)

if not INFLUXDB_AVAILABLE:
    logger.warning("influxdb_client not found. InfluxDBMeasurementConnector will not be available.")
    logger.warning("Please install with: pip install influxdb-client")

# --- Original NS and helper ---
NS = {
    "cim": "http://iec.ch/TC57/CIM100#",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
}


def _normalize_id(s: Optional[str]) -> Optional[str]:
    if s is None: return None
    return s.split('#')[-1].lstrip("_")


# --- CIMConnector (Unchanged) ---
class CIMConnector:
    """
    Minimal CIM reader that builds an element cache similar to the CIMEQToAASXConverter
    (used by your generator). It exposes connectivity nodes, terminals, and equipment.
    """

    def __init__(self, cim_eq_path: str):
        self.cim_eq_path = Path(cim_eq_path)
        if not self.cim_eq_path.exists():
            raise FileNotFoundError(f"CIM EQ file not found: {cim_eq_path}")
        self.tree = ET.parse(str(self.cim_eq_path))
        self.root = self.tree.getroot()
        self._element_cache: Dict[str, ET.Element] = {}
        self._build_element_cache()
        logger.info("CIMConnector initialized and element cache built.")

    def _build_element_cache(self):
        for elem in self.root.iter():
            elem_id = elem.get(f"{{{NS['rdf']}}}ID")
            if elem_id:
                self._element_cache[elem_id.lstrip("_")] = elem

    def find_all(self, tag_local: str) -> List[ET.Element]:
        return self.root.findall(f".//cim:{tag_local}", NS)

    def get_connected_equipment_for_node(self, node_id: str) -> List[Dict[str, str]]:
        """
        Return list of dicts: {id, name, type, terminal_id} for equipment connected to a node.
        Mirrors logic used in your converter (see cim_eq_to_aasx.py).
        """
        connected = []
        # find terminals referencing this node
        for t in self.root.findall(".//cim:Terminal", NS):
            node_ref = t.find("cim:Terminal.ConnectivityNode", NS)
            if node_ref is None:
                continue
            ref = node_ref.get(f"{{{NS['rdf']}}}resource") or node_ref.get("resource")
            ref = _normalize_id(ref)
            if ref is None:
                continue
            if ref == node_id or ref.lstrip("_") == node_id:
                # find conducting equipment ref
                eq_ref = t.find("cim:Terminal.ConductingEquipment", NS)
                eq_id = _normalize_id(eq_ref.get(f"{{{NS['rdf']}}}resource") if eq_ref is not None else None)
                if not eq_id:
                    continue
                elem = self._element_cache.get(eq_id) or self._element_cache.get(f"_{eq_id}")
                name = ""
                if elem is not None:
                    name_elem = elem.find("cim:IdentifiedObject.name", NS)
                    name = name_elem.text if name_elem is not None else eq_id
                connected.append({
                    "id": eq_id,
                    "name": name,
                    "type": elem.tag.split("}")[-1] if elem is not None else "Unknown",
                    "terminal_id": t.get(f"{{{NS['rdf']}}}ID", "") or ""
                })
        return connected

    def get_connectivity_nodes(self) -> List[str]:
        """Return list of all connectivity node IDs"""
        return [
            n.get(f"{{{NS['rdf']}}}ID").lstrip("_")
            for n in self.root.findall(".//cim:ConnectivityNode", NS)
            if n.get(f"{{{NS['rdf']}}}ID")
        ]

    def get_connectivity_node_name_map(self) -> Dict[str, str]:
        """
        Returns a mapping from CIM node ID → human-readable node name.
        Example: {'83063ed1-...': 'LV1101Bus2'}
        """
        mapping = {}
        for n in self.root.findall(".//cim:ConnectivityNode", NS):
            node_id = n.get(f"{{{NS['rdf']}}}ID")
            name_elem = n.find("cim:IdentifiedObject.name", NS)
            node_name = name_elem.text if name_elem is not None else node_id
            if node_id:
                mapping[node_id.lstrip("_")] = node_name
        return mapping


# --- NEW: MeasurementSource Protocol ---
class MeasurementSource(Protocol):
    """
    Defines the interface for any measurement source (CSV, InfluxDB, etc.)
    Any class that implements these methods can be used by the StateEstimationConnector.
    """

    def latest_by_bus(self) -> Dict[str, Dict[str, Any]]:
        """
        Returns raw measurements grouped by human-readable bus name.
        { bus_name: { measurement_name: {"value": v, "timestamp": t}, ... } }
        """
        ...

    def latest_by_node(self, connector: CIMConnector) -> Dict[str, Dict]:
        """
        Returns measurements mapped to CIM Connectivity Node IDs.
        { node_id: { measurement_name: {"value": v, "timestamp": t}, ... } }
        """
        ...


# --- Original MeasurementsStore (now implements MeasurementSource) ---
class MeasurementsStore:
    """
    Reads measurements_log.csv and returns latest values per bus (connectivity node).
    This class implements the MeasurementSource protocol.
    """

    def __init__(self, csv_path: str, timestamp_col: str = "timestamp_utc"):
        self.csv_path = Path(csv_path)
        if not self.csv_path.exists():
            raise FileNotFoundError(f"Measurements CSV not found: {csv_path}")
        self.timestamp_col = timestamp_col
        self.df = pd.read_csv(self.csv_path, parse_dates=[self.timestamp_col])
        logger.info(f"✅ Loaded {len(self.df)} measurement rows from {self.csv_path}")
        logger.info(f"Columns detected: {self.df.columns.tolist()}")

    def latest_by_bus(self) -> Dict[str, Dict[str, Any]]:
        """
        Groups measurements by bus (CIM node ID) and signal name.
        Returns:
          { bus: { measurement_name: {"value": v, "timestamp": t}, ... } }
        where measurement_name = f"{ied_name}::{ln_name}.{do_name}.{field_name}"
        """
        if self.df.empty:
            return {}

        df_sorted = self.df.sort_values(self.timestamp_col)

        # --- THIS IS THE ONLY CHANGE ---
        # Prepend the IED name to make the measurement name unique
        df_sorted["measurement_name"] = (
                df_sorted["ied_name"].astype(str) + "::" +  # <--- ADD THIS
                df_sorted["ln_name"].astype(str) + "." +
                df_sorted["do_name"].astype(str) + "." +
                df_sorted["field_name"].astype(str)
        )
        # --- END OF CHANGE ---

        last = df_sorted.groupby(["bus", "measurement_name"]).last().reset_index()

        result: Dict[str, Dict[str, Any]] = {}
        for _, row in last.iterrows():
            bus = str(row["bus"])
            meas = str(row["measurement_name"])
            val = row["value"]
            ts = row[self.timestamp_col]
            result.setdefault(bus, {})[meas] = {"value": val, "timestamp": ts}
        return result

    def latest_by_node(self, connector: CIMConnector) -> Dict[str, Dict]:
        """
        Match measurements to CIM nodes based on bus names, using relaxed normalization.
        """
        all_meas = self.latest_by_bus()
        node_name_map = connector.get_connectivity_node_name_map()

        def normalize_name(name: str) -> str:
            if not name:
                return ""
            # More aggressive normalization to handle different naming conventions
            name = name.lower()
            # Remove spaces, dots, underscores, dashes
            name = name.replace(" ", "").replace(".", "").replace("_", "").replace("-", "")
            # Handle common patterns like "LV1.101 Bus 4" -> "lv1101bus4"
            if "bus" in name:
                # Extract bus number and format consistently
                import re
                match = re.search(r'(lv|mv)(\d+)bus(\d+)', name)
                if match:
                    voltage = match.group(1)
                    grid_num = match.group(2)
                    bus_num = match.group(3)
                    name = f"{voltage}{grid_num}bus{bus_num}"
            return name

        # Precompute normalized bus names from measurements
        normalized_meas = {normalize_name(k): v for k, v in all_meas.items()}

        node_measurements: Dict[str, Dict] = {}
        for node_id, node_name in node_name_map.items():
            nname = normalize_name(node_name)
            if nname in normalized_meas:
                node_measurements[node_id] = normalized_meas[nname]
            else:
                node_measurements[node_id] = {}  # Add node even if no measurements
        return node_measurements


# --- NEW: InfluxDBMeasurementConnector (also implements MeasurementSource) ---
class InfluxDBMeasurementConnector:
    """
    Reads latest measurements from InfluxDB.
    This class implements the MeasurementSource protocol.
    """

    def __init__(self, url: str, token: str, org: str, bucket: str,
                 measurement_name: str, range_start: str = "-1h"):
        if not INFLUXDB_AVAILABLE:
            raise ImportError("InfluxDB client is not installed. Cannot create InfluxDBMeasurementConnector.")
        try:
            self.client = InfluxDBClient(url=url, token=token, org=org)
            self.query_api = self.client.query_api()
            self.bucket = bucket
            self.org = org
            self.measurement_name = measurement_name
            self.range_start = range_start

            if not self.client.health().status == "pass":
                raise Exception("InfluxDB health check failed.")
            logger.info(f"✅ Connected to InfluxDB at {url}, bucket '{bucket}'")
        except Exception as e:
            logger.error(f"❌ Failed to connect to InfluxDB: {e}")
            raise

    def latest_by_bus(self) -> Dict[str, Dict[str, Any]]:
        """
        Queries InfluxDB for the last value of each measurement, grouped by 'bus' tag
        and measurement name (field).

        Returns:
          { bus_name: { measurement_name: {"value": v, "timestamp": t}, ... } }
        """
        # This Flux query assumes:
        # 1. You have a tag named 'bus' (containing the human-readable name, e.g., 'LV1101Bus2').
        # 2. The measurement value is in '_value' and the name is in '_field'.
        flux_query = f'''
        from(bucket: "{self.bucket}")
          |> range(start: {self.range_start}) 
          |> filter(fn: (r) => r._measurement == "{self.measurement_name}") 
          |> filter(fn: (r) => exists r.bus)
          |> group(by: ["bus", "_field"])
          |> last()
          |> yield(name: "last_per_bus")
        '''

        logger.info(f"Querying InfluxDB for latest measurements (measurement: {self.measurement_name})...")
        try:
            result_tables = self.query_api.query(flux_query, org=self.org)
        except Exception as e:
            logger.error(f"InfluxDB query failed: {e}")
            return {}

        result: Dict[str, Dict[str, Any]] = {}
        for table in result_tables:
            for record in table.records:
                bus = record.values.get("bus")
                meas = record.values.get("_field")  # e.g., "MMXU.PhV.phsA"
                val = record.values.get("_value")
                ts = record.values.get("_time")

                if not all([bus, meas, val is not None, ts]):
                    continue

                measurement_name = str(meas)
                result.setdefault(str(bus), {})[measurement_name] = {"value": val, "timestamp": ts}

        logger.info(f"Retrieved {sum(len(v) for v in result.values())} latest measurement points.")
        return result

    def latest_by_node(self, connector: CIMConnector) -> Dict[str, Dict]:
        """
        Match measurements to CIM nodes based on bus names, using relaxed normalization.
        (This logic is identical to MeasurementsStore)
        """
        all_meas = self.latest_by_bus()
        node_name_map = connector.get_connectivity_node_name_map()

        def normalize_name(name: str) -> str:
            if not name:
                return ""
            # More aggressive normalization to handle different naming conventions
            name = name.lower()
            # Remove spaces, dots, underscores, dashes
            name = name.replace(" ", "").replace(".", "").replace("_", "").replace("-", "")
            # Handle common patterns like "LV1.101 Bus 4" -> "lv1101bus4"
            if "bus" in name:
                # Extract bus number and format consistently
                import re
                match = re.search(r'(lv|mv)(\d+)bus(\d+)', name)
                if match:
                    voltage = match.group(1)
                    grid_num = match.group(2)
                    bus_num = match.group(3)
                    name = f"{voltage}{grid_num}bus{bus_num}"
            return name

        normalized_meas = {normalize_name(k): v for k, v in all_meas.items()}

        node_measurements: Dict[str, Dict] = {}
        for node_id, node_name in node_name_map.items():
            nname = normalize_name(node_name)
            if nname in normalized_meas:
                node_measurements[node_id] = normalized_meas[nname]
            else:
                node_measurements[node_id] = {}  # Add node even if no measurements
        return node_measurements


# --- NEW: Unified StateEstimationConnector ---
class StateEstimationConnector:
    """
    Holds both CIM topology and a MeasurementSource.
    This class is agnostic to whether the measurements come from CSV or InfluxDB.
    """

    def __init__(self, cim_connector: CIMConnector, measurement_source: MeasurementSource):
        self.cim = cim_connector
        self.measurements = measurement_source
        self._node_measurements = None
        self._node_name_map = None
        logger.info(f"StateEstimationConnector initialized with {measurement_source.__class__.__name__}.")

    def get_node_measurements(self) -> Dict[str, Dict]:
        """
        Get latest measurements mapped to CIM Connectivity Node IDs.
        """
        if self._node_measurements is None:
            logger.info("Fetching and mapping node measurements...")
            self._node_measurements = self.measurements.latest_by_node(self.cim)
        return self._node_measurements

    def get_connectivity_nodes(self) -> List[str]:
        """Helper to get all node IDs from CIM."""
        return self.cim.get_connectivity_nodes()

    def get_node_name_map(self) -> Dict[str, str]:
        """Helper to get node ID -> name map from CIM."""
        if self._node_name_map is None:
            self._node_name_map = self.cim.get_connectivity_node_name_map()
        return self._node_name_map


# --- Original Helper (Unchanged) ---
def build_node_target_mapping(connector: CIMConnector, target_attribute: str = "asset_mrid") -> Dict[str, List[str]]:
    """
    Build a mapping node_id -> list of asset ids that are connected to that node.
    This is a simple mapping that uses get_connected_equipment_for_node (see converter for guidance).
    """
    mapping: Dict[str, List[str]] = {}
    for node in connector.get_connectivity_nodes():
        connected = connector.get_connected_equipment_for_node(node)
        mapping[node] = [c["id"] for c in connected]
    return mapping


# --- Original Debug Block (Unchanged) ---
if __name__ == "__main__":
    # This block now only demonstrates the CSV path
    cim_path = r"/app/Grids/1-LV-rural1--2-no_sw_EV_HP/CIM3/20151231T2300Z_YYY_EQ_.xml"
    csv_path = r"/app/Grids/1-LV-rural1--2-no_sw_EV_HP/measurements_log.csv"

    try:
        cim_conn = CIMConnector(cim_path)

        # --- Example of using the CSV store ---
        csv_measurement_source = MeasurementsStore(csv_path)

        # --- Example of creating the unified connector ---
        # se_main.py will do this based on config
        connector = StateEstimationConnector(cim_conn, csv_measurement_source)

        mapping = build_node_target_mapping(cim_conn)
        node_m = connector.get_node_measurements()  # Use the unified connector

        print("✅ CIM parsed successfully.")
        print(f"Number of connectivity nodes: {len(connector.get_connectivity_nodes())}")
        print(f"Sample node measurements (first 5):")

        count = 0
        for k, v in node_m.items():
            if count < 5:
                print(f"{k} → {v}")
                count += 1
            else:
                break

    except FileNotFoundError as e:
        logger.error(f"Error in __main__ debug: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")