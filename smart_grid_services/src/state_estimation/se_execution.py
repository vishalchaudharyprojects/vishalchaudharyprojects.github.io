# smart_grid_services/src/state_estimation/se_execution.py
import logging
import numpy as np
from typing import Tuple, Dict, List

# --- NEW IMPORT ---
logger = logging.getLogger("se_execution")
try:
    from state_estimation.se_mapping import get_measurement_details
    logger.info("Imported se_mapping for advanced measurement logic.")
except ImportError:
    # Fallback for relative import issues if run standalone
    try:
        from state_estimation.se_mapping import get_measurement_details
        logger.info("Imported se_mapping for advanced measurement logic.")
    except ImportError as e:
        logger.error(f"Could not import se_mapping: {e}")
        raise

logger = logging.getLogger("se_execution")

# Import pandapower (required now)
try:
    import pandapower as pp
    import pandapower.estimation

    PANDAPOWER_AVAILABLE = True
    logger.info("pandapower available - using for WLS state estimation.")
except ImportError as e:
    logger.error("pandapower is required but not available. Please install it.")
    raise e

# Add near the top of se_execution.py
def _safe_create_measurement(pp_net, m_type, element_type, element, value, std_dev, side=None):
    """Create measurement only if not already defined for same element/type."""
    df = pp_net.measurement
    exists = ((df["type"] == m_type) &
              (df["element_type"] == element_type) &
              (df["element"] == element)).any()
    if not exists:
        pp.create_measurement(pp_net, m_type, element_type, element, value, std_dev, side=side)
        logger.info(f"Added {m_type.upper()} ({element_type}) measurement at {element_type} {element}: {value}")
    else:
        logger.debug(f"Duplicate {m_type.upper()} measurement skipped for {element_type} {element}")


