from grid_measurements.libs.ie3_iec_61850_lib.iec_61850_do import *  # Import all data objects

# Define the base LogicalNode class (parent class of the logical nodes)
class LogicalNode:
    """
    Base class for a logical node

    Attributes:
    ln_id: Logical Node ID
    ln_class: Logical Node Class (e.g., MMXU, MMTR)
    description: Description of the logical node
    DO: Dictionary to hold data objects (DOs)

    Methods:
    add_data_object: Add a data object to the dictionary with the given name
    """
    def __init__(self, ln_id, ln_class, description=None):
        self.ln_id = ln_id  # Logical Node ID
        self.ln_class = ln_class  # Logical Node Class (e.g., MMXU, MMTR)
        self.description = description  # Description of the Logical Node
        self.DO = {}  # Dictionary to hold data objects (DOs)

    def add_data_object(self, name, data_object):
        self.DO[name] = data_object

# logical node MMXU class
class MMXU(LogicalNode):
    """Logical Node for three phase electrical measurements"""
    def __init__(self):
        super().__init__(ln_id="DT_MMXU", ln_class="MMXU",
                         description="Measurement logical node for electrical metering and monitoring")
        # Measured and metered values
        self.add_data_object("TotW", MV())
        self.add_data_object("TotVAr", MV())
        self.add_data_object("TotVA", MV())
        self.add_data_object("TotPF", MV())
        self.add_data_object("Hz", MV())
        self.add_data_object("PhV", WYE())
        self.add_data_object("A",WYE())
        self.add_data_object("VAr", WYE())
        self.add_data_object("VA", WYE())
        self.add_data_object("PF", WYE())
        self.add_data_object("W", WYE())

class TCTR(LogicalNode):
    """Logical Node for current transformer"""
    def __init__(self):
        super().__init__(ln_id="DT_TCTR", ln_class="TCTR",
                         description="Current Transformer")
        self.add_data_object("ARtg", ASG())
        self.add_data_object("HzRtg",ASG())
        self.add_data_object("Rat",ASG())


class STMP(LogicalNode):
    """Logical Node for temperature supervision"""
    def __init__(self):
        super().__init__(ln_id="DT_STMP", ln_class="STMP",
                         description="Temperature supervision")
        self.add_data_object("Alm", SPS())
        self.add_data_object("RteAlm", SPS())
        self.add_data_object("Trip", SPS())
        self.add_data_object("RteTrip", SPS())
        self.add_data_object("Tmp", MV())
        self.add_data_object("TmpRte", MV())
        self.add_data_object("AlmSet", ASG())
        self.add_data_object("RteAlmSet", ASG())
        self.add_data_object("TripSet", ASG())
        self.add_data_object("RteTripSet", ASG())


class DINV(LogicalNode):
    """Logical Node for the characteristics of an inverter"""
    def __init__(self):
        super().__init__(ln_id="DT_DINV", ln_class="DINV",
                         description="Inverter characteristics")
        # Inverter Nameplate
        self.add_data_object("EEName",DPL())
        # Loss of AC power
        self.add_data_object("InvACLosAlm",SPS())
        # Loss of DC power
        self.add_data_object("InvDCLosAlm",SPS())
        # Loss of grid power
        self.add_data_object("InvGriLosAlm",SPS())
        # Inverter contactor switch open or closed
        self.add_data_object("InvSwAlm",SPS())
        # Inverter stand-by status
        self.add_data_object("Stdby",SPS())
        # Inverter DC current level sufficient for operation
        self.add_data_object("CurLev",SPS())
        # Inverter DC power of modules is connected to the rest of the systems
        self.add_data_object("DCPwrSt",SPS())
        # Inverter DC voltage setpoint
        self.add_data_object("DCVSpt", APC())
        # Active power setpoint
        self.add_data_object("WSpt", APC())
        # Reactive power setpoint
        self.add_data_object("VARSpt", APC())
        # Type of inverter switch
        self.add_data_object("InvSwTyp", ENGInverterSwitchKind())
        # Inverter control source
        self.add_data_object("InvCtlSrc", ENGInverterControlSource())
        # Inverter P and S ratings
        self.add_data_object("WRtg", ASG())
        self.add_data_object("VARtg", ASG())
        # Switching frequency
        self.add_data_object("SwHz", ASG())
        # input current and voltage limits
        self.add_data_object("InAMax",ASG())
        self.add_data_object("InVMax",ASG())
        # rated bidirectional reactive power and voltage
        self.add_data_object("VArRtg",ASG())
        self.add_data_object("VRtg",ASG())


class MMTR(LogicalNode):
    """Logical Node for metering"""
    def __init__(self):
        super().__init__(ln_id="DT_MMTR", ln_class="MMTR",
                         description="Metering logical node")
        # Meter nameplate
        self.add_data_object("EEName", DPL())
        # Net apparent energy since last reset
        self.add_data_object("TotVAh", BCR())
        # Net real energy since last reset
        self.add_data_object("TotWh", BCR())
        # Net reactive energy since last reset
        self.add_data_object("TotVArh", BCR())
        # Real energy supply
        self.add_data_object("SupWh", BCR())
        # Reactive energy supply
        self.add_data_object("SupVArh", BCR())
        # Real energy demand
        self.add_data_object("DmdWh",BCR())
        # Reactive energy demand
        self.add_data_object("DmdVArh", BCR())


class XSWI(LogicalNode):
    """Logical Node for switchgear"""
    def __init__(self):
        super().__init__(ln_id="DT_XSWI", ln_class="XSWI",
                         description="Switchgear")
        # Switchgear nameplate
        self.add_data_object("EEName", DPL())
        # control behaviour at this level is allowed if true
        self.add_data_object("Loc", SPS())
        # Count of operations
        self.add_data_object("OpCnt", INS())
        #  Type of the switch
        self.add_data_object("SwTyp", ENSSwitchType())
        # Circuit breaker/switch position
        self.add_data_object("Pos", SPC())
        # If true, "opening" the switch has been blocked
        self.add_data_object("BlkOpn", SPC())
        # if true, "closing" the switch has been blocked
        self.add_data_object("BlkCls", SPC())


