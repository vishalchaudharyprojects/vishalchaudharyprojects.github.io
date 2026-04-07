"""
CIM Grid Generation Module

This module provides functionality to convert GIS data to CIM-compliant RDF/XML files
following the CGMES (Common Grid Model Exchange Standard) specifications.
"""

from .gis_to_cim_utils import create_rdf_roots, save_xml_files
from .process_equipment import *
from .process_transformers import *
import xml.etree.ElementTree as ET


def gis_to_cim2(gisData, grid_name):
    """
    Convert GIS data to CIM-compliant XML files for power system modeling.

    This is the main conversion function that processes GIS data and generates
    multiple CIM profiles (EQ, SSH, SV, etc.) as separate XML files.

    Args:
        gisData (str/ElementTree): Input GIS data as either XML string or ElementTree
        grid_name (str): Name of the grid model (used for output filenames)

    Returns:
        None: Outputs are written to XML files in the specified directory
    """
    # Define namespaces for CIM, RDF, and European CIM models
    CIM_NS = "http://iec.ch/TC57/2013/CIM-schema-cim16#"  # Core CIM namespace
    RDF_NS = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"  # RDF namespace
    EU_NS = "http://iec.ch/TC57/CIM-schema-cim100/European#"  # European extensions
    MD_NS = "http://iec.ch/TC57/61970-552/ModelDescription/1#"  # Model description

    # Register namespaces to prevent prefixes in XML output
    ET.register_namespace("cim", CIM_NS)
    ET.register_namespace("rdf", RDF_NS)
    ET.register_namespace("eu", EU_NS)
    ET.register_namespace("md", MD_NS)

    # Get the root element of the GIS data
    root = gisData.getroot()

    # Create RDF roots for different CIM profiles
    rdf_roots = create_rdf_roots(RDF_NS, MD_NS, CIM_NS, EU_NS)

    # Process transformers first as they establish voltage levels
    primary_base_voltage_id, secondary_base_voltage_id, transformer, substation_id, topological_node_ids = process_transformers(
        root, rdf_roots, CIM_NS, MD_NS, RDF_NS, EU_NS)

    # Process other power system equipment
    process_equipment(
        root, rdf_roots, CIM_NS, MD_NS,
        primary_base_voltage_id, secondary_base_voltage_id,
        transformer, substation_id, topological_node_ids,
        RDF_NS, EU_NS)

    # Save the generated XML files with proper naming convention
    save_xml_files(rdf_roots, grid_name)