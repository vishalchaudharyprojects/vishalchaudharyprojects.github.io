from .base import CIMObject, create_element
import uuid

class GLProfile(CIMObject):
    """
    Contains methods to generate geographic and location-related CIM elements like CoordinateSystem, Location, and PositionPoint.
    """
    def __init__(self, rdf_root):
        super().__init__(rdf_root)

    def create_coordinate_system(self, cim_ns):
        """
        Creates a WGS-84 coordinate system element.
        """
        coordinate_system_id = str(uuid.uuid4())
        coordinate_system = create_element(cim_ns, "CoordinateSystem", {"rdf:ID": f"_{coordinate_system_id}"})
        coordinate_system.append(create_element(cim_ns, "CoordinateSystem.crsUrn", text="urn:ogc:def:crs:EPSG::4326"))
        coordinate_system.append(create_element(cim_ns, "IdentifiedObject.mRID", text=coordinate_system_id))
        coordinate_system.append(create_element(cim_ns, "IdentifiedObject.name", text="WGS-84"))
        self.append_to_root(coordinate_system)
        return coordinate_system_id

    def create_location_and_position(self, equipment_id, equipment_name, coordinates, cim_ns, coordinate_system_id):
        """
        Creates Location and associated PositionPoint for a given equipment.
        """
        location_id = str(uuid.uuid4())
        position_point_id = str(uuid.uuid4())
        x_position, y_position = coordinates.split(',')[:2]

        location = create_element(cim_ns, "Location", {"rdf:ID": f"_{location_id}"})
        location.append(create_element(cim_ns, "IdentifiedObject.mRID", text=location_id))
        location.append(create_element(cim_ns, "IdentifiedObject.name", text=f"{equipment_name} Location"))
        location.append(create_element(cim_ns, "Location.PowerSystemResources", {"rdf:resource": f"#_{equipment_id}"}))
        location.append(create_element(cim_ns, "Location.CoordinateSystem", {"rdf:resource": f"#_{coordinate_system_id}"}))
        self.append_to_root(location)

        position_point = create_element(cim_ns, "PositionPoint", {"rdf:ID": f"_{position_point_id}"})
        position_point.append(create_element(cim_ns, "PositionPoint.Location", {"rdf:resource": f"#_{location_id}"}))
        position_point.append(create_element(cim_ns, "PositionPoint.xPosition", text=x_position))
        position_point.append(create_element(cim_ns, "PositionPoint.yPosition", text=y_position))
        self.append_to_root(position_point)
