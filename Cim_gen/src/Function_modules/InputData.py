from pathlib import Path
import yaml
import pandas as pd
from Cim_gen.src.Function_modules.InputDataCIM import inputGridData


def get_data(config_path):
    config_path = Path(config_path).resolve()
    config_data = yaml.safe_load(open(config_path))

    grid_data = {
        'gridConfig': pd.DataFrame(),
        'busData': pd.DataFrame(),
        'topology': pd.DataFrame(),
        'lineTypes': pd.DataFrame(),
        'loads': pd.DataFrame(),
        'gens': pd.DataFrame(),
        'measTopology': pd.DataFrame(),
        'switches': pd.DataFrame()
    }

    if 'cim' in config_data['Cim_gen']['grid']['input_dataformat']:
        grid_data, cimpy_results = inputGridData(config_data, grid_data)
    else:
        print("Error: No valid grid data format in config file!")
        grid_data = 'Error - no grid data'
        cimpy_results = 'Error - no CIM_Orig data'

    return config_data, grid_data, cimpy_results

