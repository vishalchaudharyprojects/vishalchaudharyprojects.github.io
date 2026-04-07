from .base import CIMObject, create_element
import xml.etree.ElementTree as ET

class FullModel:
    """
    Represents a full CIM model instance with metadata for modeling authority, profiles, and scenario time.
    """
    def __init__(self, model_id, created_time, authority, profiles, scenario_time):
        self.model_id = model_id
        self.created_time = created_time
        self.authority = authority
        self.profiles = profiles
        self.scenario_time = scenario_time

    def to_xml(self, md_ns):
        """
        Converts this full model metadata to its XML representation.
        """
        fullmodel_elem = ET.Element(f"{{{md_ns}}}FullModel", {"rdf:about": f"urn:uuid:{self.model_id}"})
        ET.SubElement(fullmodel_elem, f"{{{md_ns}}}Model.created").text = self.created_time
        ET.SubElement(fullmodel_elem, f"{{{md_ns}}}Model.modelingAuthoritySet").text = self.authority
        for profile in self.profiles:
            ET.SubElement(fullmodel_elem, f"{{{md_ns}}}Model.profile").text = profile
        ET.SubElement(fullmodel_elem, f"{{{md_ns}}}Model.scenarioTime").text = self.scenario_time
        return fullmodel_elem
