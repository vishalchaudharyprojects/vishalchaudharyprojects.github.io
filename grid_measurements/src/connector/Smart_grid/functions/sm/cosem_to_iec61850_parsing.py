from configparser import ParsingError
from grid_measurements.src.connector.Smart_grid.functions.data_storage.mmxu_to_csv import taf10_mmxu_to_csv
from grid_measurements.src.connector.Smart_grid.libs.IEC_61850.iec_61850_ln import MMXU, TCTR, LogicalNode
from grid_measurements.src.connector.Smart_grid.libs.IEC_61850.iec_61850_enum import SIUnit, Validity
import os
import xml.etree.ElementTree as Et
import pandas as pd
from datetime import datetime
import logging
from pathlib import Path


# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set to DEBUG for more verbose logs
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("taf10_cosem_to_iec61850.log"),  # Log to a file
        logging.StreamHandler()  # Also log to console
    ]
)

# constant variables
OBIS_CODES = {
    "01000e0700ff": "Ch. 0 Supply frequency Inst. value",
    "0100100700ff": "Ch. 0 Sum LI Active power (abs(QI+QIV)-abs(QII+QIII)) Inst. value",
    "01001f0700ff": "Ch. 0 L1 Current Inst. value",
    "0100200700ff": "Ch. 0 L1 Voltage Inst. value",
    "0100240700ff": "Ch. 0 L1 Active power (abs(QI+QIV)-abs(QII+QIII)) Inst. value",
    "0100330700ff": "Ch. 0 L2 Current Inst. value",
    "0100340700ff": "Ch. 0 L2 Voltage Inst. value",
    "0100380700ff": "Ch. 0 L2 Active power (abs(QI+QIV)-abs(QI+QIII)) Inst. value",
    "0100470700ff": "Ch. 0 L3 Current Inst. value",
    "0100480700ff": "Ch. 0 L3 Voltage Inst. value",
    "01004c0700ff": "Ch. 0 L3 Active power (abs(QI+QIV)-abs(QI+QIII)) Inst. value",
    "0100510701ff": "Ch. 0 Angle of U(L2) - U(L1)",
    "0100510702ff": "Ch. 0 Angle of U(L3) - U(L1)",
    "0100510704ff": "Ch. 0 Angle of I(L1) - U(L1)",
    "010051070fff": "Ch. 0 Angle of I(L2) - U(L2)",
    "010051071aff": "Ch. 0 Angle of I(L3) - U(L3)"}

# selected unit codes according to iec 62056-6-2, Table 4
UNITS = {
    1:"time (year)",
    2:"time (month)",
    3:"time (week)",
    4:"time (day)",
    5:"time (hour)",
    6:"time (minute)",
    7:"time (second)",
    8:"phase angle (degree)",
    9:"temperature (°C)",
    10:"local currency",
    22:"energy (Nm)",
    27:"active power P (W)",
    28:"apparent power S (VA)",
    29:"reactive power Q (var)",
    30:"active energy (Wh)",
    31:"apparent energy (VAh)",
    32:"reactive energy (varh)",
    33:"current (A)",
    35:"voltage (V)",
    44:"frequency (Hz)"
}

#Mapping of Obis codes to mmxu refererences
OBIS_MMXU = {
    "01000e0700ff": ["Hz","mag","f"],
    "0100100700ff": ["TotW","mag","f"],
    "01001f0700ff": ["A","phsA","cVal","mag","f"],
    "0100200700ff": ["PhV","phsA","cVal","mag","f"],
    "0100240700ff": ["W","phsA","cVal","mag","f"],
    "0100330700ff": ["A","phsB","cVal","mag","f"],
    "0100340700ff": ["PhV","phsB","cVal","mag","f"],
    "0100380700ff": ["W","phsB","cVal","mag","f"],
    "0100470700ff": ["A","phsC","cVal","mag","f"],
    "0100480700ff": ["PhV","phsC","cVal","mag","f"],
    "01004c0700ff": ["W","phsC","cVal","mag","f"],
    "0100510704ff": ["A","phsA","cVal","ang","f"],
    "010051070fff": ["A","phsB","cVal","ang","f"],
    "010051071aff": ["A","phsC","cVal","ang","f"],
    "0100510701ff": "",
    "0100510702ff": "",
}

# define the possible namespaces
NAMESPACES = {"prog": "urn:k461-dke-de:profile_generic-1",
              "xs": "http://www.w3.org/2001/XMLSchema",
              "cox": "urn:k461-dke-de:extension-1"}


