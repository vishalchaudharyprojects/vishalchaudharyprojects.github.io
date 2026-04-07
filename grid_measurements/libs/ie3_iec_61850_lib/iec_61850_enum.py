from enum import Enum


# Enumeration for the possible states of a DER
class DERStateKindTransition(Enum):
    """Different states that a DER may be in """
    START = 1
    CONNECT = 2
    DISCONNECT = 3
    DISCONNECT_UNDER_EMERGENCY_CONDITIONS = 4
    GET_BLOCKED = 5
    GET_UNBLOCKED = 6
    GO_TO_MAINTENANCE = 7
    GO_OUT_OF_MAINTENANCE = 8
    STOP = 9
    TURN_OFF_CONTROLLER = 10


# Possible test results for equipment
class EquipmentTestResultKind(Enum):
    """Enumerator with possible values for the equipment test result"""
    UNAVAILABLE = 1
    SUCCESS = 2
    FAULT = 3
    TEST_RUNNING = 4
    TEST_ABORTED = 5
    NOT_APPLICABLE_OR_UNKNOWN = 98


# DER states
class DERStateKind(Enum):
    """Enumerator for possible states of der"""
    ON_BUT_DISCONNECTED_AND_NOT_READY = 1
    STARTING_UP = 2
    DISCONNECTED_AND_AVAILABLE = 3
    DISCONNECTED_AND_AUTHORIZED = 4
    SYNCHRONIZING = 5
    RUNNING = 6
    STOPPING_AND_DISCONNECTING_UNDER_EMERGENCY_CONDITIONS = 7
    STOPPING = 8
    DISCONNECTED_AND_BLOCKED = 9
    DISCONNECTED_AND_IN_MAINTENANCE = 10
    FAILED = 11
    NOT_APPLICABLE_OR_NOT_KNOWN = 98

# Interaction of a BESS with the grid
class ChargeSourceKind(Enum):
    """Enumerator with possible values for the charge source operation"""
    MODE_A = 1 # storage may not export to the grid but may charge from it
    MODE_B = 2 # storage may export to the grid but not charge from it
    MODE_C = 3 # storage may both charge and discharge from the grid

# possible results of battery tests
class BatteryTestResultKind(Enum):
    """Enumerator with possible values for the battery test result"""
    SUCCESS = 1
    FAULT = 2
    UNKNOWN = 99

# Battery types
class BatteryKind(Enum):
    """Enumerator with possible values for the battery type"""
    LEAD_ACID = 1
    NICKEL_METAL_HYDRATE = 2
    NICKEL_CADMIUM = 3
    LITHIUM_ION = 4
    CARBON_ZINC = 5
    ZINC_CHLORIDE = 6
    ALKALINE = 7
    RECHARGABLE_ALKALINE = 8
    SODIUM_SULPHUR = 9
    FLOW = 10
    OTHER = 98
    UNKOWN = 99


# Enumeration for SI Units
class SIUnit(Enum):
    """Enumerator with possible values for SI units"""
    UNIT_1 = 1  #
    METER = 2  # m
    KILOGRAM = 3  # kg
    SECOND = 4  # s
    AMPERE = 5  # A
    KELVIN = 6  # K
    MOLE = 7  # mol
    CANDELA = 8  # cd
    DEGREE = 9  # deg
    RADIAN = 10  # radV
    STERADIAN = 11  # sr
    GRAY = 21  # Gy
    BECQUEREL = 22  # Bq
    DEGREE_CELSIUS = 23  # °C
    SIEVERT = 24  # Sv
    FARAD = 25  # F
    COULOMB = 26  # C
    SIEMENS = 27  # S
    HENRY = 28  # H
    VOLT = 29  # V
    OHM = 30  # ohm
    JOULE = 31  # J
    NEWTON = 32  # N
    HERTZ = 33  # Hz
    LUX = 34  # lx
    LUMEN = 35  # Lm
    WEBER = 36  # Wb
    TESLA = 37  # T
    WATT = 38  # W
    PASCAL = 39  # Pa
    SQUARE_METER = 41  # m²
    CUBIC_METER = 42  # m³
    METERS_PER_SECOND = 43  # m/s
    METERS_PER_SECOND_SQUARED = 44  # m/s²
    CUBIC_METERS_PER_SECOND = 45  # m³/s
    METER_PER_CUBIC_METER = 46  # m/m³
    MEGA = 47  # M
    KILOGRAM_PER_CUBIC_METER = 48  # kg/m³
    SQUARE_METER_PER_SECOND = 49  # m²/s
    WATT_PER_METER_KELVIN = 50  # W/m K
    JOULE_PER_KELVIN = 51  # J/K
    PARTS_PER_MILLION = 52  # ppm
    PER_SECOND = 53  # 1/s
    RADIANS_PER_SECOND = 54  # rad/s
    VOLT_AMPERE = 61  # VA
    WATT_HOUR = 62  # Wh
    VAR = 63  # VAr
    PHI = 64  # phi
    COS_PHI = 65  # cos(phi)
    VOLT_SECOND = 66  # Vs
    SQUARE_VOLT = 67  # V²
    AMPERE_SECOND = 68  # As
    SQUARE_AMPERE = 69  # A²
    AMPERE_SQUARE_TIME = 70  # A²t
    VOLT_AMPERE_HOUR = 71  # VAh
    VOLT_HOUR = 72  # VAh
    VAR_HOUR = 73  # VArh
    VOLT_PER_HERTZ = 74  # V/Hz
    HERTZ_PER_SECOND = 75  # Hz/s
    CHARACTER = 76  # char
    CHARACTERS_PER_SECOND = 77  # char/s
    KILOGRAM_SQUARE_METER = 78  # kgm²
    DECIBEL = 79  # dB


