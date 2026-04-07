"""
This module has the purpose to include all the input data scripts for the measurement
topology used in the toolchain

author: Thomas Schwierz
"""
import pandas as pd
import os


def fill_grid_data_meas_topology(grid_data: dict, config_data: dict) -> None:
    """

    :param grid_data: gridData as dictionary of the power system
    :param config_data: GridCalcTool-config, configurates the SmartGridPlatform
    :return: None
    """
    grid_data["measTopology"] = pd.DataFrame(columns=["type", "node_i", "node_j"])

    # fill measTopology if a state estimation is to be executed
    if (
            (config_data["PyToolchainConfig"]["module"]["type"] == "simulation" or
             config_data["PyToolchainConfig"]["module"]["type"] == "application")
            and config_data["PyToolchainConfig"]["module"]["function"] == "se"
    ):
        if config_data["PyToolchainConfig"]["grid"]["meas_input"] == "csv":
            if os.path.isfile(
                    "Grids/"
                    + config_data["PyToolchainConfig"]["grid"]["name"]
                    + "/"
                    + config_data["PyToolchainConfig"]["grid"]["input_dataformat"].upper()
                    + "/"
                    + "meas_config.csv"
            ):
                input_meas_data(
                    "Grids/"
                    + config_data["PyToolchainConfig"]["grid"]["name"]
                    + "/"
                    + config_data["PyToolchainConfig"]["grid"]["input_dataformat"].upper()
                    + "/",
                    grid_data,
                )
        elif config_data["PyToolchainConfig"]["grid"]["meas_input"] == "code":
            generate_meas_data(grid_data, config_data)
        else:
            raise ValueError("No valid measurement measurement input in Configfile found!")


def generate_meas_data(grid_data, config_data) -> None:
    """
    This function generates measurement data for the state estimation based on the meas_configuration specified in the
    configuration file

    :param grid_data: the data of the power system
    :param config_data: the configuration of the application

    :return: None
    """

    # 1) obtain the measurement scenario
    meas_config = config_data["PyToolchainConfig"]["grid"][
        "meas_scenario"
    ]

    # Scenario with smart meters at every household and cdc/lss measurements
    if meas_config == 1:
        # 2) add the measurements of the substation to the measurement topology
        trafo_lv_busbars = []
        for index, row in grid_data["transformers"].iterrows():
            # find the lv bus of the transformer
            trafo_lv_busbars.append(grid_data["transformers"]["lvBus"].iloc[index])

        # 2.1) Add a voltage measurement for every lv busbar
        add_voltage_measurements(grid_data, trafo_lv_busbars)

        # 2.2) Add power flow measurement from the busbar to the transformer
        # 2.3) Add power flow measurements from the busbar to adjacent lines
        add_powerflow_measurements(grid_data, trafo_lv_busbars)

        # 3) add the measurements from CDC to the measurement topology
        cdc = []  # list of cable distribution cabinets
        current_bus = {}
        grid_data["busData"].insert(4, "nodal_degree", 0)
        # 3.1) Generate a list of all cable distribution cabinets
        for index, row in grid_data["busData"].iterrows():
            current_bus["name"] = row["busName"]
            current_bus["nodal_degree"] = 0  # nodal degree of the current_bus
            # iteriere über alle Leitungen und definiere den Knotengrad für die Knoten
            for index2, row2 in grid_data["topology"].iterrows():
                if row2["node_i"] == current_bus["name"]:
                    current_bus["nodal_degree"] += 1
                elif row2["node_j"] == current_bus["name"]:
                    current_bus["nodal_degree"] += 1
            # iteriere über alle Trafos und definieren den Knotengrad für die Knoten
            for index2, row2 in grid_data["transformers"].iterrows():
                if row2["hvBus"] == current_bus["name"]:
                    current_bus["nodal_degree"] += 1
                elif row2["lvBus"] == current_bus["name"]:
                    current_bus["nodal_degree"] += 1
            # if the current bus has more than two neigbours and is not a lv_busbar of the trafo, then it is a cdc
            if (
                    current_bus["nodal_degree"] > 2
                    and current_bus["name"] not in trafo_lv_busbars
            ):
                cdc.append(current_bus["name"])
            # add nodal degree to gridData["busData"]
            grid_data["busData"]["nodal_degree"].loc[index] = current_bus["nodal_degree"]
        # 3.2) Add voltage measurements for all the cdc
        add_voltage_measurements(grid_data, cdc)

        # 3.3) Add powerflow measurements for all the cdc
        add_powerflow_measurements(grid_data, cdc)

        # 4) add the measurements from the smart meters to the measurement topology
        add_household_measurements(grid_data, cdc, trafo_lv_busbars)

        # 5) Calculate measurement_redundancy
        meas_redundancy = float(grid_data["measTopology"].shape[0]) / (
                2 * float(grid_data["busData"].shape[0]) - 1
        )
        gridname = config_data["PyToolchainConfig"]["grid"]["name"]
        print(
            "Measurement redundancy of measurement configuration "
            + str(meas_config)
            + " for the grid "
            + gridname
            + " is "
            + str(meas_redundancy)
        )

    else:
        raise ValueError(
            "No valid measurement scenario in state estimation configuration"
        )


