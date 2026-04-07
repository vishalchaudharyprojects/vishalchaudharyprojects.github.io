# Processing topology and operation data for grid analysis ##
import math
import pandapower as pp
import numpy as np
import pandas as pd


def grid_data_preparation_dynamic(config_data, grid_data):
    # create network
    main_grid = pp.create_empty_network(name=config_data['Aas_config']['grid']['name'], f_hz=50.0, sn_mva=1,
                                        add_stdtypes=True)

    # create buses depending of availibility of geodata
    for row in grid_data['busData'].iterrows():
        bus = row[1]
        pp.create_bus(main_grid, vn_kv=bus['voltageLevel'], name=bus['busName'], max_vm_pu=1.1,
                      min_vm_pu=0.9, in_service=True)

    # create external grid
    for row in grid_data['gridConfig'].iterrows():
        ext_grid = row[1]

        pp.create_ext_grid(main_grid, bus=int(
            grid_data['busData'][grid_data['busData']['busName'].str.fullmatch(ext_grid.extGridNode)].index[0]),
                           vm_pu=1, name=float('nan'),
                           s_sc_max_mva=float('nan'),
                           s_sc_min_mva=float('nan'), rx_max=float('nan'),
                           rx_min=float('nan'))

    # create transformer
    for row in grid_data['transformers'].iterrows():
        transformer = row[1]

        hv_bus = grid_data['busData'][grid_data['busData']['busName'].str.fullmatch(transformer['hvBus'])].index[0]
        lv_bus = grid_data['busData'][grid_data['busData']['busName'].str.fullmatch(transformer['lvBus'])].index[0]
        hv_bus_kv = transformer['hvBus_kv']
        r_ohm = float(
            grid_data['transformerTypes'][grid_data['transformerTypes']['type'].str.fullmatch(transformer['type'])][
                'r_ohm'].values[0])
        x_ohm = float(
            grid_data['transformerTypes'][grid_data['transformerTypes']['type'].str.fullmatch(transformer['type'])][
                'x_ohm'].values[0])
        sn_mva = float(
            grid_data['transformerTypes'][grid_data['transformerTypes']['type'].str.fullmatch(transformer['type'])][
                'sn_mva'].values[0])
        tap_step_percent = float(
            grid_data['transformerTypes'][grid_data['transformerTypes']['type'].str.fullmatch(transformer['type'])][
                'tap_step_percent'].values[0])
        pfe_kw = float(
            grid_data['transformerTypes'][grid_data['transformerTypes']['type'].str.fullmatch(transformer['type'])][
                'pfe_kw'].values[0])
        phase_shift_degree = float(
            grid_data['transformerTypes'][grid_data['transformerTypes']['type'].str.fullmatch(transformer['type'])][
                'phaseShift_degree'].values[0])

        # Calculation of short-circuit voltage and real part of short-circuit voltage
        i_amp = sn_mva * 1000 / (math.sqrt(3) * hv_bus_kv)
        ukr_percent = (math.sqrt(3) * i_amp * r_ohm * 100) / (hv_bus_kv * 1000)
        uk_percent = math.sqrt(3) * i_amp * math.sqrt(r_ohm ** 2 + x_ohm ** 2) * 100 / (hv_bus_kv * 1000)

        pp.create_transformer_from_parameters(main_grid, hv_bus, lv_bus, sn_mva, transformer['hvBus_kv'],
                                              transformer['lvBus_kv'], vkr_percent=ukr_percent,
                                              vk_percent=uk_percent, pfe_kw=pfe_kw, shift_degree=phase_shift_degree,
                                              tap_side="lv", i0_percent=0,
                                              tap_neutral=0, tap_max=0, tap_min=0, tap_step_percent=tap_step_percent,
                                              tap_step_degree=0, tap_pos=transformer['tapPos'], tap_phase_shifter=True,
                                              in_service=True, name=transformer['name'], vector_group=None, index=None,
                                              max_loading_percent=100.0, parallel=1, df=0.02, vk0_percent=0,
                                              vkr0_percent=0, mag0_percent=0, mag0_rx=0, si0_hv_partial=0,
                                              pt_percent=0, oltc=False)

    # create line
    for row in grid_data['topology'].iterrows():
        line = row[1]
        try:
            from_bus = int(grid_data['busData'][grid_data['busData']['busName'].str.fullmatch(line['node_i'])].index[0])
        except IndexError:
            print("No matching bus found.")
            from_bus = None

        to_bus = int(grid_data['busData'][grid_data['busData']['busName'].str.fullmatch(line['node_j'])].index[0])
        length_km = float(line['length_km'])
        type = grid_data['lineTypes'][grid_data['lineTypes']['name'].str.fullmatch(line['type'])]
        try:
            pp.create_line_from_parameters(main_grid, from_bus, to_bus, length_km, type['r_ohm_km'], type['x_ohm_km'],
                                           type['b_miks_km'] * 10 ** 3 / (np.pi * 100),
                                           type['iMax_ka'], name=line['name'], index=None, type=None, geodata=None,
                                           in_service=True,
                                           parallel=line['parallelDevices'], g_us_per_km=type['g_miks_km'],
                                           check_existing=True)
        except IndexError:
            # Handle the case where no match is found
            print("No matching bus found.")
            # from_bus = None

    for row in grid_data['switches'].iterrows():
        switch = row[1]
        bus_connected = int(
            grid_data['busData'][grid_data['busData']['busName'].str.fullmatch(switch['node_i'])].index[0])
        line_connected = int(main_grid['line'][main_grid['line']['name'].str.fullmatch(switch['line'])].index[0])
        status = switch['status']
        if status == "open":
            switch_status = False
        else:
            switch_status = True

        pp.create_switch(main_grid, bus=bus_connected, element=line_connected, closed=switch_status, et='l')

    return main_grid


