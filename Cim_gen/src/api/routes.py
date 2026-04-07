from flask import Blueprint, request, jsonify
from ..Function_modules.InputData import get_data
import yaml
from pathlib import Path

bp = Blueprint('cim_api', __name__)


@bp.route("/generate", methods=["POST"])
def generate_cim():
    try:
        config = request.get_json()
        config_path = Path("/app/config_cim.yaml")

        # Write temporary config if needed
        if 'config' in config:
            with open(config_path, 'w') as f:
                yaml.safe_dump(config['config'], f)

        grid_data, cim_results = get_data(str(config_path))
        return jsonify({
            "status": "success",
            "grid_data": grid_data,
            "cim_results": cim_results
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route('/health')
def health_check():
    return jsonify({"status": "healthy"}), 200