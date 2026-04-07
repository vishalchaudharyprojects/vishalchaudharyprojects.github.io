## Processing topology and operation data for grid analysis ##
import pandapower as pp
import numpy as np
import pandas as pd
import math as mt
import cmath


def CartPowerCalculation(input, gridData, mainGrid, voltages):

    # based on pandapower: no/yes calculate the admittance matrix (nodes in results need to have the same order!!)
    if input == "application" or input == None:
        Yij = calculateYbus(gridData)  # in pu und karth. Koordinaten
        node = pd.DataFrame(gridData["busData"]["busName"])
    elif input == "simulation":
        # Ybus mit Pandapower makeYbus
        Yij1 = pp.makeYbus_pypower(
            float(gridData["gridConfig"]["sbGrid_mva"]),
            mainGrid._ppc["bus"],
            mainGrid._ppc["branch"],
        )  # in pu und karth. Koordinaten
        Yij = Yij1[0].toarray(order=None, out=None)
        node = mainGrid.bus["name"]
    else:
        return print(
            "Error: " + "No valid configuration for Ybus in config file found!"
        )

    Ui = np.zeros(len(voltages.index), dtype=complex)
    for i in range(0, len(voltages.index)):
        Ui[i] = cmath.rect(
            voltages["vm_pu"][i], np.deg2rad(voltages["va_degree"][i])
        )  # Ui in karth. Koordinaten transformieren

    Pi_mw = np.zeros(shape=len(voltages.index))
    Qi_mvar = np.zeros(shape=len(voltages.index))

    for i in range(0, len(voltages.index)):
        for j in range(0, len(voltages.index)):  # auch ii ???????????????????????
            Pi_mw[i] = (
                Pi_mw[i]
                + Ui[i].real
                * (Ui[j].real * Yij[i, j].real - Ui[j].imag * Yij[i, j].imag)
                + Ui[i].imag
                * (Ui[j].imag * Yij[i, j].real + Ui[j].real * Yij[i, j].imag)
            )
            Qi_mvar[i] = (
                Qi_mvar[i]
                + Ui[i].imag
                * (Ui[j].real * Yij[i, j].real - Ui[j].imag * Yij[i, j].imag)
                - Ui[i].real
                * (Ui[j].imag * Yij[i, j].real + Ui[j].real * Yij[i, j].imag)
            )

    Sb = float(gridData["gridConfig"]["sbGrid_mva"])

    # Consumer Count Arrow System: positive= consumption, inductive consumption: negative= generation, inductive provision
    Pi_mw = Pi_mw * Sb * -1
    Qi_mvar = Qi_mvar * Sb * -1

    Pi_mw = pd.DataFrame(Pi_mw, columns=["p_mw"])
    Qi_mvar = pd.DataFrame(Qi_mvar, columns=["q_mvar"])

    powers = pd.concat([node, Pi_mw, Qi_mvar], axis=1)

    return powers


def PolPowerCalculation(
    input, gridData, mainGrid, voltages
):  # in PolarKoordinaten aber yij in karth. und pu

    # based on pandapower: no/yes calculate the admittance matrix (nodes in results need to have the same order!!)
    if input == "application" or input == None:
        Yij = calculateYbus(gridData)  # in pu und karth. Koordinaten
        node = pd.DataFrame(gridData["busData"]["busName"])
    elif input == "simulation":
        # Ybus mit Pandapower makeYbus
        Yij1 = pp.makeYbus_pypower(
            float(gridData["gridConfig"]["sbGrid_mva"]),
            mainGrid._ppc["bus"],
            mainGrid._ppc["branch"],
        )  # in pu und karth. Koordinaten
        Yij = Yij1[0].toarray(order=None, out=None)
        node = mainGrid.bus["name"]
    else:
        return print(
            "Error: " + "No valid configuration for Ybus in config file found!"
        )

    # Ybus in polarkoordinaten elementweise transformieren
    Yij_abs = np.zeros((len(Yij), len(Yij)))
    Yij_angle = np.zeros((len(Yij), len(Yij)))
    for i in range(0, len(Yij)):
        for j in range(0, len(Yij)):
            Yij_abs[i, j] = cmath.polar(Yij[i, j])[0]
            Yij_angle[i, j] = cmath.polar(Yij[i, j])[1]

    Pi_mw = np.zeros(shape=len(voltages.index))
    Qi_mvar = np.zeros(shape=len(voltages.index))
    for i in range(0, len(voltages.index)):
        for j in range(0, len(voltages.index)):  # auch ii ???????????????????????
            Pi_mw[i] = Pi_mw[i] + voltages["vm_pu"][i] * voltages["vm_pu"][j] * Yij_abs[
                i, j
            ] * mt.cos(
                np.deg2rad(voltages["va_degree"][i])
                - np.deg2rad(voltages["va_degree"][j])
                - Yij_angle[i, j]
            )
            Qi_mvar[i] = Qi_mvar[i] + voltages["vm_pu"][i] * voltages["vm_pu"][
                j
            ] * Yij_abs[i, j] * mt.sin(
                np.deg2rad(voltages["va_degree"][i])
                - np.deg2rad(voltages["va_degree"][j])
                - Yij_angle[i, j]
            )

    Sb = float(gridData["gridConfig"]["sbGrid_mva"])

    # Consumer Count Arrow System: positive= consumption, inductive consumption: negative= generation, inductive provision
    Pi_mw = Pi_mw * Sb * -1
    Qi_mvar = Qi_mvar * Sb * -1

    Pi_mw = pd.DataFrame(Pi_mw, columns=["p_mw"])
    Qi_mvar = pd.DataFrame(Qi_mvar, columns=["q_mvar"])

    powers = pd.concat([node, Pi_mw, Qi_mvar], axis=1)

    return powers


