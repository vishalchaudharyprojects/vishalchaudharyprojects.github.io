from .base import CIMObject, create_element
import uuid

class BatteryUnit(CIMObject):
    """
    Represents a battery energy storage unit in CIM CGMES.

    Attributes:
        name (str): Name of the battery unit.
        mrid (str): Unique identifier.
        equipment_container_id (str): Reference to the containing substation or equipment group.
        rated_e (float): Rated energy capacity in MWh.
        max_p (float): Maximum power output in MW.
        min_p (float): Minimum power output in MW.
    """

    def __init__(self, rdf_root, name, equipment_container_id, rated_e=0, max_p=0, min_p=0):
        super().__init__(rdf_root)
        self.name = name
        self.mrid = str(uuid.uuid4())
        self.equipment_container_id = equipment_container_id
        self.rated_e = rated_e
        self.max_p = max_p
        self.min_p = min_p

    def create(self, cim_ns):
        """
        Create the BatteryUnit XML element.

        Args:
            cim_ns (str): CIM namespace URI.

        Returns:
            str: Unique mRID of the BatteryUnit.
        """
        battery_unit = create_element(cim_ns, "BatteryUnit", {"rdf:ID": f"_{self.mrid}"})
        battery_unit.append(create_element(cim_ns, "IdentifiedObject.mRID", text=self.mrid))
        battery_unit.append(create_element(cim_ns, "IdentifiedObject.name", text=self.name))
        battery_unit.append(create_element(cim_ns, "BatteryUnit.ratedE", text=str(self.rated_e)))
        battery_unit.append(create_element(cim_ns, "PowerElectronicsUnit.maxP", text=str(self.max_p)))
        battery_unit.append(create_element(cim_ns, "PowerElectronicsUnit.minP", text=str(self.min_p)))
        battery_unit.append(create_element(cim_ns, "Equipment.EquipmentContainer", {"rdf:resource": f"_{self.equipment_container_id}"}))
        self.append_to_root(battery_unit)
        return self.mrid