# class for data that goes over several timestamps
class TimestampData:
    def __init__(self):
        self.data = {}

    def add_data(self, timestamp, data):
        """Add data to the dictionary with the timestamp as the key and the
        data as the value.

        :param timestamp: The timestamp for the data that is being added
        :param data: The data to be added, should be a DataFrame
        """
        if timestamp in self.data:
            self.data[timestamp] = pd.concat([self.data[timestamp], data], ignore_index=True)
        else:
            self.data[timestamp] = data

    def get_data(self, timestamp):
        """Get data for a specific timestamp.

        :param timestamp: The timestamp for which to retrieve the
            respective data
        :return: The data for the given timestamp, or None if the
            timestamp does not exist
        """
        return self.data.get(timestamp, None)

    def print_all_data(self):
        """Print all the data stored in the dictionary."""
        for timestamp, df in self.data.items():
            print(f"Timestamp: {timestamp}")
            print(df)


def parse_taf10_to_iec61850(message,outputpath: str,outputfile: str) -> None:
    """Parses a TAF 10 xml payload to iec 61850 logical nodes mmxu.

    :param message: The TAF 10 xml payload
    :param outputpath: The path where the output should be saved
    :param outputfile: The name of the file where the output should be
        saved
    :return mmxu: Object of the MMXU logical node filled with data from
        the TAF 10 payload
    :return tctr: Object of the TCTR logical node filled with data from
        the current transformer
    """
    #########
    # Here we need to instantiate the logical nodes from the SCD file IED and not as I did hardcoded ones 
    ########
    # create the required logical node objects
    mmxu = MMXU()
    tctr = TCTR()

    # Here we need to read the current transformer parameters from the SCD file 
    # import tctr config, Annahme: Aufruf per pisaaEMT
    tctr_config = pd.read_csv(os.path.join("..","libs","pisa","WAGO_855_2701_035_001.csv"),encoding='latin1',sep=';')

    # fill tctr
    fill_tctr(tctr,tctr_config)
     # obtain the root element of the message
    text_message = message.decode("utf-8")
    taf10_tree = Et.ElementTree(Et.fromstring(text_message))
    # taf10_tree = Et.parse(message) # old test version
    taf10_root = taf10_tree.getroot()

    # check if the payload is actually taf 10 data by filtering the logical name
    taf10_logical_name = taf10_root.find(".//prog:attributes/cox:logical_name", NAMESPACES).text
    if "01005e31803f" not in taf10_logical_name:
        raise TypeError(f"The message is not a TAF 10 message. "
                        f"This method is not to be used with the correct payload. "
                        f"The logical name of this method is {taf10_logical_name}")

    # go to the buffer of the taf 10 message
    dlms_payload = taf10_root.find(".//prog:attributes/prog:buffer/prog:simple_data",NAMESPACES)
    capture_objects = taf10_root.find(".//prog:attributes/prog:capture_objects", NAMESPACES)

    # number of timestamps in the buffer
    number_of_timestamps = int(dlms_payload[0].attrib["count"])
    taf_10_payload = TimestampData()

    # generate a pandas df containing different
    # information about the capture objects and dlms_payload
    payload_structure = pd.DataFrame(
        columns=["id", "obis-code [Hex]", "interpretation", "unit", "value", "status"])

    # fills an empty dataframe for each timestamp
    for timestamp_index in range(1, number_of_timestamps+1):
        timestep = dlms_payload.find(f'.//prog:entry_gateway_signed[@id="{timestamp_index}"]', NAMESPACES)
        taf_10_payload.add_data(timestep.find(".//cox:capture_time",NAMESPACES).text, payload_structure.copy())

    # iterate over the capture objects and write the information into the df
    for capture_object in capture_objects:
        element_id = capture_object.attrib["id"]
        obis_code = capture_object.find(".//cox:logical_name",NAMESPACES).text.split(".")[0] # everything before the first "."
        interpretation = interprete_obis_code(obis_code)
        new_row = pd.DataFrame([{"id": element_id, "obis-code [Hex]": obis_code, "interpretation":interpretation,"unit":"","value":"","status":""}])
        # add the static (meaning time independent) information to the dataframe
        for key, value in taf_10_payload.data.items():
            value = pd.concat([value,new_row], ignore_index=True)
            taf_10_payload.data[key] = value
            
    # iterate through all the children of the buffer
    for element in dlms_payload:
        parse_simple_data_element(element,taf_10_payload)

    # write each timestep into the mmxu
    for timestamp, data in taf_10_payload.data.items():
        for row in data.iterrows():
            assign_data_to_mmxu(mmxu,tctr, row[1], timestamp)

        # Write the data of the mmxu into a csv
        ## Here return the mmxu and tctr so that the otherm module can take care of writing them to influxdb 
        taf10_mmxu_to_csv(mmxu, outputpath, outputfile)

    return None


