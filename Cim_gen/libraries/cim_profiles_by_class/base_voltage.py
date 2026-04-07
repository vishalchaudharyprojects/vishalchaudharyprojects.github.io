from .base import CIMObject, create_element
import uuid


class BaseVoltage(CIMObject):
    """
    Represents a BaseVoltage CIM object with associated attributes.

    Attributes:
        nominal_voltage (str): The nominal voltage of the BaseVoltage object.
        description (str): A description of the BaseVoltage object.
        name (str): The name of the BaseVoltage object.
        mrid (str): A unique identifier (UUID) for the object.
    """

    def __init__(self, rdf_root, nominal_voltage, description, name):
        super().__init__(rdf_root)
        self.nominal_voltage = nominal_voltage
        self.description = description
        self.name = name
        self.mrid = str(uuid.uuid4())  # Generate a unique identifier

    def create(self, cim_ns):
        """
        Create a BaseVoltage XML element and append it to the RDF root.

        Args:
            cim_ns (str): The namespace URI for CIM elements.
        """
        # Create the root BaseVoltage element with a unique ID
        base_voltage = create_element(cim_ns, "BaseVoltage", {"rdf:ID": f"_{self.mrid}"})

        # Add child elements with relevant attributes
        base_voltage.append(create_element(cim_ns, "BaseVoltage.nominalVoltage", text=self.nominal_voltage))
        base_voltage.append(create_element(cim_ns, "IdentifiedObject.description", text=self.description))
        base_voltage.append(create_element(cim_ns, "IdentifiedObject.mRID", text=self.mrid))
        base_voltage.append(create_element(cim_ns, "IdentifiedObject.name", text=self.name))

        # Append the BaseVoltage element to the RDF root
        self.append_to_root(base_voltage)
        return self.mrid