class Validity(Enum):
    """Enumerator with possible values for the validity of the data"""
    GOOD = 0
    QUESTIONABLE = 3
    INVALID = 1
    RESERVED = 2


class CtlModels(Enum):
    """Enumerator with possible values for the control models"""
    STATUS_ONLY = 0
    DIRECT_WITH_NORMAL_SECURITY = 1
    SBO_WITH_NORMAL_SECURITY = 2
    DIRECT_WITH_ENHANCED_SECURITY = 3
    SBO_WITH_ENHANCED_SECURITY = 4


class OrCategory(Enum):
    """Enumerator with possible values for the originator category"""
    NOT_SUPPORTED = 0
    BAY_CONTROL = 1
    STATION_CONTROL = 2
    REMOTE_CONTROL = 3
    AUTOMATIC_BAY = 4
    AUTOMATIC_STATION = 5
    AUTOMATIC_REMOTE = 6
    MAINTENANCE = 7
    PROCESS = 8


class InverterSwitchKind(Enum):
    """Enumerator with possible values for the switch type of an inverter"""
    FIELD_EFFECT_TRANSISTOR = 1
    INSULATED_GATE_BIPOLAR_TRANSISTOR = 2
    THYRISTOR = 3
    GATE_TURN_OFF_THYRISTOR = 4
    NOT_APPLICABLE_OR_NOT_KNOWN = 98


class InverterControlSource(Enum):
    """Enumerator with possible values for the control source of an inverter"""
    CURRENT_SOURCE_INVERTER = 1
    VOLTAGE_CONTROLLED_VOLTAGE_SOURCE_INVERTER = 2
    CURRENT_CONTROLLED_VOLTAGE_SOURCE_INVERTER = 3
    NOT_APPLICABLE_OR_NOT_KNOWN = 98


class SwitchType(Enum):
    """Enumerator for possible types of switches"""
    Load_Break = 1
    Disconnector = 2
    Earthing_Switch = 3
    High_Speed_Earthing_Switch = 4


class DERSyncStatus(Enum):
    """Enumerator for the status of the DER synchronization"""
    UNAVAILABLE_TO_CONNECT = 1
    NOT_SYNCHRONIZED_AVAILABLE_TO_CONNECT = 2
    IN_SYNCHRONIZATION_PROCESS = 3
    SYNCHRONIZED_AND_NOT_CONNECTED = 4
    SYNCHRONIZED_AND_CONNECTED = 5
    SYNCHRONIZATION_FAILURE = 6
    DISCONNECTING_FROM_GRID = 7
    NOT_APPLICABLE_OR_NOT_KNOWN = 98


class DEROperationalStatus(Enum):
    """Enumerator for the operational status of the DER"""
    ON_BUT_DISCONNECTED_AND_NOT_READY = 1
    STARTING_UP = 2
    DISCONNECTED_AND_AVAILABLE = 3
    DISCONNECTED_AND_AUTHORIZED = 4
    SYNCHRONIZING = 5
    RUNNING = 6
    STOPPING_AND_DISCONNECTING_UNDER_EMERGENCY_CONDITIONS = 7
    STOPPING = 8
    DISCONNECTED_AND_BLOCKED = 9
    DISCONNECTED_AND_IN_MAINTENANCE = 10
    FAILED = 11
    NOT_APPLICABLE_OR_NOT_KNOWN = 98


# Define the enumeration of PV assembly type
class PVAssemblyType(Enum):
    """Enumerator for the types of PV assemblies"""
    ARRAY = 1
    SUB_ARRAY = 2
    STRING = 3
    MODULE = 4
    PLANT = 5
    NOT_APPLICABLE_OR_NOT_KNOWN = 98


# Define the enumeration for ground connections of a PV plant
class PVGroundConnection(Enum):
    """Enumerator for the types of ground connections of a PV plant"""
    POSITIVE_GROUND = 1
    NEGATIVE_GROUND= 2
    NOT_GROUNDED = 3
    NOT_APPLICABLE_OR_NOT_KNOWN = 98


class PVModuleConfig(Enum):
    """Enumerator for the types of PV module configurations"""
    FLAT_PLATE = 1
    CONCENTRATING = 2
    NOT_APPLICABLE_OR_NOT_KNOWN = 98


