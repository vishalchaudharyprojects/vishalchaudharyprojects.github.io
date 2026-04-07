import pandas as pd
import logging
import time
from influxdb_client import Point, WritePrecision


def get_measurement_data_influxdb(server, config_data):
    """
    Retrieve and process measurement data from an InfluxDB instance for power grid analysis.

    This function queries the InfluxDB database to fetch the latest line power flow data
    (Pij and Qij) for a specified grid. It filters the data based on a specified time range,
    extracts relevant fields like node names and power values, and formats them into a pandas
    DataFrame. The DataFrame contains columns representing the type of measurement (Pij or Qij),
    the "from" node, the "to" node, and the corresponding power flow value.

    Parameters:
    - server: Dictionary containing the InfluxDB connection details, including:
        - influxdb_client: The InfluxDB client object.
        - bucket: The name of the InfluxDB bucket to query.
        - grid_name: The name of the grid for which data is being queried.
    - ConfigData: Configuration data containing parameters for querying InfluxDB,
      including the time range for the query and the instance number.

    Returns:
    - A pandas DataFrame with columns ['type', 'node_i', 'node_j', 'value'] containing the latest
      power flow data (Pij, Qij). If no data is found, returns an empty DataFrame.
    """
    try:
        logging.info("Starting to retrieve measurement data from InfluxDB.")

        client = server.get('influxdb_client')
        bucket = server.get('bucket')
        grid_name = server.get('grid_name')

        if not client or not bucket or not grid_name:
            logging.error("InfluxDB client, bucket, or grid name missing from server configuration.")
            return pd.DataFrame(columns=['type', 'node_i', 'node_j', 'value'])

        logging.info(f"InfluxDB query for grid: {grid_name} with bucket: {bucket}")

        query_api = client.query_api()
        range_duration = config_data['Aas_config']['application']['range']

        # Get the instance number from the configuration
        instance = config_data['Aas_config']['services']['stateestimation']['instance']

        # Define the InfluxDB query to retrieve 'LinePowerFlow' measurement data
        query = f'''
        from(bucket: "{bucket}")
            |> range(start: -{range_duration})  // Time range for the query
            |> filter(fn: (r) => r._measurement == "LinePowerFlow")  // Filter by measurement type
            |> filter(fn: (r) => r.grid_name == "{grid_name}")  // Filter by grid name
            |> filter(fn: (r) => r.from_node != "" and r.to_node != "")  // Exclude empty node names
            |> sort(columns: ["_time"], desc: true)  // Sort by time in descending order
            |> limit(n: {instance})  // Limit the number of results to the specified instance
        '''

        # Execute the query and retrieve the data as tables
        tables = query_api.query(query)
        records_to_add = []  # List to store records

        # Loop through each table and extract relevant records
        for table in tables:
            for record in table.records:
                from_node = record.values.get('from_node', None)
                to_node = record.values.get('to_node', None)

                field_name = record.get_field() if hasattr(record, 'get_field') else None
                value = record.get_value() if hasattr(record, 'get_value') else None

                if field_name in ['pij_mw', 'qij_mvar']:
                    if isinstance(value, (int, float)):  # Ensure the value is numeric
                        measurement_type = 'Pij' if field_name == 'pij_mw' else 'Qij'
                        records_to_add.append(
                            {'type': measurement_type, 'node_i': from_node, 'node_j': to_node, 'value': value})

        # Create a pandas DataFrame from the collected records
        measurements = pd.DataFrame(records_to_add)

        if measurements.empty:
            logging.warning("No measurement data retrieved from InfluxDB.")
        else:
            logging.info(f"Measurements collected: {len(measurements)} records.")

        return measurements  # Return the DataFrame

    except Exception as e:
        logging.error(f"An error occurred while retrieving data from InfluxDB: {e}", exc_info=True)
        return pd.DataFrame(columns=['type', 'node_i', 'node_j', 'value'])  # Return an empty DataFrame on error

