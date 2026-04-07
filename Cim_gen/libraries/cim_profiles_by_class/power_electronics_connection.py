from .base import CIMObject, create_element
import uuid

class PowerElectronicsConnection(CIMObject):
    def __init__(self, rdf_root, name, equipment_container_id, power_electronics_unit_id, rated_s, rated_u, max_q, min_q):
        super().__init__(rdf_root)
        self.name = name
        self.mrid = str(uuid.uuid4())
        self.equipment_container_id = equipment_container_id
        self.power_electronics_unit_id = power_electronics_unit_id
        self.rated_s = rated_s
        self.rated_u = rated_u
        self.max_q = max_q
        self.min_q = min_q

    def create(self, cim_ns):
        connection = create_element(cim_ns, "PowerElectronicsConnection", {"rdf:ID": f"_{self.mrid}"})
        connection.append(create_element(cim_ns, "IdentifiedObject.mRID", text=self.mrid))
        connection.append(create_element(cim_ns, "IdentifiedObject.name", text=self.name))
        connection.append(create_element(cim_ns, "Equipment.EquipmentContainer", {"rdf:resource": f"_{self.equipment_container_id}"}))
        connection.append(create_element(cim_ns, "PowerElectronicsConnection.PowerElectronicsUnit", {"rdf:resource": f"_{self.power_electronics_unit_id}"}))
        connection.append(create_element(cim_ns, "PowerElectronicsConnection.ratedS", text=str(self.rated_s)))
        connection.append(create_element(cim_ns, "PowerElectronicsConnection.ratedU", text=str(self.rated_u)))
        connection.append(create_element(cim_ns, "PowerElectronicsConnection.maxQ", text=str(self.max_q)))
        connection.append(create_element(cim_ns, "PowerElectronicsConnection.minQ", text=str(self.min_q)))
        self.append_to_root(connection)