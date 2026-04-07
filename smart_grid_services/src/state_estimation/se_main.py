import logging
import yaml
from pathlib import Path
try:
    from state_estimation.se_connector import (
        CIMConnector,
        InfluxDBMeasurementConnector,
        MeasurementsStore,
        StateEstimationConnector,
        INFLUXDB_AVAILABLE
    )
    from state_estimation.se_processor import prepare_state_estimation_inputs
    from state_estimation.se_execution import run_state_estimation
    from state_estimation.se_mapping import init_auto_mapping
except ImportError as e:
    print(f"Import error: {e}")

import pandapower as pp

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

PANDAPOWER_AVAILABLE = True

# Adjust path if your config is not in the parent dir
CONFIG_PATH = Path(__file__).parent.parent.parent / "config_se.yaml"
logger.info(f"Attempting to load config from: {CONFIG_PATH.resolve()}")


def load_config(path: Path) -> dict:
    """Loads the state estimation config YAML."""
    if not path.exists():
        logger.error(f"Config file not found: {path}")
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path, 'r') as f:
        config = yaml.safe_load(f)
    logger.info("Configuration loaded.")
    return config


# --- THIS FUNCTION IS MODIFIED ---
def load_se_connector(config: dict, pandapower_net: "pp.Net") -> StateEstimationConnector:
    """
    Initializes the unified connector based on config.
    Now takes pandapower_net as parameter to ensure network is loaded first.
    """
    source_conf = config['measurement_source']

    # 1. Init CIM Connector
    cim_path = r"/app/Grids/1-LV-rural1--2-no_sw_EV_HP/CIM3/20151231T2300Z_YYY_EQ_.xml"
    cim_conn = CIMConnector(str(cim_path))

    # 2. Init the correct MeasurementSource based on config
    source_type = source_conf.get('source', 'csv')

    if source_type == 'influxdb':
        if not INFLUXDB_AVAILABLE:
            raise ImportError("Configured for InfluxDB, but 'influxdb_client' is not installed.")

        influx_conf = source_conf['influxdb']
        logging.info("Initializing InfluxDBMeasurementConnector...")
        try:
            measurement_source = InfluxDBMeasurementConnector(
                url=influx_conf['url'],
                token=influx_conf['token'],
                org=influx_conf['org'],
                bucket=influx_conf['bucket'],
                measurement_name=influx_conf['measurement_name'],
                range_start=influx_conf['range_start']
            )
        except Exception as e:
            logging.error(f"Failed to initialize InfluxDB connector: {e}")
            raise

    elif source_type == 'csv':
        csv_conf = source_conf['csv']
        logging.info(f"Initializing MeasurementsStore (CSV) from {csv_conf['path']}...")
        measurement_source = MeasurementsStore(
            csv_path=r"/app/Grids/1-LV-rural1--2-no_sw_EV_HP/measurements_log.csv",
            timestamp_col=csv_conf['timestamp_col']
        )
    else:
        raise ValueError(f"Invalid measurement 'source' in config: {source_type}. Must be 'influxdb' or 'csv'.")

    # 3. Create unified connector
    return StateEstimationConnector(cim_conn, measurement_source)


