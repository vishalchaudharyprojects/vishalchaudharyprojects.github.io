from .base import CIMObject, create_element
import uuid

class ConformLoadGroup(CIMObject):
    """
    Represents a ConformLoadGroup that groups ConformLoads in CGMES.

    Attributes:
        name (str): Name of the load group.
        mrid (str): Unique identifier.
        sub_load_area_id (str): Reference to the SubLoadArea.
    """

    def __init__(self, rdf_root, name, sub_load_area_id):
        super().__init__(rdf_root)
        self.name = name
        self.mrid = str(uuid.uuid4())
        self.sub_load_area_id = sub_load_area_id

    def create(self, cim_ns):
        """
        Create the ConformLoadGroup XML element.

        Args:
            cim_ns (str): CIM namespace URI.

        Returns:
            str: Unique mRID of the ConformLoadGroup.
        """
        load_group = create_element(cim_ns, "ConformLoadGroup", {"rdf:ID": f"_{self.mrid}"})
        load_group.append(create_element(cim_ns, "IdentifiedObject.mRID", text=self.mrid))
        load_group.append(create_element(cim_ns, "IdentifiedObject.name", text=self.name))
        load_group.append(create_element(cim_ns, "LoadGroup.SubLoadArea", {"rdf:resource": f"_{self.sub_load_area_id}"}))
        self.append_to_root(load_group)
        return self.mrid
