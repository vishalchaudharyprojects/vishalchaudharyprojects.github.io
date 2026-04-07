# smart_grid_services/src/state_estimation/se_mapping.py
import logging
import pandas as pd
import re

logger = logging.getLogger("se_mapping")
logger.setLevel(logging.INFO)

# --- GLOBAL MAPPING (auto-filled later if requested) ---
IED_TO_EQUIPMENT = {}

BUS_MEASUREMENT_PATTERNS = ["phv", "voltage"]  # Lowercase


# =====================================================================================
#  AUTO-MAPPING BUILDER
# =====================================================================================
def build_auto_mapping(measurement_csv_path: str, grid_topology_df: "pd.DataFrame", grid_transformers_df: "pd.DataFrame" = None) -> dict:
    """
    Automatically infer IED-to-equipment mapping from measurement log and grid data.

    Args:
        measurement_csv_path: Path to measurement_log.csv
        grid_topology_df: DataFrame with ['name','node_i','node_j']
        grid_transformers_df: Optional DataFrame with ['name','hvBus','lvBus']

    Returns:
        dict: {ied_name: (element_type, element_name or None)}
    """
    mapping = {}

    try:
        df = pd.read_csv(measurement_csv_path)
    except Exception as e:
        logger.error(f"Could not read measurement CSV: {e}")
        return mapping

    if "ied_name" not in df.columns or "bus" not in df.columns:
        logger.error("measurement_log.csv missing required columns ['ied_name','bus']")
        return mapping

    for ied_name in df["ied_name"].dropna().unique():
        lname = ied_name.lower()

        # --- 1️⃣ Transformer connection ---
        if "transformer" in lname:
            bus_host = df[df["ied_name"] == ied_name]["bus"].iloc[0]
            trafo_name = None

            # Try to match with known transformers
            if grid_transformers_df is not None and not grid_transformers_df.empty:
                for _, row in grid_transformers_df.iterrows():
                    hv_bus = str(row.get("hvBus", ""))
                    lv_bus = str(row.get("lvBus", ""))
                    if bus_host in [hv_bus, lv_bus]:
                        trafo_name = str(row.get("name", None))
                        break

            if trafo_name:
                mapping[ied_name] = ("trafo", trafo_name)
            else:
                mapping[ied_name] = ("trafo", None)  # fallback
            continue

        # --- 2️⃣ Connected bus pattern ---
        match = re.search(r"connected\s+to\s+(LV\d+Bus\d+)", ied_name, re.IGNORECASE)
        if match:
            connected_bus = match.group(1)
            bus_host = df[df["ied_name"] == ied_name]["bus"].iloc[0]

            # Find line connecting the two buses
            if grid_topology_df is not None and not grid_topology_df.empty:
                cond = (
                    ((grid_topology_df["node_i"] == bus_host) & (grid_topology_df["node_j"] == connected_bus))
                    | ((grid_topology_df["node_i"] == connected_bus) & (grid_topology_df["node_j"] == bus_host))
                )
                line_match = grid_topology_df[cond]
                if not line_match.empty:
                    line_name = line_match.iloc[0]["name"]
                    mapping[ied_name] = ("line", line_name)
                    continue

        # --- 3️⃣ Fallback to bus measurement ---
        mapping[ied_name] = ("bus", None)

    logger.info(f"✅ Auto-built mapping with {len(mapping)} entries.")
    return mapping


def init_auto_mapping(measurement_csv_path: str, grid_topology_df: "pd.DataFrame", grid_transformers_df: "pd.DataFrame" = None):
    """
    Initializes the global IED_TO_EQUIPMENT mapping automatically.
    If auto-mapping fails, falls back to empty mapping.
    """
    global IED_TO_EQUIPMENT

    auto_map = build_auto_mapping(measurement_csv_path, grid_topology_df, grid_transformers_df)
    if auto_map:
        IED_TO_EQUIPMENT = auto_map
        logger.info(f"🔄 IED_TO_EQUIPMENT loaded from auto-mapping ({len(IED_TO_EQUIPMENT)} entries).")
    else:
        logger.warning("⚠️ Auto-mapping failed; no entries generated.")


# =====================================================================================
#  MEASUREMENT MAPPING LOGIC
# =====================================================================================
def get_measurement_details(mtype_str: str) -> tuple:
    """
    Parses a measurement string and returns (element_type, element_name, measurement_type).

    Args:
        mtype_str (str): "IED::LN.DO.FIELD" style measurement key

    Returns:
        tuple(str, str or None, str)
    """
    try:
        ied_name, meas_type_full = mtype_str.split("::", 1)
    except ValueError:
        logger.debug(f"Defaulting to BUS measurement (no '::'): {mtype_str}")
        return "bus", None, mtype_str.lower()

    meas_type_lower = meas_type_full.lower()

    # 1️⃣ Direct pattern check for bus measurements (voltage)
    for pattern in BUS_MEASUREMENT_PATTERNS:
        if pattern in meas_type_lower:
            return "bus", None, meas_type_lower

    # 2️⃣ Lookup IED mapping
    equipment_info = IED_TO_EQUIPMENT.get(ied_name)
    if equipment_info:
        el_type, el_name = equipment_info
        if el_type == "bus":
            return "bus", None, meas_type_lower
        return el_type, el_name, meas_type_lower

    # 3️⃣ Default fallback
    logger.warning(f"IED '{ied_name}' not in mapping. Defaulting to BUS measurement.")
    return "bus", None, meas_type_lower
