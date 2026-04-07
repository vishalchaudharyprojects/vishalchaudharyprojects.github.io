"""
AAS Creator Service

Service 1 in the AAS creation pipeline:
- Reads CSV files containing datapoint information (Datapoint;unit;value)
- Builds Asset Administration Shell (AAS) JSON files compatible with BaSyx Web UI
- Creates Modbus mapping submodels from additional CSV files
- Emits RabbitMQ events for each created/updated AAS

Key Features:
- Processes CSV files from /app/assets directory
- Generates AAS with properties submodel containing datapoints
- Creates optional Modbus mapping submodel from mapping files
- Outputs JSON files to /app/basyx_aas directory
- Publishes creation events to RabbitMQ exchange

Dependencies:
- basyx.aas: For AAS model creation and serialization
- pika: For RabbitMQ communication
- loguru: For structured logging
- Custom utilities: csv_io, aas_io, rabbitmq_service

Environment Variables:
- RABBITMQ_HOST: RabbitMQ server hostname (default: rabbitmq)
- RABBITMQ_PORT: RabbitMQ server port (default: 5672)
"""

import os
import re
import uuid
import json
import pika
from pathlib import Path
from typing import List, Dict, Tuple
from loguru import logger
from .rabbitmq_service import rabbitmq_service
from basyx.aas import model
from utils.csv_io import read_csv
from utils.aas_io import write_aas_to_file

# Directory configuration
ASSETS_DIR = Path("/app/assets")  # Source directory for datapoint CSV files
MODBUS_MAPPING_DIR = Path("/app/asset_modbus_mapping")  # Directory for Modbus mapping CSV files
FINAL_AAS_DIR = Path("/app/basyx_aas")  # Output directory for generated AAS JSON files

# Ensure output directory exists
FINAL_AAS_DIR.mkdir(parents=True, exist_ok=True)

# RabbitMQ configuration
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
EXCHANGE_NAME = "aas_events"  # RabbitMQ exchange name for AAS events


def sanitize_id_short(s: str) -> str:
    """
    Sanitize strings for use as AAS identifier shorts.

    AAS identifiers must conform to specific naming conventions. This function
    replaces invalid characters with underscores and ensures proper formatting.

    Args:
        s: Input string to sanitize

    Returns:
        Sanitized string suitable for use as id_short in AAS components
    """
    s = re.sub(r'[^a-zA-Z0-9_]', '_', s.strip())  # Replace non-alphanumeric/underscore chars
    s = re.sub(r'_+', '_', s)  # Collapse multiple underscores
    return s


