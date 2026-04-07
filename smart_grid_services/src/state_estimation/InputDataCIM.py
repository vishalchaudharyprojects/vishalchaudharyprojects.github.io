import os.path
import pandas as pd
import logging
import cimpy
import math
from minio import Minio
from dotenv import load_dotenv
from urllib.parse import urlparse
from lxml import etree

logging.getLogger('cimpy').setLevel(logging.ERROR)
def inputGridData(ConfigData, gridData, new_import_result={}, error_tolerance=0.0):

    # check input data source
    if ConfigData['PyToolchainConfig']['grid']['input_datasource'] == 'local':
        grid_files = '/app/Grids/' + ConfigData['PyToolchainConfig']['grid']['name'] + '/' + ConfigData['PyToolchainConfig']['grid']['input_dataformat'].upper() + '/'
        # store a list of all cim files in the directory
        file_list = os.listdir(grid_files)

        GL = False

        # determine file names to the provided cim profile
        for file in file_list:
            filename = file.split('_')
            for abbr in filename:
                if abbr == 'DL' or abbr == 'DI' or 'DL' in abbr or 'DI' in abbr:
                    DL_file = file
                elif abbr == 'EQ' or 'EQ' in abbr:
                    EQ_file = file
                elif abbr == 'SSH' or 'SSH' in abbr:
                    SSH_file = file
                elif abbr == 'SV' or 'SV' in abbr:
                    SV_file = file
                elif abbr == 'TP' or 'TP' in abbr:
                    TP_file = file
                elif abbr == 'GL' or 'GL' in abbr:
                    GL_file = file
                    GL = True
                elif 'GL' not in abbr and 'DI' not in abbr and 'DL' not in abbr:
                    GL == False

        if GL:
            xml_files = [
                grid_files + EQ_file,
                grid_files + SSH_file,
                grid_files + SV_file,
                grid_files + TP_file,
                grid_files + DL_file,
                grid_files + GL_file,
            ]

        else:
            xml_files = [
                grid_files + EQ_file,
                grid_files + SSH_file,
                grid_files + SV_file,
                grid_files + TP_file,
            ]

    elif ConfigData['PyToolchainConfig']['grid']['input_datasource'] == 's3':
        # Load environment variables from .env file
        load_dotenv()

        # Parse MINIO_URL
        minio_url = os.getenv("MINIO_URL")  # Should be something like 'http://minio:9000'
        parsed_url = urlparse(minio_url)

        # Validate MINIO_URL
        if parsed_url.path != "":
            raise FileExistsError("path in MINIO_URL is not allowed")

        # Initialize MinIO client with extracted hostname and port
        minio_client = Minio(
            endpoint=f"{parsed_url.hostname}:{parsed_url.port}",
            access_key=os.getenv("ACCESS_KEY"),
            secret_key=os.getenv("SECRET_KEY"),
            secure=parsed_url.scheme == "https"
        )

        # Get grid name and construct the expected folder path in S3
        grid_name = ConfigData['PyToolchainConfig']['grid']['name']
        grid_folder_prefix = grid_name

        # List objects in the grid's folder
        objects = minio_client.list_objects('s3-bucket', prefix=grid_folder_prefix, recursive=True)
        # get the file list
        file_list = [obj.object_name for obj in objects if obj.object_name.endswith('.xml')]

        print("Files in the s3 bucket found", file_list)

        # Download the XML files locally
        os.makedirs(grid_folder_prefix, exist_ok=True)

        for file_obj in file_list:
            # get the name of the object in the file list
            try:
                split_string = file_obj.rsplit("/", 1)
                local_file_path = os.path.join("Base_Module/InputDataScripts", grid_folder_prefix, "", split_string[-1])
                minio_client.fget_object(bucket_name='s3-bucket', object_name=file_obj, file_path=local_file_path)
            except Exception as e:
                raise Exception(f"XML-file {file_obj} is not found. Error {e} occured.")


        DL_file, EQ_file, SSH_file, SV_file, TP_file, GL_file = None, None, None, None, None, None
        GL = False

        #iterate over local files and parse them
        for file_name in file_list:
            #local_file_path = os.path.join(grid_folder_prefix, os.path.basename(file_name)
            try:
                etree.parse(file_name)  # Try parsing the file
                print(f"{file_name} is valid XML.")
            except etree.XMLSyntaxError as xml_error:
                raise Exception(f"XML-file {file_obj} could not be parsed. Incorrect XML-structure with Error {xml_error} found.")

            # Parse filenames and categorize them
            basename = os.path.basename(file_name)  # Extract the file name with extension
            if 'DL' in basename:
                DL_file = file_name  # Use the full S3 key for later operations
            elif 'EQ' in basename:
                EQ_file = file_name
            elif 'SSH' in basename:
                SSH_file = file_name
            elif 'SV' in basename:
                SV_file = file_name
            elif 'TP' in basename:
                TP_file = file_name
            elif 'GL' in basename:
                GL_file = file_name
                GL = True

        # Construct the list of XML files using the full S3 keys
        xml_files = []
        if EQ_file:
            xml_files.append(os.path.join(grid_folder_prefix, os.path.basename(EQ_file)))
        if SSH_file:
            xml_files.append(os.path.join(grid_folder_prefix, os.path.basename(SSH_file)))
        if SV_file:
            xml_files.append(os.path.join(grid_folder_prefix, os.path.basename(SV_file)))
        if TP_file:
            xml_files.append(os.path.join(grid_folder_prefix, os.path.basename(TP_file)))
        if DL_file:
            xml_files.append(os.path.join(grid_folder_prefix, os.path.basename(DL_file)))
        if GL and GL_file:
            xml_files.append(os.path.join(grid_folder_prefix, os.path.basename(GL_file)))

        print("Prepared XML files for import:", xml_files)

    # Import XML files using cimpy
    if ConfigData['PyToolchainConfig']['grid']['input_dataformat'] == 'cim3':
        import_result = cimpy.cim_import(xml_files, "cgmes_v3_0")
        print("CIM3")
    elif ConfigData['PyToolchainConfig']['grid']['input_dataformat'] == 'cim2':
        import_result = cimpy.cim_import(xml_files, "cgmes_v2_4_15")
        print('CIM2_4_15')
    print(">>> DEBUG xml_files:", xml_files)

    # Error catching for successful import
    if import_result['topology'] == {}:
        raise TypeError("CIMPY Import unsuccessful. No objects were created. Abort Execution of program")

    # bus_branch_import_result = cimpy.utils.node_breaker_to_bus_branch(import_result)


    for key, value in import_result['topology'].items():
        if value.__class__.__name__ == "OperationalLimitType":
            if value.name in "patl":
                value.limitType = "http://entsoe.eu/CIM/SchemaExtension/3/1#LimitTypeKind.patl"
            elif value.name in "highVoltage":
                value.limitType = "http://entsoe.eu/CIM/SchemaExtension/3/1#LimitTypeKind.highVoltage"
    for key, value in import_result['topology'].items():
        if value.__class__.__name__ == "Terminal":
            value.possibleProfileList['class'] = [4, 0, 1, 2]
            if 'SvPowerFlow' in value.possibleProfileList:
                del value.possibleProfileList['SvPowerFlow']
    for key, value in import_result['topology'].items():
        if value.__class__.__name__ == "TopologicalNode":
            value.possibleProfileList['class'] = [2]
            if 'SvInjection' in value.possibleProfileList:
                del value.possibleProfileList['SvInjection']
            if 'SvVoltage' in value.possibleProfileList:
                del value.possibleProfileList['SvVoltage']
            if 'TopologicalIsland' in value.possibleProfileList:
                del value.possibleProfileList['TopologicalIsland']
    for key, value in import_result['topology'].items():
        if value.__class__.__name__ == "BaseVoltage":
            value.possibleProfileList['class'] = [0]
            if 'TopologicalNode' in value.possibleProfileList:
                del value.possibleProfileList['TopologicalNode']

    # due to the DiagramObject-problem of PowerFactory-export, value of IdentifiedObject is set to correct object
    for key, value in import_result['topology'].items():
        if value.__class__.__name__ == "DiagramObject":
            if value.IdentifiedObject.__class__.__name__ == "ConnectivityNode":
                if value.IdentifiedObject.TopologicalNode is not None:
                    value.IdentifiedObject = value.IdentifiedObject.TopologicalNode

    # due to the voltageLevel-problem of PowerFactory-export, faulty nodes get referenced their correct voltageLevel-object
    for key, value in import_result['topology'].items():
        if value.__class__.__name__ == "TopologicalNode":
            bv_mRID = value.BaseVoltage.mRID
            if (bv_mRID != value.ConnectivityNodeContainer.BaseVoltage.mRID) and (value.ConnectivityNodeContainer.name != value.name):
                for inner_key, inner_value in import_result['topology'].items():
                    if inner_value.__class__.__name__ == "VoltageLevel":
                        if (inner_value.BaseVoltage.mRID == bv_mRID) and (inner_value.name == value.name):
                            value.ConnectivityNodeContainer = inner_value
                            inner_value.TopologicalNode = [value]

    # fill header of dataframes
    gridData['gridConfig'] = pd.DataFrame(columns=['sbGrid_mva', 'vnGrid_kv', 'extGridSetpoint_pu', 'extGridSetpoint_angle', 'extGridNode', 'maxP', 'minP', 'maxQ', 'minQ', 'maxSc_mva', 'minSc_mva', 'maxRX_ratio', 'minRX_ratio', 'auxiliary_node'])
    gridData['busData'] = pd.DataFrame(columns=['busName', 'voltageLevel'])
    gridData['topology'] = pd.DataFrame(columns=['name', 'node_i', 'node_j', 'parallelDevices', 'type', 'length_km', 'bay_i', 'bay_j'])
    gridData['lineTypes'] = pd.DataFrame(columns=['name', 'r_ohm_km', 'x_ohm_km', 'b_miks_km', 'g_miks_km', 'iMax_ka', 'vRated_kv'])
    gridData['transformers'] = pd.DataFrame(columns=['name', 'hvBus', 'lvBus', 'hvBus_kv', 'lvBus_kv', 'type', 'tapPos', 'bay_i', 'bay_j'])
    gridData['transformerTypes'] = pd.DataFrame(columns=['type', 'sn_mva', 'r_ohm', 'x_ohm', 'pfe_kw', 'tap_step_percent', 'phaseShift'])
    gridData['loads'] = pd.DataFrame(columns=['name', 'busConnected', 'p_mw', 'q_mvar'])
    gridData['gens'] = pd.DataFrame(columns=['name', 'busConnected', 'p_mw', 'q_mvar'])
    gridData['measTopology'] = pd.DataFrame(columns=['type', 'node_i', 'node_j'])
    gridData['switches'] = pd.DataFrame(columns=['name', 'line', 'node_i', 'status', 'connected_to_line'])

    # fill gridConfig
    sbGrid_mva = 100  # TODO: not available in CIM_export-

    # check if mRID-attribute is the same as key
    for key, value in import_result['topology'].items():
        if hasattr(value, 'mRID'):
            value.mRID = key

    for key, value in import_result['topology'].items():
        if value.__class__.__name__ == "ExternalNetworkInjection":
            vnGrid_kv = value.EquipmentContainer.BaseVoltage.nominalVoltage
            extGridSetpoint_pu = value.RegulatingControl.targetValue/vnGrid_kv
            if len(value.EquipmentContainer.TopologicalNode) > 1:
                if value.EquipmentContainer.TopologicalNode[0].BaseVoltage.nominalVoltage > value.EquipmentContainer.TopologicalNode[1].BaseVoltage.nominalVoltage:
                    node = 0
                else:
                    node = 1
            else:
                node = 0
            extGridNode = value.EquipmentContainer.TopologicalNode[node].name
            node_mRID = value.EquipmentContainer.TopologicalNode[node].mRID
            for inner_key, inner_value in import_result['topology'].items():
                if inner_value.__class__.__name__ == "SvVoltage":
                    if inner_value.TopologicalNode.mRID == node_mRID:
                        extGridSetpoint_angle = inner_value.angle

            maxP = value.maxP
            minP = value.minP
            maxQ = value.maxQ
            minQ = value.minQ

            maxSc_mva = (value.maxInitialSymShCCurrent/1000)*value.EquipmentContainer.BaseVoltage.nominalVoltage*math.sqrt(3)
            minSc_mva = (value.minInitialSymShCCurrent/1000)*value.EquipmentContainer.BaseVoltage.nominalVoltage*math.sqrt(3)
            maxRX_ratio = value.maxR0ToX0Ratio
            minRX_ratio = value.minR0ToX0Ratio

            if maxSc_mva == float(0.0):
                maxSc_mva = 1
            if minSc_mva == float(0.0):
                minSc_mva = 1
            if maxRX_ratio == float(0.0):
                maxRX_ratio = 0.1
            if minRX_ratio == float(0.0):
                minRX_ratio = 0.1


            # deprecated python 3.7 command
            #gridData['gridConfig'] = gridData['gridConfig'].append(
            #    {'sbGrid_mva': sbGrid_mva, 'vnGrid_kv': vnGrid_kv,
            #     'extGridSetpoint_pu': extGridSetpoint_pu, 'extGridSetpoint_angle': extGridSetpoint_angle,
            #     'extGridNode': extGridNode, 'maxP': maxP, 'minP': minP, 'maxQ': maxQ, 'minQ': minQ,
            #     'maxSc_mva': maxSc_mva, 'minSc_mva': minSc_mva, 'maxRX_ratio': maxRX_ratio, 'minRX_ratio': minRX_ratio,
            #     'auxiliary_node': ConfigData['PyToolchainConfig']['grid']['auxiliary_nodes']}, ignore_index=True)


            new_row = pd.DataFrame([{'sbGrid_mva': sbGrid_mva, 'vnGrid_kv': vnGrid_kv,
                                     'extGridSetpoint_pu': extGridSetpoint_pu,
                                     'extGridSetpoint_angle': extGridSetpoint_angle,
                                     'extGridNode': extGridNode, 'maxP': maxP, 'minP': minP, 'maxQ': maxQ, 'minQ': minQ,
                                     'maxSc_mva': maxSc_mva, 'minSc_mva': minSc_mva, 'maxRX_ratio': maxRX_ratio,
                                     'minRX_ratio': minRX_ratio,
                                     'auxiliary_node': ConfigData['PyToolchainConfig']['grid']['auxiliary_nodes']}])

            gridData['gridConfig'] = pd.concat([gridData['gridConfig'], new_row], ignore_index=True)
    # fill transformer
    ## iterate over all available PowerTransformer-object
    for key, value in import_result['topology'].items():

        # initial values in case no ratios are given in cim files
        tapStep_percent = 0.18600
        tapPos = 0

        if value.__class__.__name__ == "PowerTransformer":
            name = value.name
            sn_mva = value.PowerTransformerEnd[0].ratedS
            if value.PowerTransformerEnd[0].ratedU > value.PowerTransformerEnd[1].ratedU:
                r_ohm = value.PowerTransformerEnd[0].r
                x_ohm = value.PowerTransformerEnd[0].x
                phaseShift = value.PowerTransformerEnd[1].phaseAngleClock
                hvBus_kv = value.PowerTransformerEnd[0].ratedU
                lvBus_kv = value.PowerTransformerEnd[1].ratedU
                hvBus = value.PowerTransformerEnd[0].Terminal.TopologicalNode.name
                lvBus = value.PowerTransformerEnd[1].Terminal.TopologicalNode.name

            else:
                r_ohm = value.PowerTransformerEnd[1].r
                x_ohm = value.PowerTransformerEnd[1].x
                phaseShift = value.PowerTransformerEnd[0].phaseAngleClock
                hvBus_kv = value.PowerTransformerEnd[1].ratedU
                lvBus_kv = value.PowerTransformerEnd[0].ratedU
                hvBus = value.PowerTransformerEnd[1].Terminal.TopologicalNode.name
                lvBus = value.PowerTransformerEnd[0].Terminal.TopologicalNode.name


            # # extract current limit for transformer
            # for key1, value1 in import_result['topology'].items():
            #     if value1.__class__.__name__ in "CurrentLimit":
            #         if value1.OperationalLimitSet.Terminal is not None:
            #             if value1.OperationalLimitSet.Terminal.ConductingEquipment.mRID is value.mRID:
            #                 iMax_ka = value1.value / 1000

            for inner_keyRatio, valueRatio in import_result['topology'].items():
                if valueRatio.__class__.__name__ == "RatioTapChanger" and valueRatio.name == name:
                    tapStep_percent = valueRatio.stepVoltageIncrement
                    tapPos = valueRatio.normalStep

            new_row = pd.DataFrame([{'name': name, 'hvBus': hvBus,
                                                              'lvBus': lvBus, 'hvBus_kv': hvBus_kv,
                                                              'lvBus_kv': lvBus_kv, 'type': name,
                                                              'tapPos': tapPos, 'bay_i':'', 'bay_j':''}])

            gridData['transformers'] = pd.concat([gridData['transformers'], new_row], ignore_index=True)
            # deprecated python 3.7 command
            #gridData['transformers'] = gridData['transformers'].append({'name': name, 'hvBus': hvBus,
            #                                                  'lvBus': lvBus, 'hvBus_kv': hvBus_kv,
            #                                                  'lvBus_kv': lvBus_kv, 'type': name,
            #                                                  'tapPos': tapPos, 'bay_i':'', 'bay_j':''}, ignore_index=True)

            new_row = pd.DataFrame([{'type': name, 'sn_mva': sn_mva,
                                                                'r_ohm': r_ohm, 'x_ohm': x_ohm,
                                                                'pfe_kw': 0, 'tap_step_percent': tapStep_percent,
                                                                'phaseShift': phaseShift,
                                                                'phaseShift_degree': phaseShift*30}])

            gridData['transformerTypes'] = pd.concat([gridData['transformerTypes'],new_row],ignore_index=True)


    # fill lineTypes
    i = 1
    line_types = {}
    for key, value in import_result['topology'].items():  # ierate over ACLineSegment-objects
        if value.__class__.__name__ == "ACLineSegment":
            resistance = round((value.r / value.length), 5)  # calculate resistance/km
            reactance = round((value.x / value.length), 5)  # calculate reactance/km
            b_miks = round((value.bch * 10 ** 6) / value.length, 3)  # calculate sub
            g_miks = round((value.gch * 10 ** 6) / value.length, 3)
            voltageLevel = value.BaseVoltage.nominalVoltage
            # extract current limit for specific line
            for key1, value1 in import_result['topology'].items():
                if value1.__class__.__name__ in "Terminal":
                    if value1.ConductingEquipment is not None:
                        if value1.ConductingEquipment.mRID is value.mRID:
                            for key2, value2 in import_result['topology'].items():
                                if value2.__class__.__name__ in "CurrentLimit":
                                    if value1.OperationalLimitSet[0].mRID is value2.OperationalLimitSet.mRID:
                                        iMax_ka = currentLimit = value2.value / 1000


            # check, if parameters of a line differ from existing line types
            if gridData['lineTypes'].empty:
                name = "Line type " + str(i) + " - " + str(int(round(voltageLevel, 0))) + "kV " + str(
                    int(round(iMax_ka, 3))) + "kA"
                # deprecated python 3.7 command
                #gridData['lineTypes'] = gridData['lineTypes'].append({'name': name, 'r_ohm_km': resistance,
                #                                                      'x_ohm_km': reactance,
                #                                                      'b_miks_km': b_miks,
                #                                                      'g_miks_km': g_miks, 'iMax_ka': iMax_ka,
                #                                                      'vRated_kv': voltageLevel},
                #                                                     ignore_index=True)

                new_row = pd.DataFrame([{'name': name, 'r_ohm_km': resistance,
                                                                      'x_ohm_km': reactance,
                                                                      'b_miks_km': b_miks,
                                                                      'g_miks_km': g_miks, 'iMax_ka': iMax_ka,
                                                                      'vRated_kv': voltageLevel}])

                gridData['lineTypes'] = pd.concat([gridData['lineTypes'], new_row], ignore_index=True)



            elif not (((gridData['lineTypes']['r_ohm_km'] == resistance) &
                           (gridData['lineTypes']['x_ohm_km'] == reactance) &
                           (gridData['lineTypes']['b_miks_km'] == b_miks) &
                           (gridData['lineTypes']['g_miks_km'] == g_miks) &
                           (gridData['lineTypes']['iMax_ka'] == iMax_ka) &
                           (gridData['lineTypes']['vRated_kv'] == voltageLevel)).any()):
                i += 1
                name = "Line type " + str(i) + " - " + str(int(round(voltageLevel, 0))) + "kV " + str(
                    int(round(iMax_ka, 3))) + "kA"
                # deprecated python 3.7 command
                #gridData['lineTypes'] = gridData['lineTypes'].append({'name': name, 'r_ohm_km': resistance,
                #                                                      'x_ohm_km': reactance,
                #                                                      'b_miks_km': b_miks, 'g_miks_km': g_miks,
                #                                                      'iMax_ka': iMax_ka,
                #                                                      'vRated_kv': voltageLevel},
                #                                                     ignore_index=True)

                new_row = pd.DataFrame([{'name': name, 'r_ohm_km': resistance,
                                                                      'x_ohm_km': reactance,
                                                                      'b_miks_km': b_miks,
                                                                      'g_miks_km': g_miks, 'iMax_ka': iMax_ka,
                                                                      'vRated_kv': voltageLevel}])

                gridData['lineTypes'] = pd.concat([gridData['lineTypes'], new_row], ignore_index=True)


            else:
                # when lineType already exists -> the correct type is getting selected from df and stored in name
                name = gridData['lineTypes'].loc[((gridData['lineTypes']['r_ohm_km'] == resistance) &
                                                  (gridData['lineTypes']['x_ohm_km'] == reactance) &
                                                  (gridData['lineTypes']['b_miks_km'] == b_miks) &
                                                  (gridData['lineTypes']['g_miks_km'] == g_miks) &
                                                  (gridData['lineTypes']['iMax_ka'] == iMax_ka) &
                                                  (gridData['lineTypes']['vRated_kv'] == voltageLevel))][
                    'name'].item()
            line_types[value.mRID] = name

    # fill topology
    for key, value in import_result['topology'].items():
        if value.__class__.__name__ in "ACLineSegment":
            name = value.name
            length = value.length
            skip = False
            type = line_types[value.mRID]
            for innerKey, innerValue in import_result['topology'].items():
                if innerValue.__class__.__name__ in "Terminal":
                    if innerValue.ConductingEquipment is not None:
                        if value.mRID is innerValue.ConductingEquipment.mRID:
                            if innerValue.ConductingEquipment.name and not skip:
                                node_i = innerValue.TopologicalNode.name
                                skip = True
                            elif skip:
                                node_j = innerValue.TopologicalNode.name
                                skip = False
            # deprecated python 3.7 command
            #gridData['topology'] = gridData['topology'].append(
            #    {'name': name, 'node_i': node_i, 'node_j': node_j, 'parallelDevices': 1, 'type': type,
            #     'length_km': length, 'bay_i': '', 'bay_j':''}, ignore_index=True)

            new_row = pd.DataFrame([{'name': name, 'node_i': node_i, 'node_j': node_j,
                                     'parallelDevices': 1, 'type': type,
                                    'length_km': length, 'bay_i': '', 'bay_j':''}])


            gridData['topology'] = pd.concat([gridData['topology'], new_row], ignore_index=True)
    # fill buses
    # selection of all buses in the grid #

    for key, value in import_result['topology'].items():
        if value.__class__.__name__ in "TopologicalNode":
            name = value.name
            voltageLevel = value.BaseVoltage.nominalVoltage
            # deprecated python 3.7 command
            #gridData['busData'] = gridData['busData'].append({'busName': name, 'voltageLevel': voltageLevel},
            #                                                         ignore_index=True)

            new_row = pd.DataFrame([{'busName': name, 'voltageLevel': voltageLevel}])

            gridData['busData'] = pd.concat([gridData['busData'], new_row], ignore_index=True)


    x_coord = math.nan
    y_coord = math.nan

    k = 0
    if ConfigData['PyToolchainConfig']['grid']['input_coordinates'] == 'GL':
        for var in gridData['busData']['busName']:
            for key, value in import_result['topology'].items():
                if value.__class__.__name__ in "PositionPoint" and var == value.Location.PowerSystemResources.name:
                    x_coord = value.xPosition
                    y_coord = value.yPosition
                    gridData['busData'].at[k, 'x_coord'] = float(x_coord)
                    gridData['busData'].at[k, 'y_coord'] = float(y_coord)
                    k = k+1

    elif ConfigData['PyToolchainConfig']['grid']['input_coordinates'] == 'DL':
        for var in gridData['busData']['busName']:
            for key, value in import_result['topology'].items():
                if value.__class__.__name__ == "DiagramObjectPoint":
                    if value.DiagramObject.IdentifiedObject.__class__.__name__ == 'TopologicalNode' and value.DiagramObject.IdentifiedObject.name == var:
                        x_coord = value.xPosition
                        y_coord = value.yPosition
                        gridData['busData'].at[k, 'x_coord'] = float(x_coord)
                        gridData['busData'].at[k, 'y_coord'] = float(y_coord)
                        k = k + 1

    #elif ConfigData['PyToolchainConfig']['grid']['input_coordinates'] == 'AI':
     #   inputCoordinates(grid_files, gridData)

    else:
        pass

    gridData['busData'].dropna(subset=['busName'], inplace=True)

    for row_1 in gridData['busData'].iterrows():
        k = 1
        var_1 = 0
        busName = row_1[1]['busName']
        for row_2 in gridData['topology'].iterrows():
            node_i = row_2[1]['node_i']
            node_j = row_2[1]['node_j']
            if node_i == busName:
                gridData['topology'].at[var_1, 'bay_i'] = 'Q0' + str(k)
                k = k + 1
            if node_j == busName:
                gridData['topology'].at[var_1, 'bay_j'] = 'Q0' + str(k)
                k = k + 1
            var_1 = var_1 + 1

        var_1 = 0
        for row_3 in gridData['transformers'].iterrows():
            hvBus = row_3[1]['hvBus']
            lvBus = row_3[1]['lvBus']
            if hvBus == busName:
                gridData['transformers'].at[var_1, 'bay_i'] = 'Q0' + str(k)
                k = k + 1
            if lvBus == busName:
                gridData['transformers'].at[var_1, 'bay_j'] = 'Q0' + str(k)
                k = k + 1
            var_1 = var_1 + 1

    # fill loads
    for key, value in import_result['topology'].items():
        if value.__class__.__name__ in "NonConformLoad":
            name = value.name
            busConnected = value.mRID
            for inner_key, inner_value in import_result['topology'].items():
                if inner_value.__class__.__name__ == "Terminal":
                    if inner_value.ConductingEquipment is not None:
                        if inner_value.ConductingEquipment.mRID is busConnected:
                            busConnected = inner_value.TopologicalNode.name
            p_mw = value.p
            q_mvar = value.q
            # deprecated python 3.7 command
            #gridData['loads'] = gridData['loads'].append({'name': name, 'busConnected': busConnected, 'p_mw': p_mw,
            #                                                            'q_mvar': q_mvar}, ignore_index=True)

            new_row = pd.DataFrame([{'name': name, 'busConnected': busConnected, 'p_mw': p_mw,
                                                                        'q_mvar': q_mvar}])

            gridData['loads'] = pd.concat([gridData['loads'], new_row], ignore_index=True)



    # fill gens
    for key, value in import_result['topology'].items():
        if value.__class__.__name__ in ["SynchronousMachine", "PowerElectronicsConnection"]:
            name = value.name
            busConnected = value.mRID
            for inner_key, inner_value in import_result['topology'].items():
                if inner_value.__class__.__name__ == "Terminal":
                    if inner_value.ConductingEquipment is not None:
                        if inner_value.ConductingEquipment.mRID is busConnected:
                            busConnected = inner_value.TopologicalNode.name
            p_mw = -value.p
            q_mvar = -value.q
            # deprecated python 3.7 command
            #gridData['gens'] = gridData['gens'].append({'name': name, 'busConnected': busConnected, 'p_mw': p_mw,
            #                                                            'q_mvar': q_mvar}, ignore_index=True)
            new_row = pd.DataFrame([{'name': name, 'busConnected': busConnected, 'p_mw': p_mw,
                                                                        'q_mvar': q_mvar}])

            gridData['gens'] = pd.concat([gridData['gens'], new_row], ignore_index=True)



    gridData['gridConfig']['extGridNode'] = gridData['gridConfig']['extGridNode'].str.replace('.', '').str.replace(' ', '').str.replace('_', '')
    gridData['loads']['name'] = gridData['loads']['name'].str.replace('.', '').str.replace(' ', '').str.replace('_', '')
    gridData['loads']['busConnected'] = gridData['loads']['busConnected'] .str.replace('.', '').str.replace(' ', '')
    gridData['gens']['name'] = gridData['gens']['name'].str.replace('.', '').str.replace(' ', '').str.replace('_', '')
    gridData['gens']['busConnected'] = gridData['gens']['busConnected'].str.replace('.', '').str.replace(' ', '')

    # fill measTopology
    #fill_grid_data_meas_topology(gridData, ConfigData)

    # fill profiles (timeseries, switching actions)
    #if ConfigData["PyToolchainConfig"]["module"]["type"] != "application":
