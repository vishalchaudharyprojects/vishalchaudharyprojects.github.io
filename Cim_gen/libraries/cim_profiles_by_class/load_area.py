from .base import CIMObject, create_element
import uuid

class LoadArea(CIMObject):
    """
    Represents a LoadArea in the CIM model which groups electrical loads.
    """
    def __init__(self, rdf_root, name):
        super().__init__(rdf_root)
        self.name = name
        self.mrid = str(uuid.uuid4())

    def create(self, cim_ns):
        """
        Creates the XML representation of a LoadArea.
        """
        load_area = create_element(cim_ns, "LoadArea", {"rdf:ID": f"_{self.mrid}"})
        load_area.append(create_element(cim_ns, "IdentifiedObject.mRID", text=self.mrid))
        load_area.append(create_element(cim_ns, "IdentifiedObject.name", text=self.name))
        self.append_to_root(load_area)
