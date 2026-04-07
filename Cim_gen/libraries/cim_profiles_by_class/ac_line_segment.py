from .base import CIMObject, create_element
import uuid


class ACLineSegment(CIMObject):
    """
    Represents an ACLineSegment object based on the CIM CGMES standard.

    Attributes:
        line_name (str): Name of the line segment.
        length (float): Length of the line in kilometers.
        resistance (float): Series resistance (Ω/km).
        reactance (float): Series reactance (Ω/km).
        shunt_susceptance (float): Total shunt susceptance (S/km).
        base_voltage_id (str): The mRID of the associated BaseVoltage object.
        mrid (str): Unique identifier for this line segment (UUID).
    """

    def __init__(self, rdf_root, line_name, length, resistance, reactance, shunt_susceptance, base_voltage_id):
        """
        Initialize an ACLineSegment instance.

        Args:
            rdf_root (Element): The RDF root XML element to which this element will be appended.
            line_name (str): Name of the line.
            length (float): Length of the AC line segment in kilometers.
            resistance (float): Series resistance in ohms per km.
            reactance (float): Series reactance in ohms per km.
            shunt_susceptance (float): Shunt susceptance in siemens per km.
            base_voltage_id (str): ID reference to the associated BaseVoltage object.
        """
        super().__init__(rdf_root)
        self.line_name = line_name
        self.length = length
        self.resistance = resistance
        self.reactance = reactance
        self.shunt_susceptance = shunt_susceptance
        self.base_voltage_id = base_voltage_id
        self.mrid = str(uuid.uuid4())  # Generate a unique ID for this line

    def create(self, cim_ns):
        """
        Creates the ACLineSegment XML element and appends it to the RDF document.

        Args:
            cim_ns (str): Namespace URI for CIM elements.

        Returns:
            str: The unique mRID of the created ACLineSegment.
        """
        # Create the root element for this ACLineSegment with unique RDF ID
        ac_line_element = create_element(cim_ns, "ACLineSegment", {"rdf:ID": f"_{self.mrid}"})

        # Add mandatory CIM attributes
        ac_line_element.append(create_element(cim_ns, "IdentifiedObject.mRID", text=str(self.mrid)))
        ac_line_element.append(create_element(cim_ns, "IdentifiedObject.name", text=self.line_name))
        ac_line_element.append(create_element(cim_ns, "Conductor.length", text=str(self.length)))

        # Electrical parameters as per CGMES specification
        ac_line_element.append(
            create_element(cim_ns, "ACLineSegment.shortCircuitEndTemperature", text='80'))  # default value in °C
        ac_line_element.append(create_element(cim_ns, "ACLineSegment.r", text=str(self.resistance)))
        ac_line_element.append(create_element(cim_ns, "ACLineSegment.r0", text='0'))  # zero-sequence resistance
        ac_line_element.append(create_element(cim_ns, "ACLineSegment.x", text=str(self.reactance)))
        ac_line_element.append(create_element(cim_ns, "ACLineSegment.x0", text='0'))  # zero-sequence reactance
        ac_line_element.append(
            create_element(cim_ns, "ACLineSegment.bch", text=str(self.shunt_susceptance)))  # charging susceptance
        ac_line_element.append(
            create_element(cim_ns, "ACLineSegment.b0ch", text='0'))  # zero-sequence shunt susceptance
        ac_line_element.append(
            create_element(cim_ns, "ACLineSegment.g0ch", text='0'))  # zero-sequence shunt conductance
        ac_line_element.append(create_element(cim_ns, "ACLineSegment.gch", text='0'))  # shunt conductance

        # Reference to associated BaseVoltage using rdf:resource
        ac_line_element.append(
            create_element(cim_ns, "ConductingEquipment.BaseVoltage", {"rdf:resource": f"#_{self.base_voltage_id}"})
        )

        # Append this element to the root RDF document
        self.append_to_root(ac_line_element)

        # Return the unique identifier for external reference
        return self.mrid