def run_pandapower_estimation(
        net: "pp.Net",
        z: np.ndarray,
        index_map: List[tuple],
        node_list: List[str]
) -> Dict:
    """
    Performs a WLS state estimation using pandapower.
    """
    # Debug first
    debug_network_and_measurements(net, z, index_map)

    # --- CREATE MAPPINGS FOR ALL ELEMENT TYPES ---
    # Get a mapping from CIM Node ID -> pandapower bus index
    pp_bus_map = {name: idx for idx, name in net.bus['name'].items()}
    logger.info(f"PP bus map sample: {list(pp_bus_map.items())[:3]}")

    # Get a mapping from CIM Line Name -> pandapower line index
    # **This assumes your CIM converter saves the line name in net.line.name**
    pp_line_map = {name: idx for idx, name in net.line['name'].items()}
    logger.info(f"PP line map sample: {list(pp_line_map.items())[:3]}")

    # Get a mapping from CIM Trafo Name -> pandapower trafo index
    pp_trafo_map = {name: idx for idx, name in net.trafo['name'].items()}
    logger.info(f"PP trafo map sample: {list(pp_trafo_map.items())[:3]}")

    # Clear any existing measurements
    net.measurement = net.measurement.iloc[0:0]

    # Use relative error (e.g., 2%)
    relative_error_percent = 2.0
    min_std_dev_p_q = 1e-5  # 0.00001 MW/MVAr (10W)
    min_std_dev_v = 1e-4

    measurement_count = 0
    power_measurements_added = 0
    voltage_measurements_added = 0
    line_measurements_added = 0
    trafo_measurements_added = 0

    # --- START: REPLACEMENT OF MEASUREMENT LOOP ---

    for i, (node_id, mtype_str) in enumerate(index_map):
        meas_value_raw = z[i]  # This is in W, VAr, or Volts

        # Get the mapping details
        # el_type = "bus", "line", or "trafo"
        # el_name = CIM name (e.g., "LV1101Line3") or None
        # mtype = lowercase measurement type (e.g., "q01_mmxu.totw...")
        el_type, el_name, mtype = get_measurement_details(mtype_str)

        # This is the CIM Node ID of the bus where the IED is physically located
        meas_bus_idx = pp_bus_map.get(node_id)
        if meas_bus_idx is None:
            logger.warning(f"CIM Node ID '{node_id}' not found in pandapower net. Skipping.")
            continue

        # --- BRANCH 1: BUS MEASUREMENTS (P, Q, or V) ---
        if el_type == "bus":
            bus_idx = meas_bus_idx  # The element is the bus itself

            # Active Power (P) Injection
            if "totw" in mtype or "w" in mtype:
                value_mw = meas_value_raw / 1e6  # Convert W to MW
                std_dev = max(abs(value_mw * (relative_error_percent / 100.0)), min_std_dev_p_q)
                pp.create_measurement(net, "p", "bus", value_mw, std_dev, bus_idx, name=mtype_str)
                power_measurements_added += 1
                logger.info(f"Added P (Bus) measurement at bus {bus_idx}: {value_mw:.6f} MW")

            # Reactive Power (Q) Injection
            elif "totvar" in mtype or "var" in mtype:
                value_mvar = meas_value_raw / 1e6  # Convert VAr to MVAr
                std_dev = max(abs(value_mvar * (relative_error_percent / 100.0)), min_std_dev_p_q)
                pp.create_measurement(net, "q", "bus", value_mvar, std_dev, bus_idx, name=mtype_str)
                power_measurements_added += 1
                logger.info(f"Added Q (Bus) measurement at bus {bus_idx}: {value_mvar:.6f} MVAr")

            # Voltage (V) Magnitude
            elif "phv" in mtype or "voltage" in mtype:
                bus_vn_kv = net.bus.at[bus_idx, 'vn_kv']  # Base voltage in kV (e.g., 0.4 or 20.0)
                base_v_v = bus_vn_kv * 1000  # Base voltage in Volts (e.g., 400 or 20000)
                if bus_vn_kv < 1.0:
                    base_v_v = base_v_v / np.sqrt(3)  # e.g., 400V / 1.732 = 230.9V

                value_pu = meas_value_raw / base_v_v

                std_dev = max(abs(value_pu * 0.005), min_std_dev_v)  # 0.5% error
                pp.create_measurement(net, "v", "bus", value_pu, std_dev, bus_idx, name=mtype_str)
                voltage_measurements_added += 1
                logger.info(
                    f"Added V (Bus) measurement at bus {bus_idx}: {value_pu:.6f} p.u. (Raw: {meas_value_raw}V, Base: {base_v_v:.1f}V)")

            measurement_count += 1
            continue

        # --- BRANCH 2: LINE MEASUREMENTS (P or Q) ---
        elif el_type == "line":
            line_idx = pp_line_map.get(el_name)
            if line_idx is None:
                logger.warning(f"Line '{el_name}' (from IED) not in pandapower net. Skipping.")
                continue

            # Determine measurement side ('from' or 'to')
            from_bus = net.line.at[line_idx, 'from_bus']
            to_bus = net.line.at[line_idx, 'to_bus']
            side = None
            if from_bus == meas_bus_idx:
                side = "from"
            elif to_bus == meas_bus_idx:
                side = "to"

            if side is None:
                logger.warning(
                    f"Meas. at bus {meas_bus_idx} doesn't match line '{el_name}' buses ({from_bus}, {to_bus}). Skipping.")
                continue

            # Active Power (P) Flow
            if "totw" in mtype or "w" in mtype:
                value_mw = meas_value_raw / 1e6
                std_dev = max(abs(value_mw * (relative_error_percent / 100.0)), min_std_dev_p_q)
                # --- CORRECTED LINE ---
                pp.create_measurement(
                    net, meas_type="p", element_type="line",
                    value=value_mw, std_dev=std_dev, element=line_idx,
                    side=side, name=mtype_str
                )
                line_measurements_added += 1
                logger.info(
                    f"Added P (Line) measurement at line {line_idx} ({el_name}), side {side}: {value_mw:.6f} MW")

                # Reactive Power (Q) Flow
            elif "totvar" in mtype or "var" in mtype:
                value_mvar = meas_value_raw / 1e6
                std_dev = max(abs(value_mvar * (relative_error_percent / 100.0)), min_std_dev_p_q)
                # --- CORRECTED LINE ---
                pp.create_measurement(
                    net, meas_type="q", element_type="line",
                    value=value_mvar, std_dev=std_dev, element=line_idx,
                    side=side, name=mtype_str
                )
                line_measurements_added += 1
                logger.info(
                    f"Added Q (Line) measurement at line {line_idx} ({el_name}), side {side}: {value_mvar:.6f} MVAr")

            measurement_count += 1
            continue

        # --- BRANCH 3: TRANSFORMER MEASUREMENTS (P or Q) ---
        elif el_type == "trafo":
            trafo_idx = pp_trafo_map.get(el_name)
            if trafo_idx is None:
                logger.warning(f"Trafo '{el_name}' (from IED) not in pandapower net. Skipping.")
                continue

            # Determine measurement side ('hv' or 'lv')
            hv_bus = net.trafo.at[trafo_idx, 'hv_bus']
            lv_bus = net.trafo.at[trafo_idx, 'lv_bus']
            side = None
            if hv_bus == meas_bus_idx:
                side = "hv"
            elif lv_bus == meas_bus_idx:
                side = "lv"

            if side is None:
                logger.warning(
                    f"Meas. at bus {meas_bus_idx} doesn't match trafo '{el_name}' buses ({hv_bus}, {lv_bus}). Skipping.")
                continue

            # Active Power (P) Flow
            if "totw" in mtype or "w" in mtype:
                value_mw = meas_value_raw / 1e6
                std_dev = max(abs(value_mw * (relative_error_percent / 100.0)), min_std_dev_p_q)
                # --- CORRECTED LINE ---
                pp.create_measurement(
                    net, meas_type="p", element_type="trafo",
                    value=value_mw, std_dev=std_dev, element=trafo_idx,
                    side=side, name=mtype_str
                )
                trafo_measurements_added += 1
                logger.info(
                    f"Added P (Trafo) measurement at trafo {trafo_idx} ({el_name}), side {side}: {value_mw:.6f} MW")

                # Reactive Power (Q) Flow
            elif "totvar" in mtype or "var" in mtype:
                value_mvar = meas_value_raw / 1e6
                std_dev = max(abs(value_mvar * (relative_error_percent / 100.0)), min_std_dev_p_q)
                # --- CORRECTED LINE ---
                pp.create_measurement(
                    net, meas_type="q", element_type="trafo",
                    value=value_mvar, std_dev=std_dev, element=trafo_idx,
                    side=side, name=mtype_str
                )
                trafo_measurements_added += 1
                logger.info(
                    f"Added Q (Trafo) measurement at trafo {trafo_idx} ({el_name}), side {side}: {value_mvar:.6f} MVAr")

            measurement_count += 1
            continue

    # --- END: REPLACEMENT OF MEASUREMENT LOOP ---

    logger.info(f"Total measurements created: {measurement_count}")
    logger.info(f"Bus Power measurements (P/Q): {power_measurements_added}")
    logger.info(f"Bus Voltage measurements (V): {voltage_measurements_added}")
    logger.info(f"Line measurements (P/Q): {line_measurements_added}")
    logger.info(f"Trafo measurements (P/Q): {trafo_measurements_added}")
    logger.info(f"Pandapower measurement table contains {len(net.measurement)} entries.")

    if len(net.measurement) == 0:
        logger.error("No valid measurements were mapped to the pandapower net.")
        return {"error": "No measurements mapped.", "converged": False}

    # Check if we have enough measurements for observability
    required_measurements = 2 * len(net.bus) - 1  # Basic observability requirement
    if len(net.measurement) < required_measurements:
        logger.warning(
            f"Measurement count ({len(net.measurement)}) may be insufficient for {len(net.bus)} buses (ideally need ~{required_measurements})")

    # ... (rest of the function from line 136 is unchanged) ...
    # --- Run the WLS Estimation ---
    logger.info(f"Running pandapower WLS with {len(net.measurement)} measurements...")
    try:
        # Try with different initialization and tolerance
        success = pp.estimation.estimate(
            net,
            algorithm="wls",
            init="flat",
            tolerance=1e-4,
            maximum_iterations=50
        )

        if not success:
            # Try with slack bus measurement as fallback
            logger.info("First attempt failed, trying with slack bus pseudo-measurement...")

            # Add voltage measurement at slack bus
            slack_buses = net.ext_grid.bus.values
            if len(slack_buses) > 0:
                pp.create_measurement(
                    net=net,
                    meas_type="v",
                    element_type="bus",
                    value=1.0,  # 1.0 p.u.
                    std_dev=0.01,  # 1% error
                    element=slack_buses[0]
                )
                logger.info(f"Added slack bus voltage measurement at bus {slack_buses[0]}")

            success = pp.estimation.estimate(
                net,
                algorithm="wls",
                init="flat",
                tolerance=1e-4,
                maximum_iterations=50
            )

        if not success:
            return {
                "error": "pandapower.estimation.estimate() failed to converge.",
                "converged": False
            }

        logger.info("WLS estimation successful.")

        # Extract results
        res = {
            "converged": True,
            "vm_pu": net.res_bus_est.vm_pu.to_dict(),
            "va_degree": net.res_bus_est.va_degree.to_dict(),
            "measurements_used": len(net.measurement)
        }

        # Add bus names for better readability
        bus_names = {}
        for bus_idx in res['vm_pu'].keys():
            bus_names[bus_idx] = net.bus.at[bus_idx, 'name']
        res['bus_names'] = bus_names

        return res

    except Exception as e:
        logger.error(f"Pandapower WLS estimation failed: {e}", exc_info=True)
        return {
            "error": str(e),
            "converged": False,
            "measurements_count": len(net.measurement),
            "buses_count": len(net.bus),
            "lines_count": len(net.line)
        }