class MMET(LogicalNode):
    """Logical Node for meteorological information"""
    def __init__(self):
        super().__init__(ln_id="DT_MMET", ln_class="MMET",
                         description="Meteorological information")
        # Meteorological information nameplate
        self.add_data_object("EEName", DPL())
        # Ambient temperature
        self.add_data_object("EnvTmp", MV())
        # Wet bulb temperature
        self.add_data_object("WetBlbTmp", MV())
        # Cloud cover level
        self.add_data_object("CloudCvr", MV())
        # Humidity
        self.add_data_object("EnvHum", MV())
        # Dew point
        self.add_data_object("DewPt", MV())
        # Diffuse insolation
        self.add_data_object("DffInsol", MV())
        # Direct normal insolation
        self.add_data_object("DctInsol", MV())
        # Daylight duration (time elapsed between sunrise and sunset)
        self.add_data_object("DlDur", MV())
        # Total horizontal insolation
        self.add_data_object("HorInsol", MV())
        # Horizontal wind direction
        self.add_data_object("HorWdDir", MV())
        # Horizontal wind speed
        self.add_data_object("HorWdSpd", MV())
        # Vertical wind direction
        self.add_data_object("VerWdDir", MV())
        # Vertical wind speed
        self.add_data_object("VerWdSpd", MV())
        # Wind gust speed
        self.add_data_object("WdGustSpd", MV())
        # Barometric pressure
        self.add_data_object("EnvPres", MV())
        # Rainfall
        self.add_data_object("RnFll", MV())


class MMDC(LogicalNode):
    """Logical Node for DC measurements"""
    def __init__(self):
        super().__init__(ln_id="DT_MMDC", ln_class="MMDC",
                         description="DC measurements")
        # DC measurements device nameplate
        self.add_data_object("EEName", DPL())
        # DC power
        self.add_data_object("Watt", MV())
        # DC current
        self.add_data_object("Amp", MV())
        # DC voltage
        self.add_data_object("Volt", MV())
        # DC voltage between positive pole and earth
        self.add_data_object("VoltPsGnd", MV())
        # DC voltage between negative pole and earth
        self.add_data_object("VoltNgGnd", MV())
        # DC resistance
        self.add_data_object("Ris", MV())
        # DC resistance between positive pole and earth
        self.add_data_object("RisPsGnd", MV())
        # DC resistance between negative pole and earth
        self.add_data_object("RisNgGnd", MV())


class DGEN(LogicalNode):
    """General class for DER generators"""
    def __init__(self):
        super().__init__(ln_id="DT_DGEN", ln_class="DGEN",
                         description="DER generating unit")
        # DER generator nameplate
        self.add_data_object("EEName", DPL())
        # Synchronization status of the DER generator
        self.add_data_object("GnSynSt", ENSDERSyncStatus())
        # Current state of DER operation
        self.add_data_object("DEROpSt", ENSDEROperationalStatus())
        # Maximum power the DER could output
        self.add_data_object("CnStWMax", MV())
        # Total energy generated
        self.add_data_object("GnEnTot", MV())
        # Energy generated since last reset
        self.add_data_object("GnEnPer", MV())
        # Percentage of active power from Renewable Energy Sources (RES)
        self.add_data_object("RenWPct", MV())
        # Percentage of reactive power from RES
        self.add_data_object("RenVArPct", MV())
        # Total amount of reactive power without impacting active power
        self.add_data_object("VArTot", MV())
        # Total amount of absorbable reactive power without impacting active power
        self.add_data_object("AVarTot", MV())
        # Total amount of reactive power that can be supplied without impacting active power
        self.add_data_object("IVarTot", MV())
        # Actual percentage of apparent power output bsaed on VAMax
        self.add_data_object("VAPct", MV())
        # Available capacity for increasing active power output
        self.add_data_object("AvlUpW", MV())
        # Available capacity for decreasing active power output
        self.add_data_object("AvlDnW", MV())
        # Active power setpoint
        self.add_data_object("WSpt", APC())
        # Reactive power setpoint
        self.add_data_object("VArSpt", APC())
        # Reference to the DER Unit LN associated to this generic model LN
        self.add_data_object("DERUnit", ORG())
        # nameplate maxiumum power generation
        self.add_data_object("WMaxRtg", ASG())
        # nameplate maximum apparent power generation
        self.add_data_object("VAMaxRtg", ASG())
        # nameplate maximum reactive power generation
        self.add_data_object("VArMaxRtg", ASG())
        # nameplate maximum absorbable reactive power
        self.add_data_object("AvarMaxRtg", ASG())
        # nameplate maximum injectable reactive power
        self.add_data_object("IvarMaxRtg", ASG())
        # Maximum current rating under nominal voltage and power factor
        self.add_data_object("AMaxRtg", ASG())
        # Maximum voltage rating
        self.add_data_object("VMaxRtg", ASG())
        # minimum voltage rating
        self.add_data_object("VMinRtg", ASG())
        # Minimum continuous active power generation rating
        self.add_data_object("ConsWMinRtg", ASG())
        # Maximum continuous active power generation rating
        self.add_data_object("ConsWMaxRtg", ASG())
        # Maximum generation active power ramp up rating
        self.add_data_object("WRpuMaxRtg", ASG())
        # Maximum generation active power ramp down rating
        self.add_data_object("WRpdMaxRtg", ASG())
        # Setting for maximum active power
        self.add_data_object("WMax", ASG())
        # Default ramp rate for active power, % of Wmax/s
        self.add_data_object("WRmp", ASG())
        # Setting for maximum reactive power
        self.add_data_object("VArMax", ASG())
        # Setting for maximum absorbable reactive power
        self.add_data_object("AvarMax", ASG())
        # Setting for maximum injectable reactive power
        self.add_data_object("IvarMax", ASG())
        # Setting for maxiumum voltage operational rating
        self.add_data_object("VMax", ASG())
        # Setting for minimum voltage operational rating
        self.add_data_object("VMin", ASG())
        # Setting for maximum operational current rating under nominal voltage and
        # power factor
        self.add_data_object("AMax", ASG())
        # Setting for maximum apparent power while generating
        self.add_data_object("VAMax", ASG())
        # Setting for maximum absorbable apparent power
        self.add_data_object("AvaMax", ASG())
        # Setting for maximum injectable apparent power
        self.add_data_object("IvaMax", ASG())


