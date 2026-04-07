from dotenv import load_dotenv
import os
import requests
from loguru import logger

# Load environment variables
load_dotenv()
API_URL = os.getenv("AAS_API_URL")


def read_scd_name_from_aas():
    """This function reads the scd reference for an asset from
    an AAS server

    :returns scd_name: Name of the scd file """
    # initialize return variable
    scd_name = None
    # http-get methode an die URL senden
    response = requests.get(API_URL)
    while response.status_code != 200:
        logger.error("Cannot reach AAS fetcher server, response code: ", response.status_code)
        response = requests.get(API_URL)
    # check the response status codde
    if response.status_code == 200:
        data = response.json()
        scd_name = data.get("data integration")["scd file name"]

    return scd_name
