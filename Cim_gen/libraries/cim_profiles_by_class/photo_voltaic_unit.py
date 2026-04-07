from .base import CIMObject, create_element
import uuid

class PhotoVoltaicUnit(CIMObject):
    def __init__(self, rdf_root, name, equipment_container_id, max_p=0, min_p=0):
        super().__init__(rdf_root)
        self.name = name
        self.mrid = str(uuid.uuid4())
        self.equipment_container_id = equipment_container_id
        self.max_p = max_p
        self.min_p = min_p

    def create(self, cim_ns):
        photovoltaic_unit = create_element(cim_ns, "PhotoVoltaicUnit", {"rdf:ID": f"_{self.mrid}"})
        photovoltaic_unit.append(create_element(cim_ns, "IdentifiedObject.mRID", text=self.mrid))
        photovoltaic_unit.append(create_element(cim_ns, "IdentifiedObject.name", text=self.name))
        photovoltaic_unit.append(create_element(cim_ns, "PowerElectronicsUnit.maxP", text=str(self.max_p)))
        photovoltaic_unit.append(create_element(cim_ns, "PowerElectronicsUnit.minP", text=str(self.min_p)))
        photovoltaic_unit.append(create_element(cim_ns, "Equipment.EquipmentContainer", {"rdf:resource": f"_{self.equipment_container_id}"}))
        self.append_to_root(photovoltaic_unit)
        return self.mrid