class DPVA(LogicalNode):
    """Photovoltaic array characteristics"""
    def __init__(self):
        super().__init__(ln_id="DT_DPVA", ln_class="DPVA",
                         description="Photovoltaic array characteristics")
        # PV Array nameplate
        self.add_data_object("EEName", DPL())
        # PV Assembly type
        self.add_data_object("AssType", ENGPVAssemblyType())
        # Type of ground connection
        self.add_data_object("GndConn", ENGGndConn())
        # number of modules per string
        self.add_data_object("MdulCnt", ING())
        # Number of parallel strings per subarray
        self.add_data_object("SubArrCnt", ING())
        # Number of parallel sub-arrays per array
        self.add_data_object("SubArrCnt", ING())
        # Array area
        self.add_data_object("ArrArea", ASG())
        # Array power rating
        self.add_data_object("ArrWRtg", ASG())
        # Assembly fixed tilt - degrees from horizontal
        self.add_data_object("Tilt", ASG())
        # Assembly Azimuth - degrees from true north
        self.add_data_object("Azi", ASG())


class DPVM(LogicalNode):
    """Photovoltaic module characteristics"""
    def __init__(self):
        super().__init__(ln_id="DT_DPVM", ln_class="DPVM",
                         description="Photovoltaic module characteristics")
        # nameplate of the PV module
        self.add_data_object("EEName", DPL())
        # Index into active operational point of the I-V curve
        self.add_data_object("AVCrv", INS())
        # PV module configuration type
        self.add_data_object("ModCfgTyp", ENGPVModuleConfig())
        # I-V-curve of the module at STC
        self.add_data_object("MdulAVCrv", CSG())
        # Module rated power in Wp at STC
        self.add_data_object("MdulWRtg", ASG())
        # Module rated power in Wp at 200 W/m^2
        self.add_data_object("MdulW200Rtg", ASG())
        # Module voltage at MPP in STC
        self.add_data_object("MaxMdulV", ASG())
        # Module current at MPP in stc
        self.add_data_object("MaxMdulA", ASG())
        # Module open circuit voltage at STC
        self.add_data_object("MdulOpnCctV", ASG())
        # Module short circuit current at STC
        self.add_data_object("MdulSrtCctA", ASG())
        # Module power/temperature derate as percent of degrees above 25°C
        self.add_data_object("MdulWTmpDrt", ASG())
        # Module current/temperaure derate as percent of degrees above 25°C
        self.add_data_object("MdulATmpDrt", ASG())
        # Module voltage/temperature derate as percent of degrees above 25°C
        self.add_data_object("MdulVTmpDrt", ASG())
        # Module age derate as percent over time
        self.add_data_object("MdulAgeDrtPct", ASG())


class DPVC(LogicalNode):
    """Photovoltaic Array Monitoring and Controller"""
    def __init__(self):
        super().__init__(ln_id="DT_DPVC", ln_class="DPVC",
                         description="Photovoltaic Array Monitoring and Control")
        # nameplate of the PV array controller
        self.add_data_object("EEName", DPL())
        # Array control mode status
        self.add_data_object("PVCtlSt", ENSPVControlStateKind())
        # Control of the poewr output of the array
        self.add_data_object("ArrModCtl", ENCPVArrayControlModeKind())
        # Peak power tracker reference voltage (Kennlinienverfahren?)
        self.add_data_object("PVCtlSt", ASG())
        # Power Tracker update rate (MPP)
        self.add_data_object("TrkRte", ING())
        # Voltage perturbation step of power tracker (MPP)
        self.add_data_object("TrkVStep", ASG())


class FSPT(LogicalNode):
    """Generic setpoint control function"""
    def __init__(self):
        super().__init__(ln_id="DT_FSPT", ln_class="FSPT",
                         description="Generic setpoint control function")
        # Deviation alarm trigger status
        self.add_data_object("SptDvAlm", SPS())
        # Setpoint is raising as feedback from external device
        self.add_data_object("SptUp", SPS())
        # Setpoint is lowering as feedback from external device
        self.add_data_object("SptDn", SPS())
        # Setpoint is incrementing when true, otherwise decrementing
        self.add_data_object("DptDir", SPS())
        # Status of setpoint ending
        self.add_data_object("SptEndSt", ENSSetpointEndKind())
        # Status of adjustment process
        self.add_data_object("AdjSt", ENSAdjustmentKind())
        # Local control behaviour
        self.add_data_object("Loc", SPS())
        # Analogue output of this function
        self.add_data_object("Out", MV())
        # Setpoint value mainatined in memory
        self.add_data_object("SptMem", MV())
        # Operate the setpoint adjustment in a given direction
        self.add_data_object("SptChg", BAC())
        # Controllable value of a setpoint
        self.add_data_object("SptVal", APC())
        # Automatic operation
        self.add_data_object("Auto", SPC())
        # Maximum restriction
        self.add_data_object("MaxRst", ASG())
        # Minimum restriction
        self.add_data_object("MinRst", ASG())
        # Setpoint deviation at which the alarm trigger status should be active
        self.add_data_object("DvAlm", ASG())


