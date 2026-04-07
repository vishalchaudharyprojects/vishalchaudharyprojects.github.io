from .base import CIMObject, create_element
import uuid

class ConformLoad(CIMObject):
    """
    Represents a ConformLoad (predictable load pattern) in CIM CGMES.

    Attributes:
        load_name (str): Name of the load.
        mrid (str): Unique identifier.
        equipment_container_id (str): Associated equipment container (e.g., substation).
        load_group_id (str): Reference to a ConformLoadGroup.
        load_response_id (str): Reference to LoadResponse characteristics.
    """

    def __init__(self, rdf_root, load_name, equipment_container_id, load_group_id, load_response_id):
        super().__init__(rdf_root)
        self.load_name = load_name
        self.mrid = str(uuid.uuid4())
        self.equipment_container_id = equipment_container_id
        self.load_group_id = load_group_id
        self.load_response_id = load_response_id

    def create(self, cim_ns):
        """
        Create the ConformLoad XML element.

        Args:
            cim_ns (str): CIM namespace URI.

        Returns:
            str: Unique mRID of the ConformLoad.
        """
        conform_load = create_element(cim_ns, "ConformLoad", {"rdf:ID": f"_{self.mrid}"})
        conform_load.append(create_element(cim_ns, "IdentifiedObject.mRID", text=self.mrid))
        conform_load.append(create_element(cim_ns, "IdentifiedObject.name", text=self.load_name))
        conform_load.append(create_element(cim_ns, "Equipment.EquipmentContainer", {"rdf:resource": f"_{self.equipment_container_id}"}))
        conform_load.append(create_element(cim_ns, "ConformLoad.LoadGroup", {"rdf:resource": f"_{self.load_group_id}"}))
        conform_load.append(create_element(cim_ns, "EnergyConsumer.LoadResponse", {"rdf:resource": f"_{self.load_response_id}"}))
        self.append_to_root(conform_load)
        return self.mrid
