from pandapower.estimation.state_estimation import *
from .InitMeasurementData import *
import numpy as np
import time
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set to DEBUG for more verbose logs
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("grid_analysis.log"),  # Log to a file
        logging.StreamHandler()  # Also log to console
    ]
)


def power_flow_calculation(config_data, main_grid, server):
    try:
        logging.info("Starting power flow calculation.")
        while True:
            pp.runpp(main_grid, calculate_voltage_angles=config_data['Aas_config']['application']['powerflow'][
                'calculate_voltage_angles'],
                     max_iteration=config_data['Aas_config']['application']['powerflow']['max_iteration'],
                     tolerance_mva=float(config_data['Aas_config']['application']['powerflow']['tolerance_mva']))

            logging.info("Power flow calculation completed.")

            results = calculation_results(config_data, main_grid)
            logging.info("Results of power flow calculation obtained.")

            # Broadcasting results via the configured protocol
            if config_data['Aas_config']['communication']['input']['protocol'] == 'influxdb':
                write_pf_to_influx_db(results, server)

            if config_data['Aas_config']['communication']['output'] == 'influxdb':
                read_results_from_influx_db(server, config_data)

            time.sleep(config_data['Aas_config']['communication']['runtime_sec'])
    except Exception as e:
        logging.error(f"An error occurred during PowerFlowCalculation: {e}", exc_info=True)
        raise


def state_estimation(config_data, grid_data, main_grid, server):
    try:
        logging.info("Starting the application State Estimation.")
        while True:
            measurement_data = init_measurements(grid_data, config_data, server)
            logging.info("Measurement data for state estimation retrieved.")

            measurement_preparation_dynamic(config_data, main_grid, measurement_data)
            logging.info("Measurement data for the state estimation prepared.")

            tolerance = float(config_data['Aas_config']['application']['stateestimation']['tolerance'])
            max_iterations = config_data['Aas_config']['application']['stateestimation']['max_iteration']

            estimate(main_grid, algorithm='wls', init="flat", tolerance=tolerance, maximum_iterations=max_iterations)
            logging.info("State estimation completed.")

            results = calculation_results(config_data, main_grid)
            logging.info("Results of state estimation obtained.")

            if config_data['Aas_config']['communication']['output'] == 'influxdb':
                write_se_to_influx_db(results, server)

            time.sleep(config_data['Aas_config']['communication']['runtime_sec'])
    except Exception as e:
        logging.error(f"An error occurred during StateEstimation: {e}", exc_info=True)
        raise


def calculation_results(config_data, main_grid):
    try:
        logging.info("Processing calculation results.")
        if config_data['Aas_config']['module']['function'] == 'se':
            branch_powers = pd.concat([main_grid.line[['from_bus', 'to_bus']],
                                       main_grid.res_line_est[['p_from_mw', 'q_from_mvar', 'p_to_mw', 'q_to_mvar']]],
                                      axis=1)
            trafo_power = pd.concat([main_grid.trafo[['hv_bus', 'lv_bus']],
                                     main_grid.res_trafo_est[['p_hv_mw', 'q_hv_mvar', 'p_lv_mw', 'q_lv_mvar']]], axis=1)
        elif config_data['Aas_config']['module']['function'] == 'pf':
            branch_powers = pd.concat([main_grid.line[['from_bus', 'to_bus']],
                                      main_grid.res_line[['p_from_mw', 'q_from_mvar', 'p_to_mw', 'q_to_mvar']]], axis=1)
            trafo_power = pd.concat([main_grid.trafo[['hv_bus', 'lv_bus']],
                                     main_grid.res_trafo[['p_hv_mw', 'q_hv_mvar', 'p_lv_mw', 'q_lv_mvar']]], axis=1)
        else:
            raise ValueError(f"Unexpected function: {config_data['Aas_config']['module']['function']}")

        # Combine power flows into one dataframe
        line_from_powers = pd.DataFrame(np.concatenate((trafo_power.values, branch_powers.values), axis=0)).iloc[:, 0:4]
        line_to_powers = pd.DataFrame(np.concatenate((trafo_power.values, branch_powers.values), axis=0))[[1, 0, 4, 5]]
        line_powers = pd.DataFrame(np.concatenate((line_from_powers.values, line_to_powers.values), axis=0),
                                   columns=['node_i', 'node_j', 'pij_mw', 'qij_mvar'])

        for index, row in line_powers.iterrows():
            line_powers.at[index, 'node_i'] = main_grid['bus']['name'].iloc[int(line_powers.at[index, 'node_i'])]
            line_powers.at[index, 'node_j'] = main_grid['bus']['name'].iloc[int(line_powers.at[index, 'node_j'])]

        if config_data['Aas_config']['module']['function'] == 'se':
            results = {
                'nodeVoltagesSE': pd.concat([main_grid.bus['name'], main_grid.res_bus_est[['vm_pu', 'va_degree']]],
                                            axis=1),
                'nodePowersSE': pd.concat([main_grid.bus['name'], main_grid.res_bus_est[['p_mw', 'q_mvar']]], axis=1),
                'linePowersSE': line_powers
            }
        elif config_data['Aas_config']['module']['function'] == 'pf':
            results = {
                'nodeVoltagesPF': pd.concat([main_grid.bus['name'], main_grid.res_bus[['vm_pu', 'va_degree']]], axis=1),
                'nodePowersPF': pd.concat([main_grid.bus['name'], main_grid.res_bus[['p_mw', 'q_mvar']]], axis=1),
                'linePowersPF': line_powers
            }
        else:
            raise ValueError(f"Unexpected function: {config_data['Aas_config']['module']['function']}")

        logging.info("Calculation results successfully processed.")
        return results
    except Exception as e:
        logging.error(f"An error occurred during CalculationResults: {e}", exc_info=True)
        raise
