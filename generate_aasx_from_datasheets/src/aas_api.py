"""
Simplified Asset Administration Shell (AAS) Generation Module

Handles only the specific CSV structure with columns: Datapoint;unit;value
"""

import csv
import os
import uuid
from pathlib import Path
from basyx.aas import model
import json
import re
from loguru import logger
from minio import Minio
from minio.error import S3Error
import io


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


# ==============================================================================
# MinIO Client
# ==============================================================================
class MinioClient:
    def __init__(self, endpoint, access_key, secret_key, secure):
        self.client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )

    def get_object(self, bucket_name, object_name):
        try:
            response = self.client.get_object(bucket_name, object_name)
            return response.read()
        except S3Error as e:
            logger.error(f"Error getting object '{object_name}' from MinIO: {e}")
            return None
        finally:
            if 'response' in locals() and response:
                response.close()
                response.release_conn()

    def list_objects(self, bucket_name, prefix=''):
        try:
            objects = self.client.list_objects(bucket_name, prefix=prefix)
            return [obj.object_name for obj in objects]
        except S3Error as e:
            logger.error(f"Error listing objects in bucket '{bucket_name}': {e}")
            return []

    def put_object(self, bucket_name, object_name, data, length):
        try:
            found = self.client.bucket_exists(bucket_name)
            if not found:
                self.client.make_bucket(bucket_name)
            self.client.put_object(bucket_name, object_name, io.BytesIO(data), length)
            logger.success(f"Successfully uploaded {object_name} to bucket {bucket_name}")
        except S3Error as e:
            logger.error(f"Error uploading object '{object_name}' to MinIO: {e}")
            raise


# ==============================================================================
# CSV Reading Functions
# ==============================================================================
def read_csv_from_local(file_path: Path) -> list[dict]:
    """
    Read and parse CSV file from local storage.
    """
    try:
        with open(file_path, mode='r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file, delimiter=';')
            return [{key.strip(): value.strip() for key, value in row.items()} for row in reader]
    except FileNotFoundError:
        logger.error(f"CSV file not found at {file_path}")
        raise
    except csv.Error as e:
        logger.error(f"Error parsing local CSV file: {e}")
        raise


def read_csv_from_s3(minio_client: MinioClient, bucket_name: str, object_name: str) -> list[dict]:
    """
    Read and parse CSV file from MinIO storage.
    """
    try:
        csv_data_bytes = minio_client.get_object(bucket_name, object_name)
        if csv_data_bytes is None:
            return []

        csv_data_str = csv_data_bytes.decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(csv_data_str), delimiter=';')
        return [{key.strip(): value.strip() for key, value in row.items()} for row in reader]
    except Exception as e:
        logger.error(f"Error reading CSV from MinIO object '{object_name}': {e}")
        raise


# ==============================================================================
# AAS Creation & Writing Functions
# ==============================================================================
def create_aas(equipment_name: str, data: list[dict]) -> model.AssetAdministrationShell:
    """
    Create an Asset Administration Shell from the processed data.
    """
    try:
        logger.info(f"Creating AAS for {equipment_name}")
        sanitized_name = sanitize_id_short(equipment_name)
        aas = model.AssetAdministrationShell(
            id_=f"AAS_{sanitized_name}",
            id_short=f"AAS_{sanitized_name}",
            asset_information=model.AssetInformation(
                asset_kind=model.AssetKind.INSTANCE,
                global_asset_id=str(uuid.uuid4()),
            )
        )
        submodel = model.Submodel(
            id_=f"Submodel_{sanitized_name}",
            id_short=f"Properties_{sanitized_name}"
        )

        for entry in data:
            try:
                value = entry['value']
                value_type = model.datatypes.String if entry['unit'].strip().upper() == 'NAN' else model.datatypes.Float

                if value_type == model.datatypes.Float:
                    try:
                        value = float(value)
                    except ValueError:
                        logger.warning(f"Skipping invalid numeric value: {value} for {entry['Datapoint']}")
                        continue

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

        aas.submodel.add(model.ModelReference.from_referable(submodel))
        logger.success(f"Created AAS with {len(submodel.submodel_element)} properties")
        return aas, submodel
    except Exception as e:
        logger.error(f"Error creating AAS: {e}")
        raise


