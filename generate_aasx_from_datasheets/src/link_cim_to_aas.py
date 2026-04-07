"""
Service 3: Link CIM with AAS (on CIM side)
- Consumes 'aasx.linked_to_cim' from RabbitMQ
- Writes <cim:IdentifiedObject.aasReference>globalAssetId</...> for matching MRID
- Emits 'cim.linked_to_aas'
"""
import os
import re
import json
import pika
from pathlib import Path
from typing import Optional
from loguru import logger
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
from rabbitmq_service import rabbitmq_service

# Use absolute paths within the container
GRID_FOLDER = Path("/app/Grids") / "1-LV-rural1--2-no_sw_EV_HP"
CIM_DIR = GRID_FOLDER / "CIM3"
FINAL_AAS_DIR = Path("/app/basyx_aas")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
EXCHANGE_NAME = "aas_events"

NS = {
    "cim": "http://iec.ch/TC57/CIM100#",
    "md":  "http://iec.ch/TC57/61970-552/ModelDescription/1#",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "eu":  "http://iec.ch/TC57/CIM100-European#"
}
for p, uri in NS.items():
    ET.register_namespace(p, uri)


def _find_eq_file() -> Optional[Path]:
    if not CIM_DIR.exists():
        logger.warning(f"CIM dir not found: {CIM_DIR}")
        return None
    for p in CIM_DIR.glob("*EQ*.xml"):
        return p
    return None


def _pretty_write(root: ET.Element, out_path: Path):
    xml_string = ET.tostring(root, encoding="utf-8")
    dom = minidom.parseString(xml_string)
    pretty_xml = dom.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")
    cleaned = re.sub(r"\n\s*\n", "\n", pretty_xml)
    out_path.write_text(cleaned, encoding="utf-8")

def link_cim_to_aas(payload: dict, emit_event: bool = True) -> dict:
    """
    Link CIM to AAS - can be called directly or via message
    """
    eq_file = _find_eq_file()
    if not eq_file:
        logger.error("No CIM EQ file found")
        return None

    mrid = payload.get("mrid")
    gaid = payload.get("globalAssetId")
    if not mrid or not gaid:
        logger.error("Missing MRID or globalAssetId in payload")
        return None

    tree = ET.parse(eq_file)
    root = tree.getroot()

    target = None
    # try mRID child
    for el in root.findall(".//cim:*", NS):
        mr = el.find("cim:IdentifiedObject.mRID", NS)
        if mr is not None and mr.text == mrid:
            target = el
            break
        rid = el.attrib.get(f"{{{NS['rdf']}}}ID", "").lstrip("_")
        if rid == mrid:
            target = el
            break

    if target is None:
        logger.warning(f"MRID {mrid} not found in CIM; skipping write")
        return {**payload, "cim_updated": False}

    # idempotent write
    aas_ref = target.find("cim:IdentifiedObject.aasReference", NS)
    if aas_ref is None:
        aas_ref = ET.SubElement(target, f"{{{NS['cim']}}}IdentifiedObject.aasReference")
    aas_ref.text = gaid

    _pretty_write(root, eq_file)
    logger.success(f"[Link CIM←AAS] Updated {eq_file.name} for MRID {mrid} with AAS GAID {gaid}")

    result = {**payload, "cim_updated": True, "cim_eq_path": str(eq_file)}

    if emit_event:
        try:
            rabbitmq_service.publish_message(
                exchange='aas_events',
                routing_key='cim.linked_to_aas',
                message=result
            )
            logger.success(f"[Link CIM←AAS] Emitted event to 'cim.linked_to_aas': {result}")
        except Exception as e:
            logger.error(f"[Link CIM←AAS] Failed to emit event: {e}")

    return result


def _load_aas(path: Path) -> dict:
    # If path is relative, look in the shared AAS directory
    if not path.is_absolute():
        path = FINAL_AAS_DIR / path.name
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_aas(data: dict, path: Path):
    # If path is relative, save to the shared AAS directory
    if not path.is_absolute():
        path = FINAL_AAS_DIR / path.name
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
