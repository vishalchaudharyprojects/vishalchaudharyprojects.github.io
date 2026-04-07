# Digital Twin Application

This repository contains a modular Digital Twin application that integrates Asset Administration Shell (AAS) generation, Common Information Model (CIM) generation, and real-time data integration via Typhoon HIL. The application is designed for industrial automation, energy systems, or smart grid simulations.

## Project Structure

                                                                                               
├── Cim_gen/ # Common Information Model generation module                                              
│ ├── libraries/ # CIM-related libraries                                                         
│ │ ├── cim_profiles_by_class/     
│ │ ├── __init__.py
│ │ └── cimpy_3/ # CIMpy library for CIM operations
│ ├── src                                                         
│ │ ├── api  
│ │ │  └── __init__.py 
│ │ │  └── routes.py 
│ │ ├── __init__.py 
│ │ ├── gis_to_cim_main.py # Main CIM generation script                                           
│ │ └── ... (other core scripts)  
│ ├── Grids                                                         
│ │ ├── 1-LV-rural1--2-no_sw_EV_HP
│ │ │  └── CIM3
│ │ │  │ └── 20151231T2300Z_XX_YYY_EQ.xml
│ │ │  │ └── ...
│ │ ├── Function_modules/ # Functional components for CIM processing                                   
│ │ │ ├── CalcApplication.py                                                                        
│ │ │ ├── CalcPreparation.py     
│ │ │ ├── __init__.py
│ │ │ ├── influx_db_measurements.py                                                              
│ │ │ └── ... (other functional modules)
│ ├── __init__.py 
│ ├── app.py 
│ ├── config_cim.yaml # Configuration for CIM module                                              
│ └── requirements_cim.txt # Python dependencies for CIM module 
│ └── Dockerfile # Python dependencies for CIM module
│                                                                                           
├── grid_measurement/ # Real-time data integration module (Typhoon HIL)                                          
│ ├── libs/ # External libraries                                                                 
│ │ ├── cimpy_3/ # CIMpy library                                                                 
│ │ └── ie3_iec_61850_lib/ # IEC 61850 library 
│ │ └── __init__.py 
│ ├── src                                                         
│ │ ├── api  
│ │ │  └── __init__.py 
│ │ │  └── routes.py 
│ │ ├── __init__.py
│ │ ├── Connector / # Functional components for Typhoon integration                             
│ │ │ ├── aas_interaction.py # AAS communication                                                         
│ │ │ ├── iec_61850_modbus_reading.py # IEC 61850/Modbus communication                                 
│ │ │ └── write_measurements_to_influxdb.py
│ │ │ └── __init__.py (other functional modules)
│ │ └── write_measurements_to_influxdb.py
│ ├── app.py 
│ ├── config_typhoon.yaml # Configuration for Typhoon module                                    
│ └── requirements_typhoon.txt # Python dependencies   
│ └── Dockerfile