class PVControlStateKind(Enum):
    """Enumerator for the types of control states of a PV plant"""
    NOT_READY = 1
    ASLEEP = 2
    AWAKING_UP = 3
    AWAKE = 4
    SHUTDOWN_SLEEP_TEST = 5
    UNDER_TEST = 6

class PVArrayControlModeKind(Enum):
    """Enumerator for the control modes of the PV controller"""
    MAXIMUM_POWER_POINT_TRACKING = 1
    POWER_LIMITER_CONTROLLER = 2
    DC_CURRENT_LIMIT = 3
    ARRAY_VOLTAGE_CONTROL = 4
    NOT_APPLICABLE_OR_NOT_KNOWN = 98

class Tcmd(Enum):
    """Enumartor for the command type of enumerated operate service"""
    STOP = 0
    LOWER = 1
    HIGHER = 2
    RESERVED = 3

class SetpointEndKind(Enum):
    """Enumerator for the end of the setpoint"""
    ENDED_NORMALLY = 1
    ENDED_WITH_OVERSHOOT = 2
    CANCELLED_MEASUREMENT_DEVIATING = 3
    CANCELLED_LOSS_OF_COMMUNICATION_WITH_DISPATCH_CENTRE = 4
    CANCELLED_LOSS_OF_COMMUNICATION_WITH_LOCAL_AREA_NETWORK = 5
    CANCELLED_LOSS_OF_COMMUNICATION_WITH_LOCAL_INTERFACE = 6
    CANCELLED_TIMEOUT = 7
    CANCELLED_VOLUNTARILY = 8
    CANCELLED_NOISY_ENVIRONMENTS = 9
    CANCELLED_MATERIAL_FAILURE = 10
    CANCELLED_NEW_SETPOINT_REQUEST = 11
    CANCELLED_IMPROPER_ENVIRONMENT = 12
    CANCELLED_STABILITY_TIME_REACHED = 13
    CANCELLED_IMMOBILISATION_TIME_REACHED = 14
    CANCELLED_EQUIPMENT_IN_WRONG_MONDE = 15
    UNKNOWN_CAUSES = 16

class AdjustmentKind(Enum):
    """Enumerator for the types of adjustments"""
    COMPLETED = 1
    CANCELLED = 2
    NEW_ADJUSTMENTS = 3
    UNDER_WAY = 4

class EVACConnectionState(Enum):
    """Enumerator for the connection states of the EVAC"""
    STATE_A = 1 # No vehicle connected
    STATE_B = 2 # Vehicle connected, not ready for energy flow
    STATE_C = 3 # Vehicle connected, ready for energy flow, ventilation not required
    STATE_D = 4 # Vehicle connected, ready for energy flow, ventilation required
    STATE_E = 5 # Vehicle connected, fault at charging spot
    STATE_F = 6 # Charging spot not available for action
    NOT_APPLICABLE_UNKNOWN = 98

class EVACPlugStateKind(Enum):
    """Enumerator for the plug states of the EVAC"""
    DISCONNECTED = 1
    CONNECTED_AND_UNLOCKED = 2
    CONNECTED_AND_LOCKED = 3
    CONNECTED = 4 # if there is no locking mechanism available
    NOT_APPLICABLE_OR_NOT_KNOWN = 98

class EVACCableCapabilityKind(Enum):
    """Enumerator for the cable capabilities of the EV"""
    THIRTEEN_A = 1 # 13 A per phase
    TWENTY_A = 2 # 20 A per phase
    THIRTYTWO_A = 3 # 32 A per phase
    SIXTY_THREE_SEVENTY_A = 4 # 63 A per phase or 70 A single phase

class Weekday(Enum):
    """Enumerator for the days of a week"""
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6
    SUNDAY = 7

class Month(Enum):
    """Enumerator for the months of a year"""
    JANUARY = 1
    FEBRUARY = 2
    MARCH = 3
    APRIL = 4
    MAY = 5
    JUNE = 6
    JULY = 7
    AUGUST = 8
    SEPTEMBER = 9
    OCTOBER = 10
    NOVEMBER = 11
    DECEMBER = 12

class Occurencetype(Enum):
    """Enumerator for the types of occurences"""
    TIME = 1
    WEEKDAY = 2
    WEEKOFYEAR = 3
    DAYOFMONTH = 4
    DAYOFYEAR = 98

class Occurenceperiod(Enum):
    """Enumerator for the periods of occurences"""
    HOUR = 1
    DAY = 2
    WEEK = 3
    MONTH = 4
    YEAR = 5

class EVChargingKind(Enum):
    """Enumeration for the kind of EV charging that is being done"""
    SINGLE_PHASE = 1
    THREE_PHASE = 2
    SYSTEM_A = 3 # System A DC charging
    SYSTEM_B = 4 # System B DC charging
    SYSTEM_C = 5 # System C DC charging
    NOT_APPLICABLE_OR_NOT_KNOWN = 98