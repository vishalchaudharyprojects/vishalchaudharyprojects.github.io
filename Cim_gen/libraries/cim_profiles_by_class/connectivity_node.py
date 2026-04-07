from .base import CIMObject, create_element
import uuid

class ConnectivityNode(CIMObject):
    """
    Represents a ConnectivityNode in the CIM model which is a point where terminals are connected.
    """
    def __init__(self, rdf_root, node_name, container_id):
        super().__init__(rdf_root)
        self.node_name = node_name
        self.mrid = str(uuid.uuid4())
        self.container_id = container_id

    def create(self, cim_ns):
        """
        Creates the XML representation of a ConnectivityNode.
        """
        connectivity_node = create_element(cim_ns, "ConnectivityNode", {"rdf:ID": f"_{self.mrid}"})
        connectivity_node.append(create_element(cim_ns, "IdentifiedObject.mRID", text=self.mrid))
        connectivity_node.append(create_element(cim_ns, "IdentifiedObject.name", text=self.node_name))
        connectivity_node.append(create_element(cim_ns, "ConnectivityNode.ConnectivityNodeContainer", {"rdf:resource": f"_{self.container_id}"}))
        self.append_to_root(connectivity_node)
        return self.mrid

    def create_terminal(self, connected_equipment, cim_ns, terminal_id):
        """
        Creates a Terminal element associated with this ConnectivityNode.
        """
        terminal_element = create_element(cim_ns, "Terminal", {"rdf:ID": f"_{terminal_id}"})
        terminal_element.append(create_element(cim_ns, "ACDCTerminal.sequenceNumber", text="1"))
        terminal_element.append(create_element(cim_ns, "IdentifiedObject.mRID", text=terminal_id))
        terminal_element.append(create_element(cim_ns, "IdentifiedObject.name", text=self.node_name))
        terminal_element.append(create_element(cim_ns, "Terminal.ConductingEquipment", {"rdf:resource": f"#_{connected_equipment}"}))
        terminal_element.append(create_element(cim_ns, "Terminal.ConnectivityNode", {"rdf:resource": f"#_{self.mrid}"}))
        terminal_element.append(create_element(cim_ns, "Terminal.phases", {"rdf:resource": "http://iec.ch/TC57/CIM100#PhaseCode.ABC"}))
        self.append_to_root(terminal_element)
        return terminal_id
