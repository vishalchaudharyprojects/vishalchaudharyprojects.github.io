"""
author: sebastian.raczka@tu-dortmund.de

Modifications: - 2024/08/20: Added changes for low voltage grids by Thomas Schwierz
"""

import os.path
import pandas as pd
import logging
import cimpy
import math
from .InputDataCSV import inputProfiles, inputCoordinates
from pathlib import Path
from .InputData_Logger import init_cim_import_logger, bus_type_warning, voltage_level_warning, coordinate_warning
from Cim_gen.src.Function_modules.InputMeasData import inputMeasData
from minio import Minio
from dotenv import load_dotenv

logging.getLogger('cimpy').setLevel(logging.ERROR)


def inputGridData(ConfigData, gridData, new_import_result={}, error_tolerance=0.0):
    """
    Import grid data from CIM files and fill the gridData dictionary.

    This function reads CIM files specified in the configuration data, processes the data,
    and fill the gridData dictionary with various grid components such as buses,
    transformers, lines, loads, and generators.


    :param:  ConfigData (dict): Configuration data containing information about the grid and file paths.
    :param:    gridData (dict): Dictionary to store the imported grid data.
    :param:    new_import_result (dict, optional): Dictionary to store new import results. Defaults to an empty dictionary.
    :param:    error_tolerance (float, optional): Tolerance level for errors during data import. Defaults to 0.0.

    :return:    tuple: A tuple containing the updated gridData dictionary and the import result dictionary.
    """
    BASE_DIR = Path(__file__).resolve().parents[2]  # Adjust as needed
    grid_files = (
            BASE_DIR
            / "Grids"
            / ConfigData["Cim_gen"]["grid"]["name"]
            / ConfigData["Cim_gen"]["grid"]["input_dataformat"].upper()
    )

    # store a list of all cim files in the directory
    file_list = os.listdir(str(grid_files))


    # Initialize variables
    EQ_file = SSH_file = SV_file = TP_file = DL_file = GL_file = None
    GL = False

    for file in file_list:
        filename = file.split("_")
        for abbr in filename:
            if abbr == "DL" or abbr == "DI" or "DL" in file or "DI" in file:
                DL_file = file
            elif abbr == "EQ" or "EQ" in file:
                EQ_file = file
            elif abbr == "SSH" or "SSH" in file:
                SSH_file = file
            elif abbr == "SV" or "SV" in file:
                SV_file = file
            elif abbr == "TP" or "TP" in file:
                TP_file = file
            elif abbr == "GL" or "GL" in file:
                GL_file = file
                GL = True
            elif "GL" not in file and "DI" not in file and "DL" not in file:
                GL = False

    # Check if required files exist
    required_files = [EQ_file, SSH_file, SV_file, TP_file, DL_file]
    if any(f is None for f in required_files):
        raise ValueError(f"Missing required CIM files in the directory: {file_list}")

    # Create file list
    xml_files = [
        str(grid_files / EQ_file),
        str(grid_files / SSH_file),
        str(grid_files / SV_file),
        str(grid_files / TP_file),
        str(grid_files / DL_file),
    ]

    if GL:
        xml_files.append(str(grid_files / GL_file))

    # import of xml-files via cimpy (prints amount of created objects of each class automatically)
    if ConfigData["Cim_gen"]["grid"]["input_dataformat"] == "cim3":
        import_result = cimpy.cim_import(xml_files, "cgmes_v3_0")
        print("CIM3")
    elif ConfigData["Cim_gen"]["grid"]["input_dataformat"] == "cim2":
        import_result = cimpy.cim_import(xml_files, "cgmes_v2_4_15")
        print("CIM2_4_15")
    # bus_branch_import_result = cimpy.utils.node_breaker_to_bus_branch(import_result)

    for key, value in import_result["topology"].items():
        if value.__class__.__name__ == "OperationalLimitType":
            if value.name in "patl":
                value.limitType = (
                    "http://entsoe.eu/CIM/SchemaExtension/3/1#LimitTypeKind.patl"
                )
            elif value.name in "highVoltage":
                value.limitType = (
                    "http://entsoe.eu/CIM/SchemaExtension/3/1#LimitTypeKind.highVoltage"
                )
    for key, value in import_result["topology"].items():
        if value.__class__.__name__ == "Terminal":
            value.possibleProfileList["class"] = [4, 0, 1, 2]
            if "SvPowerFlow" in value.possibleProfileList:
                del value.possibleProfileList["SvPowerFlow"]
    for key, value in import_result["topology"].items():
        if value.__class__.__name__ == "TopologicalNode":
            value.possibleProfileList["class"] = [2]
            if "SvInjection" in value.possibleProfileList:
                del value.possibleProfileList["SvInjection"]
            if "SvVoltage" in value.possibleProfileList:
                del value.possibleProfileList["SvVoltage"]
            if "TopologicalIsland" in value.possibleProfileList:
                del value.possibleProfileList["TopologicalIsland"]
    for key, value in import_result["topology"].items():
        if value.__class__.__name__ == "BaseVoltage":
            value.possibleProfileList["class"] = [0]
            if "TopologicalNode" in value.possibleProfileList:
                del value.possibleProfileList["TopologicalNode"]

    # due to the DiagramObject-problem of PowerFactory-export, value of IdentifiedObject is set to correct object
    for key, value in import_result["topology"].items():
        if value.__class__.__name__ == "DiagramObject":
            if value.IdentifiedObject.__class__.__name__ == "ConnectivityNode":
                if value.IdentifiedObject.TopologicalNode is not None:
                    value.IdentifiedObject = value.IdentifiedObject.TopologicalNode

    # due to the voltageLevel-problem of PowerFactory-export, faulty nodes get referenced their correct voltageLevel-object
    # for key, value in import_result["topology"].items():
    #     if value.__class__.__name__ == "TopologicalNode":
    #         bv_mRID = value.BaseVoltage.mRID
    #         if (bv_mRID != value.ConnectivityNodeContainer.BaseVoltage.mRID) and (
    #             value.ConnectivityNodeContainer.name != value.name
    #         ):
    #             for inner_key, inner_value in import_result["topology"].items():
    #                 if inner_value.__class__.__name__ == "VoltageLevel":
    #                     if (inner_value.BaseVoltage.mRID == bv_mRID) and (
    #                         inner_value.name == value.name
    #                     ):
    #                         value.ConnectivityNodeContainer = inner_value
    #                         inner_value.TopologicalNode = [value]

    # fill header of dataframes
    # ToDo: Fill data from datasheet database (write a new method to include data from other sources)
    gridData["gridConfig"] = pd.DataFrame(
        columns=[
            "sbGrid_mva",
            "vnGrid_kv",
            "extGridSetpoint_pu",
            "extGridSetpoint_angle",
            "extGridNode",
            "maxP",
            "minP",
            "maxQ",
            "minQ",
            "maxSc_mva",
            "minSc_mva",
            "maxRX_ratio",
            "minRX_ratio",
            "auxiliary_node",
        ]
    )
    gridData["busData"] = pd.DataFrame(columns=["busName", "voltageLevel", "bus_type"])
    gridData["topology"] = pd.DataFrame(
        columns=[
            "name",
            "node_i",
            "node_j",
            "parallelDevices",
            "type",
            "length_km",
            "bay_i",
            "bay_j",
        ]
    )
    gridData["lineTypes"] = pd.DataFrame(
        columns=[
            "name",
            "r_ohm_km",
            "x_ohm_km",
            "b_miks_km",
            "g_miks_km",
            "iMax_ka",
            "vRated_kv",
        ]
    )
    gridData["transformers"] = pd.DataFrame(
        columns=[
            "name",
            "hvBus",
            "lvBus",
            "hvBus_kv",
            "lvBus_kv",
            "type",
            "tapPos",
            "bay_i",
            "bay_j",
        ]
    )
    gridData["transformerTypes"] = pd.DataFrame(
        columns=[
            "type",
            "sn_mva",
            "r_ohm",
            "x_ohm",
            "pfe_kw",
            "tap_step_percent",
            "tap_min",
            "tap_max",
            "tap_neutral",
            "is_OLTC",
            "phaseShift",
            "phaseShift_degree",
        ]
    )
    gridData["loads"] = pd.DataFrame(
        columns=["name", "busConnected", "p_mw", "q_mvar", "type"]
    )
    gridData["gens"] = pd.DataFrame(
        columns=[
            "name",
            "busConnected",
            "p_mw",
            "q_mvar",
            "type",
            "rated_S_mva",
            "q_min_mvar",
            "q_max_mvar",
            "p_max",
            "p_min",
        ]
    )
    gridData["measTopology"] = pd.DataFrame(columns=["type", "node_i", "node_j"])
    gridData["switches"] = pd.DataFrame(
        columns=[
            "name",
            "line",
            "node_i",
            "node_j",
            "status",
            "I_rated",
            "connected_to_line",
        ]
    )
    gridData["storage_units"] = pd.DataFrame(
        columns=[
            "name",
            "busConnected",
            "p_mw",
            "q_mvar",
            "rated_S_mva",
            "q_min_mvar",
            "q_max_mvar",
            "p_max",
            "p_min",
            "rated_E",
            "SoC",
            "battery status",
        ]
    )

    # initialize cim import logger
    cim_import_logger = init_cim_import_logger()

    # fill gridConfig
    sbGrid_mva = 100  # not available in CIM_export, hardcoded

    # check if mRID-attribute is the same as key
    for key, value in import_result["topology"].items():
        if hasattr(value, "mRID"):
            value.mRID = key

    for key, value in import_result["topology"].items():
        if value.__class__.__name__ == "ExternalNetworkInjection":
            vnGrid_kv = value.EquipmentContainer.BaseVoltage.nominalVoltage
            extGridSetpoint_pu = value.RegulatingControl.targetValue / vnGrid_kv
            if len(value.EquipmentContainer.TopologicalNode) > 1:
                if (
                        value.EquipmentContainer.TopologicalNode[
                            0
                        ].BaseVoltage.nominalVoltage
                        > value.EquipmentContainer.TopologicalNode[
                    1
                ].BaseVoltage.nominalVoltage
                ):
                    node = 0
                else:
                    node = 1
            else:
                node = 0
            extGridNode = value.EquipmentContainer.TopologicalNode[node].name
            node_mRID = value.EquipmentContainer.TopologicalNode[node].mRID
            for inner_key, inner_value in import_result["topology"].items():
                if inner_value.__class__.__name__ == "SvVoltage":
                    if inner_value.TopologicalNode.mRID == node_mRID:
                        extGridSetpoint_angle = inner_value.angle

            maxP = value.maxP
            minP = value.minP
            maxQ = value.maxQ
            minQ = value.minQ

            maxSc_mva = (
                    (value.maxInitialSymShCCurrent / 1000)
                    * value.EquipmentContainer.BaseVoltage.nominalVoltage
                    * math.sqrt(3)
            )
            minSc_mva = (
                    (value.minInitialSymShCCurrent / 1000)
                    * value.EquipmentContainer.BaseVoltage.nominalVoltage
                    * math.sqrt(3)
            )
            maxRX_ratio = value.maxR0ToX0Ratio
            minRX_ratio = value.minR0ToX0Ratio

            if maxSc_mva == float(0.0):
                maxSc_mva = 1
            if minSc_mva == float(0.0):
                minSc_mva = 1
            if maxRX_ratio == float(0.0):
                maxRX_ratio = 0.1
            if minRX_ratio == float(0.0):
                minRX_ratio = 0.1

            new_row = pd.DataFrame([{
                "sbGrid_mva": sbGrid_mva,
                "vnGrid_kv": vnGrid_kv,
                "extGridSetpoint_pu": extGridSetpoint_pu,
                "extGridSetpoint_angle": extGridSetpoint_angle,
                "extGridNode": extGridNode,
                "maxP": maxP,
                "minP": minP,
                "maxQ": maxQ,
                "minQ": minQ,
                "maxSc_mva": maxSc_mva,
                "minSc_mva": minSc_mva,
                "maxRX_ratio": maxRX_ratio,
                "minRX_ratio": minRX_ratio,
                "auxiliary_node": ConfigData["Cim_gen"]["grid"][
                    "auxiliary_nodes"
                ],
            }])

            gridData["gridConfig"] = pd.concat(
                [gridData["gridConfig"], new_row], ignore_index=True
            )

    cim_import_logger.info("External Grid successfully added to gridData")

    # fill transformer
    # iterate over all available PowerTransformer-object
    for key, value in import_result["topology"].items():

        # initial values in case no ratios are given in cim files
        tapStep_percent = 0.18600
        tapPos = 0

        if value.__class__.__name__ == "PowerTransformer":
            # set is_oltc to false as default for each transformer
            is_oltc = False
            name = value.name
            sn_mva = value.PowerTransformerEnd[0].ratedS
            # get values from the respective power transformer end objects
            if (
                    value.PowerTransformerEnd[0].ratedU
                    > value.PowerTransformerEnd[1].ratedU
            ):
                r_ohm = value.PowerTransformerEnd[0].r
                x_ohm = value.PowerTransformerEnd[0].x
                phaseShift = value.PowerTransformerEnd[1].phaseAngleClock
                hvBus_kv = value.PowerTransformerEnd[0].ratedU
                lvBus_kv = value.PowerTransformerEnd[1].ratedU
                hvBus = value.PowerTransformerEnd[0].Terminal.TopologicalNode.name
                lvBus = value.PowerTransformerEnd[1].Terminal.TopologicalNode.name
                hv_switching_group = value.PowerTransformerEnd[0].connectionKind
                lv_switching_group = value.PowerTransformerEnd[1].connectionKind
                switching_group = hv_switching_group + str.lower(lv_switching_group)

            else:
                r_ohm = value.PowerTransformerEnd[1].r
                x_ohm = value.PowerTransformerEnd[1].x
                phaseShift = value.PowerTransformerEnd[0].phaseAngleClock
                hvBus_kv = value.PowerTransformerEnd[1].ratedU
                lvBus_kv = value.PowerTransformerEnd[0].ratedU
                hvBus = value.PowerTransformerEnd[1].Terminal.TopologicalNode.name
                lvBus = value.PowerTransformerEnd[0].Terminal.TopologicalNode.name
                lv_switching_group = value.PowerTransformerEnd[0].connectionKind
                hv_switching_group = value.PowerTransformerEnd[1].connectionKind
                switching_group = hv_switching_group + str.lower(lv_switching_group)

            for inner_keyRatio, valueRatio in import_result["topology"].items():
                if (
                        valueRatio.__class__.__name__ == "RatioTapChanger"
                        and valueRatio.name == name
                ):
                    tapStep_percent = valueRatio.stepVoltageIncrement
                    tapPos = valueRatio.normalStep
                    highstep = valueRatio.highStep
                    lowstep = valueRatio.lowStep
                    neutralstep = valueRatio.neutralStep
                    is_oltc = True

            new_row = pd.DataFrame([{
                "name": name,
                "hvBus": hvBus,
                "lvBus": lvBus,
                "hvBus_kv": hvBus_kv,
                "lvBus_kv": lvBus_kv,
                "type": name,
                "tapPos": tapPos,
                "bay_i": "",
                "bay_j": "",
            }])
            gridData["transformers"] = pd.concat(
                [gridData["transformers"], new_row], ignore_index=True
            )

            new_row = pd.DataFrame([{
                "type": name,
                "sn_mva": sn_mva,
                "r_ohm": r_ohm,
                "x_ohm": x_ohm,
                "pfe_kw": 0,
                "tap_step_percent": tapStep_percent,
                "is_OLTC": is_oltc,
                "phaseShift": phaseShift,
                "phaseShift_degree": phaseShift * 30,
                "switching group": switching_group
            }])
            gridData["transformerTypes"] = pd.concat(
                [gridData["transformerTypes"], new_row], ignore_index=True
            )

    cim_import_logger.info(
        "Transformers and transformer types successfully added to gridData"
    )

    # fill lineTypes
    i = 1
    line_types = {}
    for key, value in import_result[
        "topology"
    ].items():  # ierate over ACLineSegment-objects
        if value.__class__.__name__ == "ACLineSegment":
            # calculate resistance/km
            resistance = round((value.r / value.length), 5)
            # calculate reactance/km
            reactance = round((value.x / value.length), 5)
            b_miks = round((value.bch * 10 ** 6) / value.length, 3)  # calculate sub
            g_miks = round((value.gch * 10 ** 6) / value.length, 3)
            voltageLevel = value.BaseVoltage.nominalVoltage
            # extract current limit for specific line
            for key1, value1 in import_result["topology"].items():
                if value1.__class__.__name__ in "Terminal":
                    if value1.ConductingEquipment is not None:
                        if value1.ConductingEquipment.mRID is value.mRID:
                            for key2, value2 in import_result["topology"].items():
                                if value2.__class__.__name__ in "CurrentLimit":
                                    if (
                                            value1.OperationalLimitSet[0].mRID
                                            is value2.OperationalLimitSet.mRID
                                    ):
                                        iMax_ka = currentLimit = value2.value / 1000

            # check, if parameters of a line differ from existing line types
            if gridData["lineTypes"].empty:
                name = (
                        "Line type "
                        + str(i)
                        + " - "
                        + str(voltageLevel)
                        + "kV "
                        + str(iMax_ka)
                        + "kA"
                )

                new_row = pd.DataFrame([{
                    "name": name,
                    "r_ohm_km": resistance,
                    "x_ohm_km": reactance,
                    "b_miks_km": b_miks,
                    "g_miks_km": g_miks,
                    "iMax_ka": iMax_ka,
                    "vRated_kv": voltageLevel,
                }])

                gridData["lineTypes"] = pd.concat(
                    [gridData["lineTypes"], new_row], ignore_index=True
                )

            elif not (
                    (
                            (gridData["lineTypes"]["r_ohm_km"] == resistance)
                            & (gridData["lineTypes"]["x_ohm_km"] == reactance)
                            & (gridData["lineTypes"]["b_miks_km"] == b_miks)
                            & (gridData["lineTypes"]["g_miks_km"] == g_miks)
                            & (gridData["lineTypes"]["iMax_ka"] == iMax_ka)
                            & (gridData["lineTypes"]["vRated_kv"] == voltageLevel)
                    ).any()
            ):
                i += 1
                name = (
                        "Line type "
                        + str(i)
                        + " - "
                        + str(voltageLevel)
                        + "kV "
                        + str(iMax_ka)
                        + "kA"
                )

                new_row = pd.DataFrame([{
                    "name": name,
                    "r_ohm_km": resistance,
                    "x_ohm_km": reactance,
                    "b_miks_km": b_miks,
                    "g_miks_km": g_miks,
                    "iMax_ka": iMax_ka,
                    "vRated_kv": voltageLevel,
                }])

                gridData["lineTypes"] = pd.concat(
                    [gridData["lineTypes"], new_row], ignore_index=True
                )

            else:
                # when lineType already exists -> the correct type is getting selected from df and stored in name
                name = (
                    gridData["lineTypes"]
                    .loc[(
                            (gridData["lineTypes"]["r_ohm_km"] == resistance)
                            & (gridData["lineTypes"]["x_ohm_km"] == reactance)
                            & (gridData["lineTypes"]["b_miks_km"] == b_miks)
                            & (gridData["lineTypes"]["g_miks_km"] == g_miks)
                            & (gridData["lineTypes"]["iMax_ka"] == iMax_ka)
                            & (gridData["lineTypes"]["vRated_kv"] == voltageLevel)
                    )]["name"]
                    .item()
                )
            line_types[value.mRID] = name

    cim_import_logger.info("Lines and line types successfully added to gridData")

    # fill topology
    # iteriere über die Topologie und alle Leitungen
    for key, value in import_result["topology"].items():
        if value.__class__.__name__ in "ACLineSegment":
            # hole dir den Namen und die Länge der Leitung sowie dien Typen
            name = value.name
            length = value.length
            skip = False
            type = line_types[value.mRID]
            # iteriere wieder über die Topologie und suche alle Terminals
            for innerKey, innerValue in import_result["topology"].items():
                if innerValue.__class__.__name__ in "Terminal":
                    if innerValue.ConductingEquipment is not None:
                        # prüfe, ob die mRID des Terminals mit der mRID der Leitung übereinstimmt
                        if value.mRID is innerValue.ConductingEquipment.mRID:
                            # Setze Knoten i und j (wie noch nicht ganz verstanden)
                            if innerValue.ConductingEquipment.name and not skip:
                                node_i = innerValue.TopologicalNode.name
                                skip = True
                            elif skip:
                                node_j = innerValue.TopologicalNode.name
                                skip = False

            new_row = pd.DataFrame([{
                "name": name,
                "node_i": node_i,
                "node_j": node_j,
                "parallelDevices": 1,
                "type": type,
                "length_km": length,
                "bay_i": "",
                "bay_j": "",
            }])

            gridData["topology"] = pd.concat(
                [gridData["topology"], new_row], ignore_index=True
            )

    cim_import_logger.info("Topology successfully added to gridData")

    # fill buses
    for key, value in import_result["topology"].items():
        if value.__class__.__name__ in "TopologicalNode":
            name = value.name
            voltageLevel = value.BaseVoltage.nominalVoltage
            # initialize a list to store all adjacent elements
            adjacent_elements = []
            # add bus type to busData (CDC, Haushalt, LSS)
            for terminal in value.Terminal:
                # find adjacent terminals
                adjacent_element = terminal.ConductingEquipment.__class__.__name__
                adjacent_elements.append(adjacent_element)
                if contains_unknown_string(adjacent_elements) is True:
                    raise ValueError(
                        "Terminal "
                        + terminal
                        + "does not contain any conducting equipment, something is"
                          " wrong in the grid!"
                    )
            if voltageLevel == 0.4:  # Niederspannung
                bus_type = check_for_bustype(adjacent_elements, cim_import_logger)
                if bus_type == "unknown":
                    # Warnung im Logger, dass der Bustype nicht bekannt ist.
                    bus_type_warning(value, cim_import_logger)

            elif voltageLevel > 0.4 and voltageLevel < 110:  # Mittelspannung
                bus_type = check_for_bustype(adjacent_elements, cim_import_logger)
                if bus_type == "unknown":
                    # Warnung im Logger, dass der Bustype nicht bekannt ist.
                    bus_type_warning(value, cim_import_logger)

            else:  # Hochspannung und höher,
                voltage_level_warning(value, cim_import_logger)

            new_row = pd.DataFrame(
                [{"busName": name, "voltageLevel": voltageLevel, "bus_type": bus_type}]
            )
            gridData["busData"] = pd.concat(
                [gridData["busData"], new_row], ignore_index=True
            )

    cim_import_logger.info("busData successfully added to gridData")

    x_coord = math.nan
    y_coord = math.nan
    k = 0
    if ConfigData["Cim_gen"]["grid"]["input_coordinates"] == "GL":
        for var in gridData["busData"]["busName"]:
            for key, value in import_result["topology"].items():
                if (
                        value.__class__.__name__ in "PositionPoint"
                        and var == value.Location.PowerSystemResources.name
                ):
                    x_coord = value.xPosition
                    y_coord = value.yPosition
                    gridData["busData"].at[k, "x_coord"] = float(x_coord)
                    gridData["busData"].at[k, "y_coord"] = float(y_coord)
                    k = k + 1

    elif ConfigData["Cim_gen"]["grid"]["input_coordinates"] == "DL":
        # iterate over all buses in gridData
        for var in gridData["busData"]["busName"]:
            # iterate over all diagram objectpoints
            for key, value in import_result["topology"].items():
                if value.__class__.__name__ == "DiagramObjectPoint":
                    # look for the topological nodes to which the diagram objectpoints refer
                    # relevant, as we only want coordinates of the busbars from the Topological Nodes
                    if (
                            value.DiagramObject.IdentifiedObject.__class__.__name__
                            == "TopologicalNode"
                            and value.DiagramObject.IdentifiedObject.name == var
                    ):
                        # iterate over all topological nodes
                        if ConfigData["Cim_gen"]["verbose"] == "true":
                            print("Verbose: BusbarSection " + str(k) + " found")
                            print(
                                "Verbose: "
                                + value.DiagramObject.IdentifiedObject.ConnectivityNodeContainer.TopologicalNode[
                                    0
                                ].name
                            )
                        x_coord = value.xPosition
                        y_coord = value.yPosition
                        gridData["busData"].at[k, "x_coord"] = float(x_coord)
                        gridData["busData"].at[k, "y_coord"] = float(y_coord)
                        k += 1
                        break

    elif ConfigData["Cim_gen"]["grid"]["input_coordinates"] == "AI":
        inputCoordinates(grid_files, gridData)

    else:
        coordinate_warning(ConfigData, cim_import_logger)

    cim_import_logger.info("Coordinates successfully added to gridData")

    gridData["busData"].dropna(subset=["busName"], inplace=True)

    # add bays to the transformers
    for row_1 in gridData["busData"].iterrows():
        k = 1
        var_1 = 0
        busName = row_1[1]["busName"]
        for row_2 in gridData["topology"].iterrows():
            node_i = row_2[1]["node_i"]
            node_j = row_2[1]["node_j"]
            if node_i == busName:
                gridData["topology"].at[var_1, "bay_i"] = "Q0" + str(k)
                k = k + 1
            if node_j == busName:
                gridData["topology"].at[var_1, "bay_j"] = "Q0" + str(k)
                k = k + 1
            var_1 = var_1 + 1

        var_1 = 0
        for row_3 in gridData["transformers"].iterrows():
            hvBus = row_3[1]["hvBus"]
            lvBus = row_3[1]["lvBus"]
            if hvBus == busName:
                gridData["transformers"].at[var_1, "bay_i"] = "Q0" + str(k)
                k = k + 1
            if lvBus == busName:
                gridData["transformers"].at[var_1, "bay_j"] = "Q0" + str(k)
            var_1 = var_1 + 1

    # fill loads
    for key, value in import_result["topology"].items():
        if (
                value.__class__.__name__ in "NonConformLoad"
                or value.__class__.__name__ in "ConformLoad"
        ):
            name = value.name
            busConnected = value.mRID
            if "EV" in value.name:
                type = "EV"
            elif "HP" in value.name:
                type = "HP"
            else:
                type = "unknown"
                if ConfigData["Cim_gen"]["verbose"] == "true":
                    # print warning that the load type is unknown
                    print(
                        "WARNING: The load type of " + value.name + " is not specified."
                    )
                    # Set logging WARNING
                    cim_import_logger.warning(
                        "The load type of "
                        + value.name
                        + " is not specified in the assets name."
                    )

            for inner_key, inner_value in import_result["topology"].items():
                if inner_value.__class__.__name__ == "Terminal":
                    if inner_value.ConductingEquipment is not None:
                        if inner_value.ConductingEquipment.mRID is busConnected:
                            busConnected = inner_value.TopologicalNode.name

            p_mw = value.p
            q_mvar = value.q
            new_row = pd.DataFrame([{
                "name": name,
                "busConnected": busConnected,
                "p_mw": p_mw,
                "q_mvar": q_mvar,
                "type": type,
            }])
            gridData["loads"] = pd.concat(
                [gridData["loads"], new_row], ignore_index=True
            )

    # ToDo: Realize this with a decorator, doesn't have anything to do with the source code
    cim_import_logger.info("Loads successfully added to gridData")

    # fill gens
    for key, value in import_result["topology"].items():
        if value.__class__.__name__ in "SynchronousMachine":
            name = value.name
            busConnected = value.mRID
            type = "SynchronousMachine"
            for inner_key, inner_value in import_result["topology"].items():
                if inner_value.__class__.__name__ == "Terminal":
                    if inner_value.ConductingEquipment is not None:
                        if inner_value.ConductingEquipment.mRID is busConnected:
                            busConnected = inner_value.TopologicalNode.name
            p_mw = -value.p
            q_mvar = -value.q
            rated_S_mva = value.ratedS
            q_min_mvar = value.minQ
            q_max_mvar = value.maxQ
            max_power_P = value.GeneratingUnit.maxOperatingP
            min_power_P = value.GeneratingUnit.minOperatingP
            # Suche in den powerelectronicsconnections nach der powerelectronicunit und dann nach
            # dem zugehörigen Objekt in den CIM-Objekten
            new_row = pd.DataFrame([{
                "name": name,
                "busConnected": busConnected,
                "p_mw": p_mw,
                "q_mvar": q_mvar,
                "type": type,
                "rated_S_mva": rated_S_mva,
                "q_min_mvar": q_min_mvar,
                "q_max_mvar": q_max_mvar,
                "p_max": max_power_P,
                "p_min": min_power_P,
            }])

            gridData["gens"] = pd.concat([gridData["gens"], new_row], ignore_index=True)

        if value.__class__.__name__ == "PowerElectronicsConnection":
            busConnected = value.mRID
            p_mw = -value.p
            q_mvar = -value.q
            rated_S_mva = value.ratedS
            q_min_mvar = value.minQ
            q_max_mvar = value.maxQ

            # Get the connected bus
            for inner_key, inner_value in import_result["topology"].items():
                if inner_value.__class__.__name__ == "Terminal":
                    if inner_value.ConductingEquipment is not None:
                        if inner_value.ConductingEquipment.mRID == busConnected:
                            busConnected = inner_value.TopologicalNode.name

            # Handle PowerElectronicsUnit type
            if hasattr(value, 'PowerElectronicsUnit'):
                pe_unit = value.PowerElectronicsUnit

                # First try to get type from the unit's class name
                if hasattr(pe_unit, '__class__') and hasattr(pe_unit.__class__, '__name__'):
                    pe_unit_class = pe_unit.__class__.__name__
                else:
                    # Fallback to string representation if class name not available
                    pe_unit_class = str(pe_unit)

                # Handle Battery Units
                if "Battery" in pe_unit_class or "Battery" in value.name:
                    name = getattr(pe_unit, 'name', value.name)
                    max_power_P = -getattr(pe_unit, 'maxP', 0)
                    min_power_P = getattr(pe_unit, 'minP', 0)
                    ratedE = getattr(pe_unit, 'ratedE', 0)
                    storedE = getattr(pe_unit, 'storedE', 0)
                    battery_state = getattr(pe_unit, 'batteryState', "unknown")

                    new_row = pd.DataFrame([{
                        "name": name,
                        "busConnected": busConnected,
                        "p_mw": p_mw,
                        "q_mvar": q_mvar,
                        "rated_S_mva": rated_S_mva,
                        "q_min_mvar": q_min_mvar,
                        "q_max_mvar": q_max_mvar,
                        "p_max": max_power_P,
                        "p_min": min_power_P,
                        "rated_E": ratedE,
                        "SoC": storedE,
                        "battery status": battery_state,
                    }])
                    gridData["storage_units"] = pd.concat(
                        [gridData["storage_units"], new_row], ignore_index=True
                    )

                # Handle PV Units
                elif "PhotoVoltaic" in pe_unit_class or "PV" in value.name:
                    asset_type = "PV"
                    name = getattr(pe_unit, 'name', value.name)
                    max_power_P = getattr(pe_unit, 'maxP', 0)
                    min_power_P = getattr(pe_unit, 'minP', 0)

                    new_row = pd.DataFrame([{
                        "name": name,
                        "busConnected": busConnected,
                        "p_mw": p_mw,
                        "q_mvar": q_mvar,
                        "type": asset_type,
                        "rated_S_mva": rated_S_mva,
                        "q_min_mvar": q_min_mvar,
                        "q_max_mvar": q_max_mvar,
                        "p_max": max_power_P,
                        "p_min": min_power_P,
                    }])
                    gridData["gens"] = pd.concat(
                        [gridData["gens"], new_row], ignore_index=True
                    )

                # Handle Wind Units
                elif "Wind" in pe_unit_class or "Wind" in value.name:
                    asset_type = "Wind"
                    name = getattr(pe_unit, 'name', value.name)
                    max_power_P = getattr(pe_unit, 'maxP', 0)
                    min_power_P = getattr(pe_unit, 'minP', 0)

                    new_row = pd.DataFrame([{
                        "name": name,
                        "busConnected": busConnected,
                        "p_mw": p_mw,
                        "q_mvar": q_mvar,
                        "type": asset_type,
                        "rated_S_mva": rated_S_mva,
                        "q_min_mvar": q_min_mvar,
                        "q_max_mvar": q_max_mvar,
                        "p_max": max_power_P,
                        "p_min": min_power_P,
                    }])
                    gridData["gens"] = pd.concat(
                        [gridData["gens"], new_row], ignore_index=True
                    )

                else:
                    print(f"WARNING: Unrecognized PowerElectronicsUnit type: {pe_unit_class} for {value.name}")
                    cim_import_logger.warning(
                        f"Unrecognized PowerElectronicsUnit type: {pe_unit_class} for {value.name}"
                    )
            else:
                print(f"WARNING: PowerElectronicsConnection {value.name} has no PowerElectronicsUnit")
                cim_import_logger.warning(
                    f"PowerElectronicsConnection {value.name} has no PowerElectronicsUnit"
                )

    cim_import_logger.info(
        "Generators and storage units successfully added to gridData"
    )

    # fill measTopology
    if (grid_files / "meas_config.csv").is_file():
        inputMeasData(grid_files, gridData)

    # fill profiles (timeseries, switching actions)
    if (ConfigData["Cim_gen"]["converter"]["tse_generator"]["profiles"]) == True:
        inputProfiles(grid_files, gridData)

    # ToDO: check the switch import with the lv_simbench_sw_grid once simbench api works again
    # check the voltage level, switches for MV and LV work differently
    if vnGrid_kv > 30.0:  # Medium Voltage Grid as slack node is high voltage
        # fill switches
        i = 0
        # erstelle eine leere Liste, in der alle Switch-Objekte gespeichert werden sollen.
        list_of_lb_sw = []
        for key, value in import_result["topology"].items():
            if value.__class__.__name__ in "Terminal":
                if value.ConductingEquipment is not None:
                    # wenn eine Leitung gefunden wird, die an das Terminal grenzt: Füge Schalter auf beiden Seiten ein
                    if (
                            gridData["topology"]["name"]
                                    .str.fullmatch(value.ConductingEquipment.name)
                                    .any()
                    ):
                        line = value.ConductingEquipment.name
                        node_i = value.TopologicalNode.name
                        i += 1
                        name = "sw_" + str(i)
                        if value.connected:
                            status = "closed"
                        else:
                            status = "open"
                        if (
                                "PowerTransformer"
                                not in value.ConductingEquipment.__class__.__name__
                        ):
                            new_row = pd.DataFrame([{
                                "name": name,
                                "line": line,
                                "node_i": node_i,
                                "status": status,
                                "connected_to_line": True,
                            }])

                            gridData["switches"] = pd.concat(
                                [gridData["switches"], new_row], ignore_index=True
                            )

            if value.__class__.__name__ in "LoadBreakSwitch":
                # Wenn ein LoadBreakSwitch gefunden wurde, finde node i and node j und füge ihn als neue Zeile zu den Schaltern hinzu
                name = value.name
                node_j = node_i = value.EquipmentContainer.TopologicalNode[0].name
                for inner_key, inner_value in import_result["topology"].items():
                    if inner_value.__class__.__name__ in "Terminal":
                        if (inner_value.ConductingEquipment.mRID is value.mRID) and (
                                inner_value.TopologicalNode.name is not node_i
                        ):
                            node_j = inner_value.TopologicalNode.name
                            list_of_lb_sw.append(import_result["topology"][value.mRID])
                if value.open:
                    status = "open"
                else:
                    status = "closed"
                list_of_lb_sw.append(import_result["topology"][value.mRID])
                new_row = pd.DataFrame([{
                    "name": name,
                    "line": node_j,
                    "node_i": node_i,
                    "status": status,
                    "connected_to_line": False,
                }])
                gridData["switches"] = pd.concat(
                    [gridData["switches"], new_row], ignore_index=True
                )
    elif vnGrid_kv > 0.4 and vnGrid_kv <= 30.0:  # Low Voltage Grid
        # fill fuses and load breakers
        for key, value in import_result["topology"].items():
            if value.__class__.__name__ in ["Fuse", "LoadBreakSwitch"]:
                name = value.name
                node_i = value.EquipmentContainer.TopologicalNode[0].name
                iRated = value.ratedCurrent
                # look for the second node of the fuse
                for inner_key, inner_value in import_result["topology"].items():
                    if inner_value.__class__.__name__ in "Terminal":
                        if (inner_value.ConductingEquipment.mRID is value.mRID) and (
                                inner_value.TopologicalNode.name is not node_i
                        ):
                            node_j = inner_value.TopologicalNode[0].name
                # look for a line adjacent to node j (there should be exactly one)
                for inner_key, inner_value in import_result["topology"].items():
                    if inner_value.__class__.__name__ in "Terminal":
                        # look for status of the terminal (open/closed)
                        if inner_value.connected:
                            status = "closed"
                        else:
                            status = "open"
                        # look for the adjacent line
                        if (inner_value.TopologicalNode.name == node_j) and (
                                inner_value.ConductingEquipment.__class__.__name__
                                in "ACLineSegment"
                        ):
                            line = inner_value.ConductingEquipment.name
                            connected_to_line = True
                        else:
                            line = "NAN"
                            connected_to_line = False

                new_row = pd.DataFrame([{
                    "name": name,
                    "line": line,
                    "node_i": node_i,
                    "node_j": node_j,
                    "status": status,
                    "iRated": iRated,
                    "connected_to_line": connected_to_line,
                }])
                gridData["switches"] = pd.concat(
                    [gridData["switches"], new_row], ignore_index=True
                )

    cim_import_logger.info("Switches successfully added to gridData")

    # replace dots and free spaces as such strings are not compatible in external libs
    columns_to_clean = [
        ("gridConfig", "extGridNode"),
        ("loads", "name"),
        ("loads", "busConnected"),
        ("gens", "name"),
        ("gens", "busConnected"),
        ("busData", "busName"),
        ("topology", "name"),
        ("topology", "node_i"),
        ("topology", "node_j"),
        ("measTopology", "node_i"),
        ("measTopology", "node_j"),
        ("switches", "line"),
        ("switches", "node_i"),
        ("transformers", "name"),
        ("transformers", "hvBus"),
        ("transformers", "lvBus"),
        ("storage_units", "busConnected")
    ]

    for df, col in columns_to_clean:
        gridData[df][col] = (
            gridData[df][col]
            .str.replace(".", "")
            .str.replace(" ", "")
            .str.replace("_", "")
        )

    return gridData, import_result


