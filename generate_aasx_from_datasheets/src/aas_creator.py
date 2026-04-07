"""
Enhanced AAS Creator Service for CIM-first workflow

This service now works with existing AAS structures created from CIM EQ conversion
and enhances them with static data and asset mapping information.
"""

import os
import re
import uuid
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
from loguru import logger
from rabbitmq_service import rabbitmq_service
from basyx.aas import model
from utils.csv_io import read_csv
from utils.aas_io import write_aas_to_file, read_aas_from_file

# Directory configuration
ASSETS_DIR = Path("/app/assets")
MODBUS_MAPPING_DIR = Path("/app/asset_modbus_mapping")
FINAL_AAS_DIR = Path("/app/basyx_aas")

# Ensure output directory exists
FINAL_AAS_DIR.mkdir(parents=True, exist_ok=True)

def sanitize_id_short(s: str) -> str:
    """
    Sanitize strings for use as AAS identifier shorts.
    """
    s = re.sub(r'[^a-zA-Z0-9_]', '_', s.strip())
    s = re.sub(r'_+', '_', s)
    return s

def find_existing_aas_by_equipment(equipment_name: str, aas_file_path: str) -> Tuple[Optional[model.AssetAdministrationShell], Optional[model.Submodel]]:
    """
    Find existing AAS and technical submodel for a specific equipment in the CIM-generated AAS file.

    Args:
        equipment_name: Name of the equipment to find
        aas_file_path: Path to the CIM-generated AAS JSON file

    Returns:
        Tuple of (AAS, TechnicalSubmodel) or (None, None) if not found
    """
    try:
        # Read the existing AAS file
        objects = read_aas_from_file(aas_file_path)

        # Look for AAS with matching equipment name pattern
        target_aas = None
        technical_submodel = None

        for obj in objects:
            if isinstance(obj, model.AssetAdministrationShell):
                # Check if this AAS matches the equipment (case-insensitive partial match)
                id_short_lower = obj.id_short.lower()
                equipment_lower = equipment_name.lower()

                # Match patterns like "AAS_BatteryUnit_Battery1", "AAS_PhotoVoltaicUnit_PV1", etc.
                if (equipment_lower in id_short_lower
                        or id_short_lower in equipment_lower
                        or equipment_lower.replace('_', '') in id_short_lower.replace('_', '')):
                    target_aas = obj
                    logger.info(f"Found matching AAS: {obj.id_short}")
                    break

        if target_aas:
            # Find the technical submodel for this AAS
            for obj in objects:
                if isinstance(obj, model.Submodel) and obj.id_short.startswith("TechnicalData_"):
                    # Check if this submodel belongs to our target AAS
                    for ref in target_aas.submodel:
                        if ref.key[-1].value == obj.id:
                            technical_submodel = obj
                            logger.info(f"Found technical submodel: {obj.id_short}")
                            break

        return target_aas, technical_submodel

    except Exception as e:
        logger.error(f"Error finding existing AAS for {equipment_name}: {e}")
        return None, None

def create_modbus_mapping_submodel(equipment_name: str) -> model.Submodel:
    """
    Create a Modbus mapping submodel from CSV mapping files.
    (Same implementation as before)
    """
    sanitized_name = sanitize_id_short(equipment_name)

    logger.info(f"Looking for Modbus mapping files for: {equipment_name}")
    mapping_files = list(MODBUS_MAPPING_DIR.glob(f"*{equipment_name}*.csv"))

    if not mapping_files:
        logger.warning(f"No Modbus mapping file found for equipment: {equipment_name}")
        all_files = list(MODBUS_MAPPING_DIR.glob("*.csv"))
        logger.debug(f"Available mapping files: {[f.name for f in all_files]}")
        return None

    mapping_file = mapping_files[0]
    logger.info(f"Found Modbus mapping file: {mapping_file.name}")

    rows = read_csv(mapping_file)

    logger.debug(f"Read {len(rows)} rows from Modbus mapping file")
    if rows:
        logger.debug(f"First row keys: {list(rows[0].keys())}")

    if not rows or len(rows) < 2:
        logger.warning(f"No data rows in Modbus mapping file: {mapping_file.name}")
        return None

    # Create submodel for Modbus mapping
    modbus_submodel = model.Submodel(
        id_=f"Submodel_ModbusMapping_{sanitized_name}",
        id_short=f"IED_ModbusMapping_{sanitized_name}"
    )

    # Process each row in the mapping CSV
    entry_count = 0
    for i, row in enumerate(rows[1:], 1):
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

    logger.info(f"Created Modbus mapping submodel with {entry_count} entries")
    return modbus_submodel

