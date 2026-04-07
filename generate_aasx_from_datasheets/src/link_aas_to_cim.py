"""
Service 2: Link AAS with CIM (AAS Side)

This service enriches generated Asset Administration Shells (AAS) with information
from the Common Information Model (CIM) standard. It acts as a consumer of AAS
creation events and a producer of linkage completion events.

Primary Function:
- Consumes 'aasx.created' events from RabbitMQ
- Parses CIM/Equipment (EQ) XML files to find MRIDs and names matching the equipment type
- Adds a 'CimProperties' submodel to the AAS JSON containing GridName, MRID, and CIMName
- Emits 'aasx.linked_to_cim' events to signal completion

Key Features:
- Idempotent operation: Safely handles existing CimProperties submodels
- Automatic equipment type detection from AAS names
- Grid-aware CIM parsing with namespace handling
- Shared directory integration for AAS file access

Dependencies:
- xml.etree.ElementTree: For parsing CIM XML files
- loguru: For structured logging
- Custom rabbitmq_service: For message broker communication

Environment Variables:
- RABBITMQ_HOST: RabbitMQ server hostname (default: rabbitmq)
- RABBITMQ_PORT: RabbitMQ server port (default: 5672)
"""

import os
import json
import uuid
from pathlib import Path
from typing import List, Dict, Optional
from loguru import logger
import xml.etree.ElementTree as ET
from rabbitmq_service import rabbitmq_service

# Directory configuration for Grid and CIM files
GRID_FOLDER = Path("/app/Grids") / "1-LV-rural1--2-no_sw_EV_HP"  # Specific grid scenario
CIM_DIR = GRID_FOLDER / "CIM3"  # Directory containing CIM XML files
FINAL_AAS_DIR = Path("/app/basyx_aas")  # Shared directory for AAS JSON files

# RabbitMQ configuration
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
EXCHANGE_NAME = "aas_events"

# XML namespace definitions for CIM parsing
NS = {
    "cim": "http://iec.ch/TC57/CIM100#",  # Main CIM namespace
    "md":  "http://iec.ch/TC57/61970-552/ModelDescription/1#",  # Model description namespace
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#"  # RDF namespace for ID attributes
}

# Mapping from equipment name patterns to CIM class names
EQUIPMENT_MAP = {
    "battery": "BatteryUnit",
    "gens": "PhotoVoltaicUnit",
    "line": "ACLineSegment",
    "load": "ConformLoad",
    "transformer": "PowerTransformer"
}


def _guess_type(name: str) -> Optional[str]:
    """
    Guess the equipment type based on name patterns.

    Uses case-insensitive matching to determine the most likely
    equipment type from the AAS name.

    Args:
        name: Equipment name to analyze

    Returns:
        String representing the equipment type (e.g., "transformer"),
        or None if no match found
    """
    lname = name.lower()
    for k in EQUIPMENT_MAP:
        if k in lname:
            return k
    return None


def _find_eq_file() -> Optional[Path]:
    """
    Find the CIM Equipment (EQ) XML file in the CIM directory.

    Searches for files with 'EQ' in the filename, which typically
    contain equipment definitions in CIM XML format.

    Returns:
        Path to the EQ XML file, or None if not found
    """
    if not CIM_DIR.exists():
        logger.warning(f"CIM directory not found: {CIM_DIR}")
        return None
    for p in CIM_DIR.glob("*EQ*.xml"):
        return p
    return None


def _all_mrids(eq_path: Path, eq_type: str) -> List[Dict]:
    """
    Extract all MRIDs and names for a specific equipment type from CIM XML.

    Parses the CIM Equipment XML file to find all instances of a specific
    CIM class and extracts their MRID (Model Reference ID) and name.

    Args:
        eq_path: Path to the CIM Equipment XML file
        eq_type: Equipment type key (e.g., "transformer")

    Returns:
        List of dictionaries containing MRID and name for each equipment instance
    """
    try:
        tree = ET.parse(eq_path)
        root = tree.getroot()
        cim_class = EQUIPMENT_MAP.get(eq_type)
        if not cim_class:
            return []
        items = []

        # Find all elements of the specified CIM class
        for el in root.findall(f".//cim:{cim_class}", NS):
            mrid = None
            # Try to get MRID from the mRID element first
            mrid_el = el.find("cim:IdentifiedObject.mRID", NS)
            if mrid_el is not None and mrid_el.text:
                mrid = mrid_el.text
            else:
                # Fallback to RDF ID if mRID element is not present
                rid = el.attrib.get(f"{{{NS['rdf']}}}ID", "").lstrip("_")
                mrid = rid or None

            # Extract the equipment name
            name_el = el.find("cim:IdentifiedObject.name", NS)
            name = name_el.text if name_el is not None else None

            if mrid:
                items.append({"mrid": mrid, "name": name})
        return items
    except Exception as e:
        logger.error(f"CIM parse failed: {e}")
        return []


