from .base import CIMObject, create_element
import uuid

class SVProfile(CIMObject):
    def __init__(self, rdf_root):
        super().__init__(rdf_root)

    def create_sv_power_flow(self, terminal_id, p, q, cim_ns):
        mrid = str(uuid.uuid4())
        power_flow = create_element(cim_ns, "SvPowerFlow", {"rdf:ID": f"_{mrid}"})
        power_flow.append(create_element(cim_ns, "SvPowerFlow.Terminal", {"rdf:resource": f"#_{terminal_id}"}))
        power_flow.append(create_element(cim_ns, "SvPowerFlow.p", text=str(p)))
        power_flow.append(create_element(cim_ns, "SvPowerFlow.q", text=str(q)))
        self.append_to_root(power_flow)

    def create_sv_status(self, conducting_equipment_id, in_service, cim_ns):
        mrid = str(uuid.uuid4())
        status = create_element(cim_ns, "SvStatus", {"rdf:ID": f"_{mrid}"})
        status.append(create_element(cim_ns, "SvStatus.ConductingEquipment", {"rdf:resource": f"#_{conducting_equipment_id}"}))
        status.append(create_element(cim_ns, "SvStatus.inService", text=str(in_service).lower()))
        self.append_to_root(status)

    def create_sv_voltage(self, topological_node_id, angle, v, cim_ns):
        mrid = str(uuid.uuid4())
        voltage = create_element(cim_ns, "SvVoltage", {"rdf:ID": f"_{mrid}"})
        voltage.append(create_element(cim_ns, "SvVoltage.TopologicalNode", {"rdf:resource": f"#_{topological_node_id}"}))
        voltage.append(create_element(cim_ns, "SvVoltage.angle", text=str(angle)))
        voltage.append(create_element(cim_ns, "SvVoltage.v", text=str(v)))
        self.append_to_root(voltage)