class DESE(LogicalNode):
    """Charging Station (EV Supply Equipment) Logical Node"""
    def __init__(self):
        super().__init__(ln_id="DT_DESE", ln_class="DESE",
                         description="EV supply equipment logical node")
        # EVSE nameplate
        self.add_data_object("EVSENam", DPL())
        # Isolation test fault was executed before charging failed
        self.add_data_object("IsoTestFlt", SPS())
        # Short circuit test fault was executed before charging failed
        self.add_data_object("ScTestFlt", SPS())
        # Detection of loss of digital communication
        self.add_data_object("DigCommLos", SPS())
        # Detection of welding condition
        self.add_data_object("WldDet", SPS())
        # Measured charging voltage
        self.add_data_object("ChaV", MV())
        # Measured charging current
        self.add_data_object("ChaA", MV())
        # EV supply equipment ID as per ISO 15118:2014
        self.add_data_object("EVSEId", VSG())
        # Rated maximum charging power of the EVSE
        self.add_data_object("ChaPwrRtg", ASG())
        # Power that the EVSE requires from the grid
        self.add_data_object("ChaPwrTgt", ASG())
        # Power that the grid limits the charger to
        self.add_data_object("ChaPwrLim", ASG())
        # Is DC charging supported (yes means true)
        self.add_data_object("ConntypDC", SPG())
        # Is AC charging supported with n phases
        self.add_data_object("ConntypPhs", SPG())
        # Reference to the logical nodes representing the AC charging connections
        self.add_data_object("ConnACRef", ORG())
        # Reference to the logical nodes representing the DC charging connections
        self.add_data_object("ConnDCRef", ORG())


class DEAO(LogicalNode):
    """E-Mobility AC charging outlet (cable)"""
    def __init__(self):
        super().__init__(ln_id="DT_DEAO", ln_class="DEAO",
                         description="E-Mobility AC charging outlet (cable)")
        # EV charging outlet nameplate
        self.add_data_object("NamPlt", LPL())
        # Connection state according to IEC 61851-1
        self.add_data_object("ConnSt", ENSEVACConnectionState())
        # Charging plug present and locked according to IEC 61851-1
        self.add_data_object("PlgStAC", ENSEVACPlugStateKind())
        # Capability of the EV cable according to IEC 61851-1
        self.add_data_object("CabRtgAC", ENSEVACCableCapabilityKind())
        # Maximum AC charging current of the outlet
        self.add_data_object("ChaARtg", ING())
        # enable digital communication with the EV
        self.add_data_object("DigComm", SPG())
        # Available AC current to signal the ev when not using digital communication
        self.add_data_object("ChaAMax", ING())
        # Reference to the logical node instance containing information about the
        # connected EV
        self.add_data_object("EVRef", ORG())


class DEEV(LogicalNode):
    """E-Mobility EV logical node"""
    def __init__(self):
        super().__init__(ln_id="DT_DEEV", ln_class="DEEV",
                            description="E-Mobility EV logical node")
        # Name plate of external equipment
        self.add_data_object("NamPlt", LPL())
        # EV nameplate
        self.add_data_object("EVNamPlt", DPL())
        # Selected connection type according to IEC 61851-1
        self.add_data_object("ConnTypSel", ENSEVConnectionChargingKind())
        # State of charge
        self.add_data_object("Soc", MV())
        # EV ID as per ISO 15118-2:2014
        self.add_data_object("EVId", VSG())
        # E mobility accoung identifier, Annex H.1 of ISO 15118-2:2014
        self.add_data_object("EMAId", VSG())
        # Departure time with "0" meaning as soon as possible
        self.add_data_object("DptTm", TSG())
        # Amount of energy needed from the EV to reach the departure time or 100 % SoC
        self.add_data_object("EnAmnt", ASG())
        # Maximum voltage between phase and ground supported by the EV
        self.add_data_object("VMax", ASG())
        # Maximum current per phase supported by the EV
        self.add_data_object("AMax", ASG())
        # Minimum current per phase supported by the EV
        self.add_data_object("AMin", ASG())
        # Reference to the schedule logical node instance that contains information
        # on the charging profile of the EV
        self.add_data_object("SchdRef", ORG())


class SBAT(LogicalNode):
    """Battery storage supervisory control"""
    def __init__(self):
        super().__init__(ln_id="DT_SBAT", ln_class="SBAT",
                         description="Battery storage supervisory control")
        # Battery Earth Fault is present
        self.add_data_object("BatEF", SPS())
        # Minimum level of cell voltage has been exceeded
        self.add_data_object("CelVolLoAlm", SPS())
        # Maximum level of cell voltage has been exceeded
        self.add_data_object("CelVolHiAlm", SPS())
        # Battery Discharging current has exceeded the maximum threshold
        self.add_data_object("DschAmpHiAlm", SPS())
        # Maximum current threshold during charing of the battery has been exceeded
        self.add_data_object("ChaAmpHiAlm", SPS())
        # Warning current threshold during charging of the battery has been exceeded
        self.add_data_object("ChaAmpHiWrn", SPS())
        # Maximum internal temperature threshold of the battery has been exceeded
        self.add_data_object("IntnTmpHiAlm" , SPS())
        # High internal temperature warning threshold of the battery has been exceeded
        self.add_data_object("IntnTmpHiWrn", SPS())
        # Minimum internal temperature threshold of the battery has been exceeded
        self.add_data_object("IntnTmpLoAlm", SPS())
        # minimum internal temperature warning threshold of the battery has been exceeded
        self.add_data_object("IntnTmpLoWrn", SPS())
        # High level external temperature threshold of the battery has been reached
        self.add_data_object("ExtTmpHiAlm", SPS())
        # Low level external temperature threshold of the battery has been reached
        self.add_data_object("ExtTmpLoAlm", SPS())
        # Maximum external voltage limit of the battery has been reached
        self.add_data_object("ExtVolHiAlm", SPS())
        # Minimum external voltage limit of the battery has been reached
        self.add_data_object("ExtVolLoAlm", SPS())
        # Internal battery current
        self.add_data_object("IntnA", MV())
        # Internal battery voltage
        self.add_data_object("IntnV", MV())
        # Minimum cell voltage measurement of all cells since last reset
        self.add_data_object("CelVolLo", MV())
        # Maximum cell voltage measurement of all cells since last reset
        self.add_data_object("CelVolHi", MV())
        # Maximum temperature of all cells in the battery
        self.add_data_object("CelTmpMax", MV())
        # Minimum temperature of all cells in the battery
        self.add_data_object("CelTmpMin", MV())
        # Internal battery temperature in degrees celsius
        self.add_data_object("IntnTmp", MV())
        # External battery temperature in degrees celsius
        self.add_data_object("ExtTmp", MV())
        # External battery DC voltage
        self.add_data_object("ExtVol", MV())
        # Internal battery DC voltage
        self.add_data_object("IntnVol", MV())
        # Initiate reset of the calculated minimum and maximum battery voltage
        # measurements
        self.add_data_object("CelVolRs", SPC())
        # Alarm threshold for the minimum limit of a battery cell voltage
        self.add_data_object("CelVolLoAls", ASG())
        # Alarm threshold reflecting the maximum limit of a battery cell voltage
        self.add_data_object("CelVolHiAls", ASG())
        # High level discharging current threshold alarm setting
        self.add_data_object("DschAmpHiAls", ASG())
        # Warning threshold defining the high discharging current warning limit of
        # the battery in A
        self.add_data_object("DschAmpHiWrs", ASG())
        # High charging current alarm threshold of the battery in A
        self.add_data_object("ChaAmpHiAls", ASG())
        # Warning threshold defining the high charging current warning limit of the
        # battery in A
        self.add_data_object("ChaAmpHiWrs", ASG())
        # High internal temperature alarm threshold of the battery in °C
        self.add_data_object("IntnTmpHiAls", ASG())
        # High internal temperature warning threshold of the battery in °C
        self.add_data_object("IntnTmpHiWrs", ASG())
        # Low internal temperature alarm threshold of the battery in °C
        self.add_data_object("IntnTmpLoAls", ASG())
        # Low internal temperature warning threshold of the battery in °C
        self.add_data_object("IntnTmpLoWrs", ASG())
        # High external temperature alarm threshold of the battery in °C
        self.add_data_object("ExtTmpHiAls", ASG())
        # Low external temperature alarm threshold of the battery in °C
        self.add_data_object("ExtTmpLoAls", ASG())
        # High external voltage alarm threshold of the battery in V
        self.add_data_object("ExtVolHiAls", ASG())
        # Low external voltage alarm threshold of the battery in V
        self.add_data_object("ExtVolLoAls", ASG())