def UriPowerCalculation(input, gridData, mainGrid, voltages):

    # based on pandapower: no/yes calculate the admittance matrix (nodes in results need to have the same order!!)
    if input == "application" or input == None:
        Yij = calculateYbus(gridData)  # in pu und karth. Koordinaten
        node = pd.DataFrame(gridData["busData"]["busName"])
    elif input == "simulation":
        # Ybus mit Pandapower makeYbus
        Yij1 = pp.makeYbus_pypower(
            float(gridData["gridConfig"]["sbGrid_mva"]),
            mainGrid._ppc["bus"],
            mainGrid._ppc["branch"],
        )  # in pu und karth. Koordinaten
        Yij = Yij1[0].toarray(order=None, out=None)
        node = mainGrid.bus["name"]
    else:
        return print(
            "Error: " + "No valid configuration for Ybus in config file found!"
        )

    Ui = np.zeros(len(voltages.index), dtype=complex)  # komplex pu und kartheisch!
    for i in range(0, len(voltages.index)):
        Ui[i] = cmath.rect(voltages["vm_pu"][i], np.deg2rad(voltages["va_degree"][i]))

    Ii = np.zeros(len(voltages.index), dtype=complex)  # komplex pu und kartheisch!
    Ii = Yij.dot(Ui)
    Ii = np.conjugate(Ii)

    Si = np.zeros(len(voltages.index), dtype=complex)  # komplex pu und kartheisch!
    for i in range(0, len(Si)):
        Si[i] = Ui[i] * Ii[i]

    Sb = float(gridData["gridConfig"]["sbGrid_mva"])

    Pi_mw = Si.real
    Qi_mvar = Si.imag

    Pi_mw = Pi_mw * Sb * -1
    Qi_mvar = Qi_mvar * Sb * -1

    Pi_mw = pd.DataFrame(Pi_mw, columns=["p_mw"])
    Qi_mvar = pd.DataFrame(Qi_mvar, columns=["q_mvar"])

    powers = pd.concat([node, Pi_mw, Qi_mvar], axis=1)

    return powers


