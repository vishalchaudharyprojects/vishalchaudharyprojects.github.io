from collections import defaultdict
from Cim_gen.libraries.cim_profiles_by_class import *


def process_equipment(root, rdf_roots, CIM_NS, MD_NS, primary_base_voltage_id,
                      secondary_base_voltage_id, transformer, substation_id,
                      topological_node_ids, RDF_NS, EU_NS):
    """
    Process power system equipment from GIS data and create CIM-compliant representations.

    This function handles the conversion of various power system components (cables, loads, etc.)
    to CIM model elements across multiple profiles (EQ, SSH, SV, etc.).

    Args:
        root (ET.Element): Root element of the input GIS data
        rdf_roots (dict): Dictionary of RDF root elements for different CIM profiles
        CIM_NS (str): CIM namespace URI
        MD_NS (str): Model Description namespace URI
        primary_base_voltage_id (str): MRID of primary voltage level
        secondary_base_voltage_id (str): MRID of secondary voltage level
        transformer (dict): Transformer configuration data
        substation_id (str): MRID of parent substation
        topological_node_ids (list): List of topological node MRIDs
        RDF_NS (str): RDF namespace URI
        EU_NS (str): European extensions namespace URI

    Returns:
        None: Modifies the RDF roots in-place with generated equipment data
    """

    # Extract individual RDF roots from dictionary
    rdf_root = rdf_roots['rdf_root']  # Equipment (EQ) profile
    topology_rdf_root = rdf_roots['topology_rdf_root']  # Topology (TP) profile
    gl_rdf_root = rdf_roots['gl_rdf_root']  # Geographical (GL) profile
    sv_rdf_root = rdf_roots['sv_rdf_root']  # State Variables (SV) profile
    ssh_rdf_root = rdf_roots['ssh_rdf_root']  # Steady-State (SSH) profile
    diagram_rdf_root = rdf_roots['diagram_rdf_root']  # Diagram (DL) profile

    # Create FullModel metadata element
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

    # Add FullModel to all relevant profiles
    for profile_root in [ssh_rdf_root, sv_rdf_root, diagram_rdf_root, gl_rdf_root]:
        profile_root.append(fullmodel.to_xml(MD_NS))

    # Initialize data structures for model components
    diagram_positions = []  # Stores coordinates for diagram layout
    position_counter = 0  # Tracks position index for diagram objects
    busbar_counter = 0  # Counter for busbar naming
    terminal_ids = []  # Collects all terminal MRIDs
    voltage_level_ids = []  # Collects voltage level MRIDs
    current_limit_ids = []  # Collects operational limit MRIDs
    terminal_map = defaultdict(list)  # Maps positions to terminal groups
    connectivity_node_map = {}  # Maps connection points to connectivity nodes
    operational_limit_types = {}  # Stores limit type definitions

    # Cable impedance properties lookup table
    CABLE_PROPERTIES = {
        "NAYCWY 3x150/150": {"r_per_km": 0.124, "x_per_km": 0.075, "bch_per_km": 4.22606e-6},
        "NYCWY 3x25/25": {"r_per_km": 0.784, "x_per_km": 0.08, "bch_per_km": 3.5e-6},
        "NAYCWY 3x95/95": {"r_per_km": 0.176, "x_per_km": 0.07, "bch_per_km": 4.0e-6},
        "NYY 4x16": {"r_per_km": 1.21, "x_per_km": 0.09, "bch_per_km": 2.9e-6},
        "Unbekannt": {"r_per_km": 1.0, "x_per_km": 0.1, "bch_per_km": 1e-6},  # Default for unknown types
    }

    # Create load hierarchy (LoadArea -> SubLoadArea -> ConformLoadGroup)
    load_area = LoadArea(rdf_root, name="LV1.101 Load Area")
    load_area.create(CIM_NS)

    sub_load_area = SubLoadArea(
        rdf_root,
        name="LV1.101 SubLoadArea",
        load_area_id=load_area.mrid
    )
    sub_load_area.create(CIM_NS)

    conform_load_group = ConformLoadGroup(
        rdf_root,
        name="LV1.101 ConformLoadGroup",
        sub_load_area_id=sub_load_area.mrid
    )
    conform_load_group.create(CIM_NS)

    # Initialize profile handlers
    load_response_characteristics = {}  # Tracks load behavior models
    gl_profile = GLProfile(gl_rdf_root)  # Geographical location profile
    sv_profile = SVProfile(sv_rdf_root)  # State variables profile

    for equipment in root.findall('.//*'):
        """
        Process each equipment element from GIS data and create corresponding CIM objects.

        This loop handles different types of power system equipment (busbars, conductors, loads, etc.),
        creating appropriate CIM representations for each type with proper connectivity and attributes.
        """

        eq_type = equipment.tag  # Type of equipment (e.g., "Busbar_ext", "Conductor")
        node_name = equipment.get('FID', f"Unnamed {eq_type}")  # Equipment identifier
        connection_point = equipment.get('Coordinates', f"{equipment.get('FID')}_unique")  # Physical location

        # --- Busbar/Sleeve Processing ---
        if eq_type == "Busbar_ext" or eq_type == "Sleeve":
            """
            Process busbar elements which serve as connection points in substations.

            Creates:
            - VoltageLevel
            - BusbarSection
            - Terminal
            - GL location data
            - Diagram positions
            """

            # Determine voltage level (primary or secondary side of transformer)
            base_voltage_id = primary_base_voltage_id if busbar_counter == 0 else secondary_base_voltage_id

            # Create VoltageLevel associated with the substation
            voltage_name = f"Voltage Level {node_name}"
            voltage_level_id = transformer.create_voltage_level(CIM_NS, voltage_name, base_voltage_id)
            voltage_level_ids.append(voltage_level_id)

            # Create BusbarSection as conducting equipment
            conducting_equipment = BusbarSection(rdf_root, node_name, voltage_level_id)
            conducting_equipment_id = conducting_equipment.create(CIM_NS)

            # Create Terminal for connectivity
            terminal = Terminal(rdf_root, name=node_name,
                                conducting_equipment_id=conducting_equipment_id,
                                sequence_number=1)
            terminal_id = terminal.create(CIM_NS)
            terminal_ids.append(terminal_id)
            terminal_map[connection_point].append(terminal_id)

            # Add geographical information
            coordinate_system_id = gl_profile.create_coordinate_system(cim_ns=CIM_NS)
            gl_profile.create_location_and_position(
                conducting_equipment_id, node_name,
                connection_point, CIM_NS, coordinate_system_id
            )

            # Track position for diagram layout
            diagram_positions.append(
                (conducting_equipment.mrid, position_counter,
                 150 + position_counter * 50, 250 + position_counter * 30)
            )
            position_counter += 1
            busbar_counter += 1

        # --- Conductor (AC Line) Processing ---
        elif eq_type == "Conductor":
            """
            Process conductor/cable elements with electrical parameters.

            Creates:
            - ACLineSegment with impedance values
            - Two terminals (ends of line)
            - Operational limits (voltage/current)
            - GL location data
            - SV status for in-service state
            """

            # Get cable properties from predefined table
            cable_type = equipment.get("CableType", "Unbekannt")
            cable_properties = CABLE_PROPERTIES.get(cable_type, CABLE_PROPERTIES["Unbekannt"])
            state = equipment.get('STATE')  # Operational state

            # Create ACLineSegment with electrical parameters
            conducting_equipment = ACLineSegment(
                rdf_root,
                line_name=f"ACLine_{equipment.get('FID')}",
                length=100,  # Default length (could be parameterized)
                resistance=cable_properties["r_per_km"],
                reactance=cable_properties["x_per_km"],
                shunt_susceptance=cable_properties["bch_per_km"],
                base_voltage_id=secondary_base_voltage_id
            )
            conducting_equipment_id = conducting_equipment.create(CIM_NS)

            # Create terminals at both ends of the line
            terminals = []
            for seq_num in [1, 2]:  # Two terminals per line
                terminal = Terminal(rdf_root, name=f"{node_name}_T{seq_num}",
                                    conducting_equipment_id=conducting_equipment_id,
                                    sequence_number=seq_num)
                terminal_id = terminal.create(CIM_NS)
                terminal_ids.append(terminal_id)
                terminal_map[connection_point].append(terminal_id)
                terminals.append(terminal_id)

            # Create operational limits for each terminal
            for terminal_id in terminals:
                # Create limit set container
                operational_limit_set = OperationalLimitSet(
                    rdf_root,
                    terminal_id=terminal_id,
                    name=f"{eq_type} Limits"
                )
                operational_limit_set_id = operational_limit_set.create(CIM_NS)

                # Define limit types (create if they don't exist)
                limit_type_keys = [
                    ("lowVoltage", "lowVoltage", "low"),
                    ("highVoltage", "highVoltage", "high"),
                    ("currentLimit", "currentLimit", "absolute")
                ]

                for key in limit_type_keys:
                    if key not in operational_limit_types:
                        limit_obj = OperationalLimitType(
                            rdf_root,
                            limit_name=key[0],
                            kind=key[1],
                            direction=key[2]
                        )
                        operational_limit_types[key] = limit_obj.create(CIM_NS)
                        operational_limit_set.link_to_limit_type(
                            operational_limit_types[key], CIM_NS)

                # Create specific limit values
                voltage_limit = VoltageLimit(
                    rdf_root,
                    voltage_limit_value="400.0",
                    terminal_id=terminal_id,
                    name=f"{eq_type} Voltage Limit"
                )
                voltage_limit.create(
                    CIM_NS,
                    operational_limit_set_id=operational_limit_set_id,
                    operational_limit_type_id=operational_limit_types[("highVoltage", "highVoltage", "high")]
                )

                current_limit = CurrentLimit(
                    rdf_root,
                    current_limit_value="200.0",
                    terminal_id=terminal_id,
                    name=f"{eq_type} Current Limit"
                )
                current_limit_id = current_limit.create(
                    CIM_NS,
                    operational_limit_set_id=operational_limit_set_id,
                    operational_limit_type_id=operational_limit_types[("currentLimit", "currentLimit", "absolute")]
                )
                current_limit_ids.append(current_limit_id)

            # Add geographical information
            coordinate_system_id = gl_profile.create_coordinate_system(cim_ns=CIM_NS)
            gl_profile.create_location_and_position(
                conducting_equipment_id, node_name,
                connection_point, CIM_NS, coordinate_system_id
            )

            # Set operational state in SV profile
            if state == "In Betrieb":
                sv_profile.create_sv_status(conducting_equipment_id, True, CIM_NS)
            elif state == "offnen":
                sv_profile.create_sv_status(conducting_equipment_id, False, CIM_NS)

        # --- Service Point (Load) Processing ---
        elif eq_type == "Service_Point":
            """
            Process service points (loads) with voltage-dependent characteristics.

            Creates:
            - LoadResponseCharacteristic (if new type)
            - ConformLoad
            - Terminal
            - GL location data
            """

            response_name = equipment.get('LOAD_RESPONSE_NAME', "DefaultResponse")
            if response_name not in load_response_characteristics:
                load_response = LoadResponseCharacteristic(
                    rdf_root,
                    name=response_name,
                    p_voltage_exponent=2,  # Typical voltage-squared dependence
                    q_voltage_exponent=2
                )
                load_response.create(CIM_NS)
                load_response_characteristics[response_name] = load_response.mrid

            # Create load with response characteristics
            conducting_equipment = ConformLoad(
                rdf_root,
                load_name=node_name,
                equipment_container_id=transformer.equipment_container_id,
                load_group_id=conform_load_group.mrid,
                load_response_id=load_response_characteristics[response_name]
            )
            conducting_equipment_id = conducting_equipment.create(CIM_NS)

            # Create terminal for load
            terminal = Terminal(
                rdf_root,
                name=node_name,
                conducting_equipment_id=conducting_equipment_id,
                sequence_number=1
            )
            terminal_id = terminal.create(CIM_NS)
            terminal_ids.append(terminal_id)
            terminal_map[connection_point].append(terminal_id)

            # Add geographical information
            coordinate_system_id = gl_profile.create_coordinate_system(cim_ns=CIM_NS)
            gl_profile.create_location_and_position(
                conducting_equipment_id, node_name,
                connection_point, CIM_NS, coordinate_system_id
            )

        # --- Battery Processing ---
        elif eq_type == "Consumer":
            """
            Process battery storage equipment.

            Creates:
            - BatteryUnit with power ratings
            - Terminal
            - GL location data
            """

            battery_kw = float(equipment.get('KW', 0))
            conducting_equipment = BatteryUnit(
                rdf_root,
                name=node_name,
                equipment_container_id=substation_id,
                rated_e=battery_kw * 1000,  # Convert kW to W
                max_p=battery_kw,  # Discharge limit
                min_p=-battery_kw * 0.01  # Charge limit (1% of capacity)
            )
            conducting_equipment_id = conducting_equipment.create(CIM_NS)

            # Create terminal for battery
            terminal = Terminal(
                rdf_root,
                name=node_name,
                conducting_equipment_id=conducting_equipment_id,
                sequence_number=1
            )
            terminal_id = terminal.create(CIM_NS)
            terminal_ids.append(terminal_id)
            terminal_map[connection_point].append(terminal_id)

            # Add geographical information
            coordinate_system_id = gl_profile.create_coordinate_system(cim_ns=CIM_NS)
            gl_profile.create_location_and_position(
                conducting_equipment_id, node_name,
                connection_point, CIM_NS, coordinate_system_id
            )

        # --- PV Generation Processing ---
        elif eq_type == "Generator":
            """
            Process photovoltaic generation equipment.

            Creates:
            - PhotoVoltaicUnit with generation limits
            - Terminal
            - GL location data
            """

            photovoltaic_kw = float(equipment.get('KW', 0))
            conducting_equipment = PhotoVoltaicUnit(
                rdf_root,
                name=node_name,
                equipment_container_id=substation_id,
                max_p=photovoltaic_kw,  # Generation limit
                min_p=-photovoltaic_kw * 0.01  # Small absorption capability
            )
            conducting_equipment_id = conducting_equipment.create(CIM_NS)

            # Create terminal for PV unit
            terminal = Terminal(
                rdf_root,
                name=node_name,
                conducting_equipment_id=conducting_equipment_id,
                sequence_number=1
            )
            terminal_id = terminal.create(CIM_NS)
            terminal_ids.append(terminal_id)
            terminal_map[connection_point].append(terminal_id)

            # Add geographical information
            coordinate_system_id = gl_profile.create_coordinate_system(cim_ns=CIM_NS)
            gl_profile.create_location_and_position(
                conducting_equipment_id, node_name,
                connection_point, CIM_NS, coordinate_system_id
            )

        else:
            continue  # Skip unrecognized equipment types

    def find_connected_connectivity_nodes(connectivity_node_map, terminal_map):
        """
        Identify electrically connected nodes in the power system network.

        Uses a graph algorithm to group terminals and connectivity nodes that are electrically connected,
        which is essential for proper topological representation in the CIM model.

        Args:
            connectivity_node_map (dict): Mapping of positions to ConnectivityNode IDs
            terminal_map (dict): Mapping of positions to Terminal IDs

        Returns:
            list: List of connected component groups where each group contains
                  terminal and connectivity node IDs that are electrically connected
        """
        connected_groups = []
        visited = set()
        connectivity_graph = defaultdict(list)

        # Ensure every terminal position has a corresponding ConnectivityNode
        for position, terminals in terminal_map.items():
            if position not in connectivity_node_map:
                # Create missing ConnectivityNode for this position
                connectivity_node = ConnectivityNode(
                    rdf_root,
                    node_name=position,
                    container_id=substation_id
                )
                connectivity_node_id = connectivity_node.create(CIM_NS)
                connectivity_node_map[position] = connectivity_node_id

            # Build adjacency graph between terminals and their connectivity nodes
            for terminal in terminals:
                connectivity_graph[terminal].append(connectivity_node_map[position])
                connectivity_graph[connectivity_node_map[position]].append(terminal)

        def dfs(node, group):
            """
            Depth-first search helper to traverse connectivity graph.

            Args:
                node (str): Current node (terminal or connectivity node ID)
                group (list): Current group of connected nodes
            """
            if node in visited:
                return
            visited.add(node)
            group.append(node)
            for neighbor in connectivity_graph.get(node, []):
                dfs(neighbor, group)

        # Find all connected components in the graph
        for node in connectivity_graph:
            if node not in visited:
                group = []
                dfs(node, group)
                connected_groups.append(group)

        return connected_groups

    # Create topological nodes based on electrical connectivity
    topo_groups = find_connected_connectivity_nodes(connectivity_node_map, terminal_map)

    # Dictionary to map first terminal in group to topological node ID
    topological_node_map = {}
    topo_node_counter = 0  # Counter for naming topological nodes

    for group in topo_groups:
        if group:
            # Create topological node with sequential naming
            node_name = f"TopoNode {topo_node_counter}"
            topological_node = TopologicalNode(
                topology_rdf_root,
                name=node_name,
                base_voltage_id=secondary_base_voltage_id,
                equipment_container_id=conducting_equipment_id
            )
            topological_node_id = topological_node.create(CIM_NS)
            topological_node_ids.append(topological_node_id)

            # Connect all terminals in group to this topological node
            for terminal_id in group:
                # Find connectivity node for this terminal
                cn_id = None
                for pos, terminals in terminal_map.items():
                    if terminal_id in terminals:
                        cn_id = connectivity_node_map.get(pos)
                        break

                # Link connectivity node if found
                if cn_id:
                    topological_node.create_connectivity_node(
                        cn_id,
                        topological_node_id,
                        CIM_NS
                    )

                # Link terminal to topological node
                topological_node.create_terminal(
                    terminal_id,
                    topological_node_id,
                    CIM_NS
                )

            # Store mapping (using first terminal as key)
            topological_node_map[group[0]] = topological_node_id
            topo_node_counter += 1

    # Create Steady-State Hypothesis (SSH) profile
    ssh_profile = SSHProfile(ssh_rdf_root)

    # Create SSH representations for all terminals
    for position, terminal_list in terminal_map.items():
        for terminal_id in terminal_list:
            ssh_profile.create_terminal(terminal_id, CIM_NS)

    # Create SSH representations for current limits
    for current_limit in current_limit_ids:
        ssh_profile.create_current_limit(current_limit, cim_ns=CIM_NS)

    # Create State Variable (SV) power flow measurements
    for position, terminal_list in terminal_map.items():
        for terminal_id in terminal_list:
            p = 0.0037  # Default active power value (MW)
            q = 0.0014  # Default reactive power value (MVAr)
            sv_profile.create_sv_power_flow(terminal_id, p, q, CIM_NS)

    # Create SV status for switching equipment
    for equipment in root.findall('.//Riser'):
        equipment_id = equipment.get('ID')
        in_service = equipment.get('status') == 'in_service'
        sv_profile.create_sv_status(transformer.mrid, in_service, CIM_NS)

    # Create SV voltage measurements for topological nodes
    for node_id in topological_node_ids:
        angle = -145.647  # Default voltage angle (degrees)
        v = 0.404691  # Default voltage magnitude (pu)
        sv_profile.create_sv_voltage(node_id, angle, v, CIM_NS)

    # Create Diagram Layout (DL) objects
    for diagram_id, seq_num, x_pos, y_pos in diagram_positions:
        diagram_object_point = DiagramObjectPoint(
            diagram_rdf_root,
            diagram_object_id=diagram_id,
            sequence_number=seq_num,
            x_position=x_pos,
            y_position=y_pos
        )
        diagram_object_point.create(CIM_NS)