def contains_unknown_string(lst):
    """
    Check if a list contains the string "unknown".

    This function iterates over each element in the provided list and checks if any element is a string with the value "unknown".

    Args:
        lst (list): The list to check for the presence of the string "unknown".

    Returns:
        bool: Returns True if the list contains the string "unknown", otherwise returns False.
    """
    for element in lst:
        if isinstance(element, str) and element == "unknown":
            return True
    return False


def check_for_bustype(lst, cim_import_logger):
    """
    Checks the content of the list and returns the bustype of the respective bus.

    << function description >>

    Args:
        lst: A list of dictionaries containing the adjacent elements and their types.

    Returns:
        (string): bustypes, either "substation", "CDC", "customer","external_grid" or unknown if no condition holds
    """

    # save the total number of neighbours
    number_components = len(lst)
    # initialize counters for transformers, lines and generators/loads
    number_transformers = 0
    number_lines = 0
    number_gen_loads = 0
    number_external_grid = 0
    number_busbars = 0

    # iterate over the list and count the number of transformers, lines and generators/loads
    for neighbour in lst:
        if neighbour == "PowerTransformer":
            number_transformers += 1
            continue
        elif neighbour == "ACLineSegment":
            number_lines += 1
            continue
        elif neighbour in [
            "SynchronousMachine",
            "EnergyConsumer",
            "PowerElectronicsConnection",
            "ConformLoad",
            "NonConformLoad",
            "PhotoVoltaicUnit",
            "BatteryUnit"
        ]:
            number_gen_loads += 1
            continue
        elif neighbour == "ExternalNetworkInjection":
            number_external_grid += 1
            continue
        elif neighbour == "BusbarSection":
            number_busbars += 1
    #     else:
    #        #Throw Warning and save message of the neighbour type in the logger
    #        print("WARNING: The type of the neighbour " + str(neighbour["element"]) + " is unknown.")
    #        #Set logging WARNING
    #        warning_logger.warning("The type of the neighbour " + str(neighbour["element"]) + " is unknown.")

    # check if the conditions for a substation are met
    if number_transformers == 1 and number_lines == (
            number_components - number_transformers - number_busbars
    ):
        return "dLSS"
    # ToDo: CDC Mit anderem Simbench-Netz prüfen, aktuell nicht möglich, da Simbench-Server down ist.
    elif number_lines == number_components - number_busbars:
        return "dCDC"
    elif number_gen_loads + number_lines == number_components - number_busbars:
        return "customer"
    elif (
            number_transformers + number_external_grid == number_components - number_busbars
    ):
        return "slack"
    else:
        return "unknown"
