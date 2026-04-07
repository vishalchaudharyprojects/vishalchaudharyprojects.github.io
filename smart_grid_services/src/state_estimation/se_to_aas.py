# smart_grid_services/src/se_to_aas.py
import os
import json
import re
import time
import base64
import uuid
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import requests
from basyx.aas import model
from basyx.aas.adapter.json import read_aas_json_file, write_aas_json_file

logger = logging.getLogger(__name__)


# -------------------------------------------------------------------
# Helper: sanitize AAS JSON for BaSyx compatibility
# -------------------------------------------------------------------
def _sanitize_aas_json(raw_text: str) -> str:
    """
    Fix BaSyx JSON compatibility: ensure numeric 'value's are quoted strings
    when valueType is xs:double, xs:int, etc.
    """
    return re.sub(
        r'("value"\s*:\s*)(-?\d+\.?\d*)(\s*,\s*"valueType"\s*:\s*"xs:(?:double|int|float|decimal)")',
        lambda m: f'{m.group(1)}"{m.group(2)}"{m.group(3)}',
        raw_text,
    )


# -------------------------------------------------------------------
# AAS utilities
# -------------------------------------------------------------------
def _index_identifiables(objects: List[model.Identifiable]) -> Tuple[
    Dict[str, model.Identifiable], Dict[str, model.Submodel]]:
    """Quick indices by identifiable id, and a sub-index for submodels."""
    by_id = {}
    submodels = {}
    for obj in objects:
        by_id[obj.id] = obj
        if isinstance(obj, model.Submodel):
            submodels[obj.id] = obj
    return by_id, submodels


def _to_base64url(s: str) -> str:
    """Encode IDs to BaSyx base64url format (no padding)."""
    return base64.urlsafe_b64encode(s.encode("utf-8")).rstrip(b"=").decode("ascii")