def assign_data_to_mmxu(mmxu: MMXU, tctr, datapoint: pd.DataFrame, timestamp: str) -> None:
    """This function assigns the values, timestamps, status, units, etc. to the
    correct data attributes in the IEC 61850 logical node MMXU.
    :param mmxu: IEC 618150 object of the mmxu
    :param tctr: IEC 61850 object of the tctr
    :param datapoint: value of a TimeStamp Object
    :param timestamp: timestamp of the data point


    Returns: None
    """

    # get the obis code
    obis_code = datapoint["obis-code [Hex]"]
    reference = OBIS_MMXU[obis_code]
    interpretation = datapoint["interpretation"]

    if reference == "":
        logging.info(f"Obis code {obis_code}, "
                     f"{interpretation} not found in the mapping to IEC 61850")
        return

    # get the tctr parameters
    current_ratio = tctr.DO["Rat"].SDO["setMag"].DA["f"]
    # get the timestamp in UNIX
    date_time_object = datetime.fromisoformat(timestamp)
    unix_timestamp = date_time_object.timestamp()
    # assign the value, timestamp and quality:
    if reference[0] in ["Hz","TotW"]:
        # add MV object
        if reference[0] == "TotW":
            mmxu.DO[reference[0]].SDO[reference[1]].set_da(reference[2], datapoint["value"]*current_ratio)
        else:
            mmxu.DO[reference[0]].SDO[reference[1]].set_da(reference[2],datapoint["value"])
        mmxu.DO[reference[0]].SDO["t"].set_da("seconds", unix_timestamp)
    # if the reference is part of a WYE object:
    elif reference[0] in ["A","PhV","W"]:
        # add WYE object
        if reference[0] in ["A","W"] and reference[3] != "ang":
            mmxu.DO[reference[0]].SDO[reference[1]].SDO[reference[2]].SDO2[reference[3]].set_da(reference[4],datapoint["value"]*current_ratio)
        else:
            mmxu.DO[reference[0]].SDO[reference[1]].SDO[reference[2]].SDO2[reference[3]].set_da(reference[4],datapoint["value"])
        mmxu.DO[reference[0]].SDO[reference[1]].SDO["t"].set_da("seconds", unix_timestamp)

    else:
        raise ValueError(f"Reference {reference} not found in MMXU object")

    # assign the unit to the data object
    assign_unit_to_data_object(mmxu,reference,datapoint["unit"])
    #assign quality to the data object
    assign_quality_to_data_object(mmxu,reference,datapoint["status"])

    return


def assign_quality_to_data_object(ln: LogicalNode, reference: list,
                                  status: str) -> None:
    """This function maps the status-word of DLMS/COSEM to the quality object
    of the IEC 61850 logical node.

    :param ln: IEC 61850 logical node instance according to the ie3_iec61850_lib
    :param reference: Reference to the data object
    :param status: status of the respective datapoint

    Returns: None
    """
    # split the status by smgw and FNN status word
    smgw_status = status[0:8]  # first 16 bit are smgw status word
    fnn_status = status[8:]  # last 16 bit are the FNN status word

    # parse the status words into an integer and then into a binary value
    smgw_status_int = int(smgw_status,16)
    fnn_status_int = int(fnn_status, 16)
    smgw_status_bin = bin(smgw_status_int)[2:]
    fnn_status_bin = bin(fnn_status_int)[2:]

    # Flag the individual status
    smgw_fatal_error = smgw_status_bin[8] == 1
    smgw_invalid_system_time = smgw_status_bin[9] == 1
    smgw_ptb_warning = smgw_status_bin[12] == 1
    smgw_ptb_temporary_error = smgw_status_bin[14] == 1
    meter_magnetic_manipulation = fnn_status_bin[9] == 1
    meter_mechanical_manipulation = fnn_status_bin[10] == 1
    meter_no_voltage_supply = fnn_status_bin[18] == fnn_status_bin[19] == fnn_status_bin[20] == 1

    # Write the invalid/questionable conditions and set
    # the status depending on the reference (is it a MV, a WYE, etc.)
    validity_conditions = {
        Validity.QUESTIONABLE: [
            smgw_invalid_system_time, smgw_ptb_warning, meter_mechanical_manipulation
        ],
        Validity.INVALID: [
            smgw_fatal_error, smgw_ptb_temporary_error, meter_magnetic_manipulation, meter_no_voltage_supply
        ]
    }

    for validity, conditions in validity_conditions.items():
        if any(conditions):
            if reference[0] in ["Hz", "TotW", "TotVA"]:
                ln.DO[reference[0]].SDO[reference[1]].set_da("q", validity)
            elif reference[0] in ["A", "PhV", "W"]:
                ln.DO[reference[0]].SDO[reference[1]].SDO[reference[2]].set_da("q", validity)

            if validity == Validity.INVALID:
                break