├── asset_administration_shell/
│   ├── aas                                                         
│   │ ├── Battery_storage_intilion_wip.json
│   │ ├── load_EV_wallbox_WIP.json
│   │ ├── line_NaYY_J_$.json
│   │ ├── Transformer_OLTC_misc.json  
│   │ ├── gens_PV_RS_Smart_Solar_48_6000.json
│   ├── basyx                                                         
│   │ ├── aas-discovery.properties
│   │ ├── aas-env.properties
│   │ ├── aas-registry.yml
│   │ ├── sm-registry.yml 
│   ├── Readme.md                                       
│   ├── docker-compose.yml
│
├── generate_aasx_from_datasheets/ # Asset Administration Shell generation module                             
│ ├── aas_json/ # Predefined AAS JSON templates/examples                                          
│ ├── assets/ # Additional assets (images, schematics, etc.) 
│ ├── asset_modbus_mapping                                                          
│ │ └── Battery_Storage_Typhoon.csv
│ │ └── gens_PV_Typhoon.csv
│ │ └── ...
│ ├── src/                                                               
│ │ └── aas.py # Main AAS generation logic     
│ │ └── rabbitmq_service.py    
│ │ └── rabbitmq_consumer.py
│ │ └── api.py 
│ │ │  └── __init__.py 
│ │    └── routes.py
│ │ └── aas_creator.py
│ │ └── link_aas_to_cim.py 
│ │ └── link_cim_to_aas.py
│ │ └── cim_eq_to_aasx.py
│ │ └── example.py
│ │ └── Grids
│ │ │  └──  1-LV-rural1--2-no_sw_EV_HP
│ │ │  │ └──  CIM3
│ │ │  │ │  └──  20151231T2300Z_XX_YYY_DL_.xml
│ │ │  │ │  └──  20151231T2300Z_XX_YYY_DY_.xml...
│ ├── app.py 
│ ├── Dockerfile
│ ├── setup.py                                              
│ └── requirements_aas.txt # Python dependencies for AAS module                                     
│    
├── smart_grid_services/ 
│   ├── src/
│   │   ├── state_estimation
│   │   │ └──  se_connector.py
│   │   │ └──  se_processor.py
│   │   │ └──  se_execution.py
│   │   │ └──  se_main.py
│   │   ├── app.py               # Flask/FastAPI wrapper to expose an API endpoint
│   ├── config_se.yaml           # Configuration for DB, AAS endpoint, CIM paths
│   ├── requirements_se.txt      # Python dependencies (e.g., pandapower, influxdb-client)
│   └── Dockerfile               # Dockerfile for the new service
│
├── integration_layer_interface/
│   ├── docker-compose.yml (your current location)
│   ├── Dockerfile
│   ├── requirements_ssot.txt
│   ├── setup.py
│   ├── config_aas.yaml
│   ├── .env
│   ├── logs
│   ├── Grids                                                         
│   │ ├── 1-LV-rural1--2-no_sw_EV_HP
│   │ │  └── CIM3
│   │ │  │ └── 20151231T2300Z_XX_YYY_EQ.xml
│   ├── __init__.py
│   │ ├── digital_twin_2025-06-11.log  
│   ├── src                                                         
│   │ ├── api  
│   │ │  └── __init__.py 
│   │ │  └── routes.py 
│   │ ├── __init__.py
│   │ ├── main.py 
├── venv/ # Python virtual environment (ignored in Git)                                  
└── README.md                                                             


## Module Descriptions

# 1. CIM EQ -> AASX Hierarchical Converter (with DSO top-level)

## Overview
This script converts CIM EQ (and optional CIM GL) XML files into a hierarchical set of Asset Administration Shells (AAS)
and Submodels (exported as a JSON AASX-like bundle via `write_aas_to_file`). It builds a multi-level hierarchy and
adds bidirectional references back into the original CIM EQ file.

Key features:
- Creates individual AAS for many CIM asset types (Substation, PowerTransformer, ConformLoad, ACLineSegment, BatteryUnit, PhotoVoltaicUnit, ConnectivityNode, etc.).
- Adds technical submodels and location/meter/market submodels derived from CIM GL (if provided).
- Registers Netzlokation / Messlokation / Marktlokation in registries.
- Builds a hierarchical Bill-of-Material:
  - **DSO -> PowerSystem -> Substation -> PowerTransformer -> ConnectivityNode -> other assets**
- Updates the original CIM EQ file with bidirectional references for each asset:
  - `cim:IdentifiedObject.globalAssetId` — the AAS `global_asset_id` (URN/UUID string).
  - `cim:IdentifiedObject.aasIdentifier` — the AAS identifier (the full AAS `id_` value).
- The converter stores these references internally for inclusion into AAS submodels (technical data submodel includes both fields when available).


### 2. CIM Generation Module
- **Purpose**: Generates Common Information Model (CIM) representations of power system components
- **Key Features**:
  - GIS to CIM conversion
  - Equipment and transformer processing
  - InfluxDB integration for measurements
- **Main Components**:
  - `gis_to_cim_main.py`: Main conversion workflow
  - `process_equipment.py`: Equipment-specific processing
  - `process_transformers.py`: Transformer-specific processing

### 3. Typhoon Integration Module
- **Purpose**: Real-time data integration with Typhoon HIL systems
- **Key Features**:
  - IEC 61850 and Modbus communication
  - SCD file handling
  - Measurement data writing to InfluxDB
- **Main Components**:
  - `data_integration.py`: Primary execution point
  - `iec_61850_modbus_reading.py`: Communication handlers
  - `scd_handling.py`: SCD file processing

## Installation