def input_meas_data(grid_data_path, grid_data):
    """
    This function reads the measurement configuration csv-file from the specified path and loads it into
    gridData["measTopology"]
    :param grid_data_path: path to measurement configuration csv-file
    :param grid_data: gridData as dictionary of the power system
    :return: gridData["measTopology"]
    """
    meas_config = pd.read_csv(grid_data_path + "meas_config.csv", sep=";")
    grid_data["measTopology"] = meas_config.fillna("")


def add_powerflow_measurements(grid_data: pd.DataFrame, nodes: list) -> None:
    """
    This function adds power flow measurements to the measurement topology
    :param grid_data: grid Data dictionary
    :param nodes: all the nodes representing node i from which power flow measurements are to be added

    :return: None
    """
    # add power flow measurements for the lines
    for index, row in grid_data["topology"].iterrows():
        # if node i is in the list of nodes, add the power flow measurements with node_i as the from node of the line
        if grid_data["topology"]["node_i"].iloc[index] in nodes:
            pij_line_measurement = pd.DataFrame([{
                "type": "Pij",
                "node_i": grid_data["topology"]["node_i"].iloc[index],
                "node_j": grid_data["topology"]["node_j"].iloc[index],
            }])
            grid_data["measTopology"] = pd.concat(
                [grid_data["measTopology"], pij_line_measurement], ignore_index=True
            )

            qij_line_measurement = pd.DataFrame([{
                "type": "Qij",
                "node_i": grid_data["topology"]["node_i"].iloc[index],
                "node_j": grid_data["topology"]["node_j"].iloc[index],
            }])
            grid_data["measTopology"] = pd.concat(
                [grid_data["measTopology"], qij_line_measurement], ignore_index=True
            )
        # if node j is in the list of nodes, add the power flow measurements with node_j as the from node of the line
        elif grid_data["topology"]["node_j"].iloc[index] in nodes:
            pij_line_measurement = pd.DataFrame([{
                "type": "Pij",
                "node_i": grid_data["topology"]["node_j"].iloc[index],
                "node_j": grid_data["topology"]["node_i"].iloc[index],
            }])
            grid_data["measTopology"] = pd.concat(
                [grid_data["measTopology"], pij_line_measurement], ignore_index=True
            )

            qij_line_measurement = pd.DataFrame([{
                "type": "Qij",
                "node_i": grid_data["topology"]["node_j"].iloc[index],
                "node_j": grid_data["topology"]["node_i"].iloc[index],
            }])
            grid_data["measTopology"] = pd.concat(
                [grid_data["measTopology"], qij_line_measurement], ignore_index=True
            )

    # add power flow measurements for the transformer
    for index, row in grid_data["transformers"].iterrows():
        if grid_data["transformers"]["lvBus"].iloc[index] in nodes:
            pij_trafo_measurement = pd.DataFrame([{
                "type": "Pij",
                "node_i": grid_data["transformers"]["lvBus"].iloc[index],
                "node_j": grid_data["transformers"]["hvBus"].iloc[index],
            }])
            grid_data["measTopology"] = pd.concat(
                [grid_data["measTopology"], pij_trafo_measurement], ignore_index=True
            )

            qij_trafo_measurement = pd.DataFrame([{
                "type": "Qij",
                "node_i": grid_data["transformers"]["lvBus"].iloc[index],
                "node_j": grid_data["transformers"]["hvBus"].iloc[index],
            }])
            grid_data["measTopology"] = pd.concat(
                [grid_data["measTopology"], qij_trafo_measurement], ignore_index=True
            )


