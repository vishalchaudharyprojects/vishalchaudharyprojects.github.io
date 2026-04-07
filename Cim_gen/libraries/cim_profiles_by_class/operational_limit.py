from .base import CIMObject, create_element
import uuid

class OperationalLimitSet(CIMObject):
    def __init__(self, rdf_root, terminal_id, name="Voltage limits"):
        super().__init__(rdf_root)
        self.mrid = str(uuid.uuid4())
        self.terminal_id = terminal_id
        self.name = name

    def create(self, cim_ns):
        operational_limit_set = create_element(cim_ns, "OperationalLimitSet", {"rdf:ID": f"_{self.mrid}"})
        operational_limit_set.append(create_element(cim_ns, "IdentifiedObject.mRID", text=self.mrid))
        operational_limit_set.append(create_element(cim_ns, "IdentifiedObject.name", text=self.name))
        operational_limit_set.append(create_element(cim_ns, "OperationalLimitSet.Terminal", {"rdf:resource": f"#_{self.terminal_id}"}))
        self.append_to_root(operational_limit_set)
        return self.mrid

    def link_to_limit_type(self, limit_type_id, cim_ns):
        operational_limit_set = create_element(cim_ns, "OperationalLimitSet.Limits", {"rdf:resource": f"#_{limit_type_id}"})

class OperationalLimitType(CIMObject):
    def __init__(self, rdf_root, limit_name, kind, direction, duration="true"):
        super().__init__(rdf_root)
        self.mrid = str(uuid.uuid4())
        self.limit_name = limit_name
        self.kind = kind
        self.direction = direction
        self.duration = duration

    def create(self, cim_ns):
        operational_limit_type = create_element(cim_ns, "OperationalLimitType", {"rdf:ID": f"_{self.mrid}"})
        operational_limit_type.append(create_element(cim_ns, "IdentifiedObject.mRID", text=self.mrid))
        operational_limit_type.append(create_element(cim_ns, "IdentifiedObject.name", text=self.limit_name))
        operational_limit_type.append(create_element(cim_ns, "OperationalLimitType.direction", {"rdf:resource": f"http://iec.ch/TC57/CIM100#OperationalLimitDirectionKind.{self.direction}"}))
        operational_limit_type.append(create_element(cim_ns, "OperationalLimitType.isInfiniteDuration", text=self.duration))
        operational_limit_type.append(create_element(cim_ns, "OperationalLimitType.kind", {"rdf:resource": f"http://iec.ch/TC57/CIM100-European#LimitKind.{self.kind}"}))
        self.append_to_root(operational_limit_type)
        return self.mrid