def _add_cim_submodel(aas_data: dict, mrid: str, cim_name: Optional[str], grid_name: str):
    """
    Add or update a CimProperties submodel in the AAS data structure.

    This operation is idempotent - if the submodel already exists, it updates
    the properties; if not, it creates a new submodel and adds the reference
    to the AAS.

    Args:
        aas_data: The complete AAS JSON data structure
        mrid: Model Reference ID from CIM
        cim_name: Equipment name from CIM (optional)
        grid_name: Name of the electrical grid
    """
    # Check if CimProperties submodel already exists
    sm = None
    for s in aas_data.get("submodels", []):
        if s.get("idShort") == "CimProperties":
            sm = s
            break

    # Create new submodel if it doesn't exist
    if not sm:
        sm = {
            "idShort": "CimProperties",
            "modelType": "Submodel",
            "id": str(uuid.uuid4()),  # Generate unique ID for the submodel
            "submodelElements": []
        }
        aas_data.setdefault("submodels", []).append(sm)

        # Add reference to this submodel in the AAS
        for aas in aas_data.get("assetAdministrationShells", []):
            # Check if reference already exists to avoid duplicates
            already_ref = any(
                key.get("value") == sm["id"]
                for ref in aas.get("submodels", [])
                for key in ref.get("keys", [])
            )
            if not already_ref:
                aas.setdefault("submodels", []).append({
                    "type": "ModelReference",
                    "keys": [{"type": "Submodel", "value": sm["id"]}]
                })

    def upsert(id_short: str, value: str):
        """
        Helper function to update or insert a property in the submodel.

        Args:
            id_short: Property identifier (e.g., "MRID", "GridName")
            value: Property value to set
        """
        # Update existing property if found
        for el in sm["submodelElements"]:
            if el.get("idShort") == id_short:
                el["value"] = value
                return
        # Add new property if not found
        sm["submodelElements"].append({
            "idShort": id_short,
            "modelType": "Property",
            "value": value,
            "valueType": "xs:string"  # All CIM properties are stored as strings
        })

    # Add/update the standard CIM properties
    upsert("GridName", grid_name)
    upsert("MRID", mrid)
    if cim_name:
        upsert("CIMName", cim_name)


def _load_aas(path: Path) -> dict:
    """
    Load AAS JSON data from file with shared directory fallback.

    If the path is relative, it looks for the file in the shared AAS directory.

    Args:
        path: Path to the AAS JSON file

    Returns:
        Parsed AAS data as a dictionary
    """
    # If path is relative, look in the shared AAS directory
    if not path.is_absolute():
        path = FINAL_AAS_DIR / path.name
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_aas(data: dict, path: Path):
    """
    Save AAS JSON data to file with shared directory fallback.

    If the path is relative, it saves the file to the shared AAS directory.

    Args:
        data: AAS data to save
        path: Destination path for the JSON file
    """
    # If path is relative, save to the shared AAS directory
    if not path.is_absolute():
        path = FINAL_AAS_DIR / path.name
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def link_aas_to_cim(payload: dict, emit_event: bool = True) -> dict:
    """
    Main function to link an AAS with CIM information.

    Can be called directly or triggered via RabbitMQ message.
    Orchestrates the entire linking process from equipment type
    detection to CIM property addition.

    Args:
        payload: Dictionary containing AAS information including:
                - equipment: Equipment name
                - aas_json_path: Path to AAS JSON file
        emit_event: Whether to emit a RabbitMQ event after completion

    Returns:
        Enhanced payload with CIM linkage information, or None on error
    """
    eq_name = payload.get("equipment", "")
    aas_path_str = payload.get("aas_json_path")
    grid_name = "1-LV-rural1--2-no_sw_EV_HP"  # Hardcoded grid name

    # Convert to Path object and ensure it's in the shared directory
    aas_path = Path(aas_path_str)
    if not aas_path.is_absolute():
        aas_path = FINAL_AAS_DIR / aas_path.name

    if not aas_path.exists():
        logger.error(f"AAS file not found: {aas_path}")
        return None

    # Determine equipment type and find CIM file
    eq_type = _guess_type(eq_name) or "transformer"  # Default to transformer
    eq_file = _find_eq_file()

    # Extract MRIDs from CIM or generate a fallback UUID
    mrids = _all_mrids(eq_file, eq_type) if eq_file else []
    chosen = mrids[0] if mrids else {"mrid": str(uuid.uuid4()), "name": None}

    # Load, modify, and save the AAS with CIM properties
    aas = _load_aas(aas_path)
    _add_cim_submodel(aas, chosen["mrid"], chosen.get("name"), grid_name)
    _save_aas(aas, aas_path)  # This will save to the shared directory

    logger.success(f"[Link AAS→CIM] Updated AAS with MRID {chosen['mrid']} at {aas_path}")

    # Prepare result with enhanced information
    result = {
        **payload,
        "mrid": chosen["mrid"],
        "cim_name": chosen.get("name"),
        "aas_json_path": str(aas_path),  # Return the full path to shared directory
    }

    # Emit event if requested
    if emit_event:
        try:
            rabbitmq_service.publish_message(
                exchange='aas_events',
                routing_key='aasx.linked_to_cim',
                message=result
            )
            logger.success(f"[Link AAS→CIM] Emitted event to 'aasx.linked_to_cim': {result}")
        except Exception as e:
            logger.error(f"[Link AAS→CIM] Failed to emit event: {e}")

    return result