def debug_network_and_measurements(net: "pp.Net", z: np.ndarray, index_map: List[tuple]):
    """Debug function to check network and measurement setup"""
    logger.info("=== NETWORK DEBUG INFO ===")

    # Check network connectivity
    logger.info(f"Buses: {len(net.bus)}")
    logger.info(f"Lines: {len(net.line)}")
    logger.info(f"Transformers: {len(net.trafo)}")
    logger.info(f"External grids: {len(net.ext_grid)}")

    # Check bus voltage levels
    logger.info("Bus voltage levels:")
    for idx, bus in net.bus.iterrows():
        logger.info(f"  Bus {idx}: vn_kv={bus['vn_kv']}, name={bus['name']}")

    # Check if network is connected
    try:
        import pandapower.topology as top
        mg = top.create_nxgraph(net)
        connected_components = list(top.connected_components(mg))
        logger.info(f"Number of connected components: {len(connected_components)}")
        if len(connected_components) > 1:
            logger.warning("Network has multiple connected components - this can cause convergence issues!")
    except:
        pass

    # Check measurements
    logger.info(f"Measurements in net: {len(net.measurement)}")
    if len(net.measurement) > 0:
        logger.info("Measurement types:")
        for idx, meas in net.measurement.iterrows():
            logger.info(f"  {idx}: {meas['measurement_type']} at bus {meas['element']}, value={meas['value']:.6f}")

    logger.info(f"Input measurements: {len(z)}")
    logger.info("=== END DEBUG INFO ===")


def run_state_estimation(
        node_list: List[str],
        z: np.ndarray,
        index_map: List[tuple],
        pandapower_net: "pp.Net"  # Required parameter now
) -> Dict:
    """
    High-level runner: uses only pandapower WLS estimation.

    Args:
        node_list: List of CIM node IDs
        z: Measurement vector
        index_map: Mapping of measurements to nodes/types
        pandapower_net: Pandapower network

    Returns:
        Dictionary with state estimation results
    """
    if pandapower_net is None:
        raise ValueError("Pandapower network is required but was not provided")

    return run_pandapower_estimation(pandapower_net, z, index_map, node_list)