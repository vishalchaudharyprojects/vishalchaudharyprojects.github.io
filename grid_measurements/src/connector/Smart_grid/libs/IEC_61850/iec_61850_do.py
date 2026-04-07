from grid_measurements.src.connector.Smart_grid.libs.IEC_61850.iec_61850_sdo import  *
from grid_measurements.src.connector.Smart_grid.libs.IEC_61850.iec_61850_da import *
import numpy as np

# Define the DataObject class (parent class of the data
# objects)
class DataObject:
    """
    Base class for a data object

    Attributes:
    name: Name of the data object
    do_type: Type of the data object (e.g., DT_MV, DT_BCR)
    description: Description of the data object
    value: Placeholder for the actual value
    SDO: Dictionary to hold sub-data objects

    Methods:
    add_subdata_object: Add a sub-data object to the dictionary with the given name
    """
    def __init__(self, name, do_type, description=None):
        self.name = name  # Name of the Data Object
        self.do_type = do_type  # Type of the Data Object (e.g., DT_MV, DT_BCR)
        self.description = description  # Description of the Data Object
        self.value = None  # Placeholder for the actual value
        self.SDO = {}  # Class-level dictionary for sub-data objects

    def add_subdata_object(self, name, subdata_object):
        self.SDO[name] = subdata_object


# class for device name plate
class DPL(DataObject):
    """Data Object for the device name plate"""
    def __init__(self):
        super().__init__(name="DPL", do_type="DT_DPL", description="Device Name Plate")
        self.add_subdata_object("vendor", str)  # vendor, manufacturer
        self.add_subdata_object("serNum", str)  # serial number
        self.add_subdata_object("model", str)  # Model
        self.add_subdata_object("location", str)  # Location of the device
        self.add_subdata_object("name", str)  # Name of the device
        self.add_subdata_object("owner", str)  # Location of the device


# class for the type of inverter switch
class ENGInverterSwitchKind(DataObject):
    """Data Object for  switch type of an inverter"""
    def __init__(self):
        super().__init__(name="ENG_INVERTER_SWITCH_TYPE",
                         do_type="DT_ENG_INVERTER_SWITCH_TYPE",
                         description="Switch type of an inverter")
        self.add_subdata_object("setVal", InverterSwitchKind)


# class for the kind of battery
class ENGBatteryTypeKind(DataObject):
    """Data object for the kind of battery storage system"""
    def __init__(self):
        super().__init__(name="ENG_BATTERY_TYPE_KIND",
                         do_type="DT_ENG_BATTERY_TYPE_KIND",
                         description="Kind of battery storage system")
        self.add_subdata_object("setVal", BatteryKind)
# class for the control source of the inverter
class ENGInverterControlSource(DataObject):
    """Data Object for the control source of an inverter"""
    def __init__(self):
        super().__init__(name="ENG_INVERTER_CONTROL_SOURCE",
                         do_type="DT_ENG_INVERTER_CONTROL_SOURCE",
                         description="Control source of an inverter")
        self.add_subdata_object("setVal", InverterControlSource)


# Measured Values class
class MV(DataObject, AnalogueValue, Quality, TimeStamp, Units):
    """Data Object for measured values"""
    def __init__(self):
        super().__init__(name="MV",do_type = "DT_MV", description="Measured Value")
        self.add_subdata_object("mag", AnalogueValue()) # Magnitude (float) #müssten doch eigentlich statische Methoden sein, die man nicht initialisieren kann!?!?! Nachforschen, mag darf ja nie initialisiert werden, sondern muss eine abstrakte Klasse sein.
        self.add_subdata_object("q", Quality()) # Quality
        self.add_subdata_object("t", TimeStamp()) # Timestamp
        self.add_subdata_object("units", Units()) # Units