def create_cim_submodel(config_data: dict) -> model.Submodel:
    """
    Creates a submodel for CIM properties using data from the configuration.
    """
    cim_submodel = model.Submodel(
        id_=f"Submodel_CimProperties_{str(uuid.uuid4())}",
        id_short="CimProperties"
    )

    grid_name = config_data.get('Aas_gen', {}).get('grid', {}).get('name', 'N/A')
    if grid_name != 'N/A':
        cim_submodel.submodel_element.add(model.Property(
            id_short="GridName",
            value_type=model.datatypes.String,
            value=grid_name,
            description=model.MultiLanguageProperty(
                text_list=[model.LangString(language='en', text="The name of the grid used in the Common Information Model.")])
        ))

    logger.info("Created CimProperties submodel.")
    return cim_submodel


def create_grid_measurement_submodel(config_data: dict) -> model.Submodel:
    """
    Creates a submodel for grid measurement properties using data from the configuration.
    """
    grid_measurement_submodel = model.Submodel(
        id_=f"Submodel_GridMeasurement_{str(uuid.uuid4())}",
        id_short="GridMeasurement"
    )

    scd_file = config_data.get('Aas_gen', {}).get('application', {}).get('grid_measurement', {}).get('scd_file', 'N/A')
    if scd_file != 'N/A':
        grid_measurement_submodel.submodel_element.add(model.Property(
            id_short="SCDFile",
            value_type=model.datatypes.String,
            value=scd_file,
            description=model.MultiLanguageProperty(
                text_list=[model.LangString(language='en', text="The name of the SCD file used for grid measurements.")])
        ))

    logger.info("Created GridMeasurement submodel.")
    return grid_measurement_submodel


def write_aas_to_file(aas_objects: list, file_path: Path, minio_client: MinioClient = None, minio_bucket: str = None) -> None:
    """
    Write AAS objects to JSON file in exact format expected by BaSyx Web UI.
    Optionally writes to MinIO.
    """
    try:
        environment = {
            "assetAdministrationShells": [],
            "submodels": [],
            "conceptDescriptions": []
        }

        aas_list = [obj for obj in aas_objects if isinstance(obj, model.AssetAdministrationShell)]
        submodel_list = [obj for obj in aas_objects if isinstance(obj, model.Submodel)]

        for submodel_obj in submodel_list:
            submodel_dict = {
                "idShort": submodel_obj.id_short,
                "modelType": "Submodel",
                "id": submodel_obj.id,
                "submodelElements": []
            }
            for element in submodel_obj.submodel_element:
                if isinstance(element, model.Property):
                    value_type = "xs:string"
                    if isinstance(element.value, float):
                        value_type = "xs:double"
                    elif isinstance(element.value, int):
                        value_type = "xs:int"

                    prop_dict = {
                        "idShort": element.id_short,
                        "modelType": "Property",
                        "value": str(element.value),
                        "valueType": value_type
                    }
                    if element.description:
                        prop_dict["description"] = [{
                            "language": "en",
                            "text": str(element.description)
                        }]
                    submodel_dict["submodelElements"].append(prop_dict)
            environment["submodels"].append(submodel_dict)

        for aas_obj in aas_list:
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
            if aas_obj.submodel:
                for submodel_ref in aas_obj.submodel:
                    submodel_id = next((k.value for k in submodel_ref.key if k.type == model.KeyTypes.SUBMODEL), None)
                    if submodel_id:
                        aas_dict["submodels"].append({
                            "type": "ModelReference",
                            "keys": [{"type": "Submodel", "value": submodel_id}]
                        })
            environment["assetAdministrationShells"].append(aas_dict)

        # Write to local file system
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(environment, file, indent=4, ensure_ascii=False, default=str)
        logger.success(f"Successfully wrote AAS to local file {file_path}")

        # Optionally write to MinIO
        if minio_client and minio_bucket:
            json_data = json.dumps(environment, indent=4, ensure_ascii=False, default=str)
            minio_client.put_object(minio_bucket, file_path.name, json_data.encode('utf-8'), len(json_data.encode('utf-8')))
            logger.success(f"Successfully uploaded AAS to MinIO bucket '{minio_bucket}'")

    except Exception as e:
        logger.error(f"Failed to write AAS file: {e}")
        raise