def add_voltage_measurements(grid_data: pd.DataFrame, nodes: list) -> pd.DataFrame:
    """
    This function adds voltage measurements to the measurement topology of the given nodes
    :param grid_data: grid Data dictionary
    :param nodes: all the nodes for which voltage measurements are to be added
    :return: gridData["measTopology"]
    """
    for bus in nodes:
        voltage_measurement = pd.DataFrame([{
            "type": "Ui",
            "node_i": bus,
        }])
        grid_data["measTopology"] = pd.concat(
            [grid_data["measTopology"], voltage_measurement], ignore_index=True
        )

    return grid_data["measTopology"]


def add_nodal_power_measurements(grid_data: pd.DataFrame, node: str) -> pd.DataFrame:
    """
    This function adds p,q measurements for the given node
    :param grid_data: grid Data dictionary
    :param node: node for which p and q measurements are to be added
    :return: gridData["measTopology"]
    """

    p_measurement = pd.DataFrame([{
        "type": "Pi",
        "node_i": node,
    }])
    grid_data["measTopology"] = pd.concat(
        [grid_data["measTopology"], p_measurement], ignore_index=True
    )
    p_measurement = pd.DataFrame([{
        "type": "Qi",
        "node_i": node,
    }])
    grid_data["measTopology"] = pd.concat(
        [grid_data["measTopology"], p_measurement], ignore_index=True
    )

    return grid_data["measTopology"]


def add_household_measurements(
        grid_data: pd.DataFrame, cdc: list, trafo_lv_busbars: list
) -> pd.DataFrame:
    """
    This function adds v, p, q measurements for all nodes with a nodal degree of 2
    and that are not cdc or lv busbars of transformers or external grids
    :param grid_data:
    :param cdc: List of all cable distribution cabinets in the grid
    :param trafo_lv_busbars: List of all lv_busbars of the trafo

    :return: gridData["measTopology"]
    """
    for index, row in grid_data["busData"].iterrows():
        # if the nodal degree is > 2: Go to the next iteration
        if grid_data["busData"]["nodal_degree"].loc[index] > 2:
            continue
        # if the node is a cdc or a lv busbar of a transformer: Go to the next iteration
        if (
                grid_data["busData"]["busName"].loc[index] in cdc
                or grid_data["busData"]["busName"].loc[index] in trafo_lv_busbars
        ):
            continue
        # if the node is a slack node: Go to the next node
        if (
                grid_data["busData"]["busName"].loc[index]
                in grid_data["gridConfig"]["extGridNode"].values
        ):
            continue
        # execute function logic, i.e. the addition of smart meter measurements
        node = grid_data["busData"]["busName"].loc[index]
        grid_data["measTopology"] = add_voltage_measurements(grid_data, [node])
        grid_data["measTopology"] = add_nodal_power_measurements(grid_data, node)

    return grid_data["measTopology"]
