import threading
from grid_measurements.src.connector.Smart_grid.functions.sm.mako_api_lf_nb import run_server, send_command_control_create
import uuid
import datetime
import random
import string
import time

def start_server():
    # Starte den Flask-Server
    run_server(host='127.0.0.1', port=8081)

def send_smth():
    time.sleep(3)
    # Client-Aktionen
    #HOST = "127.0.0.1" #ip-address of the MSB
    #PORT = 8080 #port of the MSB channel
    # https://app.swaggerhub.com/apis-docs/edi-energy/Steuerungshandlung_2023-10-24/1.0.0#/
    TRANSACTION_ID = str(uuid.uuid4())
    # current date time in utc
    current_datetime = datetime.datetime.now(datetime.timezone.utc)
    creationdatetime = current_datetime.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    # initial transaction id
    INIT_TRANSACTION_ID = ""  # optional
    # Location ID, Steuerbare Resource ID oder Netzlokations ID
    # Quelle: https://www.bdew.de/media/documents/
    # AWH_Identifikatoren-in-der-Marktkommunikation_Version.1.2.pdf
    SR_ID = ("C".join(random.choices(string.ascii_lowercase, k=10))
            +str(random.randint(0, 9)))
    # define the actual command
    command_control = dict()
    command_control["maximumPowerValue"] = 25.124  # kW
    # determine the starting point of the control command
    datetime_start = current_datetime + datetime.timedelta(minutes=5)
    datetime_end = current_datetime + datetime.timedelta(minutes=10)

    command_control["executionTimeFrom"] = datetime_start
    command_control["executionTimeUntil"] = datetime_end
    # Sende einen Steuerbefehl (HTTP POST)
    status, response = send_command_control_create(
        transaction_id=TRANSACTION_ID,
        creationdatetime=creationdatetime,
        initial_transaction_id=INIT_TRANSACTION_ID,
        sr_id=SR_ID,
        command_control=command_control,
        host='127.0.0.1',
        port=8080
    )

# Starte den Flask-Server in einem separaten Thread
server_thread = threading.Thread(target=send_smth, daemon=True)
server_thread.start()

# Client-Aktionen
#HOST = "127.0.0.1" #ip-address of the MSB
#PORT = 8080 #port of the MSB channel
# https://app.swaggerhub.com/apis-docs/edi-energy/Steuerungshandlung_2023-10-24/1.0.0#/
TRANSACTION_ID = str(uuid.uuid4())
# current date time in utc
current_datetime = datetime.datetime.now(datetime.timezone.utc)
creationdatetime = current_datetime.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
# initial transaction id
INIT_TRANSACTION_ID = ""  # optional
# Location ID, Steuerbare Resource ID oder Netzlokations ID
# Quelle: https://www.bdew.de/media/documents/
# AWH_Identifikatoren-in-der-Marktkommunikation_Version.1.2.pdf
SR_ID = ("C".join(random.choices(string.ascii_lowercase, k=10))
         +str(random.randint(0, 9)))
# define the actual command
command_control = dict()
command_control["maximumPowerValue"] = 25.124  # kW
# determine the starting point of the control command
datetime_start = current_datetime + datetime.timedelta(minutes=5)
datetime_end = current_datetime + datetime.timedelta(minutes=10)
# Format the new datetime in the desired format
formatted_start_datetime = datetime_start.strftime('%Y-%m-%dT%H:%M:%SZ')
formatted_end_datetime = datetime_end.strftime('%Y-%m-%dT%H:%M:%SZ')
command_control["executionTimeFrom"] = datetime_start
command_control["executionTimeUntil"] = datetime_end
# Sende einen Steuerbefehl (HTTP POST)
run_server(host='127.0.0.1', port=8081)
# status, response = send_command_control_create(
#     transaction_id=TRANSACTION_ID,
#     creationdatetime=creationdatetime,
#     initial_transaction_id=INIT_TRANSACTION_ID,
#     sr_id=SR_ID,
#     command_control=command_control,
#     host='127.0.0.1',
#     port=8080
# )

# print(f"Status: {status}, Response: {response}")