1. Clone the repository:
   ```bash
   git clone https://git.ie3.e-technik.tu-dortmund.de/smvlchau/AAS.git
   cd Digital_Twin_App
   

# For AAS module
python -m venv venv/aas
source venv/aas/bin/activate  # On Windows: venv\aas\Scripts\activate
pip install -r Aas_generation/requirements_aas.txt

# Commands for different workflow
# AAS Generation based on CIM and enhancing with static data
1. curl http://localhost:5001/api/health
2. curl http://localhost:5002/api/health
3. curl http://localhost:5002/api/list-files
4. curl http://localhost:5002/api/test-imports
5. curl -X POST http://localhost:5002/api/generate-cim-aas \
  -H "Content-Type: application/json" \
  -d '{
        "workflow": "cim_only",
        "cim_eq_path": "/app/Grids/1-LV-rural1--2-sw_EV_HP/CIM3/1-LV-rural1--2-sw-reduced_fuses_EQ.xml",
        "cim_gl_path": "/app/Grids/1-LV-rural1--2-sw_EV_HP/CIM3/1-LV-rural1--2-sw-reduced_fuses_GL.xml"
      }'
6. curl -X POST http://localhost:5002/api/enhance-existing-aas \
  -H "Content-Type: application/json" \
  -d '{
        "target_aas_file": "/app/basyx_aas/cim_eq_gl_aasx_hierarchical_20151231T2300Z_YYY_EQ_.json",
        "workflow": "static_only"
      }'
7. curl -X POST http://localhost:5002/api/enhance-existing-aas \
  -H "Content-Type: application/json" \
  -d '{
        "target_aas_file": "/app/basyx_aas/cim_eq_gl_aasx_hierarchical_20151231T2300Z_YYY_EQ_.json",
        "equipment": "Transformer_Ormazabal_velatia_OLTC_misc",
        "workflow": "static_only"
      }'
8. curl -X POST http://localhost:5002/api/generate-cim-aas \
  -H "Content-Type: application/json" \
  -d '{
        "workflow": "full_cim_pipeline",
        "cim_eq_path": "/app/Grids/1-LV-rural1--2-no_sw_EV_HP/CIM3/20151231T2300Z_YYY_EQ_.xml",
        "cim_gl_path": "/app/Grids/1-LV-rural1--2-no_sw_EV_HP/CIM3/20151231T2300Z_XX_YYY_GL_.xml"
      }' 

# Data Integration
1. curl http://localhost:5004/api/typhoon/health
2. curl http://localhost:5004/api/typhoon/status
3. curl -X POST http://localhost:5004/api/typhoon/process \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "DataIntegration": {
        "runtime_sec": 10,
        "grid": {
          "name": "1-LV-rural1--2-sw_reduced"
        }
      },
      "SCD": {
        "path": "/app/Grids/1-LV-rural1--2-sw_reduced/scd",
        "file_name": "autoconfig_LV1101Bus2.scd"
      }
    }
  }'

# State Estimation
1. curl -X GET http://localhost:5003/api/se/health
2. curl -X GET http://localhost:5003/api/se/status
3. curl -X POST http://localhost:5003/api/se/run-once
4. curl -X POST http://localhost:5003/api/se/run-once \
  -H "Content-Type: application/json" \
  -d '{"aas_json_path": "/custom/path/to/aas.json"}'
5. curl -X POST http://localhost:5003/api/se/start
6. curl -X POST http://localhost:5003/api/se/start \
  -H "Content-Type: application/json" \
  -d '{
    "interval_sec": 60,
    "aas_json_path": "/custom/path/to/aas.json"
  }'



# TODO: Do the DSO AAS over the Powersystem
# TODO: Store the sate estimation in influxdb as well.
# TODO: Make the pus_to_basyx for all the CN rather than one
# TODO: When running SE for interval it's creating new se every time the se is running, correct that
# TODO: CIM properties coming in the connectivity nodes and other assets , most probably coming from last logic 
# TODO: EMT and Marktlokation, Netzlokation

Thesis -
- Verify the state estimation based on the typhoon, maybe running the se with the interval of 15 sec for 
10 -15 mins and then verify state estimation values
- Computational requirements of the entire structure and then presenting or documenting into a way that can show 
that it can be deployed on an edge device (rasberry pi / Bechoff edge device) easily
- Plots for state estimation and verification
- Differnce between verification and validation
- Characterise the tests either based on verification and validation
- 
Total breakdown:
- Bus voltage measurements: 37 (three-phase × multiple buses)
- Bus power measurements: 36 (three-phase × multiple buses)  
- Line measurements: 4
- Transformer measurements: 2
---
Total: 79 measurements