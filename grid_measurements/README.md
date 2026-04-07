
                        +------------------------------------+
                        |            SCD File                |
                        |  (DLMS + Modbus Configurations)   |
                        +-----------------------
-------------+
                                   |
        +--------------------------+--------------------------+
        |                                                     |
        v                                                     v
+-----------------------+                       +----------------------------+
| Modbus Configuration  |                       | DLMS COSEM Configuration  |
|   (scd_communication) |                       |      (scd_dlms_df)        |
+-----------------------+                       +----------------------------+
        |                                                     |
        |                                                     |
        v                                                     v
+-------------------------+                      +------------------------------+
| Modbus Data Polling     |                      | Spawn DLMS TLS Listeners     |
| read_modbus_data_from_* |                      | (start_dlms_listener)        |
+-------------------------+                      +------------------------------+
        |                                                     |
        v                                                     v
+-------------------------+                      +------------------------------+
| IEC 61850 Logical Nodes |                      | TLS Listener (per SMGW port)|
| (MMXU, TCTR)            |<------ TAF10 XML ----| run_tls_server_for_dlms      |
+-------------------------+                      +------------------------------+
        |                                                     |
        +---------------------------+-------------------------+
                                    v
                        +------------------------------+
                        |    write_ln_to_influx_db     |
                        |      InfluxDB Storage        |
                        +------------------------------+




A) Local Operation
This manual is relevant if your supervisor wants you to work on the local computer

Clone this git repository to your local harddrive (not U drive, git doesn't like that!)
Open VSCode on your device
Open the repository in VSCode
Install Extensions "Python" and "C/C++", restart VSCode
Make sure that your python version is 3.11.4 or 3.10.11
Open a terminal and run "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process"
In the python terminal: run "python -m venv venv"
----------"-----------: "./venv/Scripts/activate"
pip install -r requirements_3_10_11.txt or requirements_3_11_4.txt
move folder "cimpy_3" from "./local_libs" to "./venv/Lib/site-packages"
navigate to that folder in python terminal and execute python setup.py develop
Now you can start coding and running the python programming tool in VS Code :)
B) Virtual Machine
This manual is relevant if your supervisor works with you together on a virtual machine

Install remote-ssh package in vs Code
click "Remote-Explorer" on the left hand side
enter "username@vm-domain-name"
select local ssh config of your username
Connect to remote host and choose "Linux"
login with your password
Congratulation! You are using VS Code on a VM, now start with the manual as given in A)