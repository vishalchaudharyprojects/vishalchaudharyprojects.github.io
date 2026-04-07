# This module serves to save the data from the MMXU element to a CSV file.
from grid_measurements.src.connector.Smart_grid.libs.IEC_61850.iec_61850_ln import MMXU
import os
import pandas as pd


def taf10_mmxu_to_csv(mmxu: MMXU, filepath: str, filename: str):
    """
    This function takes the attributes,
    quality and timestamp of an mmxu including TAF10 data
    and writes it into a csv file

    :param mmxu: Logical node object of a MMXU
    :param filepath: Path where the csv file is to be saved
    :param filename: Name of the csv file containing the output

    Returns: None
    """
    # Step 1: Check if the output document already exists. If not, create it
    file = os.path.join(filepath, filename)
    # Define the columns for the DataFrame
    columns = ['Timestamp', 'Quality', 'Frequency',
               'V_L1N', 'V_L2N','V_L3N',
               'I_L1', 'I_L2', 'I_L3',
               'Arg_I1_V1N', 'Arg_I2_V2N', 'Arg_I3_V3N',
               'P_L1', 'P_L2', 'P_L3','P_3phs']

    if not os.path.exists(file):
        mmxu_df_empty = pd.DataFrame(columns = columns)
        mmxu_df_empty.to_csv(file, index=False)

    # Step 2: Read the existing file
    try:
        mmxu_df = pd.read_csv(file)
    except Exception as e:
        print(f"Error {e} file could not be read. "
              "Please check the file format (csv) and its columns")
        return

    # Check if the columns are already present in the file
    for column in columns:
        if column not in mmxu_df.columns:
            mmxu_df[column] = None

    # Step 3: Append the data to the file
    timestamp = mmxu.DO['PhV'].SDO['phsA'].SDO["t"].DA["seconds"]
    quality = mmxu.DO['PhV'].SDO['phsA'].SDO["q"].DA["validity"]
    frequency = mmxu.DO['Hz'].SDO["mag"].DA["f"]
    v_l1n = mmxu.DO['PhV'].SDO['phsA'].SDO['cVal'].SDO2["mag"].DA["f"]
    v_l2n = mmxu.DO['PhV'].SDO['phsB'].SDO['cVal'].SDO2["mag"].DA["f"]
    v_l3n = mmxu.DO['PhV'].SDO['phsC'].SDO['cVal'].SDO2["mag"].DA["f"]
    i_l1 = mmxu.DO['A'].SDO['phsA'].SDO['cVal'].SDO2["mag"].DA["f"]
    i_l2 = mmxu.DO['A'].SDO['phsB'].SDO['cVal'].SDO2["mag"].DA["f"]
    i_l3 = mmxu.DO['A'].SDO['phsC'].SDO['cVal'].SDO2["mag"].DA["f"]
    phi_i_l1_v_l1n = mmxu.DO['A'].SDO['phsA'].SDO['cVal'].SDO2["ang"].DA["f"]
    phi_i_l2_v_l2n = mmxu.DO['A'].SDO['phsB'].SDO['cVal'].SDO2["ang"].DA["f"]
    phi_i_l3_v_l3n = mmxu.DO['A'].SDO['phsC'].SDO['cVal'].SDO2["ang"].DA["f"]
    p_l1 = mmxu.DO['W'].SDO['phsA'].SDO['cVal'].SDO2["mag"].DA["f"]
    p_l2 = mmxu.DO['W'].SDO['phsB'].SDO['cVal'].SDO2["mag"].DA["f"]
    p_l3 = mmxu.DO['W'].SDO['phsC'].SDO['cVal'].SDO2["mag"].DA["f"]
    p_3phs = mmxu.DO['TotW'].SDO['mag'].DA['f']

    # Step 4: Add the data to the dataframe and save it in the csv file
    new_row = pd.DataFrame([{'Timestamp': timestamp, 'Quality': quality, 'Frequency': frequency, 'V_L1N': v_l1n,
                             'V_L2N': v_l2n, 'V_L3N': v_l3n, 'I_L1': i_l1, 'I_L2': i_l2,
                             'I_L3': i_l3, 'Arg_I1_V1N': phi_i_l1_v_l1n,
                             'Arg_I2_V2N': phi_i_l2_v_l2n, 'Arg_I3_V3N': phi_i_l3_v_l3n, 'P_L1': p_l1, 'P_L2': p_l2, 'P_L3': p_l3, 'P_3phs': p_3phs}])
    mmxu_df = pd.concat([mmxu_df, new_row], ignore_index=True)

    mmxu_df.to_csv(file, index=False)

    return None



