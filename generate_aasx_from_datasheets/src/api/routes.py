"""
Updated API Routes for CIM-first AAS Enhancement Workflow

New workflow sequence:
1. CIM EQ to AASX conversion (cim_eq_to_aasx.py) - creates hierarchical AAS structure
2. Enhance existing AAS with static data and asset mapping (enhanced aas_creator.py)
3. Optional: Link enhanced AAS with CIM model

Workflow Types:
- 'cim_only': Convert CIM EQ+GL to AASX structure only
- 'cim_with_static': CIM conversion + static data addition to existing AAS
- 'cim_with_mapping': CIM conversion + mapping data addition to existing AAS
- 'full_cim_pipeline': Complete CIM → static → mapping → enhanced AAS
"""

from flask import Blueprint, request, jsonify
import sys
import os
from pathlib import Path
import json
import requests
import base64

api_bp = Blueprint('api', __name__)


def import_cim_services():
    """
    Simplified import function that handles the Python path correctly.
    """
    try:
        # Add src directory to Python path if not already there
        src_path = "/app/src"
        if src_path not in sys.path:
            sys.path.insert(0, src_path)

        print(f"Python path for imports: {sys.path}")

        # Import all services using absolute imports
        from cim_eq_to_aasx import process_cim_eq_to_aasx
        from aas_creator import (
            enhance_existing_aas_with_static_data,
            enhance_all_equipment_with_static_data,
            process_all_csvs_standalone,
            process_single_csv_standalone
        )
        from link_aas_to_cim import link_aas_to_cim
        from link_cim_to_aas import link_cim_to_aas

        print("✓ All imports successful")
        return (process_cim_eq_to_aasx, enhance_existing_aas_with_static_data,
                enhance_all_equipment_with_static_data, process_all_csvs_standalone,
                process_single_csv_standalone, link_aas_to_cim, link_cim_to_aas)

    except ImportError as e:
        print(f"Import error: {e}")
        print(f"Files in /app/src: {os.listdir('/app/src') if os.path.exists('/app/src') else 'Directory not found'}")
        raise

