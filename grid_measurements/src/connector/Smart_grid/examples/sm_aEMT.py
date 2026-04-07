import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from grid_measurements.src.connector.Smart_grid.functions.sm.sm_tls_server import pisa_tls_server
from datetime import datetime

"""
A aEMT server for the PISA project.
It starts a TLS Server that listens for connections from the SMGW.
"""

# Add the libs folder to the Python path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(PROJECT_ROOT)
libs_path = 'libs/pisa'

CERTIFICATE_PARAMETERS = {
        "verify_client": "optional",
        "server_certificate": os.path.join(PROJECT_ROOT, libs_path, "20240918_emt_certificate_chain_tls.pem"), 
        "server_key": os.path.join(PROJECT_ROOT, libs_path , "ES.GWA.SN6_TLS.key"), 
        "client_certificate": os.path.join(PROJECT_ROOT, libs_path, "20240918_smgw_certificates_tls.pem"), 
        "cipher_suite": "ECDHE-ECDSA-AES128-GCM-SHA256",
        "check_hostname": False,
        "elliptic_curve": "brainpoolP256r1"
    }

CONNECTION_PARAMETERS = {
        "ip_address": "172.17.5.60",
        "port": 4589
    }

CMS_PARAMETERS = {
        "key_path": os.path.join(PROJECT_ROOT, libs_path, "ES.GWA.SN6_ENC.key"),
        "cert_path": os.path.join(PROJECT_ROOT, libs_path , "ES.GWA.SN6_ENC.crt") 
    }

current_date = datetime.now().strftime('%Y%m%d%H%M')
OUTPUTFILE = f"taf10_mmxu_output_{current_date}.csv"

OUTPUTPATH = os.path.join(PROJECT_ROOT, "output")

DEBUG = False
if __name__ == "__main__":
    # start the application
    pisa_tls_server(CERTIFICATE_PARAMETERS, CONNECTION_PARAMETERS, CMS_PARAMETERS, OUTPUTPATH, OUTPUTFILE, DEBUG)
