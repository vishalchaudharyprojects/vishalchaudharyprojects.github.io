from .base import CIMObject, create_element
import uuid

class LoadResponseCharacteristic(CIMObject):
    def __init__(self, rdf_root, name, p_voltage_exponent, q_voltage_exponent):
        super().__init__(rdf_root)
        self.name = name
        self.mrid = str(uuid.uuid4())
        self.p_voltage_exponent = p_voltage_exponent
        self.q_voltage_exponent = q_voltage_exponent

    def create(self, cim_ns):
        load_response = create_element(cim_ns, "LoadResponseCharacteristic", {"rdf:ID": f"_{self.mrid}"})
        load_response.append(create_element(cim_ns, "IdentifiedObject.mRID", text=self.mrid))
        load_response.append(create_element(cim_ns, "IdentifiedObject.name", text=self.name))
        load_response.append(create_element(cim_ns, "LoadResponseCharacteristic.pVoltageExponent", text=str(self.p_voltage_exponent)))
        load_response.append(create_element(cim_ns, "LoadResponseCharacteristic.qVoltageExponent", text=str(self.q_voltage_exponent)))
        self.append_to_root(load_response)