def create_properties_submodel(equipment_name: str, rows: List[Dict]) -> model.Submodel:
    """
    Create a properties submodel with datapoints from CSV.

    Args:
        equipment_name: Name of the equipment
        rows: List of dictionaries containing datapoint information

    Returns:
        Properties submodel
    """
    sanitized_name = sanitize_id_short(equipment_name)

    properties_submodel = model.Submodel(
        id_=f"Submodel_Properties_{sanitized_name}",
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
    return properties_submodel


def enhance_existing_aas_with_static_data(equipment_name: str, csv_path: Path,
                                          target_aas_file: str, emit_event: bool = True) -> dict:
    """
    Enhance an existing AAS (from CIM conversion) with static data from CSV.
    Uses direct JSON manipulation to preserve original structure.
    """
    # Use the new direct JSON approach
    result = enhance_aas_json_directly(equipment_name, csv_path, target_aas_file)

    if result and emit_event:
        try:
            rabbitmq_service.publish_message(
                exchange='aas_events',
                routing_key='aas.enhanced',
                message=result
            )
            logger.success(f"[AAS Enhancer] Emitted enhancement event: {result}")
        except Exception as e:
            logger.error(f"[AAS Enhancer] Failed to emit event: {e}")

    return result

def enhance_all_equipment_with_static_data(target_aas_file: str, emit_events: bool = True) -> list[dict]:
    """
    Enhance all equipment in the existing AAS with their respective static data.

    Args:
        target_aas_file: Path to the CIM-generated AAS file to enhance
        emit_events: Whether to emit RabbitMQ events

    Returns:
        List of enhancement results
    """
    results = []

    # Process each CSV file in the assets directory
    for csv_path in sorted(ASSETS_DIR.glob("*.csv")):
        try:
            equipment_name = csv_path.stem
            result = enhance_existing_aas_with_static_data(
                equipment_name,
                csv_path,
                target_aas_file,
                emit_events
            )
            if result:
                results.append(result)
                logger.info(f"Successfully enhanced {equipment_name}: {result}")
        except Exception as e:
            logger.error(f"Failed to enhance {csv_path.name}: {e}")
            continue

    # Log summary
    if results:
        logger.success(f"[AAS Enhancer] Enhanced {len(results)} equipment in AAS file.")
    else:
        logger.warning("[AAS Enhancer] No equipment were enhanced.")

    return results

def process_single_csv_standalone(csv_path: Path, emit_event: bool = True) -> dict:
    """
    Fallback method: Create standalone AAS if no existing AAS found.
    (Original implementation for backward compatibility)
    """
    base = csv_path.stem
    logger.info(f"[AAS Creator] Processing {csv_path.name} as standalone AAS")

    rows = read_csv(csv_path)
    if not rows:
        logger.warning(f"No rows in {csv_path.name}")
        return None

    # Create the AAS and submodels (original logic)
    aas = model.AssetAdministrationShell(
        id_=f"AAS_{sanitize_id_short(base)}",
        id_short=f"AAS_{sanitize_id_short(base)}",
        asset_information=model.AssetInformation(
            asset_kind=model.AssetKind.INSTANCE,
            global_asset_id=str(uuid.uuid4()),
        )
    )

    properties_submodel = create_properties_submodel(base, rows)
    modbus_submodel = create_modbus_mapping_submodel(base)

    # Prepare submodels for writing
    submodels_to_write = [sm for sm in [properties_submodel, modbus_submodel] if sm is not None]

    # Create file in final directory
    final_filename = f"{sanitize_id_short(base)}.json"
    final_path = FINAL_AAS_DIR / final_filename

    # Write AAS
    write_aas_to_file([aas] + submodels_to_write, final_path)

    # Add submodel references
    aas.submodel.add(model.ModelReference.from_referable(properties_submodel))
    if modbus_submodel:
        aas.submodel.add(model.ModelReference.from_referable(modbus_submodel))

    # Prepare result
    result = {
        "equipment": base,
        "aas_json_path": str(final_path),
        "globalAssetId": aas.asset_information.global_asset_id,
        "submodel_ids": {
            "properties": properties_submodel.id,
            "modbus_mapping": modbus_submodel.id if modbus_submodel else None
        },
        "submodel_idShorts": {
            "properties": properties_submodel.id_short,
            "modbus_mapping": modbus_submodel.id_short if modbus_submodel else None
        },
    }

    # Emit event if requested
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

def process_all_csvs_standalone(emit_events: bool = True) -> list[dict]:
    """
    Fallback: Process all CSV files as standalone AAS (original implementation).
    """
    FINAL_AAS_DIR.mkdir(parents=True, exist_ok=True)
    results = []

    for csv_path in sorted(ASSETS_DIR.glob("*.csv")):
        try:
            result = process_single_csv_standalone(csv_path, emit_events)
            if result:
                results.append(result)
                logger.info(f"Successfully processed {csv_path.name}: {result}")
        except Exception as e:
            logger.error(f"Failed to process {csv_path.name}: {e}")
            continue

    if results:
        logger.success(f"[AAS Creator] Created {len(results)} standalone AAS files.")
    else:
        logger.warning("[AAS Creator] No standalone AAS files were created.")

    return results


def _serialize_submodel_element_for_json(element: model.SubmodelElement) -> Optional[Dict[str, Any]]:
    """
    Helper function to serialize submodel elements for direct JSON output.
    """
    try:
        # Handle Property elements
        if isinstance(element, model.Property):
            # Determine value type
            if element.value_type == model.datatypes.Float or element.value_type == model.datatypes.Double:
                value_type_str = "xs:double"
            elif element.value_type == model.datatypes.Int or element.value_type == model.datatypes.Integer:
                value_type_str = "xs:int"
            elif element.value_type == model.datatypes.Boolean:
                value_type_str = "xs:boolean"
            else:
                value_type_str = "xs:string"

            prop_dict = {
                "idShort": element.id_short,
                "modelType": "Property",
                "value": element.value,
                "valueType": value_type_str
            }
            if element.description:
                prop_dict["description"] = [{"language": "en", "text": str(element.description)}]
            return prop_dict

        # Handle SubmodelElementCollection
        elif isinstance(element, model.SubmodelElementCollection):
            collection_dict = {
                "idShort": element.id_short,
                "modelType": "SubmodelElementCollection",
                "value": []
            }
            if element.description:
                collection_dict["description"] = [{"language": "en", "text": str(element.description)}]

            # Recursively serialize nested elements
            for nested_element in element.value:
                serialized_nested = _serialize_submodel_element_for_json(nested_element)
                if serialized_nested:
                    collection_dict["value"].append(serialized_nested)

            return collection_dict

        # Add other element types as needed (ReferenceElement, etc.)

    except Exception as e:
        logger.warning(
            f"Failed to serialize submodel element {element.id_short if hasattr(element, 'id_short') else 'unknown'}: {e}")

    return None

def enhance_aas_json_directly(equipment_name: str, csv_path: Path, target_aas_file: str) -> dict:
    """
    Enhance AAS JSON file directly without full object reconstruction.
    This preserves the original structure while adding new submodels.
    """
    try:
        logger.info(f"[AAS Enhancer] Enhancing {equipment_name} with static data from {csv_path.name}")

        # Read the original JSON file
        with open(target_aas_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Read static data from CSV
        rows = read_csv(csv_path)
        if not rows:
            logger.warning(f"No rows in {csv_path.name}")
            return None

        # Create properties submodel
        properties_submodel = create_properties_submodel(equipment_name, rows)

        # Create Modbus mapping submodel if available
        modbus_submodel = create_modbus_mapping_submodel(equipment_name)

        # Convert submodels to JSON-serializable format WITH their elements
        def submodel_to_dict(submodel):
            if not submodel:
                return None

            # Serialize submodel elements
            submodel_elements = []
            for element in submodel.submodel_element:
                serialized_element = _serialize_submodel_element_for_json(element)
                if serialized_element:
                    submodel_elements.append(serialized_element)

            return {
                "idShort": submodel.id_short,
                "modelType": "Submodel",
                "id": submodel.id,
                "submodelElements": submodel_elements
            }

        # Add new submodels to the JSON data
        new_submodels = []
        if properties_submodel:
            new_submodels.append(submodel_to_dict(properties_submodel))
        if modbus_submodel:
            new_submodels.append(submodel_to_dict(modbus_submodel))

        # Add submodels to the data
        if 'submodels' not in data:
            data['submodels'] = []
        data['submodels'].extend(new_submodels)

        # Find the AAS for this equipment and add submodel references
        target_aas = None
        for aas in data.get('assetAdministrationShells', []):
            id_short = aas.get('idShort', '').lower()
            equipment_lower = equipment_name.lower()

            # Match patterns like "AAS_BatteryUnit_Battery1", "AAS_PhotoVoltaicUnit_PV1", etc.
            if (equipment_lower in id_short or
                    id_short in equipment_lower or
                    equipment_lower.replace('_', '') in id_short.replace('_', '')):
                target_aas = aas
                break

        if not target_aas:
            logger.error(f"No AAS found for equipment: {equipment_name}")
            return None

        # Add submodel references to the AAS
        if 'submodels' not in target_aas:
            target_aas['submodels'] = []

        for submodel in [properties_submodel, modbus_submodel]:
            if submodel:
                target_aas['submodels'].append({
                    "type": "ModelReference",
                    "keys": [{"type": "Submodel", "value": submodel.id}]
                })

        # Write the enhanced JSON back to file
        with open(target_aas_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        logger.success(f"Enhanced AAS JSON for {equipment_name}")

        # Prepare result
        result = {
            "equipment": equipment_name,
            "aas_json_path": target_aas_file,
            "enhanced_aas_id": target_aas.get('id', ''),
            "enhanced_aas_id_short": target_aas.get('idShort', ''),
            "added_submodels": {
                "properties": properties_submodel.id if properties_submodel else None,
                "modbus_mapping": modbus_submodel.id if modbus_submodel else None
            }
        }

        return result

    except Exception as e:
        logger.error(f"Error enhancing AAS JSON for {equipment_name}: {e}")
        return None