def load_pandapower_network(config: dict) -> "pp.Net":
    """
    Loads the CIM grid data using InputDataCIM and converts it to a pandapower network.
    """

    def normalize_bus_name(name: str) -> str:
        """Normalize bus names for comparison"""
        if not name:
            return ""
        # Remove spaces, dots, underscores, and make lowercase
        return name.replace(" ", "").replace(".", "").replace("_", "").lower()

    try:
        from state_estimation.InputDataCIM import inputGridData
    except ImportError as e:
        logging.error(f"Could not import InputDataCIM: {e}")
        return None

    gridData = {}
    new_import_result = {}

    ConfigData = {
        "PyToolchainConfig": {
            "grid": {
                "name": config["cim"]["grid_name"],
                "input_datasource": "local",
                "input_dataformat": "cim3",
                "input_coordinates": "DL",
                "auxiliary_nodes": False
            },
            "module": {"type": "application", "function": "se"}
        }
    }

    try:
        gridData, import_result = inputGridData(ConfigData, gridData, new_import_result)
        logging.info("✅ Grid data successfully imported from CIM using InputDataCIM.")

        # --- NEW FIXED BLOCK ---
        # Extract topology dataframe before calling init_auto_mapping
        topology_df = None
        transformers_df = None
        if "topology" in gridData and gridData["topology"] is not None and not gridData["topology"].empty:
            topology_df = gridData["topology"]
        else:
            logging.warning("⚠️ No topology information found in gridData; auto-mapping may fall back to defaults.")
        if "transformers" in gridData and gridData["transformers"] is not None and not gridData["transformers"].empty:
            transformers_df = gridData["transformers"]
        else:
            logging.warning("⚠️ No transformers information found in gridData; auto-mapping may fall back to defaults.")

        # Path to your measurement log from config
        csv_path = config["measurement_source"]["csv"]["path"]

        # Initialize auto mapping using topology (if available)
        init_auto_mapping(csv_path, topology_df, transformers_df)
        # --- END FIXED BLOCK ---

    except Exception as e:
        logging.error(f"Failed to import CIM data using InputDataCIM: {e}", exc_info=True)
        return None

    try:
        net = pp.create_empty_network()

        # --- STEP 1: Build map from ConnectivityNode mRID -> name ---
        cn_map = {}
        logging.info("Building ConnectivityNode mapping...")

        # Method 1: Try to get from CIM topology
        for key, value in import_result.get("topology", {}).items():
            class_name = getattr(value, "__class__", None).__name__
            if class_name == "ConnectivityNode":
                mRID = getattr(value, "mRID", None)
                name = getattr(value, "name", None)
                if mRID and name:
                    cn_map[mRID] = name
                    logging.debug(f"CIM Node: {mRID} -> {name}")

        # Method 2: If no names found in CIM, use busData from gridData
        if not cn_map and "busData" in gridData and not gridData["busData"].empty:
            logging.info("Using busData for node name mapping...")
            for _, row in gridData["busData"].iterrows():
                bus_name = row.get("busName", "")
                # We need to find the corresponding mRID - this is tricky
                # For now, we'll create a mapping later based on name matching

        logging.info(f"Discovered {len(cn_map)} ConnectivityNodes from CIM topology.")
        if cn_map:
            logging.info(f"Sample CIM nodes: {list(cn_map.items())[:3]}")

        # --- STEP 2: Create buses using ConnectivityNode mRID as bus.name ---
        bus_mrid_map = {}

        # First, let's create a mapping from bus names to what we expect in topology
        expected_bus_names = set()
        if "topology" in gridData:
            expected_bus_names.update(gridData["topology"]["node_i"].tolist())
            expected_bus_names.update(gridData["topology"]["node_j"].tolist())
        if "transformers" in gridData:
            expected_bus_names.update(gridData["transformers"]["hvBus"].tolist())
            expected_bus_names.update(gridData["transformers"]["lvBus"].tolist())

        logging.info(f"Expected bus names in topology: {list(expected_bus_names)}")

        # Create buses - we need to match CIM nodes with topology nodes
        created_buses = 0
        bus_name_to_idx = {}  # Map from normalized bus name to bus index
        original_bus_names = {}  # Map from bus index to original bus name

        # Method 1: Use CIM connectivity nodes if we have them
        if cn_map:
            for mrid, name in cn_map.items():
                clean_mrid = mrid.lstrip("_")

                # IMPROVED VOLTAGE LEVEL DETECTION
                vn_kv = 0.4  # default LV voltage

                # Detect voltage level from bus name and transformer connections
                normalized_name = normalize_bus_name(name)
                if "mv" in normalized_name or "medium" in normalized_name:
                    vn_kv = 20.0
                elif any("mv" in normalize_bus_name(bus) for bus in expected_bus_names if bus in name):
                    vn_kv = 20.0

                # Override with busData if available
                if "busData" in gridData and not gridData["busData"].empty:
                    match = gridData["busData"][gridData["busData"]["busName"] == name]
                    if not match.empty:
                        vn_kv = match.iloc[0]["voltageLevel"]
                        logging.info(f"Using busData voltage level for {name}: {vn_kv} kV")

                bus_idx = pp.create_bus(net, vn_kv=vn_kv, name=clean_mrid)
                bus_mrid_map[clean_mrid] = bus_idx
                bus_name_to_idx[normalized_name] = bus_idx
                original_bus_names[bus_idx] = name  # Store original name
                created_buses += 1
                logging.info(f"Created bus {bus_idx} for {name} with vn_kv={vn_kv}")

        # Method 2: Create buses from topology nodes that weren't found in CIM
        for bus_name in expected_bus_names:
            normalized_name = normalize_bus_name(bus_name)
            if normalized_name not in bus_name_to_idx:
                # IMPROVED VOLTAGE LEVEL DETECTION FOR SYNTHETIC BUSES
                vn_kv = 0.4  # default LV

                # Detect from bus name
                if "mv" in normalized_name or "medium" in normalized_name:
                    vn_kv = 20.0

                # Check if this bus is connected to transformers as HV side
                if "transformers" in gridData and not gridData["transformers"].empty:
                    for _, trafo_row in gridData["transformers"].iterrows():
                        hv_bus = str(trafo_row.get("hvBus", ""))
                        if normalize_bus_name(hv_bus) == normalized_name:
                            vn_kv = trafo_row.get("hvBus_kv", 20.0)
                            logging.info(f"Detected HV bus {bus_name} from transformer, setting vn_kv={vn_kv}")
                            break

                # Override with busData if available
                if "busData" in gridData and not gridData["busData"].empty:
                    match = gridData["busData"][gridData["busData"]["busName"] == bus_name]
                    if not match.empty:
                        vn_kv = match.iloc[0]["voltageLevel"]
                        logging.info(f"Using busData voltage level for synthetic bus {bus_name}: {vn_kv} kV")

                # Create a synthetic mRID for this bus
                synthetic_mrid = f"synthetic_{normalized_name}"
                bus_idx = pp.create_bus(net, vn_kv=vn_kv, name=synthetic_mrid)
                bus_mrid_map[synthetic_mrid] = bus_idx
                bus_name_to_idx[normalized_name] = bus_idx
                original_bus_names[bus_idx] = bus_name  # Store original name
                created_buses += 1
                logging.info(f"Created synthetic bus {bus_idx} for {bus_name} with vn_kv={vn_kv}")

        logging.info(f"✅ Created {created_buses} buses.")

        # Log final bus voltage levels for debugging - FIXED VERSION
        logging.info("Final bus voltage levels:")
        for idx, bus in net.bus.iterrows():
            original_name = original_bus_names.get(idx, "Unknown")
            logging.info(f"  Bus {idx}: vn_kv={bus['vn_kv']}, name={bus['name']}, original={original_name}")

        # --- STEP 3: Add External Grid (Slack Bus) ---
        if 'gridConfig' in gridData and not gridData['gridConfig'].empty:
            ext_grid_node = gridData['gridConfig'].iloc[0]['extGridNode']
            ext_grid_vm_pu = gridData['gridConfig'].iloc[0]['extGridSetpoint_pu']
            ext_grid_va = gridData['gridConfig'].iloc[0]['extGridSetpoint_angle']

            normalized_ext_grid = normalize_bus_name(ext_grid_node)
            ext_grid_bus_idx = bus_name_to_idx.get(normalized_ext_grid)

            if ext_grid_bus_idx is not None:
                # FIX: Ensure external grid has correct voltage reference
                ext_grid_vn_kv = net.bus.at[ext_grid_bus_idx, 'vn_kv']
                logging.info(f"External grid at bus {ext_grid_bus_idx} (vn_kv: {ext_grid_vn_kv})")

                pp.create_ext_grid(net, bus=ext_grid_bus_idx, vm_pu=ext_grid_vm_pu, va_degree=ext_grid_va)
                logging.info(
                    f"✅ Added external grid at bus {ext_grid_bus_idx} (node: {ext_grid_node}, vn_kv: {ext_grid_vn_kv})")
            else:
                # Fallback: use first bus as slack
                pp.create_ext_grid(net, bus=0, vm_pu=1.0, va_degree=0.0)
                logging.warning(f"⚠️  Could not find extGridNode '{ext_grid_node}', added external grid at bus 0")
        else:
            pp.create_ext_grid(net, bus=0, vm_pu=1.0, va_degree=0.0)
            logging.warning("⚠️  No gridConfig found, added external grid at bus 0")

        # --- STEP 4: Create lines using node_i / node_j ---
        created_lines = 0
        if "topology" in gridData and not gridData["topology"].empty:
            for _, row in gridData["topology"].iterrows():
                node_i_name = str(row.get("node_i", ""))
                node_j_name = str(row.get("node_j", ""))

                normalized_node_i = normalize_bus_name(node_i_name)
                normalized_node_j = normalize_bus_name(node_j_name)

                from_bus_idx = bus_name_to_idx.get(normalized_node_i)
                to_bus_idx = bus_name_to_idx.get(normalized_node_j)

                if from_bus_idx is not None and to_bus_idx is not None:
                    try:
                        # Get line parameters
                        line_type_name = row.get("type", "")
                        r_ohm_per_km = 0.1  # default
                        x_ohm_per_km = 0.2  # default

                        if "lineTypes" in gridData and not gridData["lineTypes"].empty:
                            line_type_match = gridData["lineTypes"][gridData["lineTypes"]["name"] == line_type_name]
                            if not line_type_match.empty:
                                r_ohm_per_km = line_type_match.iloc[0]["r_ohm_km"]
                                x_ohm_per_km = line_type_match.iloc[0]["x_ohm_km"]

                        pp.create_line_from_parameters(
                            net,
                            from_bus=from_bus_idx,
                            to_bus=to_bus_idx,
                            length_km=row.get("length_km", 0.1),
                            r_ohm_per_km=r_ohm_per_km,
                            x_ohm_per_km=x_ohm_per_km,
                            c_nf_per_km=0.0,
                            max_i_ka=0.1,
                            name=row.get("name", f"Line_{created_lines}")
                        )
                        created_lines += 1
                        logging.info(f"Created line {row.get('name')} between {node_i_name} and {node_j_name}")
                    except Exception as e:
                        logging.warning(f"Could not create line between {node_i_name} and {node_j_name}: {e}")
                else:
                    logging.warning(
                        f"Could not find buses for line {row.get('name')}: {node_i_name}->{from_bus_idx}, {node_j_name}->{to_bus_idx}")

        logging.info(f"✅ Created {created_lines} lines.")

        # --- STEP 5: Create transformers ---
        created_transformers = 0
        if "transformers" in gridData and not gridData["transformers"].empty:
            for _, row in gridData["transformers"].iterrows():
                hv_bus_name = str(row.get("hvBus", ""))
                lv_bus_name = str(row.get("lvBus", ""))

                normalized_hv_bus = normalize_bus_name(hv_bus_name)
                normalized_lv_bus = normalize_bus_name(lv_bus_name)

                hv_bus_idx = bus_name_to_idx.get(normalized_hv_bus)
                lv_bus_idx = bus_name_to_idx.get(normalized_lv_bus)

                if hv_bus_idx is not None and lv_bus_idx is not None:
                    try:
                        sn_mva = row.get("sn_mva", 0.4)
                        vn_hv_kv = row.get("hvBus_kv", 20.0)
                        vn_lv_kv = row.get("lvBus_kv", 0.4)

                        # FIX: Ensure transformer buses have correct voltage levels
                        net.bus.at[hv_bus_idx, 'vn_kv'] = vn_hv_kv
                        net.bus.at[lv_bus_idx, 'vn_kv'] = vn_lv_kv
                        logging.info(
                            f"Set transformer bus voltages: HV bus {hv_bus_idx} = {vn_hv_kv} kV, LV bus {lv_bus_idx} = {vn_lv_kv} kV")

                        pp.create_transformer_from_parameters(
                            net,
                            hv_bus=hv_bus_idx,
                            lv_bus=lv_bus_idx,
                            sn_mva=sn_mva,
                            vn_hv_kv=vn_hv_kv,
                            vn_lv_kv=vn_lv_kv,
                            vkr_percent=1.0,
                            vk_percent=4.0,
                            pfe_kw=0.0,
                            i0_percent=0.0,
                            name=row.get("name", f"Trafo_{created_transformers}")
                        )
                        created_transformers += 1
                        logging.info(f"Created transformer {row.get('name')} (HV: {vn_hv_kv}kV -> LV: {vn_lv_kv}kV)")
                    except Exception as e:
                        logging.warning(f"Could not create transformer {row.get('name')}: {e}")
                else:
                    logging.warning(f"Could not find buses for transformer {row.get('name')}")

        logging.info(f"✅ Created {created_transformers} transformers.")

        # --- STEP 6: Add loads and generators ---
        created_loads = 0
        if "loads" in gridData and not gridData["loads"].empty:
            for _, row in gridData["loads"].iterrows():
                bus_name = str(row.get("busConnected", ""))
                normalized_bus = normalize_bus_name(bus_name)
                bus_idx = bus_name_to_idx.get(normalized_bus)

                if bus_idx is not None:
                    try:
                        pp.create_load(
                            net,
                            bus=bus_idx,
                            p_mw=row.get("p_mw", 0),
                            q_mvar=row.get("q_mvar", 0),
                            name=row.get("name", f"Load_{created_loads}")
                        )
                        created_loads += 1
                    except Exception as e:
                        logging.warning(f"Could not create load {row.get('name')}: {e}")

        logging.info(f"✅ Created {created_loads} loads.")

        created_gens = 0
        if "gens" in gridData and not gridData["gens"].empty:
            for _, row in gridData["gens"].iterrows():
                bus_name = str(row.get("busConnected", ""))
                normalized_bus = normalize_bus_name(bus_name)
                bus_idx = bus_name_to_idx.get(normalized_bus)

                if bus_idx is not None:
                    try:
                        pp.create_sgen(
                            net,
                            bus=bus_idx,
                            p_mw=row.get("p_mw", 0),
                            q_mvar=row.get("q_mvar", 0),
                            name=row.get("name", f"Gen_{created_gens}")
                        )
                        created_gens += 1
                    except Exception as e:
                        logging.warning(f"Could not create generator {row.get('name')}: {e}")

        logging.info(f"✅ Created {created_gens} generators.")

        logging.info(
            f"✅ Pandapower network created with {len(net.bus)} buses, {len(net.line)} lines, {len(net.trafo)} transformers")

        # Final network validation
        logging.info("Final network summary:")
        for idx, bus in net.bus.iterrows():
            original_name = original_bus_names.get(idx, "Unknown")
            logging.info(f"  Bus {idx}: vn_kv={bus['vn_kv']}, name={bus['name']}, original={original_name}")

        return net

    except Exception as e:
        logging.error(f"Failed to build pandapower net from gridData: {e}", exc_info=True)
        return None


