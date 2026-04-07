from flask import Blueprint, request, jsonify
import datetime
import yaml
from pathlib import Path

# Import your existing modules
try:
    from ..connector.initialize_data import *
    from ..connector.scd_handling import load_scd_tree
    from ..connector.data_integration import data_integration
except ImportError as e:
    print(f"Import warning: {e}")

bp = Blueprint('typhoon_api', __name__)


@bp.route("/process", methods=["POST"])
def process_integration():
    try:
        config_data = request.get_json()
        if not config_data:
            return jsonify({"status": "error", "message": "No JSON data provided"}), 400

        config_path = Path("/app/config_typhoon.yaml")

        # Write temporary config if provided in request
        if 'config' in config_data:
            with open(config_path, 'w') as f:
                yaml.safe_dump(config_data['config'], f)

        # Load and use the configuration
        config = parse_config(str(config_path))
        root_scd_tree, scd_file_name = load_scd_tree(config)
        scl_communication_df = parse_scd_communication(config, root_scd_tree)
        data_integration(config, scl_communication_df, root_scd_tree, scd_file_name)

        return jsonify({
            "status": "success",
            "timestamp": datetime.datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route('/health')
def health_check():
    return jsonify({"status": "healthy"}), 200


@bp.route('/status')
def status():
    return jsonify({
        "service": "grid_measurement",
        "status": "running",
        "timestamp": datetime.datetime.now().isoformat()
    })