def process_all_equipment(config_data: dict) -> None:
    """
    Process all equipment data from local or S3 storage.
    """
    try:
        logger.info("Starting AAS generation process")

        # --- PATHS & CONFIGURATION ---
        PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
        assets_dir_local = PROJECT_ROOT / 'generate_aasx_from_datasheets' / 'assets'
        output_dir_local = PROJECT_ROOT / 'asset_administration_shell' / 'aas'

        # MinIO configuration from .env file
        minio_ip = os.getenv("MINIO_IP")
        minio_port = os.getenv("MINIO_PORT")
        minio_endpoint = f"{minio_ip}:{minio_port}"
        minio_access_key = os.getenv("ACCESS_KEY")
        minio_secret_key = os.getenv("SECRET_KEY")
        minio_secure = os.getenv("MINIO_SECURE", "False").lower() == "true"
        minio_bucket = os.getenv("BUCKET_NAME")

        input_datasource = config_data.get('Aas_gen', {}).get('grid', {}).get('input_datasource', 'local')

        if input_datasource == 's3':
            minio_client = MinioClient(minio_endpoint, minio_access_key, minio_secret_key, minio_secure)
        else:
            minio_client = None

        # Create output directory if it doesn't exist
        output_dir_local.mkdir(parents=True, exist_ok=True)

        # --- FILE PROCESSING LOGIC ---
        processed_count = 0
        file_list = []

        if input_datasource == 's3':
            logger.info("Reading CSV files from MinIO bucket")
            file_list = minio_client.list_objects(minio_bucket, prefix='assets/')
            file_list = [f for f in file_list if f.endswith('.csv')]
        else:
            logger.info("Reading CSV files from local assets directory")
            if not assets_dir_local.exists():
                raise FileNotFoundError(f"Local assets directory not found at {assets_dir_local}")
            file_list = [f.name for f in assets_dir_local.glob('*.csv')]

        for filename in file_list:
            equipment_name = os.path.splitext(os.path.basename(filename))[0]
            try:
                logger.info(f"Processing {equipment_name}")

                # Read data based on source
                if input_datasource == 's3':
                    data = read_csv_from_s3(minio_client, minio_bucket, filename)
                else:
                    data = read_csv_from_local(assets_dir_local / filename)

                if not data:
                    logger.warning(f"No valid data found for {equipment_name}")
                    continue

                # Create AAS and submodels
                aas, submodel = create_aas(equipment_name, data)
                cim_submodel = create_cim_submodel(config_data)
                grid_measurement_submodel = create_grid_measurement_submodel(config_data)

                aas.submodel.add(model.ModelReference.from_referable(cim_submodel))
                aas.submodel.add(model.ModelReference.from_referable(grid_measurement_submodel))

                # Define output file path for local storage
                output_file_path = output_dir_local / f"{sanitize_id_short(equipment_name)}.json"

                # Write to both local storage and MinIO
                write_aas_to_file(
                    [aas, submodel, cim_submodel, grid_measurement_submodel],
                    output_file_path,
                    minio_client=minio_client,
                    minio_bucket=minio_bucket
                )

                processed_count += 1
                logger.success(f"Completed processing {equipment_name}")

            except Exception as e:
                logger.error(f"Failed to process {filename}: {e}")
                continue

        logger.success(f"Completed AAS generation. Processed {processed_count} files.")

    except Exception as e:
        logger.critical(f"AAS generation failed: {e}")
        raise
