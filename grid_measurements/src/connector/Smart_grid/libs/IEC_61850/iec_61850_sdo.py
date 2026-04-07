
from grid_measurements.src.connector.Smart_grid.libs.IEC_61850.iec_61850_da import AnalogueValue

# Define the SubDataObject class (parent class of the sub-data objects)
class SubDataObject:
    """
    Base class for a sub-data object

    Attributes:
    name: Name of the sub-data object
    SDO2: Dictionary to hold sub-sub-data objects

    Methods:
    add_subdata_object_2: Add a sub-sub-data object to the dictionary with the given name
    """
    def __init__(self, name):
        self.name = name
        self.SDO2 = {}  # Class-level dictionary for sub-sub-data objects

    def add_subdata_object_2(self, name, subdata_object_2):
        self.SDO2[name] = subdata_object_2

class ComplexValue(SubDataObject, AnalogueValue):
    """Subdata Object for complex values"""
    def __init__(self):
        super().__init__(name="ComplexValue")
        self.add_subdata_object_2("mag", AnalogueValue())  # Real part
        self.add_subdata_object_2("ang", AnalogueValue())  # Imaginary part