def create_modbus_mapping_submodel(equipment_name: str) -> model.Submodel:
    """
    Create a Modbus mapping submodel from CSV mapping files.

    Searches for Modbus mapping CSV files matching the equipment name pattern
    and creates a submodel containing mapping information for each datapoint.

    Args:
        equipment_name: Name of the equipment to find mapping for

    Returns:
        Submodel containing Modbus mapping information, or None if no mapping found
    """
    sanitized_name = sanitize_id_short(equipment_name)

    logger.info(f"Looking for Modbus mapping files for: {equipment_name}")
    # Find mapping files using pattern matching
    mapping_files = list(MODBUS_MAPPING_DIR.glob(f"*{equipment_name}*.csv"))

    if not mapping_files:
        logger.warning(f"No Modbus mapping file found for equipment: {equipment_name}")
        # Debug: list all files in the directory
        all_files = list(MODBUS_MAPPING_DIR.glob("*.csv"))
        logger.debug(f"Available mapping files: {[f.name for f in all_files]}")
        return None

    mapping_file = mapping_files[0]
    logger.info(f"Found Modbus mapping file: {mapping_file.name}")

    rows = read_csv(mapping_file)

    # DEBUG: Log what was read from the CSV
    logger.debug(f"Read {len(rows)} rows from Modbus mapping file")
    if rows:
        logger.debug(f"First row keys: {list(rows[0].keys())}")
        logger.debug(f"First row values: {list(rows[0].values())}")

    if not rows or len(rows) < 2:  # Check if there is at least one header and one data row
        logger.warning(f"No data rows in Modbus mapping file: {mapping_file.name}")
        return None

    # Create submodel for Modbus mapping
    modbus_submodel = model.Submodel(
        id_=f"Submodel_ModbusMapping_{sanitized_name}",
        id_short=f"IED_ModbusMapping_{sanitized_name}"
    )

    # DEBUG: Check if we have the expected column names
    expected_columns = ['Datapoint_named_in_Typhoon', 'Port', 'Register', 'Registertype',
                        'Unit', 'Datatype', 'Word-Order', 'Byte-Order']

    available_columns = list(rows[0].keys())
    logger.debug(f"Expected columns: {expected_columns}")
    logger.debug(f"Available columns: {available_columns}")

    # Process each row in the mapping CSV (skip header row)
    entry_count = 0
    for i, row in enumerate(rows[1:], 1):  # Skip header row (index 0)
        # Try different possible column names for the datapoint
        datapoint_name = (
                row.get('Datapoint_named_in_Typhoon') or
                row.get('Datapoint named in Typhoon') or
                row.get('Datapoint') or
                f'entry_{i}'
        )

        if not datapoint_name or datapoint_name.strip() == '':
            logger.warning(f"Skipping row {i} due to missing datapoint name")
            continue

        # Create a collection for this mapping entry
        mapping_entry = model.SubmodelElementCollection(
            id_short=sanitize_id_short(datapoint_name),
            description=f"Modbus mapping for {datapoint_name}"
        )

        # Add all properties from the row
        properties_added = 0
        for key, value in row.items():
            if key and value and key.strip() != '' and value.strip() != '':
                # Skip the datapoint name column itself
                if key in ['Datapoint_named_in_Typhoon', 'Datapoint named in Typhoon', 'Datapoint']:
                    continue

                prop = model.Property(
                    id_short=sanitize_id_short(key),
                    value_type=model.datatypes.String,
                    value=str(value).strip(),
                    description=key
                )
                mapping_entry.value.add(prop)
                properties_added += 1

        if properties_added > 0:
            modbus_submodel.submodel_element.add(mapping_entry)
            entry_count += 1
            logger.info(f"Added mapping entry for: {datapoint_name} with {properties_added} properties")
        else:
            logger.warning(f"No properties added for datapoint: {datapoint_name}")

    logger.info(f"Created Modbus mapping submodel with {entry_count} entries")
    return modbus_submodel


def create_aas(equipment_name: str, rows: List[Dict]) -> Tuple[
    model.AssetAdministrationShell, model.Submodel, model.Submodel]:
    """
    Create a complete AAS with properties and optional Modbus mapping submodels.

    Args:
        equipment_name: Name of the equipment being modeled
        rows: List of dictionaries containing datapoint information from CSV

    Returns:
        Tuple containing:
        - AssetAdministrationShell: The created AAS
        - Submodel: Properties submodel with datapoints
        - Submodel: Modbus mapping submodel (or None if not available)
    """
    sanitized_name = sanitize_id_short(equipment_name)

    # Create the main AAS with asset information
    aas = model.AssetAdministrationShell(
        id_=f"AAS_{sanitized_name}",
        id_short=f"AAS_{sanitized_name}",
        asset_information=model.AssetInformation(
            asset_kind=model.AssetKind.INSTANCE,
            global_asset_id=str(uuid.uuid4()),  # Generate unique global asset ID
        )
    )

    # Create main properties submodel
    properties_submodel = model.Submodel(
        id_=f"Submodel_{sanitized_name}",
        id_short=f"Properties_{sanitized_name}"
    )

    # Process each datapoint row from the CSV
    for r in rows:
        unit = (r.get("unit") or "").strip()
        dp = (r.get("Datapoint") or "").strip()
        val = (r.get("value") or "").strip()
        if not dp:
            continue
        try:
            # numeric unless unit is NAN
            if unit.upper() == "NAN":
                v = val
                vt = model.datatypes.String
            else:
                v = float(val)
                vt = model.datatypes.Float
        except Exception:
            logger.warning(f"Skipping invalid numeric value for '{dp}': {val}")
            continue

        # Create property for this datapoint
        prop = model.Property(
            id_short=sanitize_id_short(dp),
            value_type=vt,
            value=v,
            description=f"{dp} ({unit})" if unit else dp,
        )
        properties_submodel.submodel_element.add(prop)

    logger.info(f"Created properties submodel with {len(properties_submodel.submodel_element)} elements")

    # Create Modbus mapping submodel (if mapping file exists)
    modbus_submodel = create_modbus_mapping_submodel(equipment_name)

    if modbus_submodel:
        logger.info(f"Created Modbus mapping submodel with {len(modbus_submodel.submodel_element)} entries")
    else:
        logger.warning("No Modbus mapping submodel was created")

    # Add submodel references to AAS
    aas.submodel.add(model.ModelReference.from_referable(properties_submodel))
    if modbus_submodel:
        aas.submodel.add(model.ModelReference.from_referable(modbus_submodel))
        logger.info("Added Modbus mapping submodel reference to AAS")
    else:
        logger.warning("No Modbus mapping submodel reference added to AAS")

    return aas, properties_submodel, modbus_submodel