# Complex measured values
class CMV(DataObject, ComplexValue, Quality, TimeStamp, Units):
    """Data Object for complex measured values"""
    def __init__(self):
        super().__init__(name="CMV",do_type = "DT_CMV", description="Complex Measured Value")
        self.add_subdata_object("cVal", ComplexValue()) # Magnitude (float) #müssten doch eigentlich statische Methoden sein, die man nicht initialisieren kann!?!?! Nachforschen, mag darf ja nie initialisiert werden, sondern muss eine abstrakte Klasse sein.
        self.add_subdata_object("q", Quality()) # Quality
        self.add_subdata_object("t", TimeStamp()) # Timestamp
        self.add_subdata_object("units", Units()) # Units


class APC(DataObject, AnalogueValue, Quality, TimeStamp, Units):
    """Data object for controllable analogue process values"""
    def __init__(self):
        super().__init__(name="APC", do_type="DT_APC", description="Analogue Process Value Control")
        self.add_subdata_object("mxVal", AnalogueValue())
        self.add_subdata_object("q", Quality())
        self.add_subdata_object("t", TimeStamp())
        self.add_subdata_object("ctlModel",CtlModels)
        self.add_subdata_object("minVal",AnalogueValue())
        self.add_subdata_object("maxVal",AnalogueValue())
        # Services wie Operate, etc. müssen voraussichtlich aus der Lib IEC 61850
        # umgesetzt werden
        self.add_subdata_object("Oper", OperAnalogueValue())


# Three phase measured values
class WYE(DataObject):
    """Data Object for phase to neutral/ground measurements in a three-phase system"""
    def __init__(self):
        super().__init__(name="WYE", do_type="DT_WYE", description="Three phase measured values to neutral/ground")
        self.add_subdata_object("phsA", CMV()) # complex measured value for phase A
        self.add_subdata_object("phsB", CMV()) # complex measured value for phase B
        self.add_subdata_object("phsC", CMV()) # complex measured value for phase C


# Single point status
class SPS(DataObject, Quality, TimeStamp):
    """Data Object for singple point status"""
    def __init__(self):
        super().__init__(name="SPS", do_type="DT_SPS", description="Single point status")
        self.add_subdata_object("stVal", AnalogueValue())  # Status value (boolean)
        self.add_subdata_object("q", Quality())  # Quality
        self.add_subdata_object("t",TimeStamp())


# Analogue Setting
class ASG(DataObject, AnalogueValue, Units):
    """Data Object for analogue settings"""
    def __init__(self):
        super().__init__(name="ASG", do_type="DT_ASG", description="Analogue Setting")
        self.add_subdata_object("setMag", AnalogueValue())  # Magnitude (float)
        self.add_subdata_object("units",Units())


# Integer Status
class INS(DataObject, Quality, TimeStamp):
    """Data Object for integer status"""
    def __init__(self):
        super().__init__(name="INS", do_type="DT_INS", description="Integer Status")
        self.add_subdata_object("stVal", int)  # Status value (integer)
        self.add_subdata_object("q", Quality())  # Quality
        self.add_subdata_object("t", TimeStamp())


# Binary Counter Reading
class BCR(DataObject, AnalogueValue, TimeStamp, Quality):
    """Data Object for binary counter readings"""
    def __init__(self):
        super().__init__(name="BCR", do_type="DT_BCR", description="Binary Counter Reading")
        self.add_subdata_object("stVal", int)  # Value (integer)
        self.add_subdata_object("t", TimeStamp())  # Timestamp
        self.add_subdata_object("q", Quality())  # Quality


# Controllable Single Point
class SPC(DataObject, Quality, TimeStamp):
    """Data Object for controllable single point"""
    def __init__(self):
        super().__init__(name="SPC", do_type="DT_SPC", description="Single Point Control")
        self.add_subdata_object("stVal", bool)
        self.add_subdata_object("q", Quality())
        self.add_subdata_object("t", TimeStamp())
        self.add_subdata_object("Oper", OperBoolean())
        self.add_subdata_object("ctlModel", CtlModels)


# Enumerated status for the results of equipment test procedure
class ENSEquipmentTestResultKind(DataObject):
    """Data Object for the results of equipment test procedure"""
    def __init__(self):
        """Data object for the results of equipment test procedure"""
        super().__init__(name="ENS_EQUIPMENT_TEST_RESULT_KIND", do_type="DT_ENS_EQUIPMENT_TEST_RESULT_KIND",
                         description="Results of equipment test procedure")
        self.add_subdata_object("stVal", EquipmentTestResultKind)
        self.add_subdata_object("q", Quality())
        self.add_subdata_object("t", TimeStamp())

