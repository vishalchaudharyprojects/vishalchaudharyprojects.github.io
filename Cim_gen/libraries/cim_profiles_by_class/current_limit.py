from .base import CIMObject, create_element
import uuid

class CurrentLimit(CIMObject):
    """
    Represents a CurrentLimit CIM object defining operational limits for electrical equipment.
    """
    def __init__(self, rdf_root, current_limit_value, terminal_id, name):
        super().__init__(rdf_root)
        self.current_limit_value = current_limit_value
        self.mrid = str(uuid.uuid4())
        self.terminal_id = terminal_id
        self.name = name

    def create(self, cim_ns, operational_limit_set_id, operational_limit_type_id):
        """
        Creates the XML representation of a CurrentLimit element.
        """
        current_limit = create_element(cim_ns, "CurrentLimit", {"rdf:ID": f"_{self.mrid}"})
        current_limit.append(create_element(cim_ns, "IdentifiedObject.mRID", text=self.mrid))
        current_limit.append(create_element(cim_ns, "IdentifiedObject.name", text=self.name))
        current_limit.append(create_element(cim_ns, "CurrentLimit.normalValue", text=self.current_limit_value))
        current_limit.append(create_element(cim_ns, "OperationalLimit.OperationalLimitSet", {"rdf:resource": f"#_{operational_limit_set_id}"}))
        current_limit.append(create_element(cim_ns, "OperationalLimit.OperationalLimitType", {"rdf:resource": f"#_{operational_limit_type_id}"}))
        self.append_to_root(current_limit)
        return self.mrid
