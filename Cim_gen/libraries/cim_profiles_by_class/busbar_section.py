from .base import CIMObject, create_element
import uuid

class BusbarSection(CIMObject):
    """
    Represents a busbar section in a substation (CIM CGMES).

    Attributes:
        busbar_name (str): Name of the busbar.
        mrid (str): Unique identifier.
        equipment_container_id (str): Reference to containing substation or voltage level.
    """

    def __init__(self, rdf_root, busbar_name, equipment_container_id):
        super().__init__(rdf_root)
        self.busbar_name = busbar_name
        self.mrid = str(uuid.uuid4())
        self.equipment_container_id = equipment_container_id

    def create(self, cim_ns):
        """
        Create the BusbarSection XML element.

        Args:
            cim_ns (str): CIM namespace URI.

        Returns:
            str: Unique mRID of the BusbarSection.
        """
        busbar_section = create_element(cim_ns, "BusbarSection", {"rdf:ID": f"_{self.mrid}"})
        busbar_section.append(create_element(cim_ns, "IdentifiedObject.mRID", text=self.mrid))
        busbar_section.append(create_element(cim_ns, "IdentifiedObject.name", text=self.busbar_name))
        busbar_section.append(create_element(cim_ns, "Equipment.EquipmentContainer", {"rdf:resource": f"_{self.equipment_container_id}"}))
        self.append_to_root(busbar_section)
        return self.mrid
