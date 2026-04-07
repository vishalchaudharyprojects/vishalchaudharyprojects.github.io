"""
GIS to CIM Utilities Module

Helper services for converting GIS data to CIM format including:
- XML prettification
- RDF root creation
- File saving operations
"""

import os
from datetime import date
import xml.etree.ElementTree as ET
from collections import defaultdict


def prettify_xml(element):
    """
    Convert XML element to pretty-printed string with proper indentation.

    Args:
        element (ET.Element): XML element to format

    Returns:
        str: Pretty-printed XML string
    """
    from xml.dom import minidom
    rough_string = ET.tostring(element, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")


def parse_gis_data(gisData):
    """
    Parse GIS data from either string or ElementTree object.

    Args:
        gisData (str/ElementTree): Input GIS data

    Returns:
        ET.Element: Root element of parsed GIS data
    """
    if isinstance(gisData, str):
        return ET.ElementTree(ET.fromstring(gisData)).getroot()
    return gisData.getroot()


def create_rdf_roots(RDF_NS, MD_NS, CIM_NS, EU_NS):
    """
    Create root elements for all required CIM profiles.

    Args:
        RDF_NS (str): RDF namespace URI
        MD_NS (str): Model Description namespace URI
        CIM_NS (str): Core CIM namespace URI
        EU_NS (str): European extensions namespace URI

    Returns:
        dict: Dictionary of RDF root elements for different profiles:
            - rdf_root: Equipment (EQ) profile
            - ssh_rdf_root: Steady-State Hypothesis (SSH)
            - sv_rdf_root: State Variables (SV)
            - diagram_rdf_root: Diagram Layout (DL)
            - topology_rdf_root: Topology (TP)
            - gl_rdf_root: Geographical Location (GL)
    """
    # Create root element for each CIM profile
    profiles = {
        'rdf_root': "Equipment (EQ) profile",
        'ssh_rdf_root': "Steady-State Hypothesis (SSH)",
        'sv_rdf_root': "State Variables (SV)",
        'diagram_rdf_root': "Diagram Layout (DL)",
        'topology_rdf_root': "Topology (TP)",
        'gl_rdf_root': "Geographical Location (GL)"
    }

    rdf_roots = {}
    for profile in profiles:
        root = ET.Element(f"{{{RDF_NS}}}RDF")
        root.set(f"{{{RDF_NS}}}about", "")
        rdf_roots[profile] = root

    return rdf_roots


def save_xml_files(rdf_roots, grid_name):
    """
    Save CIM profiles to properly formatted XML files.

    Files are saved with date prefixes in the format: YYYY-MM-DD_GridName_Profile_.xml

    Args:
        rdf_roots (dict): Dictionary of RDF root elements
        grid_name (str): Name of the grid model

    Returns:
        None: Files are written to disk
    """
    # Base output directory (Note: Windows path - consider using raw string or forward slashes)
    base_path = r"D:\sgt_engineering_Thomas\Grids"
    folder_path = os.path.join(base_path, grid_name, "cim3")
    os.makedirs(folder_path, exist_ok=True)

    # Get current date for filename prefix
    today = date.today()
    date_prefix = today.strftime("%Y-%m-%d")

    # File naming convention mapping
    profile_mapping = {
        'rdf_root': 'EQ',
        'ssh_rdf_root': 'SSH',
        'sv_rdf_root': 'SV',
        'diagram_rdf_root': 'DL',
        'topology_rdf_root': 'TP',
        'gl_rdf_root': 'GL'
    }

    # Save each profile to separate file
    for profile_root, profile_suffix in profile_mapping.items():
        filename = f"{date_prefix}_{grid_name}_{profile_suffix}_.xml"
        filepath = os.path.join(folder_path, filename)

        with open(filepath, "w", encoding='utf-8') as f:
            f.write(prettify_xml(rdf_roots[profile_root]))