# Enumerated Status for switch types
class ENSSwitchType(DataObject):
    def __init__(self):
        """Data Object for switch type"""
        super().__init__(name="ENS_SWITCH_TYPE", do_type="DT_ENS_SwTyp",
                         description="Switch type")
        self.add_subdata_object("stVal", SwitchType)
        self.add_subdata_object("q", Quality())
        self.add_subdata_object("t", TimeStamp())

# states that a DER may be in
class ENSDERStateKind(DataObject):
    def __init__(self):
        """ Data Object for DER states"""
        super().__init__(name="ENS_DER_STATE_KIND", do_type="DT_ENS_DER_STATE_KIND",
                         description="DER states")
        self.add_subdata_object("stVal", DERStateKind)
        self.add_subdata_object("q", Quality())
        self.add_subdata_object("t", TimeStamp())

# Enumerated status for test results of a battery
class ENSBatteryTestResultKind(DataObject):
    def __init__(self):
        """Data object for test results of a battery storage system test"""
        super().__init__(name="ENS_BATTERY_TEST_RESULT_KIND", do_type="DT_ENS_BATTERY_TEST_RESULT_KIND",
                         description="Test results of a battery storage system test")
        self.add_subdata_object("stVal", BatteryTestResultKind)
        self.add_subdata_object("q", Quality())
        self.add_subdata_object("t", TimeStamp())

# Enumerated DER Synchronization Status
class ENSDERSyncStatus(DataObject):
    """Data Object for DER synchronization status"""
    def __init__(self):
        super().__init__(name="ENS_SYNC_STATUS", do_type="DT_ENS_SYNC_STATUS",
                         description="DER synchronization status")
        self.add_subdata_object("stVal", DERSyncStatus)
        self.add_subdata_object("q", Quality())
        self.add_subdata_object("t", TimeStamp())


# Enumerated DER operational status
class ENSDEROperationalStatus(DataObject):
    def __init__(self):
        """Data Object for DER operational status"""
        super().__init__(name="ENS_OPER_STATUS", do_type="DT_ENS_OPER_STATUS",
                         description="DER operational status")
        self.add_subdata_object("stVal", DEROperationalStatus)
        self.add_subdata_object("q", Quality())
        self.add_subdata_object("t", TimeStamp())


# Enumerated FSPT Setpoint End Kind
class ENSSetpointEndKind(DataObject):
    """Data Object for the kind of setpoint end"""
    def __init__(self):
        super().__init__(name="ENS_SETPOINT_END_KIND", do_type="DT_ENS_SETPOINT_END_KIND",
                         description="Kind of setpoint end")
        self.add_subdata_object("stVal", SetpointEndKind)
        self.add_subdata_object("q", Quality())
        self.add_subdata_object("t", TimeStamp())


# Enumerated FSPT Adjustmentkind, meaning is the setpoint currently being adjusted
class ENSAdjustmentKind(DataObject):
    """Data Object for the kind of adjustment"""
    def __init__(self):
        super().__init__(name="ENS_ADJUSTMENT_KIND", do_type="DT_ENS_ADJUSTMENT_KIND",
                         description="Kind of adjustment")
        self.add_subdata_object("stVal", AdjustmentKind)
        self.add_subdata_object("q", Quality())
        self.add_subdata_object("t", TimeStamp())

# Enumerated EV Connection State
class ENSEVACConnectionState(DataObject):
    """Data Object for the connection state of an electric vehicle"""
    def __init__(self):
        super().__init__(name="ENS_EVAC_CONNECTION_STATE", do_type="DT_ENS_EVAC_CONNECTION_STATE",
                         description="Connection state of an electric vehicle")
        self.add_subdata_object("stVal", EVACConnectionState)
        self.add_subdata_object("q", Quality())
        self.add_subdata_object("t", TimeStamp())

