from pathlib import Path
from cim_eq_to_aasx import process_cim_eq_to_aasx
import json


def run_cim_conversion_example():
    """Example script for CIM conversion with enhanced output."""

    # Relative path from src directory to Grids directory
    cim_equipment_file = Path("../Grids/1-LV-rural1--2-no_sw_EV_HP/CIM3/20151231T2300Z_YYY_EQ_.xml")
    cim_location_file = Path("../Grids/1-LV-rural1--2-no_sw_EV_HP/CIM3/20151231T2300Z_XX_YYY_GL_.xml")
    output_directory = Path("../Grids/1-LV-rural1--2-no_sw_EV_HP/CIM3/AASX")

    print("Starting CIM EQ to AASX conversion...")
    print(f"CIM EQ File: {cim_equipment_file}")
    print(f"CIM GL File: {cim_location_file}")
    print(f"Output Directory: {output_directory}")

    # Call the conversion function with both paths
    result = process_cim_eq_to_aasx(
        cim_eq_path=cim_equipment_file,
        cim_gl_path=cim_location_file,
        output_dir=output_directory
    )

    print(f"\nConversion finished successfully!")
    print(f"Output file: {result['output_file']}")
    print(f"AAS Count: {result['aas_count']}")
    print(f"Submodel Count: {result['submodel_count']}")
    print(f"Equipment Names Found: {len(result.get('equipment_names', {}))}")

    # Print some equipment names for reference
    if 'equipment_names' in result and result['equipment_names']:
        print("\nSample Equipment Names (for enhancement):")
        for i, (asset_id, name) in enumerate(list(result['equipment_names'].items())[:10]):
            print(f"  {i + 1}. {asset_id} -> {name}")
        if len(result['equipment_names']) > 10:
            print(f"  ... and {len(result['equipment_names']) - 10} more")

    return result


def check_aas_structure(output_file: str):
    """Check the structure of the generated AAS file."""
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            aas_data = json.load(f)

        print(f"\nAAS File Structure Analysis:")
        print(f"Asset Administration Shells: {len(aas_data.get('assetAdministrationShells', []))}")
        print(f"Submodels: {len(aas_data.get('submodels', []))}")

        # List AAS types
        aas_types = {}
        for aas in aas_data.get('assetAdministrationShells', []):
            asset_type = aas.get('assetInformation', {}).get('assetType', 'Unknown')
            aas_types[asset_type] = aas_types.get(asset_type, 0) + 1

        print("AAS Types Created:")
        for asset_type, count in aas_types.items():
            print(f"  {asset_type}: {count}")

    except Exception as e:
        print(f"Error analyzing AAS structure: {e}")


if __name__ == '__main__':
    # Run the conversion
    result = run_cim_conversion_example()

    # Analyze the output structure
    if result and 'output_file' in result:
        check_aas_structure(result['output_file'])

    print("\nNext steps:")
    print("1. Use the equipment names above for enhancement API calls")
    print("2. Call /enhance-existing-aas endpoint with target AAS file")
    print("3. Or use /complete-cim-pipeline for automated workflow")