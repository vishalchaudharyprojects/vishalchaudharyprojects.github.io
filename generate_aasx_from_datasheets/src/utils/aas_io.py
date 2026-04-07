import json
from loguru import logger
from typing import List, Dict, Any, Optional
from basyx.aas import model


def read_aas_from_file(file_path: str) -> List[model.Referable]:
    """
    Simplified version - read only AAS and basic submodel structure.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            logger.debug(f"Read {len(content)} characters from {file_path}")
            data = json.loads(content)

        objects = []

        # Create basic Submodels (without elements for now)
        for sm_data in data.get('submodels', []):
            sm = model.Submodel(
                id_=sm_data['id'],
                id_short=sm_data.get('idShort', '')
            )
            objects.append(sm)

        # Create Asset Administration Shells
        for aas_data in data.get('assetAdministrationShells', []):
            asset_info = model.AssetInformation(
                asset_kind=model.AssetKind.INSTANCE,
                global_asset_id=aas_data['assetInformation']['globalAssetId']
            )

            aas = model.AssetAdministrationShell(
                id_=aas_data['id'],
                id_short=aas_data.get('idShort', ''),
                asset_information=asset_info
            )

            # Add simple submodel references
            for ref_data in aas_data.get('submodels', []):
                for key_data in ref_data.get('keys', []):
                    if key_data['type'] == 'Submodel':
                        try:
                            # Create the key first
                            key = model.Key(
                                type_=model.KeyTypes.SUBMODEL,
                                value=key_data['value']
                            )
                            # Create ModelReference with the key in a tuple
                            ref = model.ModelReference(
                                key=(key,),  # Use tuple instead of list
                                type_=model.ExternalReference
                            )
                            aas.submodel.add(ref)
                            break  # Just add one reference per entry
                        except Exception as e:
                            logger.debug(f"Could not add submodel reference: {e}")
                            continue

            objects.append(aas)

        logger.success(f"Read {len(objects)} objects from AAS file: {file_path}")
        return objects

    except Exception as e:
        logger.error(f"Failed to read AAS file {file_path}: {e}")
        raise


def _deserialize_submodel_element(element_data: Dict) -> Optional[model.SubmodelElement]:
    """
    Helper function to deserialize submodel elements from JSON data.
    """
    model_type = element_data.get('modelType')

    if model_type == 'Property':
        return model.Property(
            id_short=element_data['idShort'],
            value_type=_get_value_type(element_data.get('valueType', 'xs:string')),
            value=element_data.get('value')
        )

    elif model_type == 'SubmodelElementCollection':
        collection = model.SubmodelElementCollection(
            id_short=element_data['idShort']
        )

        # Recursively deserialize nested elements
        for nested_element_data in element_data.get('value', []):
            nested_element = _deserialize_submodel_element(nested_element_data)
            if nested_element:
                collection.value.add(nested_element)

        return collection

    elif model_type == 'ReferenceElement':
        ref_element = model.ReferenceElement(
            id_short=element_data['idShort']
        )

        # Handle reference if present
        if 'reference' in element_data:
            ref_data = element_data['reference']
            keys = []
            for key_data in ref_data.get('keys', []):
                try:
                    key = model.Key(
                        type_=model.KeyTypes(key_data['type']),
                        value=key_data['value']
                    )
                    keys.append(key)
                except Exception as e:
                    logger.debug(f"Could not create key for ReferenceElement: {e}")
                    continue

            if keys:
                try:
                    # Use tuple for keys and ExternalReference for type
                    ref_element.value = model.ModelReference(
                        key=tuple(keys),  # Use tuple instead of list
                        type_=model.ExternalReference
                    )
                except Exception as e:
                    logger.debug(f"Could not create ModelReference for ReferenceElement: {e}")

        return ref_element

    return None


def _get_value_type(value_type_str: str) -> model.datatypes:
    """
    Convert string value type to basyx datatype.
    """
    type_map = {
        'xs:string': model.datatypes.String,
        'xs:double': model.datatypes.Float,
        'xs:float': model.datatypes.Float,
        'xs:int': model.datatypes.Int,
        'xs:integer': model.datatypes.Int,
        'xs:boolean': model.datatypes.Boolean
    }
    return type_map.get(value_type_str, model.datatypes.String)


def _serialize_submodel_element(el: model.SubmodelElement) -> Optional[Dict[str, Any]]:
    """
    Helper function to serialize any SubmodelElement, handling nesting recursively
    for SubmodelElementCollection.
    """

    # --- Property Serialization ---
    if isinstance(el, model.Property):
        val = el.value
        # Determine value type for JSON serialization
        if isinstance(val, float):
            vt = "xs:double"
        elif isinstance(val, int):
            vt = "xs:int"
        else:
            vt = "xs:string"

        prop_dict = {
            "idShort": el.id_short,
            "modelType": "Property",
            "value": val,
            "valueType": vt
        }
        if el.description:
            prop_dict["description"] = [{"language": "en", "text": str(el.description)}]
        return prop_dict

    # --- ReferenceElement Serialization ---
    elif isinstance(el, model.ReferenceElement):
        ref_dict = {
            "idShort": el.id_short,
            "modelType": "ReferenceElement",
        }
        if el.description:
            ref_dict["description"] = [{"language": "en", "text": str(el.description)}]

        # Serialize the reference keys properly
        if hasattr(el, "value") and el.value and hasattr(el.value, "key"):
            ref_dict["reference"] = {
                "type": "ModelReference",
                "keys": [
                    {
                        "type": k.type.value if hasattr(k.type, "value") else str(k.type),
                        "value": k.value
                    }
                    for k in el.value.key
                ]
            }
        return ref_dict

    # --- SubmodelElementCollection Serialization (RECURSIVE CASE) ---
    elif isinstance(el, model.SubmodelElementCollection):
        collection_dict = {
            "idShort": el.id_short,
            "modelType": "SubmodelElementCollection",
            "value": []  # The 'value' key holds the elements in the collection in AAS JSON
        }
        if el.description:
            collection_dict["description"] = [{"language": "en", "text": str(el.description)}]

        # Recursively serialize inner elements
        for sub_el in el.value:
            # Call the helper function recursively to handle nested collections/properties/references
            serialized_sub_el = _serialize_submodel_element(sub_el)
            if serialized_sub_el:
                collection_dict["value"].append(serialized_sub_el)

        return collection_dict

    return None  # Return None for unsupported types


def write_aas_to_file(aas_objects: List[model.Referable], out_file):
    try:
        env = {"assetAdministrationShells": [], "submodels": [], "conceptDescriptions": []}
        aas_list = [o for o in aas_objects if isinstance(o, model.AssetAdministrationShell)]
        sm_list = [o for o in aas_objects if isinstance(o, model.Submodel)]

        # --- Serialize Submodels ---
        for sm in sm_list:
            sm_dict = {
                "idShort": sm.id_short,
                "modelType": "Submodel",
                "id": sm.id,
                "submodelElements": []
            }

            for el in sm.submodel_element:
                # Use the helper function to serialize all top-level elements
                serialized_el = _serialize_submodel_element(el)
                if serialized_el:
                    sm_dict["submodelElements"].append(serialized_el)

            env["submodels"].append(sm_dict)

        # --- Serialize Asset Administration Shells (AAS) ---
        for a in aas_list:
            a_dict = {
                "idShort": a.id_short,
                "modelType": "AssetAdministrationShell",
                "id": a.id,
                "assetInformation": {
                    "assetKind": "Instance",
                    "globalAssetId": a.asset_information.global_asset_id
                },
                "submodels": []
            }

            for ref in a.submodel or []:
                sm_id = next((k.value for k in ref.key if k.type == model.KeyTypes.SUBMODEL), None)
                if sm_id:
                    a_dict["submodels"].append({
                        "type": "ModelReference",
                        "keys": [{"type": "Submodel", "value": sm_id}]
                    })

            env["assetAdministrationShells"].append(a_dict)

        # --- Write to JSON ---
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(env, f, indent=4, ensure_ascii=False, default=str)

        logger.success(f"Wrote AAS JSON with nested collections: {out_file}")

    except Exception as e:
        logger.error(f"Write AAS JSON failed: {e}")
        raise