def _push_to_basyx(aas_id: str, sm: dict, logger):
    """
    Robust BaSyx push:
    - Ensures AAS exists
    - Creates/updates submodel
    - Links submodel by updating AAS (not /submodels endpoint)
    - Registers AAS in both internal + UI registries
    - Registers Submodel in Submodel Registry
    - Forces BaSyx refresh for real-time UI update (for 2.0.0-SNAPSHOT)
    """
    basyx_url = os.getenv("BASYX_AAS_ENV_URL", "http://basyx-aas-env:8081")
    registry_url = os.getenv("BASYX_AAS_REGISTRY_URL", "http://basyx-aas-registry:8080")
    sm_registry_url = os.getenv("BASYX_SM_REGISTRY_URL", "http://basyx-sm-registry:8080")
    ui_registry_url = os.getenv("BASYX_UI_REGISTRY_URL", "http://localhost:8082")

    aas_id_raw = aas_id
    sm_id = sm["id"]
    sm_id_b64 = _to_base64url(sm_id)
    aas_id_b64 = _to_base64url(aas_id_raw)

    try:
        # --------------------------------------------------------------------------
        # 1️⃣ Ensure AAS exists in Environment
        # --------------------------------------------------------------------------
        aas_obj = {
            "id": aas_id_raw,
            "idShort": aas_id_raw,
            "modelType": "AssetAdministrationShell",
            "assetInformation": {
                "assetKind": "Instance",
                "globalAssetId": f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, aas_id_raw)}",
            },
        }

        resp = requests.post(
            f"{basyx_url}/shells",
            json=aas_obj,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        if resp.status_code not in (200, 201, 409):
            logger.warning(f"AAS {aas_id_raw} not created: ({resp.status_code}) {resp.text}")
        else:
            logger.info(f"AAS {aas_id_raw} ensured in BaSyx")

        # Wait until visible
        for _ in range(10):
            check = requests.get(f"{basyx_url}/shells/{aas_id_b64}", timeout=5)
            if check.status_code == 200:
                break
            time.sleep(1)
        else:
            logger.warning(f"AAS {aas_id_raw} still not visible after retries")

        # --------------------------------------------------------------------------
        # 2️⃣ Create or update Submodel
        # --------------------------------------------------------------------------
        r_post = requests.post(
            f"{basyx_url}/submodels",
            json=sm,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )

        if r_post.status_code == 409:
            r_put = requests.put(
                f"{basyx_url}/submodels/{sm_id_b64}",
                json=sm,
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            if r_put.status_code not in (200, 204):
                logger.warning(f"Submodel update failed ({r_put.status_code}): {r_put.text}")
            else:
                logger.info(f"BaSyx submodel updated: {sm_id}")
        elif r_post.status_code in (200, 201):
            logger.info(f"BaSyx submodel created: {sm_id}")
        else:
            logger.warning(f"Submodel push failed ({r_post.status_code}): {r_post.text}")

        # --------------------------------------------------------------------------
        # 3️⃣ Link Submodel to AAS
        # --------------------------------------------------------------------------
        aas_get = requests.get(f"{basyx_url}/shells/{aas_id_b64}", timeout=10)
        if aas_get.status_code == 200:
            aas_data = aas_get.json()

            submodel_refs = aas_data.get("submodels", [])
            existing_refs = [r["keys"][0]["value"] for r in submodel_refs if "keys" in r]

            if sm_id not in existing_refs:
                submodel_refs.append({
                    "type": "ModelReference",
                    "keys": [{"type": "Submodel", "value": sm_id}],
                })
                aas_data["submodels"] = submodel_refs

                put_resp = requests.put(
                    f"{basyx_url}/shells/{aas_id_b64}",
                    json=aas_data,
                    headers={"Content-Type": "application/json"},
                    timeout=10,
                )
                if put_resp.status_code in (200, 204):
                    logger.info(f"Linked {sm_id} → {aas_id_raw} via AAS update")
                else:
                    logger.warning(f"Failed linking via PUT ({put_resp.status_code}): {put_resp.text}")
            else:
                logger.info(f"Submodel {sm_id} already linked to {aas_id_raw}")
        else:
            logger.warning(f"Could not retrieve AAS {aas_id_raw} to link submodel: {aas_get.status_code}")

        # --------------------------------------------------------------------------
        # 4️⃣ Register AAS + Submodel in Registries
        # --------------------------------------------------------------------------
        descriptor = {
            "id": aas_id_raw,
            "idShort": aas_id_raw,
            "endpoints": [
                {
                    "interface": "AAS-3.0",
                    "protocolInformation": {
                        "href": f"{basyx_url}/shells/{aas_id_b64}",
                        "endpointProtocol": "HTTP",
                        "endpointProtocolVersion": ["1.1"],
                    },
                }
            ],
        }

        reg_resp = requests.put(
            f"{registry_url}/shell-descriptors/{aas_id_b64}",
            json=descriptor,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        if reg_resp.status_code in (200, 201, 204):
            logger.info(f"AAS {aas_id_raw} registered in internal registry")
        else:
            logger.warning(f"Registry update failed ({reg_resp.status_code}): {reg_resp.text}")

        # Register submodel descriptor
        sm_descriptor = {
            "id": sm_id,
            "idShort": sm.get("idShort", sm_id),
            "endpoints": [
                {
                    "interface": "AAS-3.0",
                    "protocolInformation": {
                        "href": f"{basyx_url}/submodels/{sm_id_b64}",
                        "endpointProtocol": "HTTP",
                        "endpointProtocolVersion": ["1.1"],
                    },
                }
            ],
        }

        sm_reg = requests.put(
            f"{sm_registry_url}/submodel-descriptors/{sm_id_b64}",
            json=sm_descriptor,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        if sm_reg.status_code in (200, 201, 204):
            logger.info(f"Submodel {sm_id} registered in Submodel Registry")
        else:
            logger.warning(f"Submodel registry update failed ({sm_reg.status_code}): {sm_reg.text}")

        # Sync with Web UI registry
        try:
            if ui_registry_url:
                ui_reg = requests.put(
                    f"{ui_registry_url}/shell-descriptors/{aas_id_b64}",
                    json=descriptor,
                    headers={"Content-Type": "application/json"},
                    timeout=10,
                )
                if ui_reg.status_code in (200, 201, 204):
                    logger.info(f"AAS {aas_id_raw} synced to UI registry at {ui_registry_url}")
                else:
                    logger.warning(f"UI registry sync failed ({ui_reg.status_code}): {ui_reg.text}")
        except Exception as e:
            logger.warning(f"Could not sync AAS to UI registry: {e}")

        # --------------------------------------------------------------------------
        # 5️⃣ Force BaSyx refresh for real-time UI update
        # --------------------------------------------------------------------------
        try:
            get_aas = requests.get(f"{basyx_url}/shells/{aas_id_b64}", timeout=5)
            if get_aas.status_code == 200:
                aas_data = get_aas.json()
                refresh_resp = requests.put(
                    f"{basyx_url}/shells/{aas_id_b64}",
                    json=aas_data,
                    headers={"Content-Type": "application/json"},
                    timeout=10,
                )
                if refresh_resp.status_code in (200, 204):
                    logger.info("🔁 BaSyx environment refreshed successfully (UI should update live)")
                else:
                    logger.warning(f"BaSyx refresh PUT failed ({refresh_resp.status_code}): {refresh_resp.text}")
            else:
                logger.warning(f"BaSyx refresh skipped (GET {get_aas.status_code}): {get_aas.text}")
        except Exception as ex:
            logger.warning(f"Could not perform BaSyx refresh: {ex}")

    except Exception as e:
        logger.warning(f"Could not push update to BaSyx: {e}")


def _iter_submodels_of_shell(aas: model.AssetAdministrationShell, by_id: Dict[str, model.Identifiable]):
    """Yield Submodel objects referenced by a given AAS (handles tuple or Key objects)."""
    for sm_ref in aas.submodel:
        sm_id = None
        if hasattr(sm_ref, "keys"):
            key_obj = sm_ref.keys[0]
            # key_obj may be a tuple, Key, or object with .value
            if isinstance(key_obj, tuple):
                # typical shape ('Submodel', 'Submodel_TechnicalData_...')
                sm_id = key_obj[-1]
            elif hasattr(key_obj, "value"):
                sm_id = key_obj.value
        elif hasattr(sm_ref, "key"):
            key_attr = sm_ref.key
            if isinstance(key_attr, (list, tuple)):
                k = key_attr[0]
                sm_id = k[-1] if isinstance(k, tuple) else getattr(k, "value", None)
            else:
                sm_id = getattr(key_attr, "value", None)

        if not sm_id:
            continue

        sm = by_id.get(sm_id)
        if isinstance(sm, model.Submodel):
            yield sm


def _find_technical_data_submodel(aas: model.AssetAdministrationShell, by_id: Dict[str, model.Identifiable]) -> \
Optional[model.Submodel]:
    """Find any submodel that contains TechnicalData or cim_asset_type property."""
    for sm_ref in aas.submodel:
        sm_id = None
        if hasattr(sm_ref, "keys"):
            sm_id = sm_ref.keys[0].value
        elif hasattr(sm_ref, "key"):
            key_attr = sm_ref.key
            sm_id = key_attr[0].value if isinstance(key_attr, list) else key_attr.value
        sm = by_id.get(sm_id)
        if not isinstance(sm, model.Submodel):
            continue

        # Heuristic: look for 'TechnicalData' or a 'cim_asset_type' property
        if sm.id_short and "TechnicalData" in sm.id_short:
            return sm
        for sme in getattr(sm, "submodel_element", []):
            if isinstance(sme, model.Property) and sme.id_short == "cim_asset_type":
                return sm
    return None


def _is_connectivity_node_shell(aas: model.AssetAdministrationShell, tech_sm: Optional[model.Submodel]) -> bool:
    """Determine if a shell represents a ConnectivityNode."""
    # Option 1: explicit type in asset_information
    atype = (getattr(aas.asset_information, "asset_type", "") or "").strip()
    if atype in ("CIM_ConnectivityNode", "ConnectivityNode"):
        return True

    # Option 2: submodel property
    if tech_sm:
        cim_type = (_get_prop(tech_sm, "cim_asset_type") or "").strip()
        if cim_type == "ConnectivityNode":
            return True

    # Option 3: idShort hint
    if tech_sm and "ConnectivityNode" in (tech_sm.id_short or ""):
        return True

    return False


def _get_prop(sm: model.Submodel, id_short: str) -> Optional[str]:
    """Get string property value from a submodel by id_short (if present)."""
    for sme in sm.submodel_element:
        if isinstance(sme, model.Property) and sme.id_short == id_short:
            # All BaSyx values can be str/float; coerce to str for IDs
            return str(sme.value) if sme.value is not None else None
    return None


def _ensure_state_sm(aas: model.AssetAdministrationShell, objects: List[model.Identifiable]) -> model.Submodel:
    """Find or create the 'StateEstimation' submodel on this shell."""
    for sm_ref in aas.submodel:
        sm = next(
            (o for o in objects if isinstance(o, model.Submodel) and o.id == sm_ref.keys[0].value),
            None
        )
        if sm and sm.id_short == "StateEstimation":
            return sm

    sm = model.Submodel(
        id_=f"{aas.id}_SM_StateEstimation_{uuid.uuid4().hex[:8]}",
        id_short="StateEstimation",
        description="Estimated states (voltages) per timestamp"
    )
    aas.submodel.add(model.ModelReference.from_referable(sm))
    objects.append(sm)
    return sm


# -------------------------------------------------------------------
# Main: write state estimation results into AAS JSON
# -------------------------------------------------------------------
def write_estimates_to_aas(aas_json: Path, se_results: dict, net):
    logger.info(f"Loading AAS JSON from: {aas_json}")
    with aas_json.open("r", encoding="utf-8") as f:
        aas_data = json.load(f)

    submodels = aas_data.get("submodels", [])
    shells = aas_data.get("assetAdministrationShells", [])
    logger.info(f"AAS JSON root type: {type(aas_data)}; "
                f"submodels found: {len(submodels)}; shells: {len(shells)}")

    # --- 1. Map ConnectivityNode TechnicalData submodels ---
    tech_sm_by_mrid = {}
    for sm in submodels:
        if not isinstance(sm, dict) or sm.get("modelType") != "Submodel":
            continue
        elems = sm.get("submodelElements", [])
        cim_type = next((e.get("value") for e in elems if e.get("idShort") == "cim_asset_type"), None)
        mrid = next((e.get("value") for e in elems if e.get("idShort") == "asset_mrid"), None)
        if cim_type == "ConnectivityNode" and mrid:
            tech_sm_by_mrid[mrid.lower()] = sm

    logger.info(f"ConnectivityNode TechnicalData submodels discovered: {len(tech_sm_by_mrid)}")

    # --- 2. Map AAS shells → which TechnicalData they contain ---
    shell_by_mrid = {}
    for aas in shells:
        if not isinstance(aas, dict):
            continue
        for sm_ref in aas.get("submodels", []):
            keys = sm_ref.get("keys", [])
            if keys:
                sm_id = keys[0].get("value")
                # see if this submodel is a TechnicalData CN one
                for mrid, sm in tech_sm_by_mrid.items():
                    if sm.get("id") == sm_id:
                        shell_by_mrid[mrid] = aas

    logger.info(f"AAS shells linked to ConnectivityNodes: {len(shell_by_mrid)}")

    # --- 3. Build bus→mRID map ---
    bus_to_mrid = {
        int(i): str(row.get("name", "")).strip().lstrip("_").lower()
        for i, row in net.bus.iterrows()
        if not str(row.get("name", "")).startswith("synthetic_")
    }

    timestamp = datetime.now(timezone.utc).isoformat()
    vm_map = se_results.get("vm_pu", {})
    va_map = se_results.get("va_degree", {})
    count = 0

    # --- 4. Inject new submodels and link them ---
    for idx, vm in vm_map.items():
        idx = int(idx)
        mrid = bus_to_mrid.get(idx)
        if not mrid:
            continue
        aas = shell_by_mrid.get(mrid)
        if not aas:
            continue

        new_sm_id = f"Submodel_StateEstimation_{mrid}"
        new_sm = {
            "idShort": f"StateEstimation_{mrid}",
            "modelType": "Submodel",
            "id": new_sm_id,
            "submodelElements": [
                {
                    "idShort": "timestamp",
                    "modelType": "Property",
                    "valueType": "xs:string",
                    "value": timestamp,
                },
                {
                    "idShort": "vm_pu",
                    "modelType": "Property",
                    "valueType": "xs:float",
                    "value": str(float(vm)),
                },
                {
                    "idShort": "va_degree",
                    "modelType": "Property",
                    "valueType": "xs:float",
                    "value": str(float(va_map.get(idx, 0.0))),
                },
            ],
        }

        # Append new submodel to global submodels list
        submodels.append(new_sm)

        # Add reference in AAS shell
        aas.setdefault("submodels", []).append({
            "type": "ModelReference",
            "keys": [
                {
                    "type": "Submodel",
                    "value": new_sm_id
                }
            ]
        })

        count += 1

    # --- 5. Save back ---
    with aas_json.open("w", encoding="utf-8") as f:
        json.dump(aas_data, f, indent=4)

    # Push live update
    _push_to_basyx(aas["id"], new_sm, logger)

    logger.info(f"✅ Created and linked SE submodels for {count} nodes into AAS: {aas_json}")