def write_pf_to_influx_db(results, server):
    """
    Write power flow results to InfluxDB.
    """
    write_api = server.get('write_api')
    bucket = server.get('bucket')
    org = server.get('org')
    grid_name = server.get('grid_name')

    # Write voltage results to NodalVoltage
    for idx, row in results['nodeVoltagesPF'].iterrows():
        node = row['name']
        voltage_magnitude = row['vm_pu']
        voltage_angle = row['va_degree']

        point = Point("NodalVoltage").tag("grid_name", grid_name).tag("node", node) \
            .field("voltage_magnitude", voltage_magnitude).field("voltage_angle", voltage_angle) \
            .time(time.time_ns(), WritePrecision.NS)
        write_api.write(bucket=bucket, org=org, record=point)

    # Write power results to NodalPowerFlow
    for idx, row in results['nodePowersPF'].iterrows():
        node = row['name']
        p_mw = row['p_mw']
        q_mvar = row['q_mvar']

        point = Point("NodalPowerFlow").tag("grid_name", grid_name).tag("node", node) \
            .field("p_mw", p_mw).field("q_mvar", q_mvar) \
            .time(time.time_ns(), WritePrecision.NS)
        write_api.write(bucket=bucket, org=org, record=point)

    # Write line power results to LinePowerFlow
    for idx, row in results['linePowersPF'].iterrows():
        node_i = row['node_i']
        node_j = row['node_j']
        pij_mw = row['pij_mw']
        qij_mvar = row['qij_mvar']

        point = Point("LinePowerFlow").tag("grid_name", grid_name).tag("from_node", node_i).tag("to_node", node_j) \
            .field("pij_mw", pij_mw).field("qij_mvar", qij_mvar) \
            .time(time.time_ns(), WritePrecision.NS)
        write_api.write(bucket=bucket, org=org, record=point)

    logging.info("Power flow results successfully written to InfluxDB.")


def write_se_to_influx_db(results, server):
    """
    Write state estimation results to InfluxDB.
    """
    write_api = server.get('write_api')
    bucket = server.get('bucket')
    org = server.get('org')
    grid_name = server.get('grid_name')

    for idx, row in results['nodeVoltagesSE'].iterrows():
        node = row['name']
        voltage_magnitude = row['vm_pu']
        voltage_angle = row['va_degree']
        power_row = results['nodePowersSE'].iloc[idx]
        p_mw = power_row['p_mw']
        q_mvar = power_row['q_mvar']

        point = Point("NodalStateEstimation").tag("grid_name", grid_name).tag("node", node) \
            .field("voltage_magnitude", voltage_magnitude).field("voltage_angle", voltage_angle) \
            .field("p_mw", p_mw).field("q_mvar", q_mvar).time(time.time_ns(), WritePrecision.NS)
        write_api.write(bucket=bucket, org=org, record=point)

    for idx, row in results['linePowersSE'].iterrows():
        node_i = row['node_i']
        node_j = row['node_j']
        pij_mw = row['pij_mw']
        qij_mvar = row['qij_mvar']

        point = (
            Point("LineStateEstimation")
            .tag("grid_name", grid_name)
            .tag("from_node", node_i)
            .tag("to_node", node_j)
            .field("pij_mw", pij_mw)
            .field("qij_mvar", qij_mvar)
            .time(time.time_ns(), WritePrecision.NS)
        )
        write_api.write(bucket=bucket, org=org, record=point)

    logging.info("State estimation results successfully written to InfluxDB.")


def read_results_from_influx_db(server, config):
    """
    Continuously read and display power flow results from InfluxDB, using a runtime interval specified in the
    configuration.

    This function queries InfluxDB to retrieve node power flow data, including voltage magnitude, voltage angle,
    and active/reactive power. The query fetches data from the past hour for a specified grid, and the results are
    displayed every 'runtime_sec' seconds as specified in the config.

    :param server: Dictionary containing InfluxDB connection details (client, bucket, org, grid_name).
    :param config: Configuration file object containing runtime settings.
                   It expects 'runtime_sec' under 'application' settings.
    :return: None
    """
    # Get InfluxDB client and query API from the server dictionary
    client = server.get('influxdb_client')
    bucket = server.get('bucket')
    org = server.get('org')
    grid_name = server.get('grid_name')  # Get the grid name from the server configuration

    # Initialize the Query API
    query_api = client.query_api()

    # Define the query to fetch power flow data for the past hour
    query = f'''
        from(bucket: "{bucket}")
          |> range(start: -1h)  // Adjust the time range as needed (last 1 hour)
          |> filter(fn: (r) => r._measurement == "NodalPowerFlow")  // Filter for PowerFlow measurement
          |> filter(fn: (r) => r.grid_name == "{grid_name}")  // Filter by the grid name
          |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")  // Pivot the data
          |> keep(columns: ["_time", "node", "p_mw", "q_mvar"])  // Keep relevant columns
    '''

    # Retrieve runtime_sec from the config file, defaulting to 10 seconds if not specified
    runtime_sec = config.get('application', {}).get('runtime_sec', 10)

    while True:
        # Execute the query and retrieve the tables of data
        tables = query_api.query(query, org=org)

        # Iterate over the returned tables and print each record
        for table in tables:
            for record in table.records:
                # Print the time, node, voltage, and power data
                print(
                    f"Time: {record['_time']}, Node: {record['node']},"
                    f"P MW: {record['p_mw']}, Q MVAR: {record['q_mvar']}"
                )

        # Wait for the specified time interval from the configuration file before querying again
        time.sleep(runtime_sec)