# Enumerated EV plug state (is the plug connected to the charging station)
class ENSEVACPlugStateKind(DataObject):
    """Data Object for the plug state of an EV at the charging station"""
    def __init__(self):
        super().__init__(name="ENS_EVAC_PLUG_STATE_KIND", do_type="DT_ENS_EVAC_PLUG_STATE_KIND",
                         description="Plug state of an EV at the charging station")
        self.add_subdata_object("stVal", EVACPlugStateKind)
        self.add_subdata_object("q", Quality())
        self.add_subdata_object("t", TimeStamp())

# Enumeration for the current carrying capability of the cable
class ENSEVACCableCapabilityKind(DataObject):
    """Data Object for the current carrying capability of the cable"""
    def __init__(self):
        super().__init__(name="ENS_EVAC_CABLE_CAPABILITY_KIND", do_type="DT_ENS_EVAC_CABLE_CAPABILITY_KIND",
                         description="Current carrying capability of the cable")
        self.add_subdata_object("stVal", EVACCableCapabilityKind)
        self.add_subdata_object("q", Quality())
        self.add_subdata_object("t", TimeStamp())

# Enumeration for the kind of EV charging
class ENSEVConnectionChargingKind(DataObject):
    """Data Object for the EV Connection States"""
    def __init__(self):
        super().__init__(name="ENS_EV_CHARGING_KIND", do_type="DT_ENS_EV_CHARGING_KIND",
                         description="EV Connection States")
        self.add_subdata_object("stVal", EVChargingKind)
        self.add_subdata_object("q", Quality())
        self.add_subdata_object("t", TimeStamp())


# Object reference setting
class ORG(DataObject):
    """Data Object for object reference settings"""
    def __init__(self):
        super().__init__(name="ORG", do_type="DT_ORG", description="Object Reference Setting")
        self.add_subdata_object("setSrcRef", str)
        # Todo: Am FNN Beispiel prüfen, welcher primäre Datentyp hinter ObjRef steckt
        #  und wie ich das modellieren kann
        self.add_subdata_object("setTstRef", str)
        self.add_subdata_object("setSrcCB", str)
        self.add_subdata_object("setTstCB", str)
        self.add_subdata_object("intAddr", str)


# Integer Status Setting
class ING(DataObject):
    """Data Object for integer status settings"""
    def __init__(self):
        super().__init__(name="ING", do_type="DT_ING", description="Integer Status Setting")
        self.add_subdata_object("setVal", int)
        self.add_subdata_object("q", Quality())
        self.add_subdata_object("t", TimeStamp())


# Enumerated Status Setting for pv Assembly type
class ENGPVAssemblyType(DataObject):
    """Data Object for  the assembly type of a PV panel """
    def __init__(self):
        super().__init__(name="ENG_PV_ASSEMBLY_TYPE",
                         do_type="DT_ENG_PV_ASSEMBLY_TYPE",
                         description="Assembly type of a PV panel")
        self.add_subdata_object("setVal", PVAssemblyType)


# Enumerated status setting for charging source kind, i.e.
# it's interaction with the grid
class ENGChargeSourceKind(DataObject):
    """Data Object for the charge source kind"""
    def __init__(self):
        super().__init__(name="ENG_CHARGE_SOURCE_KIND",
                         do_type="DT_ENG_CHARGE_SOURCE_KIND",
                         description="Charge source kind")
        self.add_subdata_object("setVal", ChargeSourceKind)
        self.add_subdata_object("q", Quality())
        self.add_subdata_object("t", TimeStamp())


# Enumerated Status Setting for ground connection of a PV plant
class ENGGndConn(DataObject):
    """Data Object for the ground connection of a PV plant"""
    def __init__(self):
        super().__init__(name="ENG_GND_CONN",
                         do_type="DT_ENG_GND_CONN",
                         description="Ground connection of a PV plant")
        self.add_subdata_object("setVal", PVGroundConnection)


