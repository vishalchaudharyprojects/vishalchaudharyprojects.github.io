#!/usr/bin/env python3
"""
Test script to verify imports work correctly
"""
import sys
import os
from pathlib import Path

# Add src to path
src_path = str(Path(__file__).parent / "src")
sys.path.append(src_path)

print("Python path:", sys.path)

try:
    from aas_creator import process_all_csvs, process_single_csv

    print("✓ aas_creator imports successful")

    from link_aas_to_cim import link_aas_to_cim

    print("✓ link_aas_to_cim imports successful")

    from link_cim_to_aas import link_cim_to_aas

    print("✓ link_cim_to_aas imports successful")

    # Test assets directory
    assets_dir = Path("/app/assets")
    print(f"Assets directory exists: {assets_dir.exists()}")
    if assets_dir.exists():
        csv_files = list(assets_dir.glob("*.csv"))
        print(f"CSV files found: {[f.name for f in csv_files]}")

except ImportError as e:
    print(f"✗ Import error: {e}")
    import traceback

    traceback.print_exc()
except Exception as e:
    print(f"✗ Other error: {e}")
    import traceback

    traceback.print_exc()