#    inputProfiles(grid_folder_prefix, gridData)

    # fill switches
    i = 0
    list_of_lb_sw = []
    for key, value in import_result['topology'].items():
        if value.__class__.__name__ in "Terminal":
            if value.ConductingEquipment is not None:
                if gridData['topology']['name'].str.fullmatch(value.ConductingEquipment.name).any():
                    line = value.ConductingEquipment.name
                    node_i = value.TopologicalNode.name
                    i+=1
                    name = "sw_" + str(i)
                    if value.connected:
                        status = "closed"
                    else:
                        status = "open"
                    if 'PowerTransformer' not in value.ConductingEquipment.__class__.__name__:
                        # deprecated python 3.7 command
                        #gridData['switches'] = gridData['switches'].append({'name': name, 'line': line, 'node_i': node_i,
                        #                                                    'status': status, 'connected_to_line': True}, ignore_index=True)
                        new_row = pd.DataFrame([{'name': name, 'line': line, 'node_i': node_i,
                                                'status': status, 'connected_to_line': True}])

                        gridData['switches'] = pd.concat([gridData['switches'], new_row], ignore_index=True)


        if value.__class__.__name__ in "LoadBreakSwitch":
            name = value.name
            node_j = node_i = value.EquipmentContainer.TopologicalNode[0].name
            for inner_key, inner_value in import_result['topology'].items():
                if inner_value.__class__.__name__ in "Terminal":
                    if (inner_value.ConductingEquipment.mRID is value.mRID) and (inner_value.TopologicalNode.name is not node_i):
                        node_j = inner_value.TopologicalNode.name
                        #deprecated python 3.7 command
                        #.list_of_lb_swappend(import_result['topology'][value.mRID])
                        list_of_lb_sw = pd.concat(list_of_lb_sw, import_result['topology'][value.mRID])
            if value.open:
                status = "open"
            else:
                status = "closed"
            # deprecated python 3.7 command
            # .list_of_lb_swappend(import_result['topology'][value.mRID])
            list_of_lb_sw = pd.concat(list_of_lb_sw, import_result['topology'][value.mRID])
            new_row = pd.DataFrame([{'name': name, 'line': node_j, 'node_i': node_i,
                                    'status': status, 'connected_to_line': False}])
            gridData['switches'] = pd.concat([gridData['switches'], new_row], ignore_index=True)
            # deprecated python 3.7 command
            #gridData['switches'] = gridData['switches'].append({'name': name, 'line': node_j, 'node_i': node_i,
            #                                                            'status': status, 'connected_to_line': False}, ignore_index=True)


    # replace dots and free spaces as such strings are not compatible in external libs
    gridData['busData']['busName'] = gridData['busData']['busName'].str.replace('.', '').str.replace(' ', '')
    gridData['gridConfig']['extGridNode'] = gridData['gridConfig']['extGridNode'] .str.replace('.', '').str.replace(' ', '')
    gridData['topology']['name'] = gridData['topology']['name'].str.replace('.', '').str.replace(' ', '')
    gridData['topology']['node_i'] = gridData['topology']['node_i'].str.replace('.', '').str.replace(' ', '')
    gridData['topology']['node_j'] = gridData['topology']['node_j'].str.replace('.', '').str.replace(' ', '')
    gridData['measTopology']['node_i'] = gridData['measTopology']['node_i'].str.replace('.', '').str.replace(' ', '')
    gridData['measTopology']['node_j'] = gridData['measTopology']['node_j'].str.replace('.', '').str.replace(' ', '')
    gridData['switches']['line'] = gridData['switches']['line'].str.replace('.', '').str.replace(' ', '')
    gridData['switches']['node_i'] = gridData['switches']['node_i'].str.replace('.', '').str.replace(' ', '')
    gridData['transformers']['name'] = gridData['transformers']['name'].str.replace('.', '').str.replace(' ', '')
    gridData['transformers']['hvBus'] = gridData['transformers']['hvBus'].str.replace('.', '').str.replace(' ', '')
    gridData['transformers']['lvBus'] = gridData['transformers']['lvBus'].str.replace('.', '').str.replace(' ', '')

    return gridData, import_result