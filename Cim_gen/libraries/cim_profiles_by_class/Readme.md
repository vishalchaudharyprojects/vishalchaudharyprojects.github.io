CIM Profiles by Class -
The cim_profiles_by_class library provides a modular, Python-based implementation of key CIM (Common Information Model) classes, conforming to CGMES (Common Grid Model Exchange Standard) specifications. It enables users to construct CIM-compliant XML representations of electrical grid components for model exchange, analysis, or integration with energy management systems.

This library is particularly useful in grid modeling, digital substations, and simulation tools where CIM-compliant data exchange is required.

Key Features -

- Modular structure: Each Python module represents a CIM class (e.g., ACLineSegment, BaseVoltage, BatteryUnit, etc.).

- Standards compliant: Implements attributes and structure based on CGMES profiles.

- RDF/XML ready: Generates XML elements using RDF syntax suitable for CIM-based systems.

- UUID-based identity: Each object has a unique mRID generated using uuid.

- Designed for extensibility and integration into larger CIM export pipelines.

For more Information about the equipments about how they are structured in this library, please look into the python scripts of the equipments itself. They are self explantory.

The step-by-step process of the library -
1. Starting with main.py, we have to got to the getData function to create the CIM files for the Master grid xml, which we recieved from the GIS.
2. We should make sure that ConfigData["PyToolchainConfig"]["grid"]["input_dataformat"] == "gis", so that we can access the Master xml and and parse it accordingly.
3. There, we are accessing the gis_to_cim2 function which converts the GIS Data to CIM-compliant power system modeling.
4. First, we have defined the namespaces as CIM_NS, RDF_NS and afterwards we are getting the root from the master xml and start parsing.
5. We are creating root elements for all of the required CIM profiles as ssh_rdf_rot, sv_rdf_root,etc, so that we can link the profiles by using the specific roots.
6. Afterwards, we are creating base voltages, transformers, substaion_id using the process_transformers function.
7. Once, the powertransformer is creating then,from there we go to create specific equipments such as battery unit, ac line segment using process_equipment function.
8. and lastly, we have the save_xml function to save all the equipments and their information in the specific profiles as per CIM CGMES compliant standard.