# Enumerated Status Setting for the Configuration of a PV module
class ENGPVModuleConfig(DataObject):
    """Data Object for the configuration of a PV module"""
    def __init__(self):
        super().__init__(name="ENG_PV_MODULE_CONFIG",
                         do_type="DT_ENG_PV_MODULE_CONFIG",
                         description="Configuration of a PV module")
        self.add_subdata_object("setVal", PVModuleConfig)

# Shape of a curve
class CSG(DataObject):
    """Data Object for the shape of a curve"""
    def __init__(self):
        super().__init__(name="CSG", do_type="DT_CSG", description="Shape of a curve")
        self.add_subdata_object("pointZ", float)
        self.add_subdata_object("numPts", int)
        self.add_subdata_object("crvPts", np.array())
        self.add_subdata_object("xUnits", Units())
        self.add_subdata_object("yUnits", Units())
        self.add_subdata_object("zUnits", Units())
        self.add_subdata_object("maxPts", int)


# Enumerated Status for the control of a PV array
class ENSPVControlStateKind(DataObject):
    """Data Object for the control state of a PV array"""
    def __init__(self):
        super().__init__(name="ENS_PV_CONTROL_STATE_KIND", do_type="DT_ENS_PV_CONTROL_STATE_KIND", description="Control state of a PV array")
        self.add_subdata_object("stVal", PVControlStateKind)
        self.add_subdata_object("q", Quality())
        self.add_subdata_object("t", TimeStamp())


# Controllable enumerated status
class ENCPVArrayControlModeKind(DataObject):
    """possible modes of controling the power output of the PV array"""
    def __init__(self):
        super().__init__(name="ENC_PV_ARRAY_CONTROL_MODE_KIND", do_type="DT_ENC_PV_ARRAY_CONTROL_MODE_KIND", description="Control mode of a PV array")
        self.add_subdata_object("setVal", PVArrayControlModeKind)
        self.add_subdata_object("q", Quality())
        self.add_subdata_object("t", TimeStamp())
        self.add_subdata_object("ctlModel", CtlModels)


# Different states that a DER may be in
class ENCDERStateTransitionKind(DataObject):
    """Data Object for the states of a DER"""
    def __init__(self):
        super().__init__(name="ENC_DER_STATE_TRANSITION_KIND",
                         do_type="DT_ENC_DER_STATE_KIND",
                         description="States of a DER and how they can transition")
        self.add_subdata_object("setVal", DERStateKindTransition)
        self.add_subdata_object("q", Quality())
        self.add_subdata_object("t", TimeStamp())
        self.add_subdata_object("ctlModel", CtlModels)

# Binary controlled analogue process value
class BAC(DataObject):
    """Data Object for binary controlled analogue process value"""
    def __init__(self):
        super().__init__(name="BAC", do_type="DT_BAC", description="Binary Controlled Analogue Process Value")
        self.add_subdata_object("mxVal", AnalogueValue())
        self.add_subdata_object("q", Quality())
        self.add_subdata_object("t", TimeStamp())
        self.add_subdata_object("ctlModel", CtlModels)
        self.add_subdata_object("Oper", OperCodedEnum())


# Single point setting group
class SPG(DataObject):
    """Data object for single point settings"""
    def __init__(self):
        super().__init__(name="SPG", do_type="DT_SPG", description="Single Point Setting")
        self.add_subdata_object("setVal", bool)


# Visible string setting group
class VSG(DataObject):
    """Data object for visible string settings"""
    def __init__(self):
        super().__init__(name="VSG", do_type="DT_VSG", description="Visible String Setting")
        self.add_subdata_object("setVal", str)


# Logical Node Nameplate
class LPL(DataObject):
    """Data Object for the logical node nameplate"""
    def __init__(self):
        super().__init__(name="LPL", do_type="DT_LPL", description="Logical Node Nameplate")
        self.add_subdata_object("vendor", str)  # vendor, manufacturer
        self.add_subdata_object("swRev", str)


# Time setting group
class TSG(DataObject):
    """Data object for time settings"""
    def __init__(self):
        super().__init__(name="TSG", do_type="DT_TSG", description="Time Setting")
        self.add_subdata_object("setTm", TimeStamp())
        self.add_subdata_object("setCal", CalendarTime())