def run_state_estimation_pipeline(connector: StateEstimationConnector, pandapower_net: "pp.Net"):
    """
    Runs the full SE pipeline using only pandapower WLS estimation.
    """
    # Get measurements mapped to CIM nodes
    node_measurements = connector.get_node_measurements()
    logging.info(f"Retrieved measurements for {len(node_measurements)} nodes.")

    # Validate network connectivity
    if pandapower_net is None:
        raise ValueError("Pandapower network is not available for state estimation")

    if len(pandapower_net.line) + len(pandapower_net.trafo) == 0:
        raise ValueError("Network has no connectivity (lines/transformers) for state estimation")

    logging.info(
        f"Pandapower network: {len(pandapower_net.bus)} buses, {len(pandapower_net.line)} lines, {len(pandapower_net.trafo)} transformers"
    )
    logging.info(f"Network has external grid: {len(pandapower_net.ext_grid) > 0}")

    # Prepare inputs for state estimation
    se_inputs = prepare_state_estimation_inputs(node_measurements, connector)
    logging.info(f"Processor created {len(se_inputs['z'])} total measurements.")

    if len(se_inputs['z']) == 0:
        logging.warning("No measurements found or mapped.")
        return {"error": "No measurements available."}

    # Run pandapower WLS estimation (no fallback to DC)
    logging.info("Using Pandapower WLS estimation...")
    results = run_state_estimation(
        node_list=se_inputs["node_list"],
        z=se_inputs["z"],
        index_map=se_inputs["index_map"],
        pandapower_net=pandapower_net
    )

    return results