def assign_unit_to_data_object(ln, reference: list, unit: str) -> None:
    """This function assigns the unit to a subdataobject :param ln: IEC 61850
    logical node instance according to the ie3_iec61850_lib :param reference:
    Reference to the data object :param unit: unit to be assigned.

    Returns: None
    """
    if unit == "frequency (Hz)" and reference[0] == "Hz":
        ln.DO[reference[0]].SDO["units"].set_da("SIUnit",SIUnit.HERTZ)
    elif unit == "voltage (V)" and reference[0] == "PhV":
        ln.DO[reference[0]].SDO[reference[1]].SDO["units"].set_da("SIUnit",SIUnit.VOLT)
    elif unit == "current (A)" and reference[0] == "A":
        ln.DO[reference[0]].SDO[reference[1]].SDO["units"].set_da("SIUnit",SIUnit.AMPERE)
    elif unit == "active power P (W)" and reference[0] == "W":
        ln.DO[reference[0]].SDO[reference[1]].SDO["units"].set_da("SIUnit",SIUnit.WATT)
    elif unit == "active power P (W)" and reference[0] == "TotW":
        ln.DO[reference[0]].SDO["units"].set_da("SIUnit",SIUnit.WATT)


def parse_simple_data_element(element: Et.SubElement, taf_10_payload: TimestampData):
    """This function parses the simple_data elements of TAF 10 data and write
    the values into the payload Timestamp :param element: The simple_data
    children to be parsed :param taf_10_payload: The dataframe containing the
    information about the capture objects/buffer elements."""
    # check how many data points were communicated
    for child_index in range(1,int(element.attrib["count"])+1):
        measurement_value = float(element.find(f'.//prog:entry_gateway_signed[@id="{child_index}"]/cox:value/cox:long64',NAMESPACES).text)
        scaler = float(element.find(f'.//prog:entry_gateway_signed[@id="{child_index}"]/cox:scaler',NAMESPACES).text)
        measurement_value = measurement_value / (10 ** abs(scaler))
        unit = UNITS[int(element.find(f'.//prog:entry_gateway_signed[@id="{child_index}"]/cox:unit',NAMESPACES).text)]
        status = element.find(f'.//prog:entry_gateway_signed[@id="{child_index}"]/cox:status/cox:octet-string',NAMESPACES).text
        time = element.find(f'.//prog:entry_gateway_signed[@id="{child_index}"]/cox:capture_time',NAMESPACES).text

        #write the values into the taf_10_payload dataframe
        taf_10_payload.data[time].loc[taf_10_payload.data[time]["id"] == element.attrib["id"],"status"] = status
        taf_10_payload.data[time].loc[taf_10_payload.data[time]["id"] == element.attrib["id"], "value"] = measurement_value
        taf_10_payload.data[time].loc[taf_10_payload.data[time]["id"] == element.attrib["id"], "unit"] = unit


def interprete_obis_code(obis_code:str):
    """This function interpretes the obis code and returns the interpretation
    of the obis code.

    :param obis_code: The obis code to be interpreted
    :return interpretation: The interpretation of the obis code
    """
    reduced_obis_code = obis_code.split(".")[0]
    try:
        interpretation = OBIS_CODES[reduced_obis_code]
    except ParsingError:
        interpretation = "Unknown"

    return interpretation

