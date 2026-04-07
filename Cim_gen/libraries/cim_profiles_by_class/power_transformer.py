from .base import CIMObject, create_element
import uuid

class PowerTransformer(CIMObject):
    def __init__(self, rdf_root, station_name):
        super().__init__(rdf_root)
        self.station_name = station_name
        self.mrid = str(uuid.uuid4())
        self.terminal_id = str(uuid.uuid4())
        self.equipment_container_id = str(uuid.uuid4())
        self.region_id = str(uuid.uuid4())

    def create_substation(self, cim_ns, geographical_region_name, sub_geographical_region_name):
        geographical_region_id = self.create_geographical_region(cim_ns, geographical_region_name)
        sub_geographical_region_id = self.create_subgeographical_region(cim_ns, sub_geographical_region_name, geographical_region_id)
        substation = create_element(cim_ns, "Substation", {"rdf:ID": f"_{self.equipment_container_id}"})
        substation.append(create_element(cim_ns, "IdentifiedObject.mRID", text=self.equipment_container_id))
        substation.append(create_element(cim_ns, "IdentifiedObject.name", text=self.station_name))
        substation.append(create_element(cim_ns, "Substation.Region", {"rdf:resource": f"#_{sub_geographical_region_id}"}))
        self.append_to_root(substation)
        return self.equipment_container_id

    def create_geographical_region(self, cim_ns, region_name):
        geographical_region_id = str(uuid.uuid4())
        geographical_region = create_element(cim_ns, "GeographicalRegion", {"rdf:ID": f"_{geographical_region_id}"})
        geographical_region.append(create_element(cim_ns, "IdentifiedObject.mRID", text=geographical_region_id))
        geographical_region.append(create_element(cim_ns, "IdentifiedObject.name", text=region_name))
        self.append_to_root(geographical_region)
        return geographical_region_id

    def create_subgeographical_region(self, cim_ns, sub_region_name, geographical_region_id):
        sub_geographical_region_id = str(uuid.uuid4())
        sub_geographical_region = create_element(cim_ns, "SubGeographicalRegion", {"rdf:ID": f"_{sub_geographical_region_id}"})
        sub_geographical_region.append(create_element(cim_ns, "IdentifiedObject.mRID", text=sub_geographical_region_id))
        sub_geographical_region.append(create_element(cim_ns, "IdentifiedObject.name", text=sub_region_name))
        sub_geographical_region.append(create_element(cim_ns, "SubGeographicalRegion.Region", {"rdf:resource": f"#_{geographical_region_id}"}))
        self.append_to_root(sub_geographical_region)
        return sub_geographical_region_id

    def create_voltage_level(self, cim_ns, voltage_name, base_voltage_id):
        voltage_level_id = str(uuid.uuid4())
        voltage_level = create_element(cim_ns, "VoltageLevel", {"rdf:ID": f"_{voltage_level_id}"})
        voltage_level.append(create_element(cim_ns, "IdentifiedObject.mRID", text=voltage_level_id))
        voltage_level.append(create_element(cim_ns, "IdentifiedObject.name", text=voltage_name))
        voltage_level.append(create_element(cim_ns, "VoltageLevel.BaseVoltage", {"rdf:resource": f"#_{base_voltage_id}"}))
        voltage_level.append(create_element(cim_ns, "VoltageLevel.Substation", {"rdf:resource": f"#_{self.mrid}"}))
        self.append_to_root(voltage_level)
        return voltage_level_id

    def create(self, cim_ns):
        transformer = create_element(cim_ns, "PowerTransformer", {"rdf:ID": f"_{self.mrid}"})
        transformer.append(create_element(cim_ns, "IdentifiedObject.mRID", text=self.mrid))
        transformer.append(create_element(cim_ns, "IdentifiedObject.name", text=self.station_name))
        transformer.append(create_element(cim_ns, "PowerTransformer.isPartOfGeneratorUnit", text="false"))
        transformer.append(create_element(cim_ns, "PowerTransformer.operationalValuesConsidered", text="false"))
        transformer.append(create_element(cim_ns, "Equipment.EquipmentContainer", {"rdf:resource": f"_{self.equipment_container_id}"}))
        self.append_to_root(transformer)
        return self.mrid

    def create_power_transformer_end(self, windings_data, base_voltage_id, transformer_id, schaltung, p_sc, p_oc, v_sc,
                                     cim_ns):
        """
        Creates winding elements (PowerTransformerEnd) and associated terminal elements for the transformer.

        Args:
            windings_data (list): A list of tuples containing winding data in the format
                                  (end_number, voltage, rated_s).
            base_voltage_id (tuple): A tuple of base voltage IDs for the primary and secondary windings.
            transformer_id (str): The unique identifier of the PowerTransformer.
            schaltung (str): The connection type (e.g., YN5, DY11) of the transformer.
            p_sc (float): The short-circuit loss of the transformer.
            p_oc (float): The open-circuit loss of the transformer.
            cim_ns (str): The CIM namespace used in the RDF document.
        """
        # Extract primary (high) voltage from windings_data
        primary_voltage = windings_data[0][1]  # First element's voltage is the high voltage
        primary_rated_power = windings_data[0][2]  # Rated power is same for both windings

        # Calculate rated current using primary (high) voltage
        rated_current = float(primary_rated_power) / (
                (float(primary_voltage) * 1000) * 3 ** 0.5)  # I_rated = S_rated / (sqrt(3) * V_primary)

        terminal_ids = []
        # Iterating over each winding data
        for end_number, voltage, rated_s in windings_data:
            winding_id = f"_{end_number}{self.mrid}"
            winding = create_element(cim_ns, "PowerTransformerEnd", {"rdf:ID": winding_id})
            winding.append(create_element(cim_ns, "IdentifiedObject.mRID", text=winding_id))
            winding.append(
                create_element(cim_ns, "IdentifiedObject.name", text=f"{self.station_name}_winding_{end_number}"))
            winding.append(create_element(cim_ns, "PowerTransformerEnd.ratedU", text=voltage))
            winding.append(create_element(cim_ns, "PowerTransformerEnd.ratedS", text=rated_s))
            winding.append(
                create_element(cim_ns, "PowerTransformerEnd.PowerTransformer", {"rdf:resource": f"#_{transformer_id}"}))

            # Assign the appropriate base voltage (primary or secondary)
            base_voltage = base_voltage_id[0] if end_number == 1 else base_voltage_id[1]
            winding.append(create_element(cim_ns, "TransformerEnd.BaseVoltage", {"rdf:resource": f"#_{base_voltage}"}))

            # Determine and append the connection type
            connection_type = self.get_winding_type(schaltung[:2] if end_number == 1 else schaltung[2:], cim_ns)
            winding.append(connection_type)

            # Extract phase angle clock from schaltung (e.g., last character)
            phase_angle_clock = schaltung[-1] if schaltung[-1].isdigit() else "0"
            winding.append(create_element(cim_ns, "PowerTransformerEnd.phaseAngleClock", text=phase_angle_clock))

            # Grounding logic based on schaltung
            is_grounded = "true" if ("n" in schaltung and end_number == 2) else "false"
            winding.append(create_element(cim_ns, "TransformerEnd.grounded", text=is_grounded))

            # Calculate impedance (resistance and reactance) only for primary side (end_number == 1)
            if end_number == 1:  # Primary winding
                z_k = (float(v_sc) / 100) * ((float(primary_voltage) * 1000) ** 2) / float(
                    rated_s)  # Z_k = (V_sc/100) * V_primary^2 / S_rated
                r_k = float(p_sc) / (3 * (rated_current ** 2))  # R_k = P_sc / I_rated^2
                x_k = (z_k ** 2 - r_k ** 2) ** 0.5  # X_k = sqrt(Z_k^2 - R_k^2)

                # Append calculated impedance values to primary winding
                winding.append(create_element(cim_ns, "PowerTransformerEnd.r", text=str(r_k)))
                winding.append(create_element(cim_ns, "PowerTransformerEnd.x", text=str(x_k)))
                winding.append(create_element(cim_ns, "PowerTransformerEnd.g", text='0'))
                winding.append(create_element(cim_ns, "PowerTransformerEnd.b", text='0'))
                winding.append(create_element(cim_ns, "PowerTransformerEnd.r0", text='0'))
                winding.append(create_element(cim_ns, "PowerTransformerEnd.x0", text='0'))
                winding.append(create_element(cim_ns, "PowerTransformerEnd.b0", text='0'))
                winding.append(create_element(cim_ns, "PowerTransformerEnd.g0", text='0'))
                # Create and append the ratio tap changer element
                ratio_tap_changer_id = str(uuid.uuid4())
                ratio_tap_changer_element = create_element(
                    cim_ns, "RatioTapChanger", {"rdf:ID": f"_{ratio_tap_changer_id}"})
                ratio_tap_changer_element.append(
                    create_element(cim_ns, "RatioTapChanger.stepVoltageIncrement", text="2.5"))
                ratio_tap_changer_element.append(
                    create_element(cim_ns, "TapChanger.highStep", text="2"))
                ratio_tap_changer_element.append(
                    create_element(cim_ns, "TapChanger.neutralStep", text="0"))
                ratio_tap_changer_element.append(
                    create_element(cim_ns, "TapChanger.lowStep", text="2"))
                ratio_tap_changer_element.append(
                    create_element(cim_ns, "TapChanger.normalStep", text="1"))
                ratio_tap_changer_element.append(
                    create_element(cim_ns, "TapChanger.neutralU", text="20"))
                ratio_tap_changer_element.append(
                    create_element(cim_ns, "TapChanger.ltcFlag", text="false"))
                ratio_tap_changer_element.append(create_element(
                    cim_ns, "IdentifiedObject.mRID", text=ratio_tap_changer_id))
                ratio_tap_changer_element.append(
                    create_element(
                        cim_ns, "IdentifiedObject.name", text=f"{self.station_name} Trafo {end_number}"))
                ratio_tap_changer_element.append(
                    create_element(cim_ns, "RatioTapChanger.TransformerEnd", {"rdf:resource": f"#{winding_id}"}))
                self.append_to_root(ratio_tap_changer_element)

            else:  # Secondary winding: Set all impedance-related values to 0
                winding.append(create_element(cim_ns, "PowerTransformerEnd.r", text='0'))
                winding.append(create_element(cim_ns, "PowerTransformerEnd.x", text='0'))
                winding.append(create_element(cim_ns, "PowerTransformerEnd.g", text='0'))
                winding.append(create_element(cim_ns, "PowerTransformerEnd.b", text='0'))
                winding.append(create_element(cim_ns, "PowerTransformerEnd.r0", text='0'))
                winding.append(create_element(cim_ns, "PowerTransformerEnd.x0", text='0'))
                winding.append(create_element(cim_ns, "PowerTransformerEnd.b0", text='0'))
                winding.append(create_element(cim_ns, "PowerTransformerEnd.g0", text='0'))

            # Generate and assign a unique terminal ID
            terminal_id = str(uuid.uuid4())
            winding.append(create_element(cim_ns, "TransformerEnd.Terminal", {"rdf:resource": f"#_{terminal_id}"}))
            winding.append(create_element(cim_ns, "TransformerEnd.endNumber", text=str(end_number)))

            self.append_to_root(winding)

            # Create and append the Terminal element
            terminal_element = create_element(cim_ns, "Terminal", {"rdf:ID": f"_{terminal_id}"})
            terminal_element.append(create_element(cim_ns, "ACDCTerminal.sequenceNumber", text="1"))
            terminal_element.append(create_element(cim_ns, "IdentifiedObject.mRID", text=terminal_id))
            terminal_element.append(
                create_element(cim_ns, "IdentifiedObject.name", text=f"{self.station_name} Terminal {end_number}"))
            terminal_element.append(
                create_element(cim_ns, "Terminal.ConductingEquipment", {"rdf:resource": f"#_{transformer_id}"}))
            self.append_to_root(terminal_element)

            terminal_ids.append(terminal_id)
        return terminal_ids

    def get_winding_type(self, schaltung, cim_ns):
        """
        Determines the connection type of the transformer winding based on the `schaltung`.

        Args:
            schaltung (str): The connection type string (e.g., YN, D, Z).
            cim_ns (str): The CIM namespace used in the RDF document.

        Returns:
            ElementTree.Element: The XML element representing the winding connection kind.
        """
        mapping = {
            "YN": "WindingConnection.Yn",
            "D": "WindingConnection.D",
            "Z": "WindingConnection.Z",
            "Y": "WindingConnection.Y",
            "ZD": "WindingConnection.Zd",
            "YD": "WindingConnection.Yd",
            "ZZ": "WindingConnection.Zz",
            "YY": "WindingConnection.Yy"
        }
        return create_element(cim_ns, "PowerTransformerEnd.connectionKind", {
            "rdf:resource": f"http://iec.ch/TC57/CIM100#{mapping.get(schaltung.strip(), 'WindingConnection.Yn')}"})

    def create_external_injection(self, cim_ns, external_injection_name, base_voltage_id, substation_id):
        """
        Creates an ExternalNetworkInjection element in the RDF document.

        Args:
            cim_ns (str): The CIM namespace used in the RDF document.
            external_injection_name (str): The name of the ExternalNetworkInjection.
            equipment_container_id (str): The ID of the associated EquipmentContainer.

        Returns:
            str: The unique ID of the created ExternalNetworkInjection.
        """
        injection_id = str(uuid.uuid4())
        voltage_level_id = str(uuid.uuid4())
        regulating_control_id = str(uuid.uuid4())
        top_id = str(uuid.uuid4())
        external_injection = create_element(cim_ns, "ExternalNetworkInjection", {"rdf:ID": f"_{injection_id}"})
        external_injection.append(create_element(cim_ns, "IdentifiedObject.mRID", text=injection_id))
        external_injection.append(create_element(cim_ns, "IdentifiedObject.name", text=external_injection_name))
        external_injection.append(
            create_element(cim_ns, "Equipment.EquipmentContainer", {"rdf:resource": f"#_{voltage_level_id}"}))

        # Add specific attributes
        attributes = {
            "governorSCD": "0",
            "maxInitialSymShCCurrent": "288675",
            "minInitialSymShCCurrent": "230940",
            "maxP": "100000",
            "minP": "0",
            "maxQ": "9999",
            "minQ": "-9999",
            "maxR0ToX0Ratio": "0.1",
            "minR0ToX0Ratio": "0.1",
            "maxR1ToX1Ratio": "0.1",
            "minR1ToX1Ratio": "0.1",
            "maxZ0ToZ1Ratio": "1",
            "minZ0ToZ1Ratio": "1",
        }
        for key, value in attributes.items():
            external_injection.append(create_element(cim_ns, f"ExternalNetworkInjection.{key}", text=value))
        external_injection.append(
            create_element(cim_ns, "RegulatingCondEq.RegulatingControl",
                           {"rdf:resource": f"#_{regulating_control_id}"}))
        self.append_to_root(external_injection)
        voltage_level = create_element(cim_ns, "VoltageLevel", {"rdf:ID": f"_{voltage_level_id}"})
        voltage_level.append(create_element(cim_ns, "IdentifiedObject.mRID", text=voltage_level_id))
        voltage_level.append(create_element(cim_ns, "IdentifiedObject.name", text='medium_voltage'))
        voltage_level.append(
            create_element(cim_ns, "VoltageLevel.BaseVoltage", {"rdf:resource": f"#_{base_voltage_id}"}))
        voltage_level.append(create_element(cim_ns, "VoltageLevel.Substation", {"rdf:resource": f"#_{substation_id}"}))
        self.append_to_root(voltage_level)
        busbar_id = str(uuid.uuid4())
        # Create the BusbarSection element with a unique ID
        busbar_section = create_element(cim_ns, "BusbarSection", {"rdf:ID": f"_{busbar_id}"})

        # Add the mRID (unique identifier) for the BusbarSection
        busbar_section.append(create_element(cim_ns, "IdentifiedObject.mRID", text=busbar_id))

        # Add the name of the BusbarSection
        busbar_section.append(create_element(cim_ns, "IdentifiedObject.name", text='Medium_voltage_bus'))
        # Add a reference to the equipment container that this BusbarSection belongs to
        busbar_section.append(
            create_element(cim_ns, "Equipment.EquipmentContainer", {"rdf:resource": f"_{voltage_level_id}"}))

        # Append the created BusbarSection to the RDF root element
        self.append_to_root(busbar_section)

        return injection_id, regulating_control_id, voltage_level_id

    def create_regulating_control(self, control_id, cim_ns, regulating_control_name, terminal_id):
        """
        Creates a RegulatingControl element in the RDF document.

        Args:
            cim_ns (str): The CIM namespace used in the RDF document.
            regulating_control_name (str): The name of the RegulatingControl.
            terminal_id (str): The ID of the associated Terminal.

        Returns:
            str: The unique ID of the created RegulatingControl.
        """
        regulating_control = create_element(cim_ns, "RegulatingControl", {"rdf:ID": f"_{control_id}"})
        regulating_control.append(create_element(cim_ns, "IdentifiedObject.mRID", text=control_id))
        regulating_control.append(create_element(cim_ns, "IdentifiedObject.name", text=regulating_control_name))
        regulating_control.append(
            create_element(cim_ns, "RegulatingControl.Terminal", {"rdf:resource": f"#_{terminal_id}"}))
        regulating_control.append(create_element(cim_ns, "RegulatingControl.mode", {
            "rdf:resource": "http://iec.ch/TC57/CIM100#RegulatingControlModeKind.voltage"}))
        self.append_to_root(regulating_control)
        return control_id

    def create_terminal(self, cim_ns, terminal_name, equipment_id):
        terminal_id = str(uuid.uuid4())
        cn_id = str(uuid.uuid4())
        terminal_element = create_element(cim_ns, "Terminal", {"rdf:ID": f"_{terminal_id}"})
        terminal_element.append(create_element(cim_ns, "ACDCTerminal.sequenceNumber", text="1"))
        terminal_element.append(create_element(cim_ns, "IdentifiedObject.mRID", text=terminal_id))
        terminal_element.append(create_element(cim_ns, "IdentifiedObject.name", text=terminal_name))
        terminal_element.append(
            create_element(cim_ns, "Terminal.ConductingEquipment", {"rdf:resource": f"#_{equipment_id}"}))
        terminal_element.append(create_element(cim_ns, "Terminal.ConnectivityNode", {"rdf:resource": f"#_{cn_id}"}))
        terminal_element.append(
            create_element(cim_ns, "Terminal.phases", {"rdf:resource": "http://iec.ch/TC57/CIM100#PhaseCode.ABC"}))
        self.rdf_root.append(terminal_element)
        return terminal_id, cn_id

    def create_connectivity_node(self, cim_ns, node_name, cn_id):
        container_id = str(uuid.uuid4())
        connectivity_node = create_element(cim_ns, "ConnectivityNode", {"rdf:ID": f"_{cn_id}"})
        connectivity_node.append(create_element(cim_ns, "IdentifiedObject.mRID", text=cn_id))
        connectivity_node.append(create_element(cim_ns, "IdentifiedObject.name", text=node_name))
        connectivity_node.append(create_element(cim_ns, "ConnectivityNode.ConnectivityNodeContainer",
                                                {"rdf:resource": f"_{container_id}"}))
        self.append_to_root(connectivity_node)
        return cn_id, container_id