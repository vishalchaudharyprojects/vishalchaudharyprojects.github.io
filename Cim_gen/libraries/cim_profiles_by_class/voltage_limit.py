from .base import CIMObject, create_element
import uuid

class VoltageLimit(CIMObject):
    def __init__(self, rdf_root, voltage_limit_value, terminal_id, name):
        super().__init__(rdf_root)
        self.voltage_limit_value = voltage_limit_value
        self.mrid = str(uuid.uuid4())
        self.terminal_id = terminal_id
        self.name = name

    def create(self, cim_ns, operational_limit_set_id, operational_limit_type_id):
        voltage_limit = create_element(cim_ns, "VoltageLimit", {"rdf:ID": f"_{self.mrid}"})
        voltage_limit.append(create_element(cim_ns, "IdentifiedObject.mRID", text=self.mrid))
        voltage_limit.append(create_element(cim_ns, "IdentifiedObject.name", text=self.name))
        voltage_limit.append(create_element(cim_ns, "VoltageLimit.normalValue", text=self.voltage_limit_value))
        voltage_limit.append(create_element(cim_ns, "OperationalLimit.OperationalLimitSet", {"rdf:resource": f"#_{operational_limit_set_id}"}))
        voltage_limit.append(create_element(cim_ns, "OperationalLimit.OperationalLimitType", {"rdf:resource": f"#_{operational_limit_type_id}"}))
        self.append_to_root(voltage_limit)