class DBAT(LogicalNode):
    """Battery storage logical node"""
    def __init__(self):
        super().__init__(ln_id="DT_DBAT", ln_class="DBAT",
                         description="Battery storage logical node")
        # SoC protection of the battery is activated
        self.add_data_object("SocPro", SPS())
        # True, battery is charging
        self.add_data_object("ChaSt", SPS())
        # True, battery is discharging
        self.add_data_object("DschSt", SPS())
        # Battery test results
        self.add_data_object("BatTestRsl", ENSBatteryTestResultKind())
        # True, battery DC switch is closed
        self.add_data_object("DCSwCls", SPS())
        # Battery drain DC current
        self.add_data_object("Amp", MV())
        # Battery DC watts
        self.add_data_object("Watt", MV())
        # Instantaneous DC current limit on charging
        self.add_data_object("ChaAmpLim", ASG())
        # Effective Ah operational value including degration
        self.add_data_object("EffAhr", MV())
        # Instantaneous voltage limit on charging
        self.add_data_object("ChaVolLim", MV())
        # Instantaneous DC current limit on discharging
        self.add_data_object("DschAmpLim", MV())
        # Number of strings of cells currently connected
        self.add_data_object("CelStrgCnt", MV())
        # Available charging capacity to be charged in Ah
        self.add_data_object("AvlChaAhr", MV())
        # Available discharge capacity to be discharged in Ah
        self.add_data_object("AvlDschAhr", MV())
        # SoC as percentage in relation to the effective energy capacity of the
        # storage resource
        self.add_data_object("SocEffAhrPct", MV())
        # State of charge deviation between estiamted value (calculated) and real
        # value (measured) in %
        self.add_data_object("SocDvPct", MV())
        # Rate of battery voltage change over time
        self.add_data_object("VChgRte", MV())
        # Instantaneous voltage limit on discharging
        self.add_data_object("DschVolLim", MV())
        # Type of Battery
        self.add_data_object("BatTyp", ENGBatteryTypeKind())
        # Maximum battery charge DC current rating
        self.add_data_object("ChaAmpMaxRtg",ASG())
        # Ah capacity rating
        self.add_data_object("AhrRtg", ASG())
        # Effective total charge capacity rating in Ah
        self.add_data_object("EffAhrRtg", ASG())
        # Minimum resting Ah capacity rating allowed
        self.add_data_object("ahrMinRtg", ASG())
        # Maximum battery charge voltage
        self.add_data_object("ChaVolMaxRtg", ASG())
        # Maximum battery discharge DC current rating
        self.add_data_object("DschAmpMxRtg", ASG())
        # Rating reflecting the maximum battery voltage while charging
        self.add_data_object("ExtVolMaxRtg", ASG())
        # Nominal external voltage of the battery
        self.add_data_object("ExtVolNom", ASG())
        # Nominal internal voltage of the battery (DC)
        self.add_data_object("IntnVolNom", ASG())
        # self discharge power rate
        self.add_data_object("SelfDschWRte", ASG())
        # Number of cells in parallel
        self.add_data_object("CelParCnt", ASG())
        # Number of cells in series
        self.add_data_object("CelSerCnt", ASG())
        # Discharge curve
        self.add_data_object("DschWattCrv", CSG())
        # Discharge curve by time
        self.add_data_object("DschWattTm", CSG())


