import xml.etree.ElementTree as ET
from xml.dom import minidom

def prettify_xml(elem):
    """
    Return a pretty-printed XML string from an ElementTree Element.

    Args:
        elem (Element): An XML element.

    Returns:
        str: Pretty-formatted XML string.
    """
    rough_string = ET.tostring(elem, 'utf-8')  # Convert element to byte string
    reparsed = minidom.parseString(rough_string)  # Parse using minidom
    return reparsed.toprettyxml(indent="  ")  # Return formatted XML


def create_element(namespace, tag, attrib=None, text=None):
    """
    Create an XML element with namespace and optional attributes and text.

    Args:
        namespace (str): XML namespace URI.
        tag (str): Element tag name.
        attrib (dict, optional): Attributes to include.
        text (str, optional): Text content for the element.

    Returns:
        Element: Constructed XML element.
    """
    ns_tag = f"{{{namespace}}}{tag}"  # Add namespace to tag
    element = ET.Element(ns_tag, attrib or {})  # Create element with attributes
    if text:
        element.text = text  # Set element text
    return element


class CIMObject:
    """
    Base class for CIM CGMES objects.

    Attributes:
        rdf_root (Element): The root RDF XML element.
    """

    def __init__(self, rdf_root):
        """
        Initialize a CIMObject with an RDF root.

        Args:
            rdf_root (Element): Root XML element for RDF model.
        """
        self.rdf_root = rdf_root

    def append_to_root(self, element):
        """
        Append a new XML element to the RDF root.

        Args:
            element (Element): The XML element to append.
        """
        self.rdf_root.append(element)