def measurement_preparation_dynamic(config_data, main_grid, measurement):
    meas_config = measurement.copy()
    # Replaced gridData['measTopology'] with measurement=>measurement is identical, but with values
    meas_data = pd.DataFrame(meas_config['node_i'].unique())

    # Considering measurements from all measured nodes
    for row in meas_config.iterrows():
        type = meas_config['type'].iloc[row[0]]
        node_i = meas_config['node_i'].iloc[row[0]]
        node_j = meas_config['node_j'].iloc[row[0]]
        line_side = None

        if type == 'Ui':
            meas_type = 'v'
            element_type = 'bus'
            element = int(main_grid.bus[main_grid.bus['name'].str.fullmatch(node_i)].index[0])
            value = float(measurement.iloc[row[0]]['value'])
            meas_config['node_j'].iloc[row[0]] = ''
            meas_config['node_i'].iloc[row[0]] = element

        elif type == 'Pi':
            meas_type = 'p'
            element_type = 'bus'
            element = int(main_grid.bus[main_grid.bus['name'].str.fullmatch(node_i)].index[0])
            value = float(measurement.iloc[row[0]]['value'])
            meas_config['node_j'].iloc[row[0]] = ''
            meas_config['node_i'].iloc[row[0]] = element

        elif type == 'Qi':
            meas_type = 'q'
            element_type = 'bus'
            element = int(main_grid.bus[main_grid.bus['name'].str.fullmatch(node_i)].index[0])
            value = float(measurement.iloc[row[0]]['value'])
            meas_config['node_j'].iloc[row[0]] = ''
            meas_config['node_i'].iloc[row[0]] = element

        elif type == 'Pij':
            meas_type = 'p'
            node_i = int(main_grid.bus[main_grid.bus['name'].str.fullmatch(node_i)].index[0])
            node_j = int(main_grid.bus[main_grid.bus['name'].str.fullmatch(node_j)].index[0])
            meas_config['node_i'].iloc[row[0]] = node_i
            meas_config['node_j'].iloc[row[0]] = node_j

            index_node_i = main_grid.line['from_bus'] == node_i
            index_node_j = main_grid.line['to_bus'] == node_j
            line_index_ij = index_node_i & index_node_j

            index_node_i = main_grid.line['to_bus'] == node_i
            index_node_j = main_grid.line['from_bus'] == node_j
            line_index_ji = index_node_i & index_node_j

            index_trafo_node_i = main_grid['trafo']['hv_bus'] == node_i
            index_trafo_node_j = main_grid['trafo']['lv_bus'] == node_j
            trafo_index_ij = index_trafo_node_i & index_trafo_node_j

            index_trafo_node_i = main_grid['trafo']['lv_bus'] == node_i
            index_trafo_node_j = main_grid['trafo']['hv_bus'] == node_j
            trafo_index_ji = index_trafo_node_i & index_trafo_node_j

            if line_index_ij.any():
                element = line_index_ij[line_index_ij].index.values[0]
                value = float(measurement.iloc[row[0]]['value'])
                element_type = 'line'

            if line_index_ji.any():
                element = line_index_ji[line_index_ji].index.values[0]
                value = float(measurement.iloc[row[0]]['value'])
                element_type = 'line'

            if trafo_index_ij.any():
                element = trafo_index_ij[trafo_index_ij].index.values[0]
                value = float(measurement.iloc[row[0]]['value'])
                element_type = 'trafo'

            if trafo_index_ji.any():
                element = trafo_index_ji[trafo_index_ji].index.values[0]
                value = float(measurement.iloc[row[0]]['value'])
                element_type = 'trafo'

            line_side = node_i

        elif type == 'Qij':
            meas_type = 'q'
            node_i = int(main_grid.bus[main_grid.bus['name'].str.fullmatch(node_i)].index[0])
            node_j = int(main_grid.bus[main_grid.bus['name'].str.fullmatch(node_j)].index[0])
            meas_config['node_i'].iloc[row[0]] = node_i
            meas_config['node_j'].iloc[row[0]] = node_j

            index_node_i = main_grid.line['from_bus'] == node_i
            index_node_j = main_grid.line['to_bus'] == node_j
            line_index_ij = index_node_i & index_node_j

            index_node_i = main_grid.line['to_bus'] == node_i
            index_node_j = main_grid.line['from_bus'] == node_j
            line_index_ji = index_node_i & index_node_j

            index_trafo_node_i = main_grid['trafo']['hv_bus'] == node_i
            index_trafo_node_j = main_grid['trafo']['lv_bus'] == node_j
            trafo_index_ij = index_trafo_node_i & index_trafo_node_j

            index_trafo_node_i = main_grid['trafo']['lv_bus'] == node_i
            index_trafo_node_j = main_grid['trafo']['hv_bus'] == node_j
            trafo_index_ji = index_trafo_node_i & index_trafo_node_j

            if line_index_ij.any():
                element = line_index_ij[line_index_ij].index.values[0]
                value = float(measurement.iloc[row[0]]['value'])
                element_type = 'line'

            if line_index_ji.any():
                element = line_index_ji[line_index_ji].index.values[0]
                value = float(measurement.iloc[row[0]]['value'])
                element_type = 'line'

            if trafo_index_ij.any():
                element = trafo_index_ij[trafo_index_ij].index.values[0]
                value = float(measurement.iloc[row[0]]['value'])
                element_type = 'trafo'

            if trafo_index_ji.any():
                element = trafo_index_ji[trafo_index_ji].index.values[0]
                value = float(measurement.iloc[row[0]]['value'])
                element_type = 'trafo'

            line_side = node_i

        pp.create.create_measurement(main_grid, meas_type, element_type, value, 0.00000001, element, side=line_side,
                                     check_existing=True)

    for row in main_grid.bus.iterrows():
        if config_data['Aas_config']['grid']['auxiliary_nodes'] in main_grid.bus['name'].iloc[row[0]] and \
                (main_grid.bus['in_service'].iloc[row[0]] is True
                 and 'EL' not in main_grid.bus['name'].iloc[row[0]]):
            element_type = 'bus'
            value = float(0.0)
            element = int(
                main_grid.bus[main_grid.bus['name'].str.fullmatch(main_grid.bus['name'].iloc[row[0]])].index[0])

            meas_type = 'p'
            pp.create.create_measurement(main_grid, meas_type, element_type, value, 0.0000001, element, side=None,
                                         check_existing=True)

            meas_type = 'q'
            pp.create.create_measurement(main_grid, meas_type, element_type, value, 0.00000001, element, side=None,
                                         check_existing=True)

    return meas_data