class GGIO(LogicalNode):
    """Generic Process Input/Output Logical Node"""
    def __init__(self):
        super().__init__(ln_id="DT_GGIO", ln_class="GGIO",
                         description="Generic Process I/O")
        # Generic grid interface object nameplate
        self.add_data_object("EEName", DPL())
        # Integer status input
        self.add_data_object("IntIn1", INS())
        # General single alarm
        self.add_data_object("Alm1", SPS())
        # General single warning
        self.add_data_object("Wrn1", SPS())
        # General single indication (binary)
        self.add_data_object("Ind1", SPS())
        # local or remote key
        self.add_data_object("LocKey", SPS())
        # local control behaviour
        self.add_data_object("Loc", SPS())
        # measured analogue input
        self.add_data_object("AnIn1", MV())
        # controllable analogue output
        self.add_data_object("AnOut1", APC())
        # resettable counter
        self.add_data_object("CntRs1", BCR())
        # Switching authority at station level
        self.add_data_object("LocSta", SPC())
        # Single point controllable status output
        self.add_data_object("SPCSO1", SPC())
        # Double point controllable status output
        #self.add_data_object("DPCSO1", DPC())
        # Integer status controllable status output
        # self.add_data_object("ISCSO1", INC())


class DSTO(LogicalNode):
    """Monitoring and controlling of energy storage services and states for single
    or aggregated elements"""
    def __init__(self):
        super().__init__(ln_id="DT_DSTO", ln_class="DSTO",
                         description="Monitoring/Controlling of energy storage "
                                     "services")
        ## abstract class DER_Storage_LN
        # Energy storage nameplate
        self.add_data_object("EEName", DPL())
        # nameplate
        self.add_data_object("NamPlt", LPL())
        # Alarm trigger for maxiumum state of charge
        self.add_data_object("SoCHiAlm", SPS())
        # Warning trigger for maximum state of charge
        self.add_data_object("SocHiWrn", SPS())
        # Alarm trigger for minimum state of charge
        self.add_data_object("SocLoAlm", SPS())
        # Warning trigger for minimum state of charge
        self.add_data_object("SocLoWrn", SPS())
        # Alarm trigger for low state of health
        self.add_data_object("SohLoAlm", SPS())
        # Count the number of equivalent full charge cycles
        self.add_data_object("ChaCycCnt", INS())
        # available energy capacity to be charged
        self.add_data_object("InWh", MV())
        # Energy stored and available for discharging
        self.add_data_object("OutWh", MV())
        # Actual state of charge expressed in Wh
        self.add_data_object("SocWh", MV())
        # usable state of charge as percent of total usable energy capacity UseWh)
        self.add_data_object("UseSocPct", MV())
        # State of charge as percentage in relation to the effective energy capacity
        # of the storage resource with respect to the degradation so far (EffWh)
        self.add_data_object("SocEffWhPct", MV())
        # Total charged energy since last reset
        self.add_data_object("ChaWhTot", MV())
        # Total discharged energy since last reset
        self.add_data_object("DschWhTot", MV())
        # Available power
        self.add_data_object("AvlDschW", MV())
        # Available charging power
        self.add_data_object("AvlChaW", MV())
        # Available charging time
        self.add_data_object("AvlChaWTm", MV())
        # Available discharging time
        self.add_data_object("AvlDschWTm", MV())
        # reset of ChaWhTot, total energy charged, if true
        self.add_data_object("ChaWhTotRs", SPC())
        # reset of DschWhTot, total energy discharged, if true
        self.add_data_object("DschWhTotRs", SPC())
        # reference to the equivalent DGEN intance
        self.add_data_object("EqGn", ORG())
        # reference to the equivalent DLOD instance
        self.add_data_object("DLOD", ORG())
        # High state of charge alam threshold in percent
        self.add_data_object("SoCHiAlsPct", ASG())
        # High state of charge warning threshold of the battery in percent
        self.add_data_object("SoCHiWrsPct", ASG())
        # Low state of charge alarm threshold in percent
        self.add_data_object("SoCLoAlsPct", ASG())
        # Low state of charge warning threshold of the battery in percent
        self.add_data_object("SoCLoWrsPct", ASG())
        # Low state of health alarm threshold in percent
        self.add_data_object("SohLoAlsPct", ASG())
        # Roundtrip efficiency at normal conditions
        self.add_data_object("RntEffPct", ASG())
        ## abstract class StorageOperationalSettingsLN
        # the total amount of reactive power available for absorbing even if impacting
        # active power output throughout charging
        self.add_data_object("ChaAvarTot", MV())
        # the total amount of reactive power available for absorbing even if possibly
        # impacting active power output while discharging
        self.add_data_object("DschAvarTot", MV())
        # The total amount of reactive power available for injecting even if possibly
        # impacting active power output while charging
        self.add_data_object("ChaIvarTot", MV())
        # The total amount of reactive power available for injecting even if possibly
        # impacting active power output while discharging
        self.add_data_object("DschIvarTot", MV())
        # The amount of reactive power available for absorbing without impacting
        # active power output while charging
        self.add_data_object("ChaAvarAvl", MV())
        # The amount of reactive power available for absorbing without impacting
        # active power while discharging
        self.add_data_object("DschAvarAvl", MV())
        # The amount of reactive power available for injecting without impacting
        # active power output while charging
        self.add_data_object("ChaIvarAvl", MV())
        # The amount of reactive power available for injecting
        # without impacting active power output while
        # discharging
        self.add_data_object("DschIvarAvl", MV())
        # Effective actual total energy capacity (in Wh)
        # provided by the storage resource. Due to
        # degradation, the amount may be less than the rated
        # total energy capacity (WhRtg).
        self.add_data_object("EffWh", MV())
        # Effective actual total energy capacity (expressed as
        # percentage of WhRtg) provided by the storage
        # resource. Due to degradation, the amount may be
        # less than the rated total energy capacity (WhRtg).
        # In case both WhEffCapPct and WhEffCap DOs are
        # present in a same LN instance, the application shall
        # ensure to keep the values of both DOs consistent.
        self.add_data_object("EffWhPct", MV())
        # Maximum active power while charging
        self.add_data_object("ChaWMax", ASG())
        # maximum active powr while discharging
        self.add_data_object("DschWMax", ASG())
        # Default ramp rate for changes in active power:
        # percentage of WMax per second while charging
        self.add_data_object("ChaWRmp", ASG())
        # Default ramp rate for changes in active power:
        # percentage of WMax per second while discharging
        self.add_data_object("DschWRmp", ASG())
        # Charging reactive power maximum
        self.add_data_object("ChaVArMax", ASG())
        # Discharging reactive power maximum
        self.add_data_object("DschVArMax", ASG())
        # Maximum apparent charging power
        self.add_data_object("ChaVAMax", ASG())
        # Operational setpoint for maximum apparent power
        # while discharging
        self.add_data_object("DschVAMax", ASG())
        # Operational setpoint for maximum absorbing reactive
        # power while charging
        self.add_data_object("ChaAvarMax", ASG())
        # Operational setpoint for maximum absorbing reactive
        # power while discharging
        self.add_data_object("DschAvarMax", ASG())
        # Operational setpoint for maximum supply (injection)
        # reactive power while charging
        self.add_data_object("ChaIvarMax", ASG())
        # Operational setpoint for maximum supply (injection)
        # reactive power while discharging
        self.add_data_object("DschIvarMax", ASG())
        # Operational setting for maximum voltage while
        # charging
        self.add_data_object("ChaVMax", ASG())
        # Operational setpoint for maximum voltage while
        # discharging
        self.add_data_object("DschVMax", ASG())
        # Operational setting for minimum voltage while
        # charging
        self.add_data_object("ChaVMin", ASG())
        # Operational setpoint for minimum voltage while
        # discharging
        self.add_data_object("DschVMin", ASG())
        # Operational setting for maximum current under
        # nominal voltage under nominal power factor while
        # charging
        self.add_data_object("ChaAMax", ASG())
        # Operational setpoint for maximum current under
        # nominal voltage under nominal power factor while
        # discharging
        self.add_data_object("DschAMax", ASG())
        # Charging efficiency curve [% over SoC]
        self.add_data_object("ChaEfC", CSG())
        # Discharging efficiency curve [% over SoC]
        self.add_data_object("DschEfC", CSG())
        # The energy reserve level above which the storage
        # system may be only be charged in emergency
        # situations, expressed as a percentage of the usable
        # capacity, WhUseCap.
        self.add_data_object("UseWhMaxPct", ASG())
        # The energy reserve level below which the storage
        # system may be only be discharged in emergency
        # situations, expressed as a percentage of the usable
        # capacity, WhUseCap.
        self.add_data_object("UseWhMinPct", ASG())
        # Operational setpoint for usable energy storage
        # capacity in Wh
        self.add_data_object("UseWh", ASG())
        # Net Energy Metering (NEM) Policy Mode which
        # establishes whether the DER qualifies as renewable.
        # Mode A = Storage may charge from the grid but may
        # not discharge to the grid (acts only as load).
        # Mode B = Storage may not charge from the grid but
        # may discharge to the grid (charges from local energy
        # source).
        # Mode C = Storage may charge or discharge from the
        # grid at will / in response to commands for location
        # where there are no NEM integrity concerns.
        self.add_data_object("ChaSrc", ENGChargeSourceKind())
        ## Abstract class storage LN
        # Charge reactive power setpoint (unsigned). In case
        # VArSpt (signed) is used, reading the value of this
        # DO will reflect the charging setpoint value only (0
        # when discharging)
        self.add_data_object("ChaVArSpt", APC())
        # Charge active power setpoint (unsigned). In case
        # WSpt (signed) is used, reading the value of this DO
        # will reflect the charging setpoint value only (0 when
        # discharging)
        self.add_data_object("ChaWSpt", APC())
        # Discharge reactive power setpoint (unsigned). In
        # case VArSpt (signed) is used, reading the value of
        # this DO will reflect the discharging setpoint value
        # only (0 when charging)
        self.add_data_object("DschVArSpt", APC())
        # Discharge active power setpoint (unsigned). In
        # case WSpt (signed) is used, reading the value of
        # this DO will reflect the discharging setpoint value
        # only (0 when charging)
        self.add_data_object("DschWSpt", APC())
        ## Abstract class DER_AbstractState_LN
        # DER operational status
        self.add_data_object("DEROpSt", ENSDERStateKind())
        # Set to true at the end of the test procedure
        # (just before Test.stVal goes from true to false to notify
        # the end of the test) if all tests successful, otherwise set to false.
        # Its value remains unchanged until a new test procedure is launched.
        # Set systematically to false at warm or cold start of
        # the equipment, and at the time a new test is
        # initiated (when the Test.stVal goes from false to true).
        self.add_data_object("TestRsl", SPS())
        # Reflects the equipment test additional results
        # at the end of the test procedure (just before
        # Test.stVal goes from true to false to notify
        # the end of the test).
        # Set systematically to value 'test running' at
        # the time a new test is initiated (when the Test.stVal
        # goes from false to true).
        self.add_data_object("TestAddRsl", ENSEquipmentTestResultKind())
        # (controllable) if true, the DER is authorized
        # to connect, otherwise it has to remain (or become)
        # disconnected. Authorization may come from an
        # external source or may be a default setting.
        self.add_data_object("AuthConn", SPC())
        # (controllable) Operating with  the value expressed
        # in ctlVal (selected among the list specified in
        # DERStateControlKind) initiates the appropriate
        # transition request. The reading of its attribute
        # stVal is meaningless. The resulting state of the
        # DER shall be observed in the DEROpSt DO.
        self.add_data_object("DEROpStCtl", ENCDERStateTransitionKind())
        # (controllable) Operating with value true initiates
        # the cease to energize state of the DER (see definition
        # of "cease to energize"); operating with value false initiates
        # the return to service (get back to Idle, then reflect
        # the settings of any or all default settings, enabled
        # operational services, and/or schedules) of the DER
        self.add_data_object("CeaEgzCtl", SPC())
        # Active power setpoint. Its mxVal attribute
        # reflects the value of the setpoint that is requested.
        self.add_data_object("WSpt", APC())
        # Reactive power setpoint. Its mxVal attribute
        # reflects the value of the setpoint that is requested.
        self.add_data_object("VArSpt", APC())
        # (controllable) if true the DER shall operate
        # in emergency mode, otherwise shall operate in
        # normal mode. In emergency mode, emergency settings,
        # emergency limits, and other emergency-related
        # setpoints will be in effect.
        self.add_data_object("EmgMod", SPC())
        # (controllable) if true, the DER is authorized
        # to disconnect, otherwise shall remain
        # connected (if possible)
        self.add_data_object("AuthDscon", SPC())
        # (controllable) If set to true, entering
        # into test mode for the DER is allowed, otherwise forbidden
        self.add_data_object("TestEna", SPC())
        # (controllable) Operating with value true initiates
        # starting a test of the DER equipment and resets the
        # values of TestRsl.stVal (set to 'false') and TestAddRsl.stVal
        # (set to 'test running'); operating with value false
        # aborts the test. The reading of the status indicates
        # whether the equipment is under test or not.
        # The content of such test is implementation dependant.
        self.add_data_object("Test", SPC())
        # Maximum time from starting to connect
        # to the grid until achieving grid connection
        self.add_data_object("StrMaxTms", ING())
        # Minimal time the DER needs to stay
        # off after being switched off
        self.add_data_object("OffMinTms", ING())
        # Minimal time the DER needs to stay
        # on after being switched on
        self.add_data_object("OnMinTms", ING())
        # Minimal time delay before stopping
        # and/or disconnecting after a disconnect command received
        self.add_data_object("StopDlMinTms", ING())
        # Maximum time from starting to disconnect
        # from the grid until achieving grid disconnection
        self.add_data_object("StopMaxTms", ING())
        # Minimal time delay before starting or
        # restarting after a connect command has been received
        self.add_data_object("StrDlMinTms", ING())
        # if true, the DER can automatically initate its starting up
        self.add_data_object("AutoStr", SPG())
        # if true, the DER can automatically initiate its connection to the grid
        self.add_data_object("AutoConn", SPG())
        ## Actual power informatin
        # Actual self service energy used
        self.add_data_object("SelfSvcWh", MV())
        # Actual percentage of apparent power output based on VAMax
        self.add_data_object("VAPct", MV())
        # Available capability (measured or calculated)
        # for increasing active output, including increasing
        # generation of active power, even if currently consuming power.
        self.add_data_object("AvlUpW", MV())
        # Available capability (measured or calculated) for
        # decreasing active power, including increasing the
        # consumption of active power, even if currently generating power.
        self.add_data_object("AvlDnW", MV())
        ## Abstract Class StorageNameplateRatings
        # Nameplate maximum active power rating while charging
        self.add_data_object("ChaWMaxRtg", ASG())
        # Nameplate maximum active power rating while discharging
        self.add_data_object("DschWMaxRtg", ASG())
        # Nameplate ramp rate for changes in active
        # power while charging: percentage of WMax per second
        self.add_data_object("ChaWRmpRtg", ASG())
        # Nameplate ramp rate for changes in active power
        # while discharging: percentage of WMax per second
        self.add_data_object("DschWRmpRtg", ASG())
        # Active power charging rating at specified over-excited PF
        self.add_data_object("ChaWOvPFRtg", ASG())
        # Nameplate active power discharging rating
        # at specified over-excited power factor, OvPFRtg
        self.add_data_object("DschWOvPFRtg", ASG())
        # Active power charging rating at specified under-excited PF
        self.add_data_object("ChaWUnPFRtg", ASG())
        # Nameplate active power discharging rating at specified under-excited power
        # factor, UnPFRtg
        self.add_data_object("DschWUnPFRtg", ASG())
        # Nameplate maximum apparent charging power rating
        self.add_data_object("ChaVAMaxRtg", ASG())
        # Nameplate maximum apparent discharging power rating
        self.add_data_object("DschVAMaxRtg", ASG())
        # Nameplate rating for maximum absorbing reactive power while charging
        self.add_data_object("ChaAvarRtg", ASG())
        # Nameplate rating for maximum absorbing reactive power while discharging
        self.add_data_object("DschAvarRtg", ASG())
        # Nameplate rating for maximum supply (injection) reactive power while charging
        self.add_data_object("ChaIvarRtg", ASG())
        # Nameplate rating for maximum supply (injection) reactive power while discharging
        self.add_data_object("DschIvarRtg", ASG())
        # Nameplate rating for maximum voltage while charging
        self.add_data_object("ChaVMaxRtg", ASG())
        # Nameplate rating for maximum voltage while discharging
        self.add_data_object("DschVMaxRtg", ASG())
        # Nameplate rating for minimum voltage while charging
        self.add_data_object("ChaVMinRtg", ASG())
        # Nameplate rating for minimum voltage while discharging
        self.add_data_object("DschVMinRtg", ASG())
        # Nameplate rating for maximum current under nominal voltage under nominal power factor while charging
        self.add_data_object("ChaAMaxRtg", ASG())
        # Nameplate rating for maximum current under nominal voltage under nominal power factor while discharging
        self.add_data_object("DschAMaxRtg", ASG())
        # Nameplate energy storage capacity rating in Wh
        self.add_data_object("WhRtg", ASG())
        # Nameplate maximum amount of energy (in Wh) to be stored in the
        # storage resource for e.g. supporting long life and avoid
        # faster degradation
        self.add_data_object("WhMaxRtg", ASG())
        # Nameplate minimum amount of energy (in Wh) to be
        # retained in the storage resource for e.g. supporting
        # long life and avoid faster degradation or to ensure
        # a reserve of energy stored for emergencies and other purposes.
        self.add_data_object("WhMinRtg", ASG())
        # Charging efficiency curve [% over SoC]
        self.add_data_object("ChaEfcRtg", CSG())
        # Discharging efficiency curve [% over SoC]
        self.add_data_object("DschEfcRtg", CSG())
        # Net Energy Metering (NEM) Policy Mode which establishes whether the DER qualifies as renewable.
        # Mode A = Storage may charge from the grid but may not discharge to the grid (acts only as load).
        # Mode B = Storage may not charge from the grid but may discharge to the grid (charges from local energy source).
        # Mode C = Storage may charge or discharge from the grid at will / in response to commands for location where there are no NEM integrity concerns.
        self.add_data_object("ChaSrcRtg", ENGChargeSourceKind())