def fill_tctr(tctr: TCTR, tctr_config: pd.DataFrame):
    """This function fills the TCTR object with the configuration from the csv
    file :param tctr: The TCTR object to be filled :param tctr_config: The
    configuration of the TCTR object."""

    for _, row in tctr_config.iterrows():
        # obtain the data object, subdata object and data attribute reference
        reference = [row["DOI"],row["SDI1"],row["SDI2"],row["SDI3"],row["DAI"]]
        if reference[1] == "NAN" and "NAN" not in reference[2:]:
            tctr.DO[reference[0]].SDO[reference[2]].SDO2[reference[3]].set_da(reference[4],float(row["value"]))
        elif reference[1] == reference[2] == "NAN"  and "NAN" not in reference[3:]:
            tctr.DO[reference[0]].SDO[reference[3]].set_da(reference[4], float(row["value"]))
        elif reference[1] == reference[2] == reference[3] == "NAN" and "NAN" not in reference[4:]:
            tctr.DO[reference[0]].set_da(reference[4], float(row["value"]))
        else:
            raise ValueError(f"Reference {reference} not found in TCTR object")


def parse_taf10_to_iec61850_2(message: bytes) -> tuple:
    """
    Parses a TAF 10 XML payload to IEC 61850 logical nodes MMXU and TCTR.

    :param message: The TAF 10 XML payload as bytes.
    :return: tuple (mmxu, tctr) fully populated from TAF 10 payload.
    """

    mmxu = MMXU()
    tctr = TCTR()

    # Use absolute path for TCTR config CSV
    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
    tctr_config_path = PROJECT_ROOT / 'libs' / 'pisa' / 'WAGO_855_2701_035_001.csv'
    tctr_config = pd.read_csv(
        tctr_config_path,
        encoding='latin1',
        sep=';'
    )
    fill_tctr(tctr, tctr_config)

    text_message = message.decode("utf-8")
    taf10_tree = Et.ElementTree(Et.fromstring(text_message))
    taf10_root = taf10_tree.getroot()

    taf10_logical_name = taf10_root.find(".//prog:attributes/cox:logical_name", NAMESPACES).text
    if "01005e31803f" not in taf10_logical_name:
        raise TypeError(
            f"The message is not a TAF 10 message. "
            f"This method is not to be used with this payload. "
            f"Logical name found: {taf10_logical_name}"
        )

    dlms_payload = taf10_root.find(".//prog:attributes/prog:buffer/prog:simple_data", NAMESPACES)
    capture_objects = taf10_root.find(".//prog:attributes/prog:capture_objects", NAMESPACES)

    number_of_timestamps = int(dlms_payload[0].attrib["count"])
    taf_10_payload = TimestampData()

    payload_structure = pd.DataFrame(
        columns=["id", "obis-code [Hex]", "interpretation", "unit", "value", "status"]
    )

    # Fill empty dataframes for each timestamp
    for timestamp_index in range(1, number_of_timestamps + 1):
        timestep = dlms_payload.find(f'.//prog:entry_gateway_signed[@id="{timestamp_index}"]', NAMESPACES)
        taf_10_payload.add_data(
            timestep.find(".//cox:capture_time", NAMESPACES).text,
            payload_structure.copy()
        )

    # Fill static capture object data
    for capture_object in capture_objects:
        element_id = capture_object.attrib["id"]
        obis_code = capture_object.find(".//cox:logical_name", NAMESPACES).text.split(".")[0]
        interpretation = interprete_obis_code(obis_code)
        new_row = pd.DataFrame([{
            "id": element_id,
            "obis-code [Hex]": obis_code,
            "interpretation": interpretation,
            "unit": "",
            "value": "",
            "status": ""
        }])
        for key, value in taf_10_payload.data.items():
            value = pd.concat([value, new_row], ignore_index=True)
            taf_10_payload.data[key] = value

    # Fill dynamic values from payload
    for element in dlms_payload:
        parse_simple_data_element(element, taf_10_payload)

    # Populate MMXU with parsed values
    for timestamp, data in taf_10_payload.data.items():
        for _, row in data.iterrows():
            assign_data_to_mmxu(mmxu, tctr, row, timestamp)
    
    mmxu.ln_name = "DLMS_COSEM_MMXU"
    tctr.ln_name = "DLMS_COSEM_TCTR"

    return mmxu, tctr


if __name__ == "__main__":
    # test the function with a hardcoded message
    filename = r"EEMH0012830981.SMGW #1 ES.GWA_59713_1emh0013150392-taf10a_"
    filename += r"1733630057058_SigErr.xml"
    taf_10_filepath = os.path.join("..","..","libs","pisa",filename)
    # specify filepath for the output to be stored in
    outputpath = os.path.join("..","..","output")
    # specifiy the name of the file
    outputfile = "taf10_mmxu_output.csv"
    # fill the attributes of mmxu and tctr with the values from the cosem file
    parse_taf10_to_iec61850(taf_10_filepath, outputpath, outputfile)


