# smart_grid_services/src/state_estimation/se_processor.py
from typing import Dict, Any, List, Tuple
import numpy as np
import logging

try:
    from state_estimation.se_connector import StateEstimationConnector
except ImportError as e:
    print(f"Import error: {e}")


logger = logging.getLogger("se_processor")
logger.setLevel(logging.INFO)


def build_measurement_vector(node_measurements: Dict[str, Dict]) -> Tuple[np.ndarray, List[Tuple[str, str]]]:
    """
    Build measurement vector z and index mapping from node measurements.

    Args:
        node_measurements: {node_id: {measurement_name: {value: v, timestamp: t}}}

    Returns:
        z: Measurement vector as numpy array
        index_map: List of (node_id, measurement_type) tuples
    """
    entries = []
    z = []

    for node_id, measures in node_measurements.items():
        for mtype, rec in measures.items():
            entries.append((node_id, mtype))
            z.append(float(rec["value"]))

    if len(z) == 0:
        return np.array([]), []

    return np.array(z, dtype=float), entries


def normalize_measurements(z: np.ndarray, cov_default: float = 1e-2) -> Tuple[np.ndarray, np.ndarray]:
    """
    Normalize measurements and create covariance matrix.

    Args:
        z: Measurement vector
        cov_default: Default covariance value

    Returns:
        z: Normalized measurement vector (unchanged for now)
        R: Covariance matrix
    """
    if z.size == 0:
        return z, np.array([])

    R = np.eye(len(z)) * cov_default
    return z, R


def build_topology_index(connector: StateEstimationConnector, node_list: List[str]) -> Dict[str, int]:
    """
    Build mapping from node ID to index in state vector.

    Args:
        connector: StateEstimationConnector instance
        node_list: List of connectivity node IDs

    Returns:
        Dictionary mapping node_id -> index
    """
    return {node_id: idx for idx, node_id in enumerate(node_list)}


def prepare_state_estimation_inputs(
        node_measurements: Dict[str, Dict],
        connector: StateEstimationConnector
) -> Dict[str, Any]:
    """
    Convert node_measurements + CIM connector into state estimation inputs.
    """
    # Debug: Check what node IDs we have
    node_name_map = connector.get_node_name_map()
    logging.info(f"Available CIM nodes: {list(node_name_map.keys())}")
    logging.info(f"Nodes with measurements: {list(node_measurements.keys())}")

    # Enhanced matching debug
    for node_id, measurements in node_measurements.items():
        if node_id in node_name_map:
            cim_name = node_name_map[node_id]
            meas_count = len(measurements)
            logging.info(f"✓ Node {node_id} ('{cim_name}') has {meas_count} measurements")
            # Log first few measurement types
            for i, (mtype, rec) in enumerate(measurements.items()):
                if i < 3:  # Show first 3 measurements per node
                    logging.info(f"  - {mtype}: {rec['value']}")
        else:
            logging.warning(f"✗ Node {node_id} not found in CIM node map")

    # Build measurement vector and mapping
    z, index_map = build_measurement_vector(node_measurements)
    z, R = normalize_measurements(z)
    node_list = connector.get_connectivity_nodes()
    topology_index = build_topology_index(connector, node_list)

    # Enhanced measurement statistics
    measurement_types = {}
    measurement_values = {}

    for _, mtype in index_map:
        measurement_types[mtype] = measurement_types.get(mtype, 0) + 1

    # Count by measurement category
    p_measurements = sum(1 for _, mtype in index_map if 'w' in mtype.lower())
    q_measurements = sum(1 for _, mtype in index_map if 'var' in mtype.lower())
    v_measurements = sum(1 for _, mtype in index_map if 'phv' in mtype.lower() or 'voltage' in mtype.lower())

    logging.info(f"Measurement distribution:")
    logging.info(f"  - Active Power (P): {p_measurements}")
    logging.info(f"  - Reactive Power (Q): {q_measurements}")
    logging.info(f"  - Voltage (V): {v_measurements}")
    logging.info(f"  - Total: {len(z)}")
    logging.info(f"Total nodes: {len(node_list)}")

    return {
        "node_list": node_list,
        "z": z,
        "index_map": index_map,
        "R": R,
        "topology_index": topology_index
    }