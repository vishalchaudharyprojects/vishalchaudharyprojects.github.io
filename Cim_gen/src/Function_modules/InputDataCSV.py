"""
author: sebastian.raczkar@tu-dortmund.de
"""

import math
import os.path
import sqlite3
import pandas as pd
from igraph import Graph
from Cim_gen.src.Function_modules.PowerCalculation import PolPowerCalculation
from Cim_gen.src.Function_modules.InputMeasData import  inputMeasData



def inputGridData(ConfigData, gridData):
    # store grid configuration data #
    # UbHV [kV]; UbLV [kV]; sbGrid [MVA]; extGridSetpoint [pu]; noTransformer; tapPos; tapStep_percent; extGridNode; maxSc [MVA]; minSc [MVA]; maxRX_ratio; minRX_ratio
    gridDataPath = (
        "Grids/"
        + ConfigData["PyToolchainConfig"]["grid"]["name"]
        + "/"
        + ConfigData["PyToolchainConfig"]["grid"]["input_dataformat"].upper()
        + "/"
    )
    gridConfig = pd.read_csv(gridDataPath + "grid_config.csv", sep=";")

    # store topology connection data #
    # name; bus i; bus j; type; tap position
    if os.path.isfile(gridDataPath + "transformers.csv"):
        transformers = pd.read_csv(gridDataPath + "transformers.csv", sep=";")
        transformers["bay_i"] = "A"
        transformers["bay_j"] = "B"
    else:
        transformers = pd.DataFrame(columns=["name", "hvBus", "lvBus"])

    # store transformer data #
    # name; high voltage bus; low voltage bus; parallel devices; type; length [km]
    topology = pd.read_csv(gridDataPath + "topology_grid.csv", sep=";")
    topology["bay_i"] = "A"
    topology["bay_j"] = "B"

    # selection of all buses in the grid #
    busName = pd.concat(
        [topology.node_i, topology.node_j, transformers.hvBus, transformers.lvBus]
    )
    busName = pd.unique(busName)
    busName = pd.DataFrame(busName)
    busName.columns = ["busName"]
    busName = busName.sort_values(by="busName")
    busName = busName.reset_index(drop=True)

    # bus dataframe
    busData = pd.DataFrame(busName["busName"])

    # Add voltage level for all buses #
    busData["voltageLevel"] = float((gridConfig["vnGrid_kv"].values[0]))

    # Find in bus dataframe high voltage level node #
    k = 0
    for var in transformers["hvBus"]:
        index_hV = int(
            busData[
                busData["busName"].str.fullmatch((transformers["hvBus"].values)[k])
            ].index[0]
        )
        index_lV = int(
            busData[
                busData["busName"].str.fullmatch((transformers["lvBus"].values)[k])
            ].index[0]
        )
        # Add high voltage level to specific nodes #
        busData.loc[index_hV, "voltageLevel"] = float(
            (transformers["hvBus_kv"].values[k])
        )
        busData.loc[index_lV, "voltageLevel"] = float(
            (transformers["lvBus_kv"].values[k])
        )
        k = k + 1

    # store line parameter data #
    # name; r [Ohm/km]; x [Ohm/km]; b [µS/km]; g [µS/km]; iMax [kA] ; vRated [kV]; type #
    lineTypes = pd.read_csv(gridDataPath + "line_types.csv", sep=";")

    # store transformer parameter data #
    # name; r [Ohm/km]; x [Ohm/km]; b [µS/km]; g [µS/km]; iMax [kA] ; vRated [kV]; type #
    if os.path.isfile(gridDataPath + "transformer_types.csv"):
        transformerTypes = pd.read_csv(gridDataPath + "transformer_types.csv", sep=";")
        gridData["transformerTypes"] = transformerTypes
    else:
        gridData["transformerTypes"] = pd.DataFrame()

    # store switch data of an operation point if available #
    # name; busConnected; p [MW]; q [MVAr]
    if os.path.isfile(gridDataPath + "switches.csv"):
        switches = pd.read_csv(gridDataPath + "switches.csv", sep=";")
        gridData["switches"] = switches
    else:
        gridData["switches"] = pd.DataFrame()

    # store load data of an operation point if available #
    # name; busConnected; p [MW]; q [MVAr]
    if os.path.isfile(gridDataPath + "loads.csv"):
        busLoad = pd.read_csv(gridDataPath + "loads.csv", sep=";")
        gridData["loads"] = busLoad
    else:
        gridData["loads"] = pd.DataFrame()

    # store generator data of an operation point if available#
    # name; line; node_i; status (closed, open)
    if os.path.isfile(gridDataPath + "gens.csv"):
        busGen = pd.read_csv(gridDataPath + "gens.csv", sep=";")
        gridData["gens"] = busGen
    else:
        gridData["gens"] = pd.DataFrame()

    gridData["loads"]["name"] = (
        gridData["loads"]["name"]
        .str.replace(".", "")
        .str.replace(" ", "")
        .str.replace("_", "")
    )
    gridData["loads"]["busConnected"] = (
        gridData["loads"]["busConnected"].str.replace(".", "").str.replace(" ", "")
    )
    gridData["gens"]["name"] = (
        gridData["gens"]["name"]
        .str.replace(".", "")
        .str.replace(" ", "")
        .str.replace("_", "")
    )
    gridData["gens"]["busConnected"] = (
        gridData["gens"]["busConnected"].str.replace(".", "").str.replace(" ", "")
    )

    gridData["gridConfig"] = gridConfig
    gridData["busData"] = busData
    gridData["topology"] = topology
    gridData["transformers"] = transformers
    gridData["lineTypes"] = lineTypes

    inputCoordinates(gridDataPath, gridData)

    if os.path.isfile(gridDataPath + "meas_config.csv"):
        inputMeasData(gridDataPath, gridData)
    else:
        gridData["measTopology"] = pd.DataFrame(columns=["type", "node_i", "node_j"])

    inputProfiles(gridDataPath, gridData)

    inputSubstation(gridDataPath, gridData)

    if os.path.isfile(gridDataPath + "SocioEconomic.csv"):
        inputSocioEconomics(gridDataPath, gridData)

    # replace dots and free spaces as such strings are not compatible in external libs
    gridData["busData"]["busName"] = (
        gridData["busData"]["busName"].str.replace(".", "").str.replace(" ", "")
    )
    gridData["gridConfig"]["extGridNode"] = (
        gridData["gridConfig"]["extGridNode"].str.replace(".", "").str.replace(" ", "")
    )
    gridData["topology"]["name"] = (
        gridData["topology"]["name"].str.replace(".", "").str.replace(" ", "")
    )
    gridData["topology"]["node_i"] = (
        gridData["topology"]["node_i"].str.replace(".", "").str.replace(" ", "")
    )
    gridData["topology"]["node_j"] = (
        gridData["topology"]["node_j"].str.replace(".", "").str.replace(" ", "")
    )
    gridData["measTopology"]["node_i"] = (
        gridData["measTopology"]["node_i"].str.replace(".", "").str.replace(" ", "")
    )
    gridData["measTopology"]["node_j"] = (
        gridData["measTopology"]["node_j"].str.replace(".", "").str.replace(" ", "")
    )
    gridData["switches"]["line"] = (
        gridData["switches"]["line"].str.replace(".", "").str.replace(" ", "")
    )
    gridData["switches"]["node_i"] = (
        gridData["switches"]["node_i"].str.replace(".", "").str.replace(" ", "")
    )
    gridData["transformers"]["name"] = (
        gridData["transformers"]["name"].str.replace(".", "").str.replace(" ", "")
    )
    gridData["transformers"]["hvBus"] = (
        gridData["transformers"]["hvBus"].str.replace(".", "").str.replace(" ", "")
    )
    gridData["transformers"]["lvBus"] = (
        gridData["transformers"]["lvBus"].str.replace(".", "").str.replace(" ", "")
    )

    return gridData


