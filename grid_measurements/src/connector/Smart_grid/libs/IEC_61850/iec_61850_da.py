from grid_measurements.src.connector.Smart_grid.libs.IEC_61850.iec_61850_enum import *


# Define the Data Attribute class (parent class of the data attributes)
class DataAttribute:
    """
    Base class for data attributes

    Attributes:
    name: Name of the data attribute
    DA: Dictionary to hold data attributes

    Methods:
    add_data_attribute: Add a data attribute to the dictionary with given name
    set_da: Set the value of a data attribute with the given name
    """
    def __init__(self, name):
        self.name = name
        self.DA = {}

    def add_data_attribute(self, name, value):
        self.DA[name] = value

    def set_da(self,name,value):
        if name in self.DA:
            self.DA[name] = value
        else:
            raise KeyError(f"Data attribute {name} not found")

# Analoguevalue class, includes floating point and integer values
class AnalogueValue(DataAttribute):
    """Data Attribute for analogue values"""
    def __init__(self):
        super().__init__("AnalogueValue")
        self.add_data_attribute("f", 0.0)  # Floating point value
        self.add_data_attribute("i", 0)  # Integer value


# Timestamp class
class TimeStamp(DataAttribute):
    """Data Attribute for the timestamp"""
    def __init__(self, seconds=0, nanoseconds=0):
        super().__init__("TimeStamp")
        self.add_data_attribute("seconds", 0)  # Seconds since the epoch (UNIX timestamp), int32 (IEC 61850-7-2:2010)
        self.add_data_attribute("second_fractions", 0)  # Fractions of a second, int 64 (IEC 61850-7-2:2010)


# Quality class
class Quality(DataAttribute):
    """Data Attribute for quality"""
    def __init__(self, validity: Validity = Validity.GOOD):
        super().__init__("Quality")
        self.add_data_attribute("validity", validity)  # Validity of the data (Enum)


# class for the Originator of a control message
class Originator(DataAttribute):
    """Data Attribute for the originator of a control message"""
    def __init__(self):
        super().__init__("Originator")
        self.add_data_attribute("orCat", orCategory)
        self.add_data_attribute("orIdent", str)

# class for the data object of the operate service
class OperAnalogueValue(DataAttribute):
    def __init__(self):
        """Data Object for the operate service of analogue values"""
        super().__init__("Oper_AnalogueValue")
        self.add_data_attribute("ctlVal", AnalogueValue())
        self.add_data_attribute("origin", Originator())
        self.add_data_attribute("ctlNum", int)
        self.add_data_attribute("T", TimeStamp())
        self.add_data_attribute("Test", bool)


# class for the data object of the operate service with boolean data type
class OperBoolean(DataAttribute):
    def __init__(self):
        """Data Object for the operate service of analogue values"""
        super().__init__("Oper_Boolean")
        self.add_data_attribute("ctlVal", bool)
        self.add_data_attribute("origin", Originator())
        self.add_data_attribute("ctlNum", int)
        self.add_data_attribute("T", TimeStamp())
        self.add_data_attribute("Test", bool)


# Operate service with enumerated data type
class OperCodedEnum(DataAttribute):
    def __init__(self):
        """Data Object for the operate service of analogue values"""
        super().__init__("Oper_Boolean")
        self.add_data_attribute("ctlVal", Tcmd)
        self.add_data_attribute("origin", Originator())
        self.add_data_attribute("ctlNum", int)
        self.add_data_attribute("T", TimeStamp())
        self.add_data_attribute("Test", bool)


# Units class, includes standards SI units and multipliers as enums
class Units(DataAttribute):
    """Data Attribute for units"""
    def __init__(self, si_unit: SIUnit=None):
        super().__init__("Units")
        self.add_data_attribute("SIUnit",si_unit)  # Standard SI unit (e.g., "W", "V", "A")


# CalendarTime class, for calendar entries
class CalendarTime(DataAttribute):
    """Data Attribute for calendar time"""
    def __init__(self):
        super().__init__("CalendarTime")
        self.add_data_attribute("occ", int) # occurence of a calendar event,
        # 0 used for last, for week numbers 01-52, etc.
        self.add_data_attribute("occType", Occurencetype) # the kind of occurence
        # given in the CalendarTime object
        self.add_data_attribute("occPer", Occurenceperiod) #in which period is an
        # occurence appearing
        self.add_data_attribute("year", int)  # Year
        self.add_data_attribute("weekDay", Weekday)  # Weekday
        self.add_data_attribute("day", int)  # Day
        self.add_data_attribute("hr", int)  # Hour
        self.add_data_attribute("mn", int)  # Minute
        self.add_data_attribute("month", Month)  # Month