if __name__ == "__main__":
    try:
        config = load_config(CONFIG_PATH)

        # --- NEW WORKFLOW ORDER: Load network first ---
        logger.info("Step 1: Loading pandapower network from CIM...")
        net = load_pandapower_network(config)

        if net is None:
            raise RuntimeError("Failed to load pandapower network from CIM data")

        logger.info("Step 2: Loading measurement connector...")
        connector = load_se_connector(config, net)

        # Run pipeline
        logger.info("Step 3: Running state estimation pipeline...")
        se_results = run_state_estimation_pipeline(connector, net)

        print("\n--- State Estimation Results ---")
        if se_results.get("converged"):
            print("✅ Estimation Converged.")
            if "vm_pu" in se_results:
                print("Estimated Voltages (p.u.):")
                for bus_idx, voltage in se_results['vm_pu'].items():
                    bus_name = net.bus.at[bus_idx, 'name']
                    print(f"  Bus {bus_idx} ({bus_name}): {voltage:.6f} p.u.")
            if "va_degree" in se_results:
                print("Estimated Voltage Angles (degrees):")
                for bus_idx, angle in se_results['va_degree'].items():
                    bus_name = net.bus.at[bus_idx, 'name']
                    print(f"  Bus {bus_idx} ({bus_name}): {angle:.6f}°")
        else:
            print(f"❌ Estimation Failed: {se_results.get('error', 'Unknown')}")

    except Exception as e:
        logging.error(f"Pipeline failed: {e}", exc_info=True)