def inputCoordinates(gridDataPath, gridData):
    coordinates = pd.DataFrame(columns=["x_coord", "y_coord"])

    coord_file = gridDataPath / "coordinates.csv"

    if coord_file.is_file():
        BusCoord = pd.read_csv(coord_file, sep=";", encoding="latin-1")
        for row in gridData["busData"].iterrows():
            busName = row[1]["busName"]
            match = BusCoord["Bezeichnung"] == busName

            if match.any():
                idx = match.idxmax()
                x_coord = BusCoord.loc[idx, "X_Coord"]
                y_coord = BusCoord.loc[idx, "Y_Coord"]
            else:
                x_coord = None
                y_coord = None

            coordinates = pd.concat(
                [coordinates, pd.DataFrame([{"x_coord": x_coord, "y_coord": y_coord}])],
                ignore_index=True,
            )

    else:
        # fallback plotting if coordinates.csv is missing
        scaling_factor = 2.0
        connections = gridData["topology"][["node_i", "node_j"]].values.tolist()
        connections += gridData["transformers"][["hvBus", "lvBus"]].values.tolist()

        bus_names = {name for conn in connections for name in conn}

        g = Graph()
        vertex_indices = {}
        for bus_name in bus_names:
            v = g.add_vertex(name=bus_name)
            vertex_indices[bus_name] = v.index

        for bus1, bus2 in connections:
            g.add_edge(vertex_indices[bus1], vertex_indices[bus2])

        layout = g.layout_fruchterman_reingold()
        x_coordinates = [coord[0] * scaling_factor for coord in layout.coords]
        y_coordinates = [coord[1] * scaling_factor for coord in layout.coords]

        for row in gridData["busData"].itertuples(index=False):
            bus_i = row.busName
            idx = list(vertex_indices.keys()).index(bus_i) if bus_i in vertex_indices else None
            x_coord = x_coordinates[idx] if idx is not None else None
            y_coord = y_coordinates[idx] if idx is not None else None

            coordinates = pd.concat(
                [coordinates, pd.DataFrame([{"x_coord": x_coord, "y_coord": y_coord}])],
                ignore_index=True,
            )

    gridData["busData"] = gridData["busData"].join(coordinates)



def inputSocioEconomics(gridDataPath, gridData):
    SocioEconomic = pd.read_csv(
        gridDataPath + "SocioEconomic.csv", sep=";", decimal=",", encoding="latin-1"
    )

    gridData["SocioEconomic"] = SocioEconomic


def inputSubstation(gridDataPath, gridData):
    if os.path.isfile(gridDataPath + "topology_substation.csv"):
        substationTopology = pd.read_csv(
            gridDataPath + "topology_substation.csv", sep=";"
        )

        for row in gridData["topology"].iterrows():
            topData_node_i = row[1]["node_i"]
            topData_node_j = row[1]["node_j"]

            subData_i = substationTopology["node_i"] == topData_node_i
            subData_j = substationTopology["node_j"] == topData_node_j

            topsubData = subData_i & subData_j
            index = topsubData[topsubData].index.values[0]

            gridData["topology"]["bay_i"].iloc[row[0]] = substationTopology[
                "bay_i"
            ].iloc[index]
            gridData["topology"]["bay_j"].iloc[row[0]] = substationTopology[
                "bay_j"
            ].iloc[index]

    else:
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
                    k = k + 1
                var_1 = var_1 + 1


# generate profiles from a given csv or results from state estimation stored in a database
def inputProfiles(gridDataPath, gridData):
    if os.path.isfile(gridDataPath + "profiles.csv"):
        timeseries_profiles = pd.read_csv(gridDataPath + "profiles.csv", sep=";")
        gridData["profiles"] = {}

        # build active power profile list
        load_p_mw = pd.DataFrame()
        for load in gridData["loads"].iterrows():
            name = load[1]["name"]
            for data in timeseries_profiles:
                if name in data and "p_mw" in data and name == data.split("_")[0]:
                    # Create a list to hold DataFrames
                    df = [load_p_mw, timeseries_profiles[data]]
                    # Concatenate the list of DataFrames along the rows
                    load_p_mw = pd.concat(df, ignore_index=True)

        # load_p_mw = load_p_mw.drop_duplicates()
        load_p_mw = load_p_mw.T
        load_p_mw.columns = load_p_mw.columns.str.strip("_p_mw")

        for load in gridData["loads"].iterrows():
            name = load[1]["name"]
            var = 0
            for data in load_p_mw:
                if name == data:
                    load_p_mw.rename(
                        columns={load_p_mw.columns[var]: load[0]}, inplace=True
                    )
                var = var + 1

        # build reactive power profile list
        load_q_mvar = pd.DataFrame()
        for load in gridData["loads"].iterrows():
            name = load[1]["name"]
            for data in timeseries_profiles:
                if name in data and "q_mvar" in data and name == data.split("_")[0]:
                    # Create a list to hold DataFrames
                    df = [load_q_mvar, timeseries_profiles[data]]
                    # Concatenate the list of DataFrames along the rows
                    load_p_mvar = pd.concat(df, ignore_index=True)
        # load_q_mvar = load_q_mvar.drop_duplicates()
        load_q_mvar = load_q_mvar.T
        load_q_mvar.columns = load_q_mvar.columns.str.strip("_q_mvar")

        for load in gridData["loads"].iterrows():
            name = load[1]["name"]
            var = 0
            for data in load_q_mvar:
                if name == data:
                    load_q_mvar.rename(
                        columns={load_q_mvar.columns[var]: load[0]}, inplace=True
                    )
                var = var + 1

        # build active power profile list for static generators
        gen_p_mw = pd.DataFrame()
        for gen in gridData["gens"].iterrows():
            name = gen[1]["name"]
            for data in timeseries_profiles:
                if name in data and "p_mw" in data and name == data.split("_")[0]:
                    # Create a list to hold DataFrames
                    df = [gen_p_mw, timeseries_profiles[data]]
                    # Concatenate the list of DataFrames along the rows
                    gen_p_mw = pd.concat(df, ignore_index=True)

        gen_p_mw = gen_p_mw.T
        gen_p_mw.columns = gen_p_mw.columns.str.replace("_p_mw", "")

        for gen in gridData["gens"].iterrows():
            name = gen[1]["name"]
            var = 0
            for data in gen_p_mw:
                if name == data:
                    gen_p_mw.rename(
                        columns={gen_p_mw.columns[var]: gen[0]}, inplace=True
                    )
                var = var + 1

        # build reactive power profile list for static generators
        gen_q_mvar = pd.DataFrame()
        for gen in gridData["gens"].iterrows():
            name = gen[1]["name"]
            for data in timeseries_profiles:
                if name in data and "_q_mvar" in data and name == data.split("_")[0]:
                    # Create a list to hold DataFrames
                    df = [gen_q_mvar, timeseries_profiles[data]]
                    # Concatenate the list of DataFrames along the rows
                    gen_q_mvar = pd.concat(df, ignore_index=True)

        # gen_q_mvar = gen_q_mvar.drop_duplicates()
        gen_q_mvar = gen_q_mvar.T
        gen_q_mvar.columns = gen_q_mvar.columns.str.replace("_q_mvar", "")

        for gen in gridData["gens"].iterrows():
            name = gen[1]["name"]
            var = 0
            for data in gen_q_mvar:
                if name == data:
                    gen_q_mvar.rename(
                        columns={gen_q_mvar.columns[var]: gen[0]}, inplace=True
                    )
                var = var + 1

        # build switching profiles
        switch_bool = pd.DataFrame()
        for switch in gridData["switches"].iterrows():
            name = switch[1]["name"]
            for data in timeseries_profiles:
                if name in data:
                    # Create a list to hold DataFrames
                    df = [switch_bool, timeseries_profiles[data]]
                    # Concatenate the list of DataFrames along the rows
                    switch_bool = pd.concat(df, ignore_index=True)

        switch_bool = switch_bool.loc[~switch_bool.index.duplicated(keep="first")]
        switch_bool = switch_bool.T

        for switch in gridData["switches"].iterrows():
            name = switch[1]["name"]
            var = 0
            for data in switch_bool:
                if name == data:
                    switch_bool.rename(
                        columns={switch_bool.columns[var]: switch[0]}, inplace=True
                    )
                var = var + 1

        # build voltage amplitude for external grids
        ext_grid_pu = pd.DataFrame()
        for extGrid in gridData["gridConfig"].iterrows():
            name = extGrid[1]["extGridNode"]
            for data in timeseries_profiles:
                if name in data and "pu" in data and name == data.split("_")[0]:
                    # Create a list to hold DataFrames
                    df = [ext_grid_pu, timeseries_profiles[data]]
                    # Concatenate the list of DataFrames along the rows
                    ext_grid_pu = pd.concat(df, ignore_index=True)

        ext_grid_pu = ext_grid_pu.T
        ext_grid_pu.columns = ext_grid_pu.columns.str.replace("_pu", "")

        for extGrid in gridData["gridConfig"].iterrows():
            name = extGrid[1]["extGridNode"]
            var = 0
            for data in ext_grid_pu:
                if name == data:
                    ext_grid_pu.rename(
                        columns={ext_grid_pu.columns[var]: extGrid[0]}, inplace=True
                    )
                var = var + 1

        # build voltage angle for external grids
        ext_grid_degree = pd.DataFrame()
        for extGrid in gridData["gridConfig"].iterrows():
            name = extGrid[1]["extGridNode"]
            for data in timeseries_profiles:
                if name in data and "degree" in data and name == data.split("_")[0]:
                    # Create a list to hold DataFrames
                    df = [ext_grid_degree, timeseries_profiles[data]]
                    # Concatenate the list of DataFrames along the rows
                    ext_grid_degree = pd.concat(df, ignore_index=True)

        ext_grid_degree = ext_grid_degree.T
        ext_grid_degree.columns = ext_grid_degree.columns.str.replace("_degree", "")

        for extGrid in gridData["gridConfig"].iterrows():
            name = extGrid[1]["extGridNode"]
            var = 0
            for data in ext_grid_degree:
                if name == data:
                    ext_grid_degree.rename(
                        columns={ext_grid_degree.columns[var]: extGrid[0]}, inplace=True
                    )
                var = var + 1

        gridData["profiles"]["load", "p_mw"] = load_p_mw
        gridData["profiles"]["load", "q_mvar"] = load_q_mvar
        gridData["profiles"]["sgen", "p_mw"] = gen_p_mw
        gridData["profiles"]["sgen", "q_mvar"] = gen_q_mvar
        gridData["profiles"]["switch", "bool"] = switch_bool
        gridData["profiles"]["ext_grid", "vm_pu"] = ext_grid_pu
        gridData["profiles"]["ext_grid", "va_degree"] = ext_grid_degree

    # if results from state estimation are available as a database
    if os.path.isfile(gridDataPath + "se_results.db"):
        conn = sqlite3.connect(gridDataPath + "se_results.db")
        nodeVoltages = pd.DataFrame()
        df = pd.read_sql_query("SELECT * FROM se_results", conn)
        gridData["profiles"] = {}
        load_p_mw = pd.DataFrame()
        load_q_mvar = pd.DataFrame()
        ext_grid_pu = pd.DataFrame()

        for var in df.iterrows():

            for row in gridData["busData"].iterrows():
                name = row[1]["busName"].split("_")[1]
                vm_pu = (
                    float(
                        df.loc[
                            var[0],
                            df.columns.str.contains("Umag")
                            & df.columns.str.contains(name),
                        ]
                    )
                    / (float(gridData["gridConfig"]["vnGrid_kv"]) * 1000)
                    * math.sqrt(3)
                )
                va_degree = float(
                    df.loc[
                        var[0],
                        df.columns.str.contains("Uang") & df.columns.str.contains(name),
                    ]
                )
                nodeVoltages.at[row[0], "vm_pu"] = vm_pu
                nodeVoltages.at[row[0], "va_degree"] = va_degree

            # calculate nodal powers of all buses based on polar coordinate formulas
            Powers = PolPowerCalculation(None, gridData, None, nodeVoltages)

            # build active power profile list
            for load in gridData["loads"].iterrows():
                busConnected = load[1]["busConnected"]
                for data in Powers.iterrows():
                    if busConnected in data[1]["busName"]:
                        load_p_mw.loc[var[0], load[0]] = data[1]["p_mw"]
                        load_q_mvar.loc[var[0], load[0]] = data[1]["q_mvar"]

            # build active power profile list
            for load in gridData["loads"].iterrows():
                busConnected = load[1]["busConnected"]
                for data in Powers.iterrows():
                    if busConnected in data[1]["busName"]:
                        load_p_mw.loc[var[0], load[0]] = data[1]["p_mw"]
                        load_q_mvar.loc[var[0], load[0]] = data[1]["q_mvar"]

            ext_grid_pu.loc[var[0], 0] = (
                float(
                    df.loc[
                        var[0],
                        df.columns.str.contains("Umag")
                        & df.columns.str.contains(
                            str(gridData["gridConfig"]["extGridNode"][0]).split("_")[1]
                        ),
                    ]
                )
                / (float(gridData["gridConfig"]["vnGrid_kv"]) * 1000)
                * math.sqrt(3)
            )

        gridData["profiles"]["load", "p_mw"] = load_p_mw
        gridData["profiles"]["load", "q_mvar"] = load_q_mvar
        gridData["profiles"]["ext_grid", "vm_pu"] = ext_grid_pu
