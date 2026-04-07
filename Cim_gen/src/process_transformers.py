import re
from Cim_gen.libraries.cim_profiles_by_class import *

def process_transformers(root, rdf_roots, CIM_NS, MD_NS, RDF_NS, EU_NS):
    """
    Processes transformer-related data from an XML structure and creates CIM-compliant elements
    including substations, base voltages, terminals, connectivity nodes, transformer windings,
    regulating controls, and topological nodes.

    Args:
        root (Element): The root XML element containing transformer definitions.
        rdf_roots (dict): Dictionary of RDF root elements for different profiles.
            - 'rdf_root': Core RDF model root.
            - 'topology_rdf_root': RDF root for topology elements.
        CIM_NS (str): The CIM namespace URI.
        MD_NS (str): The metadata namespace URI.
        RDF_NS (str): The RDF namespace URI.
        EU_NS (str): The EU namespace URI.

    Returns:
        tuple:
            - primary_base_voltage_id (str): mRID of the primary base voltage.
            - secondary_base_voltage_id (str): mRID of the secondary base voltage.
            - transformer (PowerTransformer): The last created transformer object.
            - substation_id (str): mRID of the created substation.
            - topological_node_ids (list): List of mRIDs for all created topological nodes.
    """
    rdf_root = rdf_roots['rdf_root']
    topology_rdf_root = rdf_roots['topology_rdf_root']

    # Create and append a FullModel element describing the CIM metadata
    fullmodel = FullModel(
        model_id="ebb750a0-e235-4bb0-a702-1a6e03635f12",
        created_time="2025-02-21T12:24:45Z",
        authority="ie3.etit.tu-dortmund.de",
        profiles=[
            "http://iec.ch/TC57/ns/CIM/CoreEquipment-EU/3.0",
            "http://iec.ch/TC57/ns/CIM/ShortCircuit-EU/3.0",
            "http://iec.ch/TC57/ns/CIM/Operation-EU/3.0"
        ],
        scenario_time="2025-02-211T23:00:00Z"
    )
    rdf_root.append(fullmodel.to_xml(MD_NS))
    topology_rdf_root.append(fullmodel.to_xml(MD_NS))

    # Variables to track created elements
    primary_base_voltage_id = None
    secondary_base_voltage_id = None
    transformer = None
    substation_id = None
    topological_node_ids = []

    # Iterate over all Trafo elements in the input XML
    for trafo in root.findall('Trafo'):
        # Extract transformer metadata
        transformer_name = trafo.get("STATION", "Unknown Station").strip()
        connection_point = trafo.get('Coordinates', f"{trafo.get('FID')}_unique")

        # Split nominal voltage (e.g., "110/20") and convert to float
        primary_voltage = trafo.get("NominalVoltage").split('/')[0].strip().replace(",", ".")
        secondary_voltage = trafo.get("NominalVoltage").split('/')[1].strip().replace(",", ".")
        primary_voltage_value = float(re.sub(r"[^\d\.]", "", primary_voltage))
        secondary_voltage_value = float(re.sub(r"[^\d\.]", "", secondary_voltage))

        # Create and register BaseVoltage objects
        primary_base_voltage = BaseVoltage(rdf_root, str(primary_voltage_value), "Primary baseVoltage", "Primary Voltage")
        secondary_base_voltage = BaseVoltage(rdf_root, str(secondary_voltage_value), "Secondary baseVoltage", "Secondary Voltage")
        primary_base_voltage_id = primary_base_voltage.create(CIM_NS)
        secondary_base_voltage_id = secondary_base_voltage.create(CIM_NS)

        # Initialize transformer object
        schaltung = trafo.get("Schaltung", "DefaultSchaltung").strip()
        transformer = PowerTransformer(rdf_root, station_name=transformer_name)
        transformer_id = transformer.create(CIM_NS)

        # Create substation and regional hierarchy
        substation_id = transformer.create_substation(
            cim_ns=CIM_NS,
            geographical_region_name="GeographicalRegionName",
            sub_geographical_region_name="SubGeographicalRegionName"
        )

        # Create ExternalNetworkInjection with RegulatingControl and Voltage
        external_injection_id, regulating_control_id, voltage_id = transformer.create_external_injection(
            cim_ns=CIM_NS,
            external_injection_name=f"{transformer_name} External Injection",
            base_voltage_id=primary_base_voltage.mrid,
            substation_id=substation_id,
        )

        # Create Terminal and associated ConnectivityNode
        terminal_id, cn_id = transformer.create_terminal(
            cim_ns=CIM_NS,
            terminal_name=f"{transformer_name} Terminal",
            equipment_id=external_injection_id
        )
        connectivity_node_id, container_id = transformer.create_connectivity_node(
            CIM_NS, node_name="position", cn_id=cn_id
        )

        # Create topological node and link it to terminal and connectivity node
        topological_node = TopologicalNode(
            topology_rdf_root, name="TopoNode",
            base_voltage_id=secondary_base_voltage_id,
            equipment_container_id=voltage_id
        )
        topological_node_id = topological_node.create(CIM_NS)
        topological_node_ids.append(topological_node_id)

        topological_node.create_terminal(terminal_id, topological_node_id, CIM_NS)
        topological_node.create_connectivity_node(connectivity_node_id, topological_node_id, CIM_NS)

        # Create RegulatingControl element for voltage control
        transformer.create_regulating_control(
            cim_ns=CIM_NS,
            control_id=regulating_control_id,
            regulating_control_name=f"{transformer_name} Regulating Control",
            terminal_id=terminal_id
        )

        # Extract transformer winding and loss data
        rated_power = str(int(trafo.get("SCHEINLEIS").strip()) * 1000)
        p_sc = float(trafo.get("ShortCircuitLoss").strip())
        p_oc = float(trafo.get("NoLoadLoss").strip())
        v_sc = float(trafo.get("ShortCircuitVolatge").strip())

        windings_data = [
            (1, primary_voltage, rated_power),
            (2, secondary_voltage, rated_power)
        ]

        # Create TransformerEnds for the two windings
        terminal_id2, terminal_id3 = transformer.create_power_transformer_end(
            windings_data=windings_data,
            base_voltage_id=(primary_base_voltage.mrid, secondary_base_voltage.mrid),
            transformer_id=transformer_id,
            schaltung=schaltung,
            p_sc=p_sc,
            p_oc=p_oc,
            v_sc=v_sc,
            cim_ns=CIM_NS
        )

        # Create another TopologicalNode to link to transformer ends
        topological_node = TopologicalNode(
            topology_rdf_root, name="TopoNode",
            base_voltage_id=secondary_base_voltage_id,
            equipment_container_id=transformer_id
        )
        topological_node_id = topological_node.create(CIM_NS)

        topological_node.create_terminal(terminal_id2, topological_node_id, CIM_NS)
        topological_node.create_terminal(terminal_id3, topological_node_id, CIM_NS)

    # Final result includes base voltages, transformer, substation, and topology node IDs
    return primary_base_voltage_id, secondary_base_voltage_id, transformer, substation_id, topological_node_ids
