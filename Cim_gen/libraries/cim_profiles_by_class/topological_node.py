from .base import CIMObject, create_element
import uuid

class TopologicalNode(CIMObject):
    def __init__(self, rdf_root, name, base_voltage_id, equipment_container_id):
        super().__init__(rdf_root)
        self.name = name
        self.mrid = str(uuid.uuid4())
        self.base_voltage_id = base_voltage_id
        self.connectivity_node_container_id = equipment_container_id

    def create(self, cim_ns):
        topo_node = create_element(cim_ns, "TopologicalNode", {"rdf:ID": f"_{self.mrid}"})
        topo_node.append(create_element(cim_ns, "IdentifiedObject.mRID", text=self.mrid))
        topo_node.append(create_element(cim_ns, "IdentifiedObject.name", text=self.name))
        topo_node.append(create_element(cim_ns, "TopologicalNode.BaseVoltage", {"rdf:resource": f"#_{self.base_voltage_id}"}))
        topo_node.append(create_element(cim_ns, "TopologicalNode.ConnectivityNodeContainer", {"rdf:resource": f"#_{self.connectivity_node_container_id}"}))
        self.append_to_root(topo_node)
        return self.mrid

    def create_connectivity_node(self, connectivity_node_id, topo_id, cim_ns):
        connectivity_node = create_element(cim_ns, "ConnectivityNode", {"rdf:about": f"#_{connectivity_node_id}"})
        connectivity_node.append(create_element(cim_ns, "ConnectivityNode.TopologicalNode", {"rdf:resource": f"#_{topo_id}"}))
        self.append_to_root(connectivity_node)

    def create_terminal(self, terminal_id, topo_id, cim_ns):
        terminal = create_element(cim_ns, "Terminal", {"rdf:about": f"#_{terminal_id}"})
        terminal.append(create_element(cim_ns, "Terminal.TopologicalNode", {"rdf:resource": f"#_{topo_id}"}))
        self.append_to_root(terminal)