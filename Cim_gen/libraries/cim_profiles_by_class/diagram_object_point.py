from .base import CIMObject, create_element
import uuid

class DiagramObjectPoint(CIMObject):
    """
    Represents a DiagramObjectPoint used to visually locate elements on diagrams.
    """
    def __init__(self, rdf_root, diagram_object_id, sequence_number, x_position, y_position):
        super().__init__(rdf_root)
        self.diagram_object_id = diagram_object_id
        self.sequence_number = sequence_number
        self.x_position = x_position
        self.y_position = y_position
        self.mrid = str(uuid.uuid4())

    def create(self, cim_ns):
        """
        Creates the XML representation of a DiagramObjectPoint element.
        """
        diagram_object_point = create_element(cim_ns, "DiagramObjectPoint", {"rdf:ID": f"_{self.mrid}"})
        diagram_object_point.append(create_element(cim_ns, "DiagramObjectPoint.DiagramObject", {"rdf:resource": f"#_{self.diagram_object_id}"}))
        diagram_object_point.append(create_element(cim_ns, "DiagramObjectPoint.sequenceNumber", text=str(self.sequence_number)))
        diagram_object_point.append(create_element(cim_ns, "DiagramObjectPoint.xPosition", text=str(self.x_position)))
        diagram_object_point.append(create_element(cim_ns, "DiagramObjectPoint.yPosition", text=str(self.y_position)))
        self.append_to_root(diagram_object_point)
