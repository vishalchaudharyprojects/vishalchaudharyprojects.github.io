"""
Simplified Asset Administration Shell (AAS) Generation Module

Handles only the specific CSV structure with columns: Datapoint;unit;value
"""

import csv
import uuid
from pathlib import Path
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
from basyx.aas import model
from basyx.aas.adapter import json
import json
import re
from loguru import logger


def sanitize_id_short(id_short: str) -> str:
    """
    Sanitize id_short strings to comply with AAS naming requirements.
    Converts special characters to underscores and removes any trailing whitespace.
    """
    # Replace any non-alphanumeric character with underscore
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', id_short.strip())
    # Remove any consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    return sanitized


def read_csv(file_path: Path) -> list[dict]:
    """
    Read and parse CSV file with the specific structure.

    Expected format:
    Datapoint;unit;value
    """
    try:
        with open(file_path, mode='r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file, delimiter=';')
            return [{key.strip(): value.strip() for key, value in row.items()} for row in reader]
    except FileNotFoundError:
        logger.error(f"CSV file not found at {file_path}")
        raise
    except csv.Error as e:
        logger.error(f"Error parsing CSV file: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error reading CSV: {e}")
        raise


def create_aas(equipment_name: str, data: list[dict]) -> model.AssetAdministrationShell:
    """
    Create an Asset Administration Shell from the processed data.
    """
    try:
        logger.info(f"Creating AAS for {equipment_name}")

        # Sanitize equipment name for IDs
        sanitized_name = sanitize_id_short(equipment_name)

        # Create AAS with proper identifiers
        aas = model.AssetAdministrationShell(
            id_=f"AAS_{sanitized_name}",
            id_short=f"AAS_{sanitized_name}",
            asset_information=model.AssetInformation(
                asset_kind=model.AssetKind.INSTANCE,
                global_asset_id=str(uuid.uuid4()),
            )
        )

        # Create submodel for properties
        submodel = model.Submodel(
            id_=f"Submodel_{sanitized_name}",
            id_short=f"Properties_{sanitized_name}"
        )

        for entry in data:
            try:
                # Determine value type
                value_type = model.datatypes.String if entry['unit'] == 'NAN' else model.datatypes.Float
                value = entry['value']

                # Convert value if numeric
                if value_type == model.datatypes.Float:
                    try:
                        value = float(value)
                    except ValueError:
                        logger.warning(f"Skipping invalid numeric value: {value} for {entry['Datapoint']}")
                        continue

                # Create property
                property_ = model.Property(
                    id_short=sanitize_id_short(entry['Datapoint']),
                    value_type=value_type,
                    value=value,
                    description=f"{entry['Datapoint']} ({entry['unit']})"
                )
                submodel.submodel_element.add(property_)

            except KeyError as e:
                logger.warning(f"Missing required field in entry: {e}")
                continue
            except Exception as e:
                logger.warning(f"Error processing entry {entry}: {e}")
                continue

        # Add submodel to AAS
        aas.submodel.add(model.ModelReference.from_referable(submodel))

        logger.success(f"Created AAS with {len(submodel.submodel_element)} properties")
        return aas, submodel

    except Exception as e:
        logger.error(f"Error creating AAS: {e}")
        raise


def write_aas_to_file(aas_objects: list, file_path: Path) -> None:
    """
    Write AAS objects to JSON file in exact format expected by BaSyx Web UI
    """
    try:
        # Initialize the environment structure
        environment = {
            "assetAdministrationShells": [],
            "submodels": [],
            "conceptDescriptions": []
        }

        # Separate AAS and Submodel objects for easier processing
        aas_list = [obj for obj in aas_objects if isinstance(obj, model.AssetAdministrationShell)]
        submodel_list = [obj for obj in aas_objects if isinstance(obj, model.Submodel)]

        # Process Submodels first to get their IDs
        for submodel_obj in submodel_list:
            # Build Submodel with all required fields
            submodel_dict = {
                "idShort": submodel_obj.id_short,
                "modelType": "Submodel",
                "id": submodel_obj.id,
                "submodelElements": []
            }

            for element in submodel_obj.submodel_element:
                if isinstance(element, model.Property):
                    # Determine correct valueType
                    if isinstance(element.value, float):
                        value_type = "xs:double"
                    elif isinstance(element.value, int):
                        value_type = "xs:int"
                    else:
                        value_type = "xs:string"

                    prop_dict = {
                        "idShort": element.id_short,
                        "modelType": "Property",
                        "value": element.value,
                        "valueType": value_type
                    }

                    # Add description if it exists
                    if element.description:
                        prop_dict["description"] = [{
                            "language": "en",
                            "text": str(element.description)
                        }]

                    submodel_dict["submodelElements"].append(prop_dict)

            environment["submodels"].append(submodel_dict)

        # Now, process AAS objects and link the submodels
        for aas_obj in aas_list:
            # Build AAS structure
            aas_dict = {
                "idShort": aas_obj.id_short,
                "modelType": "AssetAdministrationShell",
                "id": aas_obj.id,
                "assetInformation": {
                    "assetKind": "Instance",
                    "globalAssetId": aas_obj.asset_information.global_asset_id
                },
                "submodels": []
            }

            # Loop through all submodel references of the AAS
            if aas_obj.submodel:
                for submodel_ref in aas_obj.submodel:
                    # Extract the submodel ID from the reference
                    # A more robust way to get the ID from a ModelReference
                    submodel_id = next((k.value for k in submodel_ref.key if k.type == model.KeyTypes.SUBMODEL), None)

                    if submodel_id:
                        aas_dict["submodels"].append({
                            "type": "ModelReference",
                            "keys": [{
                                "type": "Submodel",
                                "value": submodel_id
                            }]
                        })

            environment["assetAdministrationShells"].append(aas_dict)

        # Write with proper JSON formatting
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(environment, file,
                      indent=4,
                      ensure_ascii=False,
                      default=str)

        logger.success(f"Successfully wrote AAS to {file_path}")

    except Exception as e:
        logger.error(f"Failed to write AAS file: {str(e)}")
        raise


def process_all_equipment(config_data: dict) -> None:
    """
    Process all CSV files in the assets folder, creating multiple AASX files when needed.
    Also updates CIM files with AAS references.
    """
    try:
        logger.info("Starting AAS generation process")

        # Set up paths
        PROJECT_ROOT = Path(__file__).parent.parent.parent
        assets_dir = PROJECT_ROOT / 'generate_aasx_from_datasheets' / 'assets'
        output_dir = PROJECT_ROOT / 'generate_aasx_from_datasheets' / 'aas_json'
        aas_dir = PROJECT_ROOT / 'asset_administration_shell' / 'aas'

        # Validate directories
        if not assets_dir.exists():
            raise FileNotFoundError(f"Assets directory not found at {assets_dir}")
        output_dir.mkdir(parents=True, exist_ok=True)
        aas_dir.mkdir(parents=True, exist_ok=True)

        # Get CIM file path from config
        grid_folder = config_data.get('Aas_gen', {}).get('grid', {}).get('folder', '')
        cim_eq_path = Path(grid_folder) / 'CIM3' / '20151231T2300Z_YYY_EQ_.xml' if grid_folder else None

        # Process all CSV files
        processed_count = 0
        for csv_file in assets_dir.glob('*.csv'):
            try:
                base_equipment_name = csv_file.stem
                logger.info(f"Processing {base_equipment_name}")

                # Read and validate data
                data = read_csv(csv_file)
                if not data:
                    logger.warning(f"No valid data found in {csv_file.name}")
                    continue

                # Determine equipment type from filename
                equipment_type = None
                lower_name = base_equipment_name.lower()
                for key in ['battery', 'gens', 'line', 'load', 'transformer']:
                    if key in lower_name:
                        equipment_type = key
                        break

                if not equipment_type:
                    logger.warning(f"Could not determine equipment type for {base_equipment_name}")
                    continue

                # Get all matching CIM objects
                cim_objects = []
                if cim_eq_path and cim_eq_path.exists():
                    cim_objects = get_all_mrids_from_cim(equipment_type, cim_eq_path)

                if not cim_objects:
                    logger.warning(f"No CIM objects found for {equipment_type}, creating single AAS")
                    cim_objects = [{'mrid': str(uuid.uuid4()), 'name': base_equipment_name}]

                # Create one AAS for each CIM object
                for i, cim_obj in enumerate(cim_objects):
                    # Create unique equipment name
                    if len(cim_objects) > 1:
                        equipment_name = f"{base_equipment_name}_{i + 1}"
                    else:
                        equipment_name = base_equipment_name

                    # Create and save AAS
                    aas, submodel = create_aas(equipment_name, data)
                    cim_submodel = create_cim_submodel(config_data, cim_obj['mrid'], cim_obj['name'])
                    grid_measurement_submodel = create_grid_measurement_submodel(config_data)

                    # Add submodels to the AAS
                    aas.submodel.add(model.ModelReference.from_referable(cim_submodel))
                    aas.submodel.add(model.ModelReference.from_referable(grid_measurement_submodel))

                    output_file = output_dir / f"{sanitize_id_short(equipment_name)}.json"
                    write_aas_to_file([aas, submodel, cim_submodel, grid_measurement_submodel], output_file)

                    # Copy to final AAS directory
                    final_aas_file = aas_dir / f"{sanitize_id_short(equipment_name)}.json"
                    final_aas_file.write_text(output_file.read_text())

                    # Update CIM file with AAS reference
                    if cim_eq_path and cim_eq_path.exists():
                        update_cim_with_aas_reference(final_aas_file, cim_eq_path)

                    processed_count += 1
                    logger.success(f"Created AAS for {equipment_name} with MRID {cim_obj['mrid']}")

            except Exception as e:
                logger.error(f"Failed to process {csv_file.name}: {e}")
                continue

        logger.success(f"Completed AAS generation. Created {processed_count} AAS files.")

    except Exception as e:
        logger.critical(f"AAS generation failed: {e}")
        raise


#  New function to create the CIM submodel
def create_cim_submodel(config_data: dict, mrid: str, cim_name: str = None) -> model.Submodel:
    """
    Creates a submodel for CIM properties using the provided MRID and name.
    """
    cim_submodel = model.Submodel(
        id_=str(uuid.uuid4()),
        id_short="CimProperties"
    )

    grid_name = config_data.get('Aas_gen', {}).get('grid', {}).get('name', 'N/A')

    if grid_name != 'N/A':
        cim_submodel.submodel_element.add(model.Property(
            id_short="GridName",
            value_type=model.datatypes.String,
            value=grid_name,
            description="The name of the grid used in the Common Information Model."
        ))

    # Add MRID property
    cim_submodel.submodel_element.add(model.Property(
        id_short="MRID",
        value_type=model.datatypes.String,
        value=mrid,
        description="MRID from CIM model for this equipment"
    ))

    # Add CIM Name if available
    if cim_name:
        cim_submodel.submodel_element.add(model.Property(
            id_short="CIMName",
            value_type=model.datatypes.String,
            value=cim_name,
            description="Name of this equipment in the CIM model"
        ))

    logger.info(f"Created CimProperties submodel with MRID {mrid}")
    return cim_submodel


# New function to create the Grid Measurement submodel
def create_grid_measurement_submodel(config_data: dict) -> model.Submodel:
    """
    Creates a submodel for grid measurement properties using data from the configuration.
    """
    grid_measurement_submodel = model.Submodel(
        id_=str(uuid.uuid4()),
        id_short="GridMeasurement"
    )

    scd_file = config_data.get('Aas_gen', {}).get('application', {}).get('grid_measurement', {}).get('scd_file', 'N/A')

    if scd_file != 'N/A':
        grid_measurement_submodel.submodel_element.add(model.Property(
            id_short="SCDFile",
            value_type=model.datatypes.String,
            value=scd_file,
            description="The name of the SCD file used for grid measurements."
        ))

    logger.info("Created GridMeasurement submodel.")
    return grid_measurement_submodel


def get_all_mrids_from_cim(equipment_type: str, cim_eq_file: Path) -> list[dict]:
    """
    Extract all MRIDs and names from CIM EQ file for a specific equipment type.
    Returns list of dicts with 'mrid' and 'name' for each matching equipment.
    """
    try:
        tree = ET.parse(cim_eq_file)
        root = tree.getroot()

        ns = {
            'cim': 'http://iec.ch/TC57/CIM100#',
            'md': 'http://iec.ch/TC57/61970-552/ModelDescription/1#',
            'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'
        }

        equipment_mapping = {
            'battery': 'BatteryUnit',
            'gens': 'PhotoVoltaicUnit',
            'line': 'ACLineSegment',
            'load': 'ConformLoad',
            'transformer': 'PowerTransformer'
        }

        cim_class = equipment_mapping.get(equipment_type.lower())
        if not cim_class:
            logger.warning(f"No CIM class mapping found for {equipment_type}")
            return []

        results = []
        for elem in root.findall(f'.//cim:{cim_class}', ns):
            # Get MRID
            mrid = None
            mrid_elem = elem.find('cim:IdentifiedObject.mRID', ns)
            if mrid_elem is not None:
                mrid = mrid_elem.text
            else:
                rdf_id = elem.attrib.get(f'{{{ns["rdf"]}}}ID')
                if rdf_id:
                    mrid = rdf_id.lstrip('_')

            # Get name
            name = None
            name_elem = elem.find('cim:IdentifiedObject.name', ns)
            if name_elem is not None and name_elem.text:
                name = name_elem.text

            if mrid:
                results.append({'mrid': mrid, 'name': name})

        return results

    except Exception as e:
        logger.error(f"Error parsing CIM file {cim_eq_file}: {e}")
        return []


def update_cim_with_aas_reference(aas_file: Path, cim_eq_file: Path) -> None:
    """
    Updates CIM EQ file with AAS globalAssetId reference for the matching equipment,
    preserving the original formatting and indentation.
    """
    try:
        # Load AAS JSON file
        with open(aas_file, 'r', encoding='utf-8') as f:
            aas_data = json.load(f)

        # Extract AAS information
        aas_shell = aas_data['assetAdministrationShells'][0]
        global_asset_id = aas_shell['assetInformation']['globalAssetId']

        # Find the MRID in the CIMProperties submodel
        mrid = None
        for submodel in aas_data['submodels']:
            if submodel['idShort'] == 'CimProperties':
                for prop in submodel['submodelElements']:
                    if prop['idShort'] == 'MRID':
                        mrid = prop['value']
                        break
                if mrid:
                    break

        if not mrid:
            logger.warning(f"No MRID found in AAS file {aas_file.name}")
            return

        # Define and register namespaces to preserve original prefixes
        ns_map = {
            'cim': 'http://iec.ch/TC57/CIM100#',
            'md': 'http://iec.ch/TC57/61970-552/ModelDescription/1#',
            'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
            'eu': 'http://iec.ch/TC57/CIM100-European#' # Add any other namespaces present
        }
        for prefix, uri in ns_map.items():
            ET.register_namespace(prefix, uri)

        # Parse CIM EQ file with ElementTree
        tree = ET.parse(cim_eq_file)
        root = tree.getroot()

        # Find the element with matching MRID
        element = None
        for elem in root.findall('.//cim:*', ns_map):
            # Check mRID element
            mrid_elem = elem.find('cim:IdentifiedObject.mRID', ns_map)
            if mrid_elem is not None and mrid_elem.text == mrid:
                element = elem
                break

            # Check rdf:ID attribute
            rdf_id = elem.attrib.get(f'{{{ns_map["rdf"]}}}ID', '').lstrip('_')
            if rdf_id == mrid:
                element = elem
                break

        if element is None:
            logger.warning(f"No matching element found in CIM for MRID {mrid}")
            return

        # Create or update AAS reference
        aas_ref = element.find('cim:IdentifiedObject.aasReference', ns_map)
        if aas_ref is None:
            aas_ref = ET.SubElement(element, f'{{{ns_map["cim"]}}}IdentifiedObject.aasReference')
        aas_ref.text = global_asset_id

        # Convert ElementTree to a string and then parse with minidom for pretty printing
        xml_string = ET.tostring(root, encoding='utf-8')
        dom = minidom.parseString(xml_string)

        # Manually get the pretty-printed XML and clean up newlines
        pretty_xml = dom.toprettyxml(indent='  ', encoding='utf-8').decode('utf-8')

        # This regex removes multiple consecutive blank lines
        cleaned_xml = re.sub(r'\n\s*\n', '\n', pretty_xml)

        # Write the cleaned XML to the file
        with open(cim_eq_file, 'w', encoding='utf-8') as f:
            f.write(cleaned_xml)

        logger.success(
            f"Updated CIM file with AAS reference {global_asset_id} for MRID {mrid} and preserved formatting")

    except Exception as e:
        logger.error(f"Error updating CIM file with AAS reference: {e}")
        raise