def _register_with_basyx(aas_file_path: str) -> dict:
    """Register AAS with BaSyx"""
    try:
        with open(aas_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        aas_list = data.get("assetAdministrationShells", [])
        submodels = data.get("submodels", [])

        if not aas_list:
            return {"aas_file": aas_file_path, "error": "No AssetAdministrationShells found in JSON file"}

        basyx_url = os.getenv("BASYX_AAS_ENV_URL", "http://basyx-aas-env:8081")
        registry_url = os.getenv("BASYX_AAS_REGISTRY_URL", "http://basyx-aas-registry:8080")

        def to_base64url(s: str) -> str:
            return base64.urlsafe_b64encode(s.encode('utf-8')).rstrip(b'=').decode('ascii')

        results = []
        sm_resps = []

        # Register submodels
        for sm in submodels:
            sm_id = sm.get("id")
            sm_id_b64 = to_base64url(sm_id)
            sm_url = f"{basyx_url}/submodels/{sm_id_b64}"

            sm_resp = requests.post(
                f"{basyx_url}/submodels",
                json=sm,
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            if sm_resp.status_code == 409:
                sm_resp = requests.put(
                    sm_url,
                    json=sm,
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
            sm_resps.append({"idShort": sm.get("idShort"), "status": sm_resp.status_code})

        # Register AAS shells
        for aas in aas_list:
            aas_id = aas.get("id")
            aas_id_b64 = to_base64url(aas_id)
            aas_url = f"{basyx_url}/shells/{aas_id_b64}"

            aas_resp = requests.post(
                f"{basyx_url}/shells",
                json=aas,
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            if aas_resp.status_code == 409:
                aas_resp = requests.put(
                    aas_url,
                    json=aas,
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )

            descriptor = {
                "id": aas_id,
                "idShort": aas.get("idShort"),
                "endpoints": [{
                    "protocolInformation": {
                        "href": f"{basyx_url}/shells/{aas_id_b64}",
                        "endpointProtocol": "HTTP"
                    }
                }]
            }

            reg_resp = requests.put(
                f"{registry_url}/shell-descriptors/{aas_id_b64}",
                json=descriptor,
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            results.append({
                "aas_idShort": aas.get("idShort"),
                "aas_env_status": aas_resp.status_code,
                "registry_status": reg_resp.status_code,
                "submodels_registered": sm_resps
            })

        return {"aas_file": aas_file_path, "results": results}

    except Exception as e:
        import traceback
        return {"aas_file": aas_file_path, "error": str(e), "traceback": traceback.format_exc()}

def process_cim_workflow(workflow_type: str, cim_eq_path: str = None, cim_gl_path: str = None,
                        equipment: str = None, target_aas_file: str = None) -> dict:
    """
    Process CIM-first AAS generation workflows with enhanced AAS enhancement.

    Args:
        workflow_type: Type of workflow ('cim_only', 'cim_with_static', 'cim_with_mapping', 'full_cim_pipeline')
        cim_eq_path: Path to CIM EQ XML file
        cim_gl_path: Path to CIM GL XML file
        equipment: Optional specific equipment name for static data
        target_aas_file: Optional target AAS file for enhancement (if not provided, uses CIM output)
    """
    results = {}

    try:
        # Import services
        (process_cim_eq_to_aasx, enhance_existing_aas_with_static_data,
         enhance_all_equipment_with_static_data, process_all_csvs_standalone,
         process_single_csv_standalone, link_aas_to_cim, link_cim_to_aas) = import_cim_services()

        # STEP 1: CIM EQ to AASX Conversion (required for all workflows)
        if not cim_eq_path:
            return {
                "success": False,
                "error": "CIM EQ file path is required for CIM workflows"
            }

        cim_eq_file = Path(cim_eq_path)
        cim_gl_file = Path(cim_gl_path) if cim_gl_path else None

        # Set output directory
        output_dir = Path("/app/basyx_aas")

        # Process CIM conversion
        cim_result = process_cim_eq_to_aasx(
            cim_eq_path=cim_eq_file,
            output_dir=output_dir,
            cim_gl_path=cim_gl_file
        )
        results["cim_conversion"] = cim_result

        # Determine target AAS file for enhancement
        enhancement_target = target_aas_file or cim_result.get("output_file")

        # For cim_only workflow, we're done after CIM conversion
        if workflow_type == "cim_only":
            # Auto-register the CIM-generated AAS
            if "output_file" in cim_result:
                reg_result = _register_with_basyx(cim_result["output_file"])
                results["basyx_registration"] = reg_result

            return {"success": True, "workflow": workflow_type, "results": results}

        # STEP 2: Add Static Data to Existing AAS (for workflows that include static data)
        if workflow_type in ["cim_with_static", "full_cim_pipeline"] and enhancement_target:
            if equipment:
                # Add static data for specific equipment to existing AAS
                assets_dir = Path("/app/assets")
                csv_path = assets_dir / f"{equipment}.csv"
                if csv_path.exists():
                    static_result = enhance_existing_aas_with_static_data(
                        equipment, csv_path, enhancement_target, emit_event=False
                    )
                    results["static_data_enhancement"] = static_result
                else:
                    available_files = [f.name for f in assets_dir.glob("*.csv")]
                    return {
                        "success": False,
                        "error": f"CSV file not found for equipment: {equipment}",
                        "available_files": available_files
                    }
            else:
                # Add static data for all equipment to existing AAS
                static_results = enhance_all_equipment_with_static_data(
                    enhancement_target, emit_events=False
                )
                results["static_data_enhancement"] = static_results

        # STEP 3: Add Asset Mapping Data (for workflows that include mapping)
        if workflow_type in ["cim_with_mapping", "full_cim_pipeline"] and "static_data_enhancement" in results:
            # Use the enhanced AAS file for mapping
            mapping_target = enhancement_target

            if equipment and isinstance(results["static_data_enhancement"], dict):
                # For single equipment enhancement
                mapping_result = link_aas_to_cim(results["static_data_enhancement"], emit_event=False)
                if mapping_result:
                    results["asset_mapping"] = mapping_result
            elif isinstance(results["static_data_enhancement"], list) and results["static_data_enhancement"]:
                # For multiple equipment enhancement - use first result
                first_enhancement = results["static_data_enhancement"][0]
                mapping_result = link_aas_to_cim(first_enhancement, emit_event=False)
                if mapping_result:
                    results["asset_mapping"] = mapping_result

        # STEP 4: Enhanced AAS Linking (full pipeline only)
        if workflow_type == "full_cim_pipeline" and "asset_mapping" in results and isinstance(results["asset_mapping"], dict):
            enhanced_result = link_cim_to_aas(results["asset_mapping"], emit_event=False)
            if enhanced_result:
                results["enhanced_aas"] = enhanced_result

        # Auto-register the final AAS
        final_aas_file = None
        if "enhanced_aas" in results:
            final_aas_file = results["enhanced_aas"].get("aas_json_path")
        elif "asset_mapping" in results:
            final_aas_file = results["asset_mapping"].get("aas_json_path")
        elif "static_data_enhancement" in results:
            # For enhancement workflow, use the enhanced file
            final_aas_file = enhancement_target

        # Fallback to CIM-generated file if no enhanced file
        if not final_aas_file and "output_file" in cim_result:
            final_aas_file = cim_result["output_file"]

        if final_aas_file:
            reg_result = _register_with_basyx(final_aas_file)
            results["basyx_registration"] = reg_result

        return {"success": True, "workflow": workflow_type, "results": results}

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        return {
            "success": False,
            "error": str(e),
            "traceback": error_trace,
            "workflow": workflow_type
        }

@api_bp.route('/generate-cim-aas', methods=['POST'])
def generate_cim_aas():
    """
    Generate AAS starting from CIM models with configurable workflow.

    Request Body:
        {
            "workflow": "cim_only" | "cim_with_static" | "cim_with_mapping" | "full_cim_pipeline",
            "cim_eq_path": "path/to/cim_eq.xml",
            "cim_gl_path": "path/to/cim_gl.xml",  # optional
            "equipment": "optional_equipment_name"  # for static data enhancement
        }
    """
    data = request.get_json()

    workflow = data.get("workflow", "cim_only")
    cim_eq_path = data.get("cim_eq_path")
    cim_gl_path = data.get("cim_gl_path")
    equipment = data.get("equipment")

    try:
        results = process_cim_workflow(workflow, cim_eq_path, cim_gl_path, equipment)
        return jsonify(results), 200 if results.get("success") else 500
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@api_bp.route('/enhance-existing-aas', methods=['POST'])
def enhance_existing_aas():
    """
    Enhance existing CIM-generated AAS with static data and asset mapping.

    Request Body:
        {
            "target_aas_file": "path/to/cim_generated_aas.json",
            "equipment": "optional_equipment_name",  # if empty, enhance all equipment
            "workflow": "static_only" | "mapping_only" | "full_enhancement"
        }
    """
    data = request.get_json()

    target_aas_file = data.get("target_aas_file")
    equipment = data.get("equipment")
    workflow = data.get("workflow", "full_enhancement")

    if not target_aas_file:
        return jsonify({
            "success": False,
            "error": "target_aas_file is required"
        }), 400

    try:
        # Import enhanced AAS creator
        (process_cim_eq_to_aasx, enhance_existing_aas_with_static_data,
         enhance_all_equipment_with_static_data, process_all_csvs_standalone,
         process_single_csv_standalone, link_aas_to_cim, link_cim_to_aas) = import_cim_services()

        results = {}

        if equipment:
            # Enhance specific equipment
            assets_dir = Path("/app/assets")
            csv_path = assets_dir / f"{equipment}.csv"

            if csv_path.exists():
                enhancement_result = enhance_existing_aas_with_static_data(
                    equipment,
                    csv_path,
                    target_aas_file,
                    emit_event=False
                )
                results["enhancement"] = enhancement_result
            else:
                available_files = [f.name for f in assets_dir.glob("*.csv")]
                return jsonify({
                    "success": False,
                    "error": f"CSV file not found for equipment: {equipment}",
                    "available_files": available_files
                }), 404
        else:
            # Enhance all equipment
            enhancement_results = enhance_all_equipment_with_static_data(
                target_aas_file,
                emit_events=False
            )
            results["enhancement"] = enhancement_results

        # Add asset mapping if requested
        if workflow in ["mapping_only", "full_enhancement"] and "enhancement" in results:
            if equipment and isinstance(results["enhancement"], dict):
                mapping_result = link_aas_to_cim(results["enhancement"], emit_event=False)
                if mapping_result:
                    results["asset_mapping"] = mapping_result
            elif isinstance(results["enhancement"], list) and results["enhancement"]:
                # Use first enhancement result for mapping
                first_enhancement = results["enhancement"][0]
                mapping_result = link_aas_to_cim(first_enhancement, emit_event=False)
                if mapping_result:
                    results["asset_mapping"] = mapping_result

        # Auto-register the enhanced AAS with BaSyx
        if "enhancement" in results or "asset_mapping" in results:
            reg_result = _register_with_basyx(target_aas_file)
            results["basyx_registration"] = reg_result

        return jsonify({
            "success": True,
            "workflow": workflow,
            "target_aas_file": target_aas_file,
            "results": results
        }), 200

    except Exception as e:
        import traceback
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@api_bp.route('/complete-cim-pipeline', methods=['POST'])
def complete_cim_pipeline():
    """
    Complete CIM pipeline: conversion + enhancement in one call.

    Request Body:
        {
            "cim_eq_path": "path/to/cim_eq.xml",
            "cim_gl_path": "path/to/cim_gl.xml",
            "enhance_with_static": true/false,
            "equipment": "optional_equipment_name"
        }
    """
    data = request.get_json()

    cim_eq_path = data.get("cim_eq_path")
    cim_gl_path = data.get("cim_gl_path")
    enhance_with_static = data.get("enhance_with_static", True)
    equipment = data.get("equipment")

    if not cim_eq_path:
        return jsonify({
            "success": False,
            "error": "cim_eq_path is required"
        }), 400

    try:
        # Import services
        (process_cim_eq_to_aasx, enhance_existing_aas_with_static_data,
         enhance_all_equipment_with_static_data, process_all_csvs_standalone,
         process_single_csv_standalone, link_aas_to_cim, link_cim_to_aas) = import_cim_services()

        results = {}

        # Step 1: CIM Conversion
        cim_eq_file = Path(cim_eq_path)
        cim_gl_file = Path(cim_gl_path) if cim_gl_path else None
        output_dir = cim_eq_file.parent / "AASX"

        cim_result = process_cim_eq_to_aasx(
            cim_eq_path=cim_eq_file,
            output_dir=output_dir,
            cim_gl_path=cim_gl_file
        )
        results["cim_conversion"] = cim_result

        # Step 2: Enhancement (if requested)
        if enhance_with_static and "output_file" in cim_result:
            if equipment:
                # Enhance specific equipment
                assets_dir = Path("/app/assets")
                csv_path = assets_dir / f"{equipment}.csv"
                if csv_path.exists():
                    enhancement_result = enhance_existing_aas_with_static_data(
                        equipment, csv_path, cim_result["output_file"], emit_event=False
                    )
                    results["enhancement"] = enhancement_result
            else:
                # Enhance all equipment
                enhancement_results = enhance_all_equipment_with_static_data(
                    cim_result["output_file"],
                    emit_events=False
                )
                results["enhancement"] = enhancement_results

            # Register enhanced AAS
            reg_result = _register_with_basyx(cim_result["output_file"])
            results["basyx_registration"] = reg_result

        return jsonify({
            "success": True,
            "pipeline": "complete_cim_pipeline",
            "results": results
        }), 200

    except Exception as e:
        import traceback
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@api_bp.route('/list-cim-files', methods=['GET'])
def list_cim_files():
    """
    List available CIM files in the Grids directory.
    """
    grids_dir = Path("/app/Grids")
    cim_files = []

    if grids_dir.exists():
        for eq_file in grids_dir.rglob("*_EQ_.xml"):
            gl_file = eq_file.parent / eq_file.name.replace("_EQ_.xml", "_GL_.xml")
            cim_files.append({
                "eq_file": str(eq_file.relative_to(grids_dir)),
                "gl_file": str(gl_file.relative_to(grids_dir)) if gl_file.exists() else None,
                "directory": str(eq_file.parent.relative_to(grids_dir))
            })

    return jsonify({
        "success": True,
        "grids_directory": str(grids_dir),
        "cim_files": cim_files
    }), 200

# Keep the existing endpoints for backward compatibility
@api_bp.route('/generate-aas', methods=['POST'])
def generate_aas():
    """Legacy endpoint - uses standalone AAS creation"""
    data = request.get_json()
    workflow = data.get("workflow", "aas_only")
    equipment = data.get("equipment")

    try:
        (process_cim_eq_to_aasx, enhance_existing_aas_with_static_data,
         enhance_all_equipment_with_static_data, process_all_csvs_standalone,
         process_single_csv_standalone, link_aas_to_cim, link_cim_to_aas) = import_cim_services()

        results = {}

        # Use standalone AAS creation for legacy workflow
        if equipment:
            assets_dir = Path("/app/assets")
            csv_path = assets_dir / f"{equipment}.csv"
            if csv_path.exists():
                aas_result = process_single_csv_standalone(csv_path, emit_event=False)
                results["aas_creation"] = aas_result
            else:
                available_files = [f.name for f in assets_dir.glob("*.csv")]
                return jsonify({
                    "success": False,
                    "error": f"CSV file not found for equipment: {equipment}",
                    "available_files": available_files
                }), 404
        else:
            aas_results = process_all_csvs_standalone(emit_events=False)
            results["aas_creation"] = aas_results

        # Auto-register created AAS
        if "aas_creation" in results:
            if isinstance(results["aas_creation"], dict):
                aas_file = results["aas_creation"].get("aas_json_path")
                if aas_file:
                    reg_result = _register_with_basyx(aas_file)
                    results["basyx_registration"] = reg_result
            elif isinstance(results["aas_creation"], list) and results["aas_creation"]:
                # Register first AAS file
                aas_file = results["aas_creation"][0].get("aas_json_path")
                if aas_file:
                    reg_result = _register_with_basyx(aas_file)
                    results["basyx_registration"] = reg_result

        return jsonify({
            "success": True,
            "workflow": workflow,
            "results": results
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# Keep existing health and diagnostic endpoints
@api_bp.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200

@api_bp.route('/test-imports', methods=['GET'])
def test_imports():
    try:
        (process_cim_eq_to_aasx, enhance_existing_aas_with_static_data,
         enhance_all_equipment_with_static_data, process_all_csvs_standalone,
         process_single_csv_standalone, link_aas_to_cim, link_cim_to_aas) = import_cim_services()

        return jsonify({
            "success": True,
            "message": "All CIM workflow imports working correctly",
            "imported_functions": [
                "process_cim_eq_to_aasx",
                "enhance_existing_aas_with_static_data",
                "enhance_all_equipment_with_static_data",
                "process_all_csvs_standalone",
                "process_single_csv_standalone",
                "link_aas_to_cim",
                "link_cim_to_aas"
            ]
        }), 200
    except ImportError as e:
        return jsonify({
            "success": False,
            "error": f"Import error: {e}",
            "python_path": sys.path
        }), 500

@api_bp.route('/list-files', methods=['GET'])
def list_files():
    """List both CSV assets and CIM files"""
    assets_dir = Path("/app/assets")
    grids_dir = Path("/app/Grids")

    result = {"success": True}

    if assets_dir.exists():
        result["assets_directory"] = str(assets_dir)
        result["csv_files"] = [f.name for f in assets_dir.glob("*.csv")]
    else:
        result["assets_directory_error"] = f"Directory not found: {assets_dir}"

    if grids_dir.exists():
        result["grids_directory"] = str(grids_dir)
        cim_files = []
        for eq_file in grids_dir.rglob("*_EQ_.xml"):
            cim_files.append(str(eq_file.relative_to(grids_dir)))
        result["cim_files"] = cim_files
    else:
        result["grids_directory_error"] = f"Directory not found: {grids_dir}"

    return jsonify(result), 200