# Die beiden Ansätze liefern das gleiche Ergebnis!: mainGrid berücksichtigt Trafo!, gridData auch
def calculateLosses(gridData, mainGrid, ResultsMeasure, Ybus):
    # U aus ResultsMeasure in pu (PF oder Measure geladen)  in komplexen Vektor cmath und numpy array
    Ub = float(gridData["gridConfig"]["ubLV_kv"])
    Sb = float(gridData["gridConfig"]["sbGrid_mva"])
    Zb = Ub**2 / Sb

    if (
        mainGrid == None or Ybus == "gridData"
    ):  # Yij hat mit Knotenadmittanzmatrix erstmal nichts zu tun! Ansatz: Leitungen durchlaufen! Yij wird nicht gebraucht!
        Ui = np.zeros(
            len(ResultsMeasure.index), dtype=complex
        )  # komplex pu und kartheisch!
        for i in range(0, len(ResultsMeasure.index)):
            Ui[i] = cmath.rect(
                ResultsMeasure["vm_pu"][i], np.deg2rad(ResultsMeasure["va_degree"][i])
            )

        # hier Verluste selber berechnen für jede Leitung nacheinadner! (komplex pu und kartheisch!) Elementweise! -> gridData['topology'] durchgehen!
        lines = gridData["topology"]
        types = gridData["lineTypes"]

        lines = lines.merge(right=types, how="left", left_on="type", right_on="name")
        indxBus = gridData["busData"][["busName"]]

        Sij = np.zeros(len(lines.index), dtype=complex)  # komplex pu und kartheisch!
        Sji = np.zeros(len(lines.index), dtype=complex)  # komplex pu und kartheisch!

        for row in range(
            0, len(lines.index)
        ):  # ToDo: Schaltzustände ->  Leitung auslassen! Implementierung einfach -> if! in gridData vorher!
            line = lines.loc[row, :]
            Z = complex(
                line["r_ohm_km"] * line["length_km"],
                line["x_ohm_km"] * line["length_km"],
            )
            Z = Z / Zb  # nun in pu
            Yij = 1 / Z
            node_i = np.where(indxBus == line["node_i"])[0]
            node_j = np.where(indxBus == line["node_j"])[0]
            Yi0 = complex(
                (line["g_miks_km"] / 2) * line["length_km"] * (10**-6),
                (line["b_miks_km"] / 2) * line["length_km"] * (10**-6),
            )  # auch 0!
            Yi0 = Yi0 * Zb
            Yj0 = complex(
                (line["g_miks_km"] / 2) * line["length_km"] * (10**-6),
                (line["b_miks_km"] / 2) * line["length_km"] * (10**-6),
            )  # auch 0!
            Yj0 = Yj0 * Zb

            Sij[row] = np.conjugate(
                np.conjugate(Ui[node_i]) * (Ui[node_i] - Ui[node_j]) * Yij
                + (cmath.polar(Ui[node_i])[0] ** 2) * Yi0
            )
            Sji[row] = np.conjugate(
                np.conjugate(Ui[node_j]) * (Ui[node_j] - Ui[node_i]) * Yij
                + (cmath.polar(Ui[node_j])[0] ** 2) * Yj0
            )
        # ToDo: sqrt(3) ???????????????????????
        Sv = Sij + Sji

        Sv = Sv * Sb

        Pv = Sv.real  # mw
        Qv = Sv.imag  # mvar

        Pvges = np.sum(Pv)
        Qvges = np.sum(Qv)

    elif Ybus == "mainGrid":
        # hier Verluste aus mainGrid nutzen! Lines und Trafos!
        # Vektor über gridData und topology
        Pv = np.zeros(
            len(mainGrid["res_line"]["pl_mw"].index)
            + len(mainGrid["res_trafo"]["pl_mw"].index)
        )  # in pu
        Qv = np.zeros(
            len(mainGrid["res_line"]["ql_mvar"].index)
            + len(mainGrid["res_trafo"]["ql_mvar"].index)
        )  # in pu
        for i in range(0, len(mainGrid["res_line"]["pl_mw"].index)):
            Pv[i] = mainGrid["res_line"]["pl_mw"][i]
            Qv[i] = mainGrid["res_line"]["ql_mvar"][i]
        for i in range(
            len(mainGrid["res_line"]["pl_mw"].index) + 1,
            len(mainGrid["res_line"]["pl_mw"].index)
            + len(mainGrid["res_trafo"]["pl_mw"].index),
        ):
            Pv[i] = mainGrid["res_trafo"]["pl_mw"][i]
            Qv[i] = mainGrid["res_trafo"]["ql_mvar"][i]

        Pvges = np.sum(Pv)
        Qvges = np.sum(Qv)

    else:
        return print(
            "Error: " + "No valid configuration for Ybus in config file found!"
        )

    return Pv, Qv, Pvges, Qvges


def calculateIijIji(
    gridData, ResultsMeasure
):  # Iij und Iji immer über l definieren! in pu!
    # U aus ResultsMeasure in pu (PF oder Measure geladen)  in komplexen Vektor cmath und numpy array
    Ub = float(gridData["gridConfig"]["ubLV_kv"])
    Sb = float(gridData["gridConfig"]["sbGrid_mva"])
    Zb = Ub**2 / Sb

    Ui = np.zeros(
        len(ResultsMeasure.index), dtype=complex
    )  # komplex pu und kartheisch!
    for i in range(0, len(ResultsMeasure.index)):
        Ui[i] = cmath.rect(
            ResultsMeasure["vm_pu"][i], np.deg2rad(ResultsMeasure["va_degree"][i])
        )

    # hier Verluste selber berechnen für jede Leitung nacheinadner! (komplex pu und kartheisch!) Elementweise! -> gridData['topology'] durchgehen!
    lines = gridData["topology"]
    types = gridData["lineTypes"]

    lines = lines.merge(right=types, how="left", left_on="type", right_on="name")
    indxBus = gridData["busData"][["busName"]]

    Iij = np.zeros(len(lines.index), dtype=complex)  # komplex pu und kartheisch!
    Iji = np.zeros(len(lines.index), dtype=complex)  # komplex pu und kartheisch!

    for row in range(0, len(lines.index)):
        line = lines.loc[row, :]
        Z = complex(
            line["r_ohm_km"] * line["length_km"], line["x_ohm_km"] * line["length_km"]
        )
        Z = Z / Zb  # nun in pu
        Yij = 1 / Z
        node_i = np.where(indxBus == line["node_i"])[0]
        node_j = np.where(indxBus == line["node_j"])[0]
        Yi0 = complex(
            (line["g_miks_km"] / 2) * line["length_km"] * (10**-6),
            (line["b_miks_km"] / 2) * line["length_km"] * (10**-6),
        )  # auch 0!
        Yi0 = Yi0 * Zb
        Yj0 = complex(
            (line["g_miks_km"] / 2) * line["length_km"] * (10**-6),
            (line["b_miks_km"] / 2) * line["length_km"] * (10**-6),
        )  # auch 0!
        Yj0 = Yj0 * Zb

        # Iij und Iji in pu!
        Iij[row] = (Ui[node_i] - Ui[node_j]) * Yij + Ui[
            node_i
        ] * Yi0  # ToDo: sqrt(3) ???????????????????????
        Iji[row] = (Ui[node_j] - Ui[node_i]) * Yij + Ui[node_j] * Yj0

    return Iij, Iji
