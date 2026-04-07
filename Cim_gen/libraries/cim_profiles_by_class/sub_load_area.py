from .base import CIMObject, create_element
import uuid

class SubLoadArea(CIMObject):
    def __init__(self, rdf_root, name, load_area_id):
        super().__init__(rdf_root)
        self.name = name
        self.mrid = str(uuid.uuid4())
        self.load_area_id = load_area_id

    def create(self, cim_ns):
        sub_load_area = create_element(cim_ns, "SubLoadArea", {"rdf:ID": f"_{self.mrid}"})
        sub_load_area.append(create_element(cim_ns, "IdentifiedObject.mRID", text=self.mrid))
        sub_load_area.append(create_element(cim_ns, "IdentifiedObject.name", text=self.name))
        sub_load_area.append(create_element(cim_ns, "SubLoadArea.LoadArea", {"rdf:resource": f"_{self.load_area_id}"}))
        self.append_to_root(sub_load_area)