import uuid
from pathlib import Path
from typing import Dict, List, Optional
from loguru import logger
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import re
from collections import defaultdict
from basyx.aas import model
from utils.aas_io import write_aas_to_file

# Namespace handling for CIM XML
NS = {
    "cim": "http://iec.ch/TC57/CIM100#",
    "md": "http://iec.ch/TC57/61970-552/ModelDescription/1#",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "eu": "http://iec.ch/TC57/CIM100-European#"
}

class CIMEQToAASXConverter:
    def __init__(self, cim_eq_file: Path, output_dir: Path, cim_gl_file: Optional[Path] = None):
        self.cim_eq_file = cim_eq_file
        self.cim_gl_file = cim_gl_file

        if output_dir is None:
            self.output_dir = Path("/app/basyx_aas")
        else:
            self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.tree = ET.parse(cim_eq_file)
        self.root = self.tree.getroot()

        self._element_cache = {}
        self._build_element_cache()

        self.location_data: Dict[str, Dict[str, float]] = {}
        if self.cim_gl_file:
            self._parse_gl_file()

        # Store AAS references for bidirectional linking
        # mapping: CIM MRID -> {"global_asset_id": ..., "aas_id": ...}
        self.aas_references: Dict[str, Dict[str, str]] = {}  # CIM MRID -> dict

    def _build_element_cache(self):
        """Build a cache of all elements by their ID for faster lookup."""
        for elem in self.root.iter():
            elem_id = elem.get(f"{{{NS['rdf']}}}ID")
            if elem_id:
                self._element_cache[elem_id] = elem

    def _pretty_write_cim(self, root: ET.Element, out_path: Path):
        """Write CIM XML with proper formatting."""
        xml_string = ET.tostring(root, encoding="utf-8")
        dom = minidom.parseString(xml_string)
        pretty_xml = dom.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")
        cleaned = re.sub(r"\n\s*\n", "\n", pretty_xml)
        out_path.write_text(cleaned, encoding="utf-8")

    def _add_aas_reference_to_cim(self, cim_element: ET.Element, global_asset_id: str, aas_id: str):
        """Add AAS references to CIM element (globalAssetId + aasIdentifier) and store mapping."""
        # Store the reference for later use
        elem_id = cim_element.get(f"{{{NS['rdf']}}}ID", "").lstrip("_")
        if elem_id:
            # store both values so submodels can reference them later
            self.aas_references[elem_id] = {"global_asset_id": global_asset_id, "aas_id": aas_id}

        # Add or update globalAssetId element under IdentifiedObject
        global_elem = cim_element.find("cim:IdentifiedObject.globalAssetId", NS)
        if global_elem is None:
            global_elem = ET.SubElement(cim_element, f"{{{NS['cim']}}}IdentifiedObject.globalAssetId")
        global_elem.text = global_asset_id

        # Add or update aasIdentifier element under IdentifiedObject
        aasid_elem = cim_element.find("cim:IdentifiedObject.aasIdentifier", NS)
        if aasid_elem is None:
            aasid_elem = ET.SubElement(cim_element, f"{{{NS['cim']}}}IdentifiedObject.aasIdentifier")
        aasid_elem.text = aas_id

        logger.debug(
            f"Added AAS references to CIM element {elem_id}: globalAssetId={global_asset_id}, aasIdentifier={aas_id}")

    def _update_cim_file_with_aas_references(self):
        """Update the original CIM EQ file with all AAS references."""
        try:
            self._pretty_write_cim(self.root, self.cim_eq_file)
            logger.success(f"Updated CIM EQ file with {len(self.aas_references)} AAS references: {self.cim_eq_file}")
        except Exception as e:
            logger.error(f"Failed to update CIM file with AAS references: {e}")

    def _parse_gl_file(self):
        """
        Parse the CIM GL file to extract location data.

        Robust features:
          - collects PositionPoint coords
          - maps Location -> PowerSystemResources (including VoltageLevel -> Substation)
          - maps Location -> Terminals -> ConnectivityNode and ConductingEquipment
          - tolerates rdf:resource with/without '#' and leading underscores
          - logs detailed info for debugging
        """
        if not self.cim_gl_file or not self.cim_gl_file.is_file():
            logger.warning("No GL file provided or GL file not found.")
            return

        logger.info(f"Parsing Geographical Location file: {self.cim_gl_file.name}")
        gl_tree = ET.parse(self.cim_gl_file)
        gl_root = gl_tree.getroot()

        position_points: Dict[str, Dict[str, float]] = {}

        # Helper to normalize IDs from rdf:resource values
        def _normalize_ref(ref: Optional[str]) -> Optional[str]:
            if not ref:
                return None
            # ref may be like '#id', '_id', 'id', or 'file#id'
            ref = ref.split('#')[-1]
            return ref.lstrip("_")

        # 1) Collect coordinates from PositionPoint elements
        for pp in gl_root.findall(".//cim:PositionPoint", NS):
            loc_ref = pp.find("cim:PositionPoint.Location", NS)
            if loc_ref is None:
                continue
            loc_ref_attr = loc_ref.get(f"{{{NS['rdf']}}}resource") or loc_ref.get("resource")
            loc_id = _normalize_ref(loc_ref_attr)
            x_pos = pp.find("cim:PositionPoint.xPosition", NS)
            y_pos = pp.find("cim:PositionPoint.yPosition", NS)
            if loc_id and x_pos is not None and y_pos is not None:
                try:
                    position_points[loc_id] = {"x": float(x_pos.text), "y": float(y_pos.text)}
                except (TypeError, ValueError):
                    logger.warning(f"Invalid coordinates for PositionPoint linked to Location {loc_id}: "
                                   f"x='{x_pos.text}' y='{y_pos.text}'")

        logger.debug(f"Collected {len(position_points)} PositionPoint coordinate entries.")

        # Prepare a set to collect location links we created (for dedup/logging)
        linked_locations = set()
        unmatched_locations = []

        # 2) Iterate Location entries and try several linking strategies
        for loc in gl_root.findall(".//cim:Location", NS):
            loc_id = loc.get(f"{{{NS['rdf']}}}ID")
            if not loc_id:
                continue
            loc_id = loc_id.lstrip("_")
            if loc_id not in position_points:
                unmatched_locations.append(loc_id)
                continue

            coords = position_points[loc_id]

            # A) PowerSystemResources direct link -> map to that PSR ID
            psr_elems = loc.findall("cim:Location.PowerSystemResources", NS)
            for psr_elem in psr_elems:
                psr_ref = psr_elem.get(f"{{{NS['rdf']}}}resource") or psr_elem.get("resource")
                psr_id = _normalize_ref(psr_ref)
                if not psr_id:
                    continue

                # If PSR is a VoltageLevel, find its container and contained equipment
                psr_elem_from_eq = self._element_cache.get(psr_id) or self._element_cache.get(f"_{psr_id}")
                if psr_elem_from_eq is not None and psr_elem_from_eq.tag.endswith("VoltageLevel"):
                    voltage_level_id = psr_id
                    # Map the parent Substation
                    sub_ref = psr_elem_from_eq.find("cim:VoltageLevel.Substation", NS)
                    if sub_ref is not None:
                        sub_id = _normalize_ref(sub_ref.get(f"{{{NS['rdf']}}}resource") or sub_ref.get("resource"))
                        if sub_id:
                            self.location_data[sub_id] = coords
                            linked_locations.add(sub_id)
                            logger.debug(f"Location {loc_id} -> VoltageLevel {voltage_level_id} -> Substation {sub_id}")

                    # Find and map all equipment within this VoltageLevel
                    for equip_elem in self.root.findall(".//*[cim:Equipment.EquipmentContainer]", NS):
                        container_ref_elem = equip_elem.find("cim:Equipment.EquipmentContainer", NS)
                        container_ref = container_ref_elem.get(f"{{{NS['rdf']}}}resource")
                        container_id = _normalize_ref(container_ref)
                        if container_id == voltage_level_id:
                            equip_id_raw = equip_elem.get(f"{{{NS['rdf']}}}ID")
                            equip_id = _normalize_ref(equip_id_raw)
                            if equip_id:
                                self.location_data[equip_id] = coords
                                linked_locations.add(equip_id)
                                equip_type = self.extract_asset_type(equip_elem)
                                logger.debug(
                                    f"Location {loc_id} -> VoltageLevel {voltage_level_id} -> {equip_type} {equip_id}")
                else:
                    # General PSR mapping (e.g., for ACLineSegment not in a VoltageLevel)
                    self.location_data[psr_id] = coords
                    linked_locations.add(psr_id)
                    logger.debug(f"Location {loc_id} -> PowerSystemResource {psr_id}")

            # B) Terminals mapping: Location.Terminals -> Terminal -> ConnectivityNode / ConductingEquipment
            term_elems = loc.findall("cim:Location.Terminals", NS)
            for term_elem in term_elems:
                term_ref = term_elem.get(f"{{{NS['rdf']}}}resource") or term_elem.get("resource")
                terminal_id = _normalize_ref(term_ref)
                if not terminal_id:
                    continue

                terminal_elem_from_eq = self._element_cache.get(terminal_id) or self._element_cache.get(
                    f"_{terminal_id}")
                if terminal_elem_from_eq is None:
                    continue

                # ConnectivityNode
                node_ref = terminal_elem_from_eq.find("cim:Terminal.ConnectivityNode", NS)
                if node_ref is not None:
                    node_id = _normalize_ref(node_ref.get(f"{{{NS['rdf']}}}resource") or node_ref.get("resource"))
                    if node_id:
                        self.location_data[node_id] = coords
                        linked_locations.add(node_id)
                        logger.debug(f"Location {loc_id} -> Terminal {terminal_id} -> ConnectivityNode {node_id}")

                # ConductingEquipment
                equip_ref = terminal_elem_from_eq.find("cim:Terminal.ConductingEquipment", NS)
                if equip_ref is not None:
                    equip_id = _normalize_ref(equip_ref.get(f"{{{NS['rdf']}}}resource") or equip_ref.get("resource"))
                    if equip_id:
                        self.location_data[equip_id] = coords
                        linked_locations.add(equip_id)
                        logger.debug(f"Location {loc_id} -> Terminal {terminal_id} -> ConductingEquipment {equip_id}")

        # --- Post-processing: propagate locations for missing asset types ---

        # (A) Substation propagation — for equipment directly under substations
        for loc_id, coords in list(self.location_data.items()):
            elem = self._element_cache.get(loc_id)
            if elem is not None and elem.tag.endswith("Substation"):
                substation_id = loc_id
                for equip_elem in self._find_substation_equipment(substation_id):
                    eid = equip_elem.get(f"{{{NS['rdf']}}}ID", "").lstrip("_")
                    if eid and eid not in self.location_data:
                        self.location_data[eid] = coords
                        linked_locations.add(eid)
                        logger.debug(f"Propagated location {loc_id} -> Substation {substation_id} -> Equipment {eid}")

        # (B) ConnectivityNode propagation — assign location via its container or connected equipment
        for node_elem in self.root.findall(".//cim:ConnectivityNode", NS):
            node_id = node_elem.get(f"{{{NS['rdf']}}}ID", "").lstrip("_")

            # If the node already has a location, skip
            if node_id in self.location_data:
                continue

            # 1) Try to infer location via its container (VoltageLevel, Bay, etc.)
            container_ref_elem = node_elem.find("cim:ConnectivityNode.ConnectivityNodeContainer", NS)
            if container_ref_elem is not None:
                container_ref = container_ref_elem.get(f"{{{NS['rdf']}}}resource", "")
                container_id = container_ref.lstrip("#_")
                if container_id in self.location_data:
                    self.location_data[node_id] = self.location_data[container_id]
                    linked_locations.add(node_id)
                    logger.debug(f"Location propagated via container {container_id} -> ConnectivityNode {node_id}")
                    continue  # Done if found

            # 2) Try to infer via connected equipment (ACLineSegment, etc.)
            connected_equipment = self.get_connected_equipment_for_node(node_id)
            for equip in connected_equipment:
                eid = equip["id"]
                if eid in self.location_data:
                    self.location_data[node_id] = self.location_data[eid]
                    linked_locations.add(node_id)
                    logger.debug(f"Location propagated from connected equipment {eid} -> ConnectivityNode {node_id}")
                    break

        # (C) ConnectivityNode → connected equipment (e.g., ACLineSegment)
        for node_id, coords in list(self.location_data.items()):
            node_elem = self._element_cache.get(node_id)
            if node_elem is not None and node_elem.tag.endswith("ConnectivityNode"):
                connected_equipment = self.get_connected_equipment_for_node(node_id)
                for equip in connected_equipment:
                    eid = equip["id"]
                    if eid not in self.location_data:
                        self.location_data[eid] = coords
                        linked_locations.add(eid)
                        logger.debug(f"Propagated location {node_id} -> connected equipment {eid}")

        # (D) Second pass: ensure ConnectivityNodes that received their locations late
        # also propagate them to connected equipment (like transformers and line segments)
        for node_id, coords in list(self.location_data.items()):
            node_elem = self._element_cache.get(node_id)
            if node_elem is not None and node_elem.tag.endswith("ConnectivityNode"):
                connected_equipment = self.get_connected_equipment_for_node(node_id)
                for equip in connected_equipment:
                    eid = equip["id"]
                    if eid not in self.location_data:
                        self.location_data[eid] = coords
                        linked_locations.add(eid)
                        logger.debug(
                            f"[2nd pass] Location propagated from ConnectivityNode {node_id} -> connected equipment {eid}"
                        )

        # --- Final logging summary ---
        logger.success(f"Parsed {len(linked_locations)} distinct location links from GL file (with propagation).")

        unmatched_locations = [l for l in position_points if l not in linked_locations]
        if unmatched_locations:
            logger.debug(
                f"Locations with position points but no asset links found: {unmatched_locations[:50]} (showing up to 50)")

        # Debug summary of keys (limited)
        logger.debug(f"Final location_data keys sample: {list(self.location_data.keys())[:50]}")

    # --- HELPER METHODS for sanitizing, extracting info (unchanged) ---
    def sanitize_id_short(self, s: str) -> str:
        import re
        s = re.sub(r'[^a-zA-Z0-9_]', '_', s.strip())
        s = re.sub(r'_+', '_', s)
        return s

    def extract_asset_type(self, element: ET.Element) -> str:
        tag = element.tag.split('}')[-1] if '}' in element.tag else element.tag
        return tag

    def get_element_name(self, element: ET.Element) -> str:
        name_elem = element.find("cim:IdentifiedObject.name", NS)
        return name_elem.text if name_elem is not None else ""

        # --- NEW HELPER METHODS for creating location and registry submodels ---

    def create_registry_submodel(self, id_short: str, description: str) -> tuple[
        model.Submodel, model.SubmodelElementCollection]:
        """Creates an empty registry submodel with a collection to hold references."""
        registry_sm = model.Submodel(id_=f"Submodel_{id_short}", id_short=id_short, description=description)
        registry_entries = model.SubmodelElementCollection(
            id_short="RegistryEntries",
            description=f"A collection of references to all {id_short.replace('Registry', '')} instances."
        )
        registry_sm.submodel_element.add(registry_entries)
        return registry_sm, registry_entries

    def create_netzlokation_submodel(self, node_element: ET.Element, coords: Dict[str, float]) -> model.Submodel:
        """Creates a detailed Netzlokation submodel for a connectivity node with arbitrary measurements."""
        node_id = node_element.get(f"{{{NS['rdf']}}}ID", "").lstrip("_")
        node_name = self.get_element_name(node_element) or f"ConnectionPoint_{node_id}"

        # Generate arbitrary measurements for the connectivity node
        voltage_level = 400.0  # Arbitrary voltage level in V
        max_power = 1000.0  # Arbitrary max power in kW

        sm = model.Submodel(
            id_=f"Submodel_Netzlokation_{self.sanitize_id_short(node_id)}",
            id_short=f"Netzlokation_{self.sanitize_id_short(node_name)}",
            description=f"Physical grid connection point (Netzlokation) for connectivity node {node_name}"
        )

        sm.submodel_element.add(
            model.Property(id_short="NetzlokationID", value_type=model.datatypes.String, value=node_id))
        sm.submodel_element.add(
            model.Property(id_short="x_position", value_type=model.datatypes.Float, value=coords.get('x', 0.0)))
        sm.submodel_element.add(
            model.Property(id_short="y_position", value_type=model.datatypes.Float, value=coords.get('y', 0.0)))
        sm.submodel_element.add(
            model.Property(id_short="voltage_level", value_type=model.datatypes.Float, value=voltage_level))
        sm.submodel_element.add(
            model.Property(id_short="max_power_kw", value_type=model.datatypes.Float, value=max_power))

        return sm

    def create_messlokation_submodel(self, node_id_short: str, node_id: str) -> model.Submodel:
        """Creates a Messlokation submodel for a connectivity node (shared by all connected assets)."""
        # Generate consistent melo_id based on node ID for all assets connected to this node
        if node_id_short == "LV1_101_Bus_2":
            melo_id = "DETAF100000000001001EMH0015652689"
        elif node_id_short == "LV1_101_Bus_7":
            melo_id = "DETAF100000000001001EMH0013150392"
        else:
            melo_id = f"DE001{node_id_short[:20].upper()}"

        sm = model.Submodel(
            id_=f"Submodel_Messlokation_{self.sanitize_id_short(node_id)}",
            id_short=f"Messlokation_{node_id_short}",
            description=f"Metering point (Messlokation) for connectivity node {node_id_short}"
        )
        sm.submodel_element.add(
            model.Property(id_short="MesslokationID", value_type=model.datatypes.String, value=melo_id))

        return sm

    def create_marktlokation_submodel(self, asset_id_short: str, asset_type: str) -> model.Submodel:
        """Creates a Marktlokation submodel with type-specific ID pattern."""
        if asset_type in ["ConformLoad"]:
            # Load assets
            malo_id = f"DE002LOAD{asset_id_short[:15].upper()}"
        elif asset_type in ["PhotoVoltaicUnit", "BatteryUnit", "ExternalNetworkInjection"]:
            # Generating assets
            malo_id = f"DE002GEN{asset_id_short[:15].upper()}"
        else:
            # Other assets
            malo_id = f"DE002OTHER{asset_id_short[:15].upper()}"

        sm = model.Submodel(
            id_=f"Submodel_Marktlokation_{self.sanitize_id_short(asset_id_short)}",
            id_short=f"Marktlokation_{asset_id_short}",
            description=f"Market point (Marktlokation) for {asset_type} {asset_id_short}"
        )
        sm.submodel_element.add(
            model.Property(id_short="MarktlokationID", value_type=model.datatypes.String, value=malo_id))
        return sm

    def find_terminals_for_connection_point(self, node_id: str) -> List[ET.Element]:
        """Find all terminals connected to a specific connection point."""
        terminals = []
        all_terminals = self.root.findall(".//cim:Terminal", NS)
        for terminal in all_terminals:
            connection_point_ref = terminal.find("cim:Terminal.ConnectivityNode", NS)
            if connection_point_ref is not None:
                ref_id = connection_point_ref.get(f"{{{NS['rdf']}}}resource", "").lstrip("#")
                if ref_id == node_id or ref_id == f"_{node_id}" or ref_id.lstrip("_") == node_id:
                    terminals.append(terminal)
        return terminals

    def _find_terminals_for_equipment(self, equipment_id: str) -> List[ET.Element]:
        """Finds all terminals belonging to a specific piece of conducting equipment."""
        terminals = []
        possible_ids = {equipment_id, f"_{equipment_id}"}

        for terminal in self.root.findall(".//cim:Terminal", NS):
            equip_ref = terminal.find("cim:Terminal.ConductingEquipment", NS)
            if equip_ref is None:
                continue

            ref_id = equip_ref.get(f"{{{NS['rdf']}}}resource", "")
            ref_id = ref_id.split("#")[-1].lstrip("_")

            if ref_id in possible_ids:
                terminals.append(terminal)

        return terminals

    def get_connected_equipment_for_node(self, node_id: str) -> List[Dict]:
        """Get detailed information about equipment connected to a connection point."""
        connected_equipment = []
        terminals = self.find_terminals_for_connection_point(node_id)
        for terminal in terminals:
            equip_ref = terminal.find("cim:Terminal.ConductingEquipment", NS)
            if equip_ref is not None:
                equip_ref_attr = equip_ref.get(f"{{{NS['rdf']}}}resource", "")
                equip_id = equip_ref_attr.lstrip("#") if equip_ref_attr else ""
                if equip_id:
                    equip = self._element_cache.get(equip_id) or self._element_cache.get(f"_{equip_id}")
                    if equip is not None:
                        connected_equipment.append({
                            "id": equip_id.lstrip("_"),
                            "name": self.get_element_name(equip) or equip_id,
                            "type": self.extract_asset_type(equip),
                            "terminal_id": terminal.get(f"{{{NS['rdf']}}}ID", "").lstrip("_")
                        })
        return connected_equipment

    def _find_substation_equipment(self, substation_id: str) -> List[ET.Element]:
        """Find all equipment that belongs to a specific substation."""
        equipment_in_substation = []
        possible_ids = {substation_id, f"_{substation_id}"}
        voltage_levels = [
            vl.get(f"{{{NS['rdf']}}}ID", "").lstrip("_")
            for vl in self.root.findall(".//cim:VoltageLevel", NS)
            if vl.find("cim:VoltageLevel.Substation", NS) is not None and
               vl.find("cim:VoltageLevel.Substation", NS).get(f"{{{NS['rdf']}}}resource", "").lstrip(
                   "#_") in possible_ids
        ]

        for elem in self.root.findall(".//*[cim:Equipment.EquipmentContainer]", NS):
            container_ref = elem.find("cim:Equipment.EquipmentContainer", NS)
            if container_ref is not None:
                ref_id = container_ref.get(f"{{{NS['rdf']}}}resource", "").lstrip("#_")
                if ref_id in possible_ids or ref_id in voltage_levels:
                    equipment_in_substation.append(elem)
        logger.info(f"Substation {substation_id} contains {len(equipment_in_substation)} equipment elements.")
        return equipment_in_substation

    def create_bill_of_material_submodel(self, parent_aas: model.AssetAdministrationShell,
                                         children_aas: List[model.AssetAdministrationShell]) -> model.Submodel:
        """Creates a BoM submodel that links a parent AAS to its children with proper references."""
        logger.info(f"Creating BoM submodel for {parent_aas.id_short} with {len(children_aas)} children")

        bom_sm = model.Submodel(
            id_=f"{parent_aas.id}_BoM_{uuid.uuid4().hex[:8]}",
            id_short="BillOfMaterial",
            semantic_id=model.ExternalReference(
                key=(model.Key(type_=model.KeyTypes.GLOBAL_REFERENCE, value='0173-1#02-AAO631#002'),)),
            description=f"Bill of Material for {parent_aas.id_short}"
        )

        bom_sm.submodel_element.add(model.Property(
            id_short="child_count", value_type=model.datatypes.Int, value=len(children_aas),
            description="Number of child AAS in this BoM"
        ))

        if children_aass := children_aas:
            children_collection = model.SubmodelElementCollection(
                id_short="child_references",
                description="A collection of references to all child AAS"
            )

            for i, child_aas in enumerate(children_aass):
                child_reference = model.ModelReference.from_referable(child_aas)

                child_detail_collection = model.SubmodelElementCollection(
                    id_short=f"Child_{self.sanitize_id_short(child_aas.id)}_{i}",
                    description=f"Details for child asset: {child_aas.id_short}"
                )

                child_ref_element = model.ReferenceElement(
                    id_short="AssetReference",
                    description=f"Reference to {child_aas.id_short}",
                    category="CONSTANT",
                    value=child_reference
                )
                child_detail_collection.value.add(child_ref_element)

                full_id_property = model.Property(
                    id_short="FullAASID",
                    value_type=model.datatypes.String,
                    value=child_aas.id,
                    description="The full Asset Administration Shell identifier"
                )
                child_detail_collection.value.add(full_id_property)

                children_collection.value.add(child_detail_collection)

            bom_sm.submodel_element.add(children_collection)

        logger.debug(f"BoM {bom_sm.id_short} has {len(bom_sm.submodel_element)} submodel elements")
        for sm_elem in bom_sm.submodel_element:
            if isinstance(sm_elem, model.SubmodelElementCollection):
                logger.debug(f"Collection '{sm_elem.id_short}' contains {len(sm_elem.value)} elements")
        logger.info(f"BoM submodel created with {len(children_aas)} child references")
        return bom_sm

    def create_messlokation_aas(self, node_id: str, node_id_short: str) -> model.AssetAdministrationShell:
        """Create full AAS for a Messlokation, including global asset id."""
        global_asset_id = f"urn:uuid:{uuid.uuid4()}"

        melo_aas = model.AssetAdministrationShell(
            id_=f"AAS_Messlokation_{self.sanitize_id_short(node_id)}",
            id_short=f"AAS_Messlokation_{node_id_short}",
            asset_information=model.AssetInformation(
                asset_kind=model.AssetKind.INSTANCE,
                global_asset_id=global_asset_id,
                asset_type="CIM_Messlokation"
            )
        )
        return melo_aas
    def create_connection_point_submodel(self, connection_point: ET.Element) -> model.Submodel:
        """Create submodel for connection points."""
        node_id = connection_point.get(f"{{{NS['rdf']}}}ID", "").lstrip("_")
        node_name = self.get_element_name(connection_point) or f"ConnectionPoint_{node_id}"
        connected_equipment = self.get_connected_equipment_for_node(node_id)
        sm = model.Submodel(
            id_=f"Submodel_ConnectionPoint_{self.sanitize_id_short(node_id)}",
            id_short=f"ConnectionPoint_{self.sanitize_id_short(node_name)}",
            description=f"Connection point {node_name} with connected equipment"
        )
        sm.submodel_element.add(
            model.Property(id_short="connection_point_id", value_type=model.datatypes.String, value=node_id))
        sm.submodel_element.add(
            model.Property(id_short="connection_point_name", value_type=model.datatypes.String, value=node_name))
        sm.submodel_element.add(model.Property(id_short="connected_equipment_count", value_type=model.datatypes.Int,
                                               value=len(connected_equipment)))
        if connected_equipment:
            connected_equip_collection = model.SubmodelElementCollection(id_short="connected_equipment",
                                                                         description="Equipment connected to this connection point")
            for i, equip in enumerate(connected_equipment):
                equip_entry = model.SubmodelElementCollection(id_short=f"equipment_{i + 1}",
                                                              description=f"Connected equipment: {equip['name']}")
                equip_properties = [
                    model.Property(id_short="equipment_mrid", value_type=model.datatypes.String, value=equip['id']),
                    model.Property(id_short="equipment_name", value_type=model.datatypes.String, value=equip['name']),
                    model.Property(id_short="equipment_type", value_type=model.datatypes.String, value=equip['type']),
                    model.Property(id_short="terminal_mrid", value_type=model.datatypes.String,
                                   value=equip['terminal_id'])
                ]
                for prop in equip_properties:
                    equip_entry.value.add(prop)
                connected_equip_collection.value.add(equip_entry)
            sm.submodel_element.add(connected_equip_collection)
        return sm

    def create_technical_data_submodel(self, asset_element: ET.Element, asset_type: str) -> model.Submodel:
        """Creates the technical data submodel for an asset with CIM reference."""
        asset_id = asset_element.get(f"{{{NS['rdf']}}}ID", "").lstrip("_")
        asset_name = self.get_element_name(asset_element) or f"{asset_type}_{asset_id}"

        sm = model.Submodel(
            id_=f"Submodel_TechnicalData_{self.sanitize_id_short(asset_id)}",
            id_short=f"TechnicalData_{self.sanitize_id_short(asset_name)}",
            description=f"Technical details for {asset_type} {asset_name}"
        )

        # Add CIM reference to technical data
        sm.submodel_element.add(
            model.Property(id_short="asset_mrid", value_type=model.datatypes.String, value=asset_id))
        sm.submodel_element.add(
            model.Property(id_short="asset_name", value_type=model.datatypes.String, value=asset_name))
        sm.submodel_element.add(
            model.Property(id_short="cim_asset_type", value_type=model.datatypes.String, value=asset_type))

        # Add AAS global asset ID and aas identifier reference if available
        ref = self.aas_references.get(asset_id, {})
        if ref:
            if "global_asset_id" in ref:
                sm.submodel_element.add(
                    model.Property(id_short="global_asset_id", value_type=model.datatypes.String, value=ref["global_asset_id"]))
            if "aas_id" in ref:
                sm.submodel_element.add(
                    model.Property(id_short="aas_identifier", value_type=model.datatypes.String, value=ref["aas_id"]))

        return sm

    def create_empty_collection_submodel(self, name):
        sm = model.Submodel(
            id_=f"Submodel_{name}",
            id_short=name,
            description=f"{name} registry for EMT"
        )
        collection = model.SubmodelElementCollection(
            id_short="entries",
            description=f"Container for all {name}"
        )
        sm.submodel_element.add(collection)
        return sm, collection

    def _create_reference_summary_collection(self, target_sm: model.Submodel,
                                             collection_short: str = "ref_summary") -> model.SubmodelElementCollection:
        """
        Create a minimal reference-summary collection:
          - ModelReference to target submodel
          - target_idShort
          - target_id
        This keeps things compact and avoids exposing full submodel content,
        making the viewer less cluttered.
        """
        summary = model.SubmodelElementCollection(
            id_short=collection_short,
            description=f"Minimal reference summary for {target_sm.id_short}"
        )

        # Add the actual reference
        summary.value.add(model.ReferenceElement(
            id_short=f"{target_sm.id_short}_ref",
            value=model.ModelReference.from_referable(target_sm)
        ))

        # Add minimal identity properties
        summary.value.add(model.Property(
            id_short="target_idShort",
            value_type=model.datatypes.String,
            value=getattr(target_sm, "id_short", "")
        ))
        summary.value.add(model.Property(
            id_short="target_id",
            value_type=model.datatypes.String,
            value=target_sm.id
        ))

        return summary

    def create_id_reference_collection(self, id_short, target_aas):
        coll = model.SubmodelElementCollection(id_short=id_short)
        coll.value.add(
            model.ReferenceElement(
                id_short="aas_ref",
                value=model.ModelReference.from_referable(target_aas)
            )
        )
        coll.value.add(
            model.Property(
                id_short="aas_id",
                value_type=model.datatypes.String,
                value=target_aas.id
            )
        )
        coll.value.add(
            model.Property(
                id_short="global_asset_id",
                value_type=model.datatypes.String,
                value=target_aas.asset_information.global_asset_id
            )
        )
        return coll

    def classify_fuse_side(self, fuse_elem: ET.Element) -> str:
        """
        Classifies fuse side dynamically from its name.
        Uses the LAST bus occurrence as receiving side.

        Examples:
            Fuse LV Bus 4 LV Bus 2  -> LV2
            Fuse LV Bus 4 LV Bus 7  -> LV7
            Fuse LV Bus 4 MV Bus 4  -> MV
        """
        name = self.get_element_name(fuse_elem)
        if not name:
            return "MV"

        # Look for all LV bus occurrences
        lv_matches = re.findall(r"LV Bus\s*(\d+)", name)

        # Look for MV occurrence
        mv_matches = re.findall(r"MV Bus\s*\d*", name)

        # Determine receiving side based on LAST occurrence in string
        last_lv_pos = name.rfind("LV Bus")
        last_mv_pos = name.rfind("MV Bus")

        if last_mv_pos > last_lv_pos:
            return "MV"

        if lv_matches:
            return f"LV{lv_matches[-1]}"

        return "MV"

    def create_instrument_transformer_aas(
            self,
            asset_id: str,
            id_short: str,
            asset_type: str,
            technical_data: Dict[str, str]
    ) -> List[model.Identifiable]:

        objects = []

        aas = model.AssetAdministrationShell(
            id_=f"AAS_{asset_id}",
            id_short=id_short,
            asset_information=model.AssetInformation(
                asset_kind=model.AssetKind.INSTANCE,
                global_asset_id=f"urn:uuid:{uuid.uuid4()}",
                asset_type=asset_type
            )
        )
        objects.append(aas)

        tech_sm = model.Submodel(
            id_=f"SM_TechnicalData_{asset_id}",
            id_short="TechnicalData"
        )

        for k, v in technical_data.items():
            tech_sm.submodel_element.add(
                model.Property(
                    id_short=k,
                    value_type=model.datatypes.String,
                    value=v
                )
            )

        aas.submodel.add(model.ModelReference.from_referable(tech_sm))
        objects.append(tech_sm)

        return objects, aas

    def create_terminal_aas(self, terminal_elem: ET.Element, fuse_aas=None):
        terminal_id = terminal_elem.get(f"{{{NS['rdf']}}}ID", "").lstrip("_")
        terminal_name = self.get_element_name(terminal_elem) or terminal_id

        aas_id = f"AAS_Terminal_{self.sanitize_id_short(terminal_id)}"
        sm_id = f"SM_Tech_Terminal_{self.sanitize_id_short(terminal_id)}"

        terminal_aas = model.AssetAdministrationShell(
            id_=aas_id,
            id_short=f"Terminal_{self.sanitize_id_short(terminal_name)}",
            asset_information=model.AssetInformation(
                asset_kind=model.AssetKind.INSTANCE,
                global_asset_id=f"urn:uuid:{uuid.uuid4()}",
                asset_type="CIM_Terminal"
            )
        )

        # ✅ Create Submodel
        tech_sm = model.Submodel(
            id_=sm_id,
            id_short="TechnicalData"
        )

        # ✅ Populate Submodel (THIS is what UI shows)
        tech_sm.submodel_element.add(
            model.Property(
                id_short="mRID",
                value_type=model.datatypes.String,
                value=terminal_id
            )
        )

        seq = terminal_elem.find("cim:ACDCTerminal.sequenceNumber", NS)
        if seq is not None:
            tech_sm.submodel_element.add(
                model.Property(
                    id_short="sequenceNumber",
                    value_type=model.datatypes.Integer,
                    value=int(seq.text)
                )
            )

        # ConnectivityNode reference
        cn_ref = terminal_elem.find("cim:Terminal.ConnectivityNode", NS)
        if cn_ref is not None:
            cn_id = cn_ref.get(f"{{{NS['rdf']}}}resource", "").split("#")[-1].lstrip("_")
            tech_sm.submodel_element.add(
                model.Property(
                    id_short="ConnectivityNode",
                    value_type=model.datatypes.String,
                    value=cn_id
                )
            )

        # Link Submodel to AAS
        terminal_aas.submodel.add(
            model.ModelReference.from_referable(tech_sm)
        )

        # ---- Connected Fuse Submodel (Conditional) ----
        if fuse_aas is not None:
            fuse_sm = model.Submodel(
                id_=f"SM_ConnectedFuse_{self.sanitize_id_short(terminal_id)}",
                id_short="ConnectedFuse",
                description="Reference to connected Fuse AAS"
            )

            fuse_sm.submodel_element.add(
                self.create_id_reference_collection("Ref_Fuse", fuse_aas)
            )

            terminal_aas.submodel.add(
                model.ModelReference.from_referable(fuse_sm)
            )

            return terminal_aas, tech_sm, fuse_sm

        return terminal_aas, tech_sm, None

    # [MODIFICATION: Helper methods with correct Beckhoff data and object returning]
    def create_beckhoff_edge_device(self, substation_name: str) -> List[model.Identifiable]:
        """
        Creates the CX2043 Edge Device AAS and Submodels.
        Data Source: Beckhoff CX2043 Datasheet
        """
        objects_to_return = []
        device_id = f"Beckhoff_CX2043_{self.sanitize_id_short(substation_name)}"

        # 1. AAS
        aas = model.AssetAdministrationShell(
            id_=f"AAS_EdgeDevice_{device_id}",
            id_short=f"EdgeDevice_{device_id}",
            asset_information=model.AssetInformation(
                asset_kind=model.AssetKind.INSTANCE,
                global_asset_id=f"urn:uuid:{uuid.uuid4()}",
                asset_type="EdgeDevice_IPC"
            )
        )
        objects_to_return.append(aas)

        # 2. Manufacturer Submodel
        mfg_sm = model.Submodel(id_=f"SM_Mfg_{device_id}", id_short="ManufacturerInfo")
        mfg_sm.submodel_element.add(model.Property("Manufacturer", model.datatypes.String, "Beckhoff Automation"))
        mfg_sm.submodel_element.add(model.Property("Model", model.datatypes.String, "CX2043"))
        aas.submodel.add(model.ModelReference.from_referable(mfg_sm))
        objects_to_return.append(mfg_sm)

        # 3. Technical Data Submodel (Corrected values + IP Address)
        tech_sm = model.Submodel(id_=f"SM_Tech_{device_id}", id_short="TechnicalData")

        # [NEW] Add IP Address
        tech_sm.submodel_element.add(
            model.Property("IP_Address", model.datatypes.String, "172.17.5.204"))

        # CPU: AMD Ryzen V1000 series (V1202B or V1807B)
        tech_sm.submodel_element.add(
            model.Property("CPU", model.datatypes.String, "AMD Ryzen™ V1202B (2.3 GHz, 2 cores)"))
        tech_sm.submodel_element.add(model.Property("RAM", model.datatypes.String, "8 GB DDR4"))
        tech_sm.submodel_element.add(
            model.Property("OS", model.datatypes.String, "Windows 10 IoT Enterprise 2019 LTSC"))

        interfaces = model.SubmodelElementCollection(id_short="Interfaces")
        # Interfaces: 2 x RJ45, 1 x DVI-I, 4 x USB 3.1 Gen 2
        interfaces.value.add(model.Property("Ethernet", model.datatypes.String, "2 x RJ45 10/100/1000 Mbit/s"))
        interfaces.value.add(model.Property("USB", model.datatypes.String, "4 x USB 3.1 Gen 2"))
        interfaces.value.add(model.Property("Video", model.datatypes.String, "1 x DVI-I"))
        tech_sm.submodel_element.add(interfaces)

        aas.submodel.add(model.ModelReference.from_referable(tech_sm))
        objects_to_return.append(tech_sm)

        # 4. Licenses Submodel
        lic_sm = model.Submodel(id_=f"SM_Lic_{device_id}", id_short="Licenses")
        licenses = ["TC1220-0160", "TF6510-0160", "TF6760-0160", "TF8350-0160"]
        for i, lic in enumerate(licenses):
            lic_sm.submodel_element.add(model.Property(f"License_{i + 1}", model.datatypes.String, lic))
        aas.submodel.add(model.ModelReference.from_referable(lic_sm))
        objects_to_return.append(lic_sm)

        return objects_to_return

    def create_equipment_terminals_submodel(self, equipment_elem: ET.Element) -> model.Submodel:
        """Creates a submodel listing the specific terminals of an equipment instance."""
        equip_id = equipment_elem.get(f"{{{NS['rdf']}}}ID", "").lstrip("_")
        equip_name = self.get_element_name(equipment_elem) or equip_id

        sm = model.Submodel(
            id_=f"Submodel_Terminals_{self.sanitize_id_short(equip_id)}",
            id_short=f"Terminals_{self.sanitize_id_short(equip_name)}",
            description=f"Local terminals for {equip_name}"
        )

        terminals = self._find_terminals_for_equipment(equip_id)

        terminal_collection = model.SubmodelElementCollection(
            id_short="DeviceTerminals",
            description="List of terminals belonging to this device"
        )

        for i, term in enumerate(terminals):
            t_id = term.get(f"{{{NS['rdf']}}}ID", "").lstrip("_")
            t_name = self.get_element_name(term) or f"Terminal_{i + 1}"

            # Find what this terminal connects to (The Connectivity Node)
            cn_ref = term.find("cim:Terminal.ConnectivityNode", NS)
            connected_node = "Unconnected"
            if cn_ref is not None:
                ref = cn_ref.get(f"{{{NS['rdf']}}}resource") or cn_ref.get("resource")
                connected_node = ref.split('#')[-1].lstrip("_")

            # Add to collection
            t_group = model.SubmodelElementCollection(id_short=f"Terminal_{i + 1}")
            t_group.value.add(model.Property("TerminalID", model.datatypes.String, t_id))
            t_group.value.add(model.Property("TerminalName", model.datatypes.String, t_name))
            t_group.value.add(model.Property("ConnectedNodeID", model.datatypes.String, connected_node))

            terminal_collection.value.add(t_group)

        sm.submodel_element.add(terminal_collection)
        return sm

    def create_beckhoff_measurement_setup(
            self,
            substation_name: str,
            fuses_by_side: Dict[str, list],
            ct_aas: model.AssetAdministrationShell,
            vt_aas: model.AssetAdministrationShell
    ) -> List[model.Identifiable]:

        objects_to_return = []
        device_id = f"Beckhoff_EL3475_{self.sanitize_id_short(substation_name)}"

        # ------------------------------------------------------------------
        # 1. Measurement Device AAS
        # ------------------------------------------------------------------
        aas = model.AssetAdministrationShell(
            id_=f"AAS_MeasDevice_{device_id}",
            id_short=f"MeasDevice_{device_id}",
            asset_information=model.AssetInformation(
                asset_kind=model.AssetKind.INSTANCE,
                global_asset_id=f"urn:uuid:{uuid.uuid4()}",
                asset_type="MeasurementDevice_Terminal"
            )
        )
        objects_to_return.append(aas)

        # ------------------------------------------------------------------
        # 2. Device Information Submodel
        # ------------------------------------------------------------------
        info_sm = model.Submodel(
            id_=f"SM_Info_{device_id}",
            id_short="DeviceInformation"
        )

        info_sm.submodel_element.add(
            model.Property("Manufacturer", model.datatypes.String, "Beckhoff Automation")
        )
        info_sm.submodel_element.add(
            model.Property("Model", model.datatypes.String, "EL3475")
        )

        aas.submodel.add(model.ModelReference.from_referable(info_sm))
        objects_to_return.append(info_sm)

        # ------------------------------------------------------------------
        # 3. Dynamic Measurement Points (One per side)
        # ------------------------------------------------------------------

        # Sort sides for predictable order (MV first, then LV numerically)
        def side_sort_key(side):
            if side == "MV":
                return (0, 0)
            if side.startswith("LV"):
                return (1, int(side.replace("LV", "")))
            return (2, 0)

        for side in sorted(fuses_by_side.keys(), key=side_sort_key):

            fuse_list = fuses_by_side[side]

            mp_sm = model.Submodel(
                id_=f"SM_MP_{side}_{device_id}",
                id_short=f"MeasurementPoint_{side}",
                description=f"{side} Measurement Point"
            )

            # Add fuse references
            for i, fuse_aas in enumerate(fuse_list):
                mp_sm.submodel_element.add(
                    self.create_id_reference_collection(
                        f"Corresponding_asset",
                        fuse_aas
                    )
                )

            # Add CT always
            mp_sm.submodel_element.add(
                self.create_id_reference_collection(
                    "Ref_CurrentTransformer",
                    ct_aas
                )
            )

            # Add VT only for MV side
            if side == "MV":
                mp_sm.submodel_element.add(
                    self.create_id_reference_collection(
                        "Ref_VoltageTransformer",
                        vt_aas
                    )
                )

            aas.submodel.add(model.ModelReference.from_referable(mp_sm))
            objects_to_return.append(mp_sm)

        return objects_to_return

    def create_beckhoff_el3702_device(
            self,
            substation_name: str,
            index: int,
            ext_grid_terminal_aas: Optional[model.AssetAdministrationShell]
    ) -> List[model.Identifiable]:
        """Creates the EL3702 Measurement Device AAS pointing to the External Grid."""
        objects_to_return = []
        device_id = f"Beckhoff_EL3702_{index}_{self.sanitize_id_short(substation_name)}"

        # 1. AAS
        aas = model.AssetAdministrationShell(
            id_=f"AAS_MeasDevice_{device_id}",
            id_short=f"MeasDevice_{device_id}",
            asset_information=model.AssetInformation(
                asset_kind=model.AssetKind.INSTANCE,
                global_asset_id=f"urn:uuid:{uuid.uuid4()}",
                asset_type="MeasurementDevice_Terminal"
            )
        )
        objects_to_return.append(aas)

        # 2. Device Information Submodel
        info_sm = model.Submodel(
            id_=f"SM_Info_{device_id}",
            id_short="DeviceInformation"
        )
        info_sm.submodel_element.add(model.Property("Manufacturer", model.datatypes.String, "Beckhoff Automation"))
        info_sm.submodel_element.add(model.Property("Model", model.datatypes.String, "EL3702"))
        info_sm.submodel_element.add(model.Property("Description", model.datatypes.String,
                                                    "2-Channel Analog Input, Voltage, ±10 V, 16 Bit, Oversampling"))

        aas.submodel.add(model.ModelReference.from_referable(info_sm))
        objects_to_return.append(info_sm)

        # 3. Measurement Point Submodel (External Grid)
        if ext_grid_terminal_aas:
            mp_sm = model.Submodel(
                id_=f"SM_MP_{device_id}",
                id_short="MeasurementPoint_ExternalGrid",
                description="Measurement Point connected to External Network Injection"
            )
            mp_sm.submodel_element.add(
                self.create_id_reference_collection("Corresponding_asset", ext_grid_terminal_aas)
            )
            aas.submodel.add(model.ModelReference.from_referable(mp_sm))
            objects_to_return.append(mp_sm)

        return objects_to_return

    def create_asset_aas(self, asset_element: ET.Element, asset_type: str) -> model.AssetAdministrationShell:
        """Create separate AAS for specific asset with bidirectional linking."""
        asset_id = asset_element.get(f"{{{NS['rdf']}}}ID", "").lstrip("_")
        asset_name = self.get_element_name(asset_element) or f"{asset_type}_{asset_id}"

        # Generate global asset ID for this AAS
        global_asset_id = f"urn:uuid:{uuid.uuid4()}"

        # Create AAS
        asset_aas = model.AssetAdministrationShell(
            id_=f"AAS_{asset_type}_{self.sanitize_id_short(asset_id)}",
            id_short=f"AAS_{asset_type}_{self.sanitize_id_short(asset_name)}",
            asset_information=model.AssetInformation(
                asset_kind=model.AssetKind.INSTANCE,
                global_asset_id=global_asset_id,
                asset_type=f"CIM_{asset_type}"
            )
        )

        # Add bidirectional references (both globalAssetId and full AAS id) to the CIM element
        self._add_aas_reference_to_cim(asset_element, global_asset_id, asset_aas.id)

        return asset_aas

    def convert(self) -> Dict:
        """Main conversion method with new lokation strategy and DSO top-level."""
        logger.info("Starting conversion with connectivity-node-based Netzlokation strategy.")

        all_objects: List[model.Identifiable] = []
        aas_cache: Dict[str, model.AssetAdministrationShell] = {}

        # Track created submodels for linking
        node_to_nelo_sm: Dict[str, model.Submodel] = {}
        node_to_melo_sm: Dict[str, model.Submodel] = {}
        processed_nodes_for_messlokation: Dict[str, Dict[str, object]] = {}

        # == STEP 1: Create DSO top-level AAS, PowerSystem, and EMTs ==
        dso_global_id = f"urn:uuid:{uuid.uuid4()}"
        dso_aas = model.AssetAdministrationShell(
            id_="AAS_DSO", id_short="AAS_DSO",
            asset_information=model.AssetInformation(asset_kind=model.AssetKind.INSTANCE, global_asset_id=dso_global_id,
                                                     asset_type="CIM_DSO")
        )
        all_objects.append(dso_aas)

        system_aas = model.AssetAdministrationShell(
            id_="AAS_PowerSystem", id_short="AAS_PowerSystem",
            asset_information=model.AssetInformation(asset_kind=model.AssetKind.INSTANCE,
                                                     global_asset_id=f"urn:uuid:{uuid.uuid4()}",
                                                     asset_type="CIM_PowerSystem")
        )
        all_objects.append(system_aas)

        # Create EMTs
        emt1 = model.AssetAdministrationShell(
            id_="AAS_EMT1", id_short="AAS_EMT1",
            asset_information=model.AssetInformation(asset_kind=model.AssetKind.INSTANCE,
                                                     global_asset_id=f"urn:uuid:{uuid.uuid4()}", asset_type="CIM_EMT")
        )
        emt2 = model.AssetAdministrationShell(
            id_="AAS_EMT2", id_short="AAS_EMT2",
            asset_information=model.AssetInformation(asset_kind=model.AssetKind.INSTANCE,
                                                     global_asset_id=f"urn:uuid:{uuid.uuid4()}", asset_type="CIM_EMT")
        )
        all_objects.extend([emt1, emt2])

        # Dictionary to store the assignment submodels for easy access later
        emt_asset_submodels: Dict[str, model.Submodel] = {}

        # EMT Communication Submodels
        def create_emt_comm(emt, report_ip, report_port, cls_ip, cls_port):
            info = model.Submodel(id_=f"SM_InfoReport_{emt.id_short}", id_short="InfoReport")
            info.submodel_element.add(model.Property("ip", model.datatypes.String, report_ip))
            info.submodel_element.add(model.Property("port", model.datatypes.Int, report_port))

            cls = model.Submodel(id_=f"SM_CLS_{emt.id_short}", id_short="CLS")
            cls.submodel_element.add(model.Property("ip", model.datatypes.String, cls_ip))
            cls.submodel_element.add(model.Property("port", model.datatypes.Int, cls_port))

            all_objects.extend([info, cls])
            emt.submodel.add(model.ModelReference.from_referable(info))
            emt.submodel.add(model.ModelReference.from_referable(cls))

            asset_sm = model.Submodel(
                id_=f"SM_AssignedAssets_{emt.id_short}",
                id_short="AssignedAssets",
                description="References to Netzlokation and Metering Devices"
            )
            all_objects.append(asset_sm)
            emt.submodel.add(model.ModelReference.from_referable(asset_sm))
            emt_asset_submodels[emt.id_short] = asset_sm  # Store for later steps

        create_emt_comm(emt1, "172.17.5.100", 4589, "129.217.202.59", 4591)
        create_emt_comm(emt2, "172.17.5.100", 4589, "129.217.202.59", 4590)

        # DSO BoM
        dso_bom = self.create_bill_of_material_submodel(dso_aas, [system_aas, emt1, emt2])
        all_objects.append(dso_bom)
        dso_aas.submodel.add(model.ModelReference.from_referable(dso_bom))

        # Registries (PowerSystem)
        netz_reg, netz_entries = self.create_registry_submodel("NetzlokationRegistry",
                                                               "Registry of grid connection points.")
        mess_reg, mess_entries = self.create_registry_submodel("MesslokationRegistry", "Registry of metering points.")
        markt_reg, markt_entries = self.create_registry_submodel("MarktlokationRegistry", "Registry of market points.")
        all_objects.extend([netz_reg, mess_reg, markt_reg])
        system_aas.submodel.add(model.ModelReference.from_referable(netz_reg))
        system_aas.submodel.add(model.ModelReference.from_referable(mess_reg))
        system_aas.submodel.add(model.ModelReference.from_referable(markt_registry := markt_reg))

        # == STEP 2: Create AAS for all assets ==
        # ---- Instrument Transformers (Beckhoff) ----

        ct_data = {
            "Manufacturer": "Beckhoff Automation",
            "Model": "SCL6123-0040",
            "PrimaryCurrent": "40 A",
            "SecondarySignal": "0.333 V",
            "AccuracyClass": "0.5",
            "RatedBurden": "5 VA",
            "RatedFrequency": "50/60 Hz",
            "ProductURL": "https://www.beckhoff.com/de-de/produkte/i-o/messwandler/uebersicht-stromwandler/scl6123-0040.html"
        }

        # [MODIFIED] SI Units, Value Corrections, Renaming
        vt_data = {
            "Manufacturer": "Beckhoff Automation",
            "Model": "SVL1323",
            "PrimaryPhaseToGroundVoltage": "277 V",  # Renamed from PrimaryVoltage, Value: 10kV -> 277 V
            "SecondaryVoltage": "0.333 V",  # Value: 100 V -> 0.333 V
            "AccuracyClass": "0.5",
            "RatedFrequency": "50/60 Hz",
            "InsulationLevel": "12 kV",  # Kept as is per datasheet for insulation
            "ProductURL": "https://www.beckhoff.com/de-de/produkte/i-o/messwandler/svl1xxx-kleinsignal-spannungswandler/svl1323.html"
        }

        ct_objs, ct_aas = self.create_instrument_transformer_aas(
            asset_id="CT_SCL6123_0040",
            id_short="CurrentTransformer_SCL6123_0040",
            asset_type="CurrentTransformer",
            technical_data=ct_data
        )

        vt_objs, vt_aas = self.create_instrument_transformer_aas(
            asset_id="VT_SVL1323",
            id_short="VoltageTransformer_SVL1323",
            asset_type="VoltageTransformer",
            technical_data=vt_data
        )

        all_objects.extend(ct_objs + vt_objs)

        fuses_by_side = defaultdict(list)
        ext_grid_terminal_aass = []

        asset_types = ["Substation", "PowerTransformer", "ConformLoad", "ACLineSegment",
                       "BatteryUnit", "PhotoVoltaicUnit", "ConnectivityNode", "BusbarSection",
                       "PowerElectronicsConnection", "ExternalNetworkInjection", "Fuse"]

        for asset_type in asset_types:
            for asset_elem in self.root.findall(f".//cim:{asset_type}", NS):
                raw_id = asset_elem.get(f"{{{NS['rdf']}}}ID", "")
                asset_id = raw_id.lstrip("_")
                if asset_id in aas_cache: continue

                asset_aas = self.create_asset_aas(asset_elem, asset_type)
                aas_cache[asset_id] = asset_aas
                all_objects.append(asset_aas)

                tech_sm = self.create_technical_data_submodel(asset_elem, asset_type)
                all_objects.append(tech_sm)
                asset_aas.submodel.add(model.ModelReference.from_referable(tech_sm))

                # [MODIFICATION] If asset is Fuse, create AAS for its terminals and link them
                if asset_type == "Fuse":
                    side = self.classify_fuse_side(asset_elem)
                    fuses_by_side[side].append(asset_aas)
                    fuse_terminals = self._find_terminals_for_equipment(asset_id)
                    fuse_terminal_aass = []

                    for term in fuse_terminals:
                        t_id = term.get(f"{{{NS['rdf']}}}ID", "").lstrip("_")

                        # Create or reuse Terminal AAS
                        if t_id not in aas_cache:
                            t_aas, t_sm, fuse_sm = self.create_terminal_aas(term, fuse_aas=asset_aas)

                            all_objects.extend([t_aas, t_sm, fuse_sm])

                            aas_cache[t_id] = t_aas
                        else:
                            t_aas = aas_cache[t_id]

                        fuse_terminal_aass.append(t_aas)

                    # Create reference submodel inside Fuse AAS
                    if fuse_terminal_aass:
                        term_ref_sm = model.Submodel(
                            id_=f"SM_TermRefs_{asset_id}",
                            id_short="ConnectedTerminals"
                        )

                        for i, t_aas in enumerate(fuse_terminal_aass):
                            term_ref_sm.submodel_element.add(
                                self.create_id_reference_collection(
                                    f"Ref_Terminal_{i + 1}",
                                    t_aas
                                )
                            )

                        all_objects.append(term_ref_sm)
                        asset_aas.submodel.add(model.ModelReference.from_referable(term_ref_sm))

                # [NEW MODIFICATION] Capture External Network Injection terminals
                elif asset_type == "ExternalNetworkInjection":
                    ext_terminals = self._find_terminals_for_equipment(asset_id)
                    for term in ext_terminals:
                        t_id = term.get(f"{{{NS['rdf']}}}ID", "").lstrip("_")
                        if t_id not in aas_cache:
                            t_aas, t_sm, _ = self.create_terminal_aas(term)
                            all_objects.extend([t_aas, t_sm])
                            aas_cache[t_id] = t_aas
                        else:
                            t_aas = aas_cache[t_id]
                        ext_grid_terminal_aass.append(t_aas)

        # == STEP 3: Create Netzlokation for Connectivity Nodes ==
        logger.info("Creating Netzlokation submodels...")
        for node_elem in self.root.findall(".//cim:ConnectivityNode", NS):
            node_id = node_elem.get(f"{{{NS['rdf']}}}ID", "").lstrip("_")
            node_aas = aas_cache.get(node_id)
            if not node_aas: continue

            coords = self.location_data.get(node_id, {"x": 0.0, "y": 0.0})
            nelo_sm = self.create_netzlokation_submodel(node_elem, coords)
            all_objects.append(nelo_sm)
            node_aas.submodel.add(model.ModelReference.from_referable(nelo_sm))

            node_to_nelo_sm[node_id] = nelo_sm

            # Register in PowerSystem Registry
            if nelo_sm.id_short not in {e.id_short for e in netz_entries.value}:
                netz_entries.value.add(model.ReferenceElement(id_short=nelo_sm.id_short,
                                                              value=model.ModelReference.from_referable(nelo_sm)))

        # == STEP 3.5: Link Netzlokation to EMTs (CORRECTED LOCATION) ==
        # This is now OUTSIDE the loop to ensure clean linking
        emt_node_map = {
            "LV1.101 Bus 2": emt1,
            "LV1.101 Bus 7": emt2
        }

        logger.info("Linking Netzlokations to EMTs via Reference Collections...")
        for node_id, nelo_sm in node_to_nelo_sm.items():
            node_elem = self._element_cache.get(node_id) or self._element_cache.get(f"_{node_id}")
            if not node_elem: continue

            elem_name = self.get_element_name(node_elem)

            if elem_name in emt_node_map:
                target_emt = emt_node_map[elem_name]
                asset_sm = emt_asset_submodels.get(target_emt.id_short)

                if asset_sm:
                    # Create a reference collection instead of adding the submodel itself
                    ref_collection = self._create_reference_summary_collection(
                        nelo_sm,
                        collection_short=f"ref_{nelo_sm.id_short}"
                    )
                    asset_sm.submodel_element.add(ref_collection)
                    logger.success(f"Added Netzlokation reference to {target_emt.id_short}'s AssignedAssets")

        # == STEP 4: Universal Messlokation & Specialized Devices ==
        logger.info("Assigning Messlokations to ALL buses and creating specialized devices for Bus 2/7...")

        # Guard to prevent duplicate device creation
        created_special_buses = set()
        special_buses = ["LV1.101 Bus 2", "LV1.101 Bus 7"]

        for node_elem in self.root.findall(".//cim:ConnectivityNode", NS):
            node_id = node_elem.get(f"{{{NS['rdf']}}}ID", "").lstrip("_")
            node_name = self.get_element_name(node_elem) or f"Node_{node_id}"
            node_id_short = self.sanitize_id_short(node_name)

            if node_id in processed_nodes_for_messlokation:
                melo_entry = processed_nodes_for_messlokation[node_id]
                melo_aas = melo_entry["aas"]
                melo_sm = melo_entry["submodel"]
            else:
                melo_aas = self.create_messlokation_aas(node_id, node_id_short)
                all_objects.append(melo_aas)

                melo_sm = self.create_messlokation_submodel(node_id_short, node_id)
                all_objects.append(melo_sm)
                melo_aas.submodel.add(model.ModelReference.from_referable(melo_sm))

                # --- CHANGE 1: Current Transformer Ratio (35/1) & No Voltage Transformer ---
                ct_ratio_sm = model.Submodel(
                    id_=f"SM_CT_Ratio_{self.sanitize_id_short(node_id)}",
                    id_short="current_transformer_ratio",
                    description="Current Transformer Ratio Settings"
                )
                ct_ratio_sm.submodel_element.add(
                    model.Property(id_short="primary_current", value_type=model.datatypes.Float, value=35.0))
                ct_ratio_sm.submodel_element.add(
                    model.Property(id_short="secondary_current", value_type=model.datatypes.Float, value=1.0))
                ct_ratio_sm.submodel_element.add(
                    model.Property(id_short="ratio_string", value_type=model.datatypes.String, value="35/1"))

                melo_aas.submodel.add(model.ModelReference.from_referable(ct_ratio_sm))
                all_objects.append(ct_ratio_sm)

                processed_nodes_for_messlokation[node_id] = {"aas": melo_aas, "submodel": melo_sm}
                node_to_melo_sm[node_id] = melo_sm
                mess_entries.value.add(model.ReferenceElement(id_short=melo_aas.id_short,
                                                              value=model.ModelReference.from_referable(melo_aas)))

            def create_ferraris_meter(node_short, melo_aas, melo_sm):
                meter_id = f"FER_{node_short}"

                aas = model.AssetAdministrationShell(
                    id_=f"AAS_FerrarisMeter_{node_short}",
                    id_short=f"AAS_FerrarisMeter_{node_short}",
                    asset_information=model.AssetInformation(
                        asset_kind=model.AssetKind.INSTANCE,
                        global_asset_id=f"urn:uuid:{uuid.uuid4()}",
                        asset_type="Custom_FerrarisMeter"
                    )
                )
                all_objects.append(aas)

                tech = model.Submodel(
                    id_=f"SM_Tech_Ferraris_{node_short}",
                    id_short="Technical_FerrarisMeter"
                )

                tech.submodel_element.add(
                    model.Property("meter_id", model.datatypes.String, meter_id)
                )
                tech.submodel_element.add(
                    model.Property("meter_type", model.datatypes.String, "Ferraris")
                )

                tech.submodel_element.add(
                    self.create_id_reference_collection("Ref_Messlokation", melo_aas)
                )

                aas.submodel.add(model.ModelReference.from_referable(tech))
                all_objects.append(tech)

                # Back-reference from Messlokation
                melo_sm.submodel_element.add(
                    self._create_reference_summary_collection(aas, f"ferraris_ref_{node_short}")
                )

                return aas

            if node_name not in special_buses:
                create_ferraris_meter(
                    node_id_short,
                    processed_nodes_for_messlokation[node_id]["aas"],
                    processed_nodes_for_messlokation[node_id]["submodel"]
                )

            # --- CHANGE 2: Specialized devices ONLY for Bus 2 and Bus 7 ---
            if node_name in special_buses and node_name not in created_special_buses:
                created_special_buses.add(node_name)

                if node_name == "LV1.101 Bus 2":
                    node_emt = emt1
                else:
                    node_emt = emt2

                # Helper functions for devices (SMGW, DM, CB)
                # (Note: These are unchanged logic-wise, just re-indented inside this block)
                def create_smgw(node_short, emt, melo_aas, melo_sm):
                    if "Bus 2" in node_name:
                        deltat, taf_id = 15, "01005e31802a.1emh0015652689-taf10a.sm"
                    else:
                        deltat, taf_id = 60, "01005e31802a.1emh0013150392-taf10b-dtm.sm"

                    aas = model.AssetAdministrationShell(
                        id_=f"AAS_SMGW_{node_short}", id_short=f"AAS_SmartMeterGateway_{node_short}",
                        asset_information=model.AssetInformation(asset_kind=model.AssetKind.INSTANCE,
                                                                 global_asset_id=f"urn:uuid:{uuid.uuid4()}",
                                                                 asset_type="Custom_SMGW")
                    )
                    all_objects.append(aas)

                    taf10_sm = model.Submodel(
                        id_=f"SM_TAF10_{node_short}",
                        id_short="TAF10",
                        description="Tariff Use Case 10 configuration"
                    )

                    taf10_sm.submodel_element.add(
                        model.Property("delta_t", model.datatypes.Int, deltat)
                    )
                    taf10_sm.submodel_element.add(
                        model.Property("time", model.datatypes.String, "00:00:00")
                    )
                    taf10_sm.submodel_element.add(
                        model.Property("taf_id", model.datatypes.String, taf_id)
                    )
                    taf10_sm.submodel_element.add(
                        model.Property("current_status", model.datatypes.String, "active")
                    )

                    aas.submodel.add(model.ModelReference.from_referable(taf10_sm))
                    all_objects.append(taf10_sm)

                    ref_sm = model.Submodel(id_=f"SM_Ref_SMGW_{node_short}", id_short="Technical_Data")
                    ref_sm.submodel_element.add(model.Property("id", model.datatypes.String, "01005e31802a"))
                    ref_sm.submodel_element.add(
                        model.Property("ip_address", model.datatypes.String, "172.17.5.60"))

                    aas.submodel.add(model.ModelReference.from_referable(ref_sm))
                    # Optional references
                    ref_sm.submodel_element.add(
                        self.create_id_reference_collection("Ref_Messlokation", melo_aas)
                    )
                    ref_sm.submodel_element.add(
                        self.create_id_reference_collection("Ref_EMT", emt)
                    )
                    all_objects.append(ref_sm)

                    melo_sm.submodel_element.add(
                        self._create_reference_summary_collection(aas, f"smgw_ref_{node_short}"))
                    return aas

                def create_dm(node_short, emt, melo_aas, melo_sm):
                    dm_id = "1emh0015652689" if "Bus 2" in node_name else "1emh0013150392"
                    aas = model.AssetAdministrationShell(
                        id_=f"AAS_DM_{node_short}", id_short=f"AAS_DigitalMeter_{node_short}",
                        asset_information=model.AssetInformation(asset_kind=model.AssetKind.INSTANCE,
                                                                 global_asset_id=f"urn:uuid:{uuid.uuid4()}",
                                                                 asset_type="Custom_DigitalMeter")
                    )
                    all_objects.append(aas)

                    tech = model.Submodel(id_=f"SM_Tech_DM_{node_short}", id_short="Technical_DigitalMeter")
                    tech.submodel_element.add(model.Property("id", model.datatypes.String, dm_id))
                    tech.submodel_element.add(model.Property("type", model.datatypes.String, "iMSys"))

                    # Updated Referencing Strategy to match SMGW
                    tech.submodel_element.add(self.create_id_reference_collection("Ref_Messlokation", melo_aas))
                    tech.submodel_element.add(self.create_id_reference_collection("Ref_EMT", emt))

                    aas.submodel.add(model.ModelReference.from_referable(tech))
                    all_objects.append(tech)

                    melo_sm.submodel_element.add(
                        self._create_reference_summary_collection(aas, f"dm_ref_{node_short}"))
                    return aas

                def create_cb(node_short, emt, melo_aas, melo_sm):
                    cb_id = "GSWIC025040254" if "Bus 2" in node_name else "GSWIC025040253"
                    aas = model.AssetAdministrationShell(
                        id_=f"AAS_CB_{node_short}", id_short=f"AAS_ControlBox_{node_short}",
                        asset_information=model.AssetInformation(asset_kind=model.AssetKind.INSTANCE,
                                                                 global_asset_id=f"urn:uuid:{uuid.uuid4()}",
                                                                 asset_type="Custom_ControlBox")
                    )
                    all_objects.append(aas)

                    tech = model.Submodel(id_=f"SM_Tech_CB_{node_short}", id_short="Technical_ControlBox")
                    tech.submodel_element.add(model.Property("id", model.datatypes.String, cb_id))
                    tech.submodel_element.add(model.Property("type", model.datatypes.String, "EEBus"))

                    cls_conf = [("EMS", True), ("PV", False), ("EV", False), ("OTHER", False)]
                    for idx, (t, p) in enumerate(cls_conf, 1):
                        c = model.SubmodelElementCollection(id_short=f"CLS_{idx}")
                        c.value.add(model.Property("type", model.datatypes.String, t))
                        c.value.add(model.Property("present", model.datatypes.Boolean, p))
                        tech.submodel_element.add(c)

                    # Updated Referencing Strategy to match SMGW
                    tech.submodel_element.add(self.create_id_reference_collection("Ref_Messlokation", melo_aas))
                    tech.submodel_element.add(self.create_id_reference_collection("Ref_EMT", emt))

                    aas.submodel.add(model.ModelReference.from_referable(tech))
                    all_objects.append(tech)

                    melo_sm.submodel_element.add(
                        self._create_reference_summary_collection(aas, f"cb_ref_{node_short}"))
                    return aas

                # Create the special devices
                melo_entry = processed_nodes_for_messlokation[node_id]
                smgw_aas = create_smgw(node_id_short, node_emt, melo_entry["aas"], melo_entry["submodel"])
                dm_aas = create_dm(node_id_short, node_emt, melo_entry["aas"], melo_entry["submodel"])
                cb_aas = create_cb(node_id_short, node_emt, melo_entry["aas"], melo_entry["submodel"])

                # Add references to EMT
                emt_asset_sm = emt_asset_submodels.get(node_emt.id_short)
                if emt_asset_sm:
                    for device_aas in [smgw_aas, dm_aas, cb_aas]:
                        dev_ref_coll = model.SubmodelElementCollection(
                            id_short=f"ref_{device_aas.id_short}",
                            description=f"Reference to {device_aas.id_short}"
                        )
                        emt_asset_sm.submodel_element.add(
                            self.create_id_reference_collection(
                                f"Ref_{device_aas.id_short}",
                                device_aas
                            )
                        )

            # Link Messlokation to Netzlokation if exists
            if node_id in node_to_nelo_sm:
                nelo_sm_obj = node_to_nelo_sm[node_id]
                melo_sm.submodel_element.add(
                    self._create_reference_summary_collection(nelo_sm_obj, "netzlokation_ref"))
                nelo_sm_obj.submodel_element.add(
                    self._create_reference_summary_collection(melo_aas, "messlokation_ref"))

        # == STEP 5: Asset Linking to Messlokation/Marktlokation (BIDIRECTIONAL) ==
        logger.info("Linking assets to Mess/Marktlokation with bidirectional references...")

        for node_id, melo_entry in processed_nodes_for_messlokation.items():
            melo_aas = melo_entry["aas"]
            melo_sm = melo_entry["submodel"]

            # --- CHANGE 3: Create Collection in Messlokation to hold Marktlokation references ---
            malo_collection = model.SubmodelElementCollection(
                id_short="Connected_Marktlokationen",
                description="List of all Marktlokationen connected to this Messlokation."
            )
            melo_sm.submodel_element.add(malo_collection)

            connected = self.get_connected_equipment_for_node(node_id)
            for equip in connected:
                if equip['type'] in ["ConformLoad", "PhotoVoltaicUnit", "BatteryUnit",
                                     "ExternalNetworkInjection"]:
                    asset_aas = aas_cache.get(equip['id'])
                    if asset_aas:
                        # 1. Create Marktlokation AAS/Submodel
                        malo_sm = self.create_marktlokation_submodel(self.sanitize_id_short(equip['name']),
                                                                     equip['type'])
                        all_objects.append(malo_sm)

                        # Add Marktlokation to the Asset (Load/PV) AAS
                        asset_aas.submodel.add(model.ModelReference.from_referable(malo_sm))

                        # Add to Registry
                        markt_entries.value.add(model.ReferenceElement(id_short=malo_sm.id_short,
                                                                       value=model.ModelReference.from_referable(
                                                                           malo_sm)))

                        # --- CHANGE 3.1: Link MARKTLOKATION -> MESSLOKATION (Bidirectional) ---
                        melo_ref_collection = model.SubmodelElementCollection(
                            id_short="Ref_Messlokation",
                            description="Reference to the parent Messlokation"
                        )
                        melo_ref_collection.value.add(model.ReferenceElement(
                            id_short="Messlokation_Reference",
                            value=model.ModelReference.from_referable(melo_aas)
                        ))
                        # Explicit ID property for easier reading
                        melo_ref_collection.value.add(model.Property(
                            id_short="Messlokation_GlobalAssetId",
                            value_type=model.datatypes.String,
                            value=melo_aas.asset_information.global_asset_id
                        ))
                        malo_sm.submodel_element.add(melo_ref_collection)

                        # --- CHANGE 3.2: Link MESSLOKATION -> MARKTLOKATION (Bidirectional) ---
                        # Add a reference to this specific Marktlokation into the collection created above
                        malo_ref_entry = model.SubmodelElementCollection(
                            id_short=f"Ref_{malo_sm.id_short}",
                            description=f"Reference to Marktlokation for {equip['name']}"
                        )
                        malo_ref_entry.value.add(model.ReferenceElement(
                            id_short="Marktlokation_Reference",
                            value=model.ModelReference.from_referable(malo_sm)
                        ))
                        malo_collection.value.add(malo_ref_entry)

        # == STEP 6: Build Hierarchy ==
        # HIERARCHY LEVEL 1: DSO -> PowerSystem (already created as dso_bom)
        logger.info("DSO top-level exists. PowerSystem is attached under DSO via BoM.")

        # HIERARCHY LEVEL 2: PowerSystem -> Substation
        logger.info("Building hierarchy level: PowerSystem -> Substation")

        substation_aass = [
            aas for aas in aas_cache.values()
            if aas.asset_information.asset_type == "CIM_Substation"
        ]

        # Storage for Edge Devices per Substation
        edge_devices_by_substation = {}

        if substation_aass:

            # Link PowerSystem -> Substations
            bom_system = self.create_bill_of_material_submodel(system_aas, substation_aass)
            all_objects.append(bom_system)
            system_aas.submodel.add(model.ModelReference.from_referable(bom_system))

            for sub_aas in substation_aass:

                sub_id = next(
                    key for key, val in aas_cache.items()
                    if val is sub_aas
                )

                # ---- Find Transformer Terminals (MV / LV detection logic preserved) ----
                mv_terminal_aas = None
                lv_terminal_aas = None

                transformers = self._find_substation_equipment(sub_id)

                target_transformer = next(
                    (t for t in transformers if self.extract_asset_type(t) == "PowerTransformer"),
                    None
                )

                if target_transformer:

                    trans_id = target_transformer.get(f"{{{NS['rdf']}}}ID", "").lstrip("_")
                    trans_terminals = self._find_terminals_for_equipment(trans_id)

                    for t in trans_terminals:

                        t_id = t.get(f"{{{NS['rdf']}}}ID", "").lstrip("_")

                        seq_elem = t.find("cim:ACDCTerminal.sequenceNumber", NS)
                        seq_num = int(seq_elem.text) if seq_elem is not None else 0

                        if t_id not in aas_cache:
                            t_aas, t_sm, _ = self.create_terminal_aas(t)
                            all_objects.append(t_aas)
                            all_objects.append(t_sm)
                            aas_cache[t_id] = t_aas
                        else:
                            t_aas = aas_cache[t_id]

                        if seq_num == 1:
                            mv_terminal_aas = t_aas
                        elif seq_num > 1:
                            lv_terminal_aas = t_aas
                        else:
                            if mv_terminal_aas is None:
                                mv_terminal_aas = t_aas
                            elif lv_terminal_aas is None:
                                lv_terminal_aas = t_aas

                # ---- Create Edge Device ----
                edge_objects = self.create_beckhoff_edge_device(sub_aas.id_short)
                all_objects.extend(edge_objects)

                edge_aas = edge_objects[0]

                # Store edge device for Level 3 BoM creation
                edge_devices_by_substation[sub_id] = edge_aas

                # ---- Create Primary Measurement Device (EL3475) ----
                meas_objects = self.create_beckhoff_measurement_setup(
                    sub_aas.id_short,
                    fuses_by_side,
                    ct_aas,
                    vt_aas
                )

                all_objects.extend(meas_objects)
                meas_aas = meas_objects[0]

                # Prepare a list of all child devices for the Edge Device BoM
                child_devices_for_edge = [meas_aas]

                # ---- Create 3x EL3702 Measurement Devices ----
                ext_terminal_aas = ext_grid_terminal_aass[0] if ext_grid_terminal_aass else None
                for i in range(1, 4):
                    el3702_objs = self.create_beckhoff_el3702_device(sub_aas.id_short, i, ext_terminal_aas)
                    all_objects.extend(el3702_objs)
                    child_devices_for_edge.append(el3702_objs[0])

                # ---- Link Edge Device -> All Measurement Devices ----
                edge_meas_bom = self.create_bill_of_material_submodel(edge_aas, child_devices_for_edge)
                edge_meas_bom.id_short = "BillofMaterial"

                all_objects.append(edge_meas_bom)
                edge_aas.submodel.add(model.ModelReference.from_referable(edge_meas_bom))

        # HIERARCHY LEVEL 3: Substation -> PowerTransformer + EdgeDevice
        logger.info("Building hierarchy level: Substation -> PowerTransformer")

        for substation_elem in self.root.findall(".//cim:Substation", NS):

            substation_id = substation_elem.get(f"{{{NS['rdf']}}}ID", "").lstrip("_")
            substation_aas = aas_cache.get(substation_id)

            if not substation_aas:
                continue

            child_aass = []

            # ---- Collect Transformers ----
            child_equipment_elems = self._find_substation_equipment(substation_id)

            for equip_elem in child_equipment_elems:

                if self.extract_asset_type(equip_elem) == "PowerTransformer":

                    equip_id = equip_elem.get(f"{{{NS['rdf']}}}ID", "").lstrip("_")

                    if equip_id in aas_cache:
                        child_aass.append(aas_cache[equip_id])

            # ---- Add Edge Device ----
            edge_aas = edge_devices_by_substation.get(substation_id)

            if edge_aas:
                child_aass.append(edge_aas)

            # ---- Create Unified BoM ----
            if child_aass:

                # Prevent duplicate BoM creation
                existing_bom = any(
                    sm_ref.key[0].value.endswith("_BoM")
                    for sm_ref in substation_aas.submodel
                )

                if not existing_bom:
                    bom_substation = self.create_bill_of_material_submodel(
                        substation_aas,
                        child_aass
                    )

                    all_objects.append(bom_substation)
                    substation_aas.submodel.add(
                        model.ModelReference.from_referable(bom_substation)
                    )

        # HIERARCHY LEVEL 4: PowerTransformer -> ConnectivityNode
        logger.info("Building hierarchy level: PowerTransformer -> ConnectivityNode")
        for transformer_elem in self.root.findall(".//cim:PowerTransformer", NS):
            transformer_id = transformer_elem.get(f"{{{NS['rdf']}}}ID", "").lstrip("_")
            transformer_aas = aas_cache.get(transformer_id)
            if not transformer_aas: continue

            terminals = self._find_terminals_for_equipment(transformer_id)
            connected_node_ids = set()
            for terminal in terminals:
                node_ref = terminal.find("cim:Terminal.ConnectivityNode", NS)
                if node_ref is not None:
                    node_id = node_ref.get(f"{{{NS['rdf']}}}resource", "").lstrip("#_")
                    connected_node_ids.add(node_id)

            child_node_aass = [aas_cache[node_id] for node_id in connected_node_ids if node_id in aas_cache]
            if child_node_aass:
                bom_transformer = self.create_bill_of_material_submodel(transformer_aas, child_node_aass)
                all_objects.append(bom_transformer)
                transformer_aas.submodel.add(model.ModelReference.from_referable(bom_transformer))

        # HIERARCHY LEVEL 5: ConnectivityNode -> Other Assets (PV, Battery, Load, etc.)
        logger.info("Building hierarchy level: ConnectivityNode -> Other Assets")
        for node_elem in self.root.findall(".//cim:ConnectivityNode", NS):
            node_id = node_elem.get(f"{{{NS['rdf']}}}ID", "").lstrip("_")
            node_aas = aas_cache.get(node_id)
            if not node_aas: continue

            connected_equipment = self.get_connected_equipment_for_node(node_id)
            child_asset_aass = []
            for equip in connected_equipment:
                if equip['type'] != 'PowerTransformer' and equip['id'] in aas_cache:
                    child_asset_aass.append(aas_cache[equip['id']])

            if child_asset_aass:
                bom_node = self.create_bill_of_material_submodel(node_aas, child_asset_aass)
                all_objects.append(bom_node)
                node_aas.submodel.add(model.ModelReference.from_referable(bom_node))

        # == STEP 7: Write all created objects to the output file ==
        output_file = self.output_dir / f"cim_eq_gl_aasx_hierarchical_{self.cim_eq_file.stem}.json"
        write_aas_to_file(all_objects, output_file)
        self._update_cim_file_with_aas_references()

        logger.success(f"Hierarchical CIM EQ+GL to AASX conversion with bidirectional linking completed: {output_file}")
        aas_count = len([obj for obj in all_objects if isinstance(obj, model.AssetAdministrationShell)])
        submodel_count = len([obj for obj in all_objects if isinstance(obj, model.Submodel)])
        logger.info(f"Created {aas_count} AAS and {submodel_count} submodels")
        logger.info(f"Added {len(self.aas_references)} bidirectional references to CIM file")

        return {
            "output_file": str(output_file),
            "aas_count": aas_count,
            "submodel_count": submodel_count,
            "cim_updated": True,
            "bidirectional_links": len(self.aas_references)
        }


def process_cim_eq_to_aasx(cim_eq_path: Path, output_dir: Path = None, cim_gl_path: Optional[Path] = None):
    """Main function to process CIM EQ to AASX conversion."""
    converter = CIMEQToAASXConverter(cim_eq_path, output_dir, cim_gl_path)
    return converter.convert()