def process_single_csv(csv_path: Path, emit_event: bool = True) -> dict:
    """
    Process a single CSV file to create an AAS and optionally emit an event.

    Args:
        csv_path: Path to the CSV file to process
        emit_event: Whether to emit a RabbitMQ event after creation

    Returns:
        Dictionary containing processing results including:
        - equipment: Equipment name
        - aas_json_path: Path to generated JSON file
        - globalAssetId: Global asset ID of the created AAS
        - submodel_ids: Dictionary of submodel IDs
        - submodel_idShorts: Dictionary of submodel idShorts
    """
    base = csv_path.stem  # Get filename without extension
    logger.info(f"[AAS Creator] Processing {csv_path.name}")

    rows = read_csv(csv_path)
    if not rows:
        logger.warning(f"No rows in {csv_path.name}")
        return None

    # Create the AAS and submodels
    aas, properties_sm, modbus_sm = create_aas(base, rows)

    # Prepare submodels for writing (filter out None values)
    submodels_to_write = [sm for sm in [properties_sm, modbus_sm] if sm is not None]

    # Create file directly in the final directory
    final_filename = f"{sanitize_id_short(base)}.json"
    final_path = FINAL_AAS_DIR / final_filename

    # Write directly to the final directory
    write_aas_to_file([aas] + submodels_to_write, final_path)

    # DEBUG: Check if FINAL_AAS_DIR exists and is writable
    logger.info(f"FINAL_AAS_DIR: {FINAL_AAS_DIR}")
    logger.info(f"FINAL_AAS_DIR exists: {FINAL_AAS_DIR.exists()}")
    logger.info(f"FINAL_AAS_DIR is writable: {os.access(FINAL_AAS_DIR, os.W_OK)}")

    # Prepare result dictionary
    result = {
        "equipment": base,
        "aas_json_path": str(final_path),
        "globalAssetId": aas.asset_information.global_asset_id,
        "submodel_ids": {
            "properties": properties_sm.id,
            "modbus_mapping": modbus_sm.id if modbus_sm else None
        },
        "submodel_idShorts": {
            "properties": properties_sm.id_short,
            "modbus_mapping": modbus_sm.id_short if modbus_sm else None
        },
    }

    # Emit RabbitMQ event if requested
    if emit_event:
        try:
            rabbitmq_service.publish_message(
                exchange='aas_events',
                routing_key='aasx.created',
                message=result
            )
            logger.success(f"[AAS Creator] Emitted event to 'aasx.created': {result}")
        except Exception as e:
            logger.error(f"[AAS Creator] Failed to emit event: {e}")

    return result


def process_all_csvs(emit_events: bool = True) -> list[dict]:
    """
    Process all CSV files in the assets directory and create AAS files.

    Args:
        emit_events: Whether to emit RabbitMQ events for each created AAS

    Returns:
        List of result dictionaries for each successfully processed file
    """
    # Ensure output directory exists
    FINAL_AAS_DIR.mkdir(parents=True, exist_ok=True)

    results = []

    # Process each CSV file in the assets directory
    for csv_path in sorted(ASSETS_DIR.glob("*.csv")):
        try:
            result = process_single_csv(csv_path, emit_events)
            if result:
                results.append(result)
                logger.info(f"Successfully processed {csv_path.name}: {result}")
        except Exception as e:
            logger.error(f"Failed to process {csv_path.name}: {e}")
            continue

    # Log summary of processing
    if results:
        logger.success(f"[AAS Creator] Created {len(results)} AAS files.")
    else:
        logger.warning("[AAS Creator] No AAS files were created.")

    return results