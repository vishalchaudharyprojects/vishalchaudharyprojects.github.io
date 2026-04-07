from .base import CIMObject, create_element
import uuid

class Terminal:
    def __init__(self, rdf_root, name, conducting_equipment_id, sequence_number):
        self.rdf_root = rdf_root
        self.name = name
        self.conducting_equipment_id = conducting_equipment_id
        self.sequence_number = sequence_number
        self.mrid = str(uuid.uuid4())
        self.connectivity_node_id = None

    def create(self, cim_ns):
        terminal_element = create_element(cim_ns, "Terminal", {"rdf:ID": f"_{self.mrid}"})
        terminal_element.append(create_element(cim_ns, "ACDCTerminal.sequenceNumber", text=str(self.sequence_number)))
        terminal_element.append(create_element(cim_ns, "IdentifiedObject.mRID", text=self.mrid))
        terminal_element.append(create_element(cim_ns, "IdentifiedObject.name", text=self.name))
        terminal_element.append(create_element(cim_ns, "Terminal.ConductingEquipment", {"rdf:resource": f"#_{self.conducting_equipment_id}"}))
        if self.connectivity_node_id:
            terminal_element.append(create_element(cim_ns, "Terminal.ConnectivityNode", {"rdf:resource": f"#_{self.connectivity_node_id}"}))
        terminal_element.append(create_element(cim_ns, "Terminal.phases", {"rdf:resource": "http://iec.ch/TC57/CIM100#PhaseCode.ABC"}))
        self.rdf_root.append(terminal_element)
        return self.mrid