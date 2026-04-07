from flask import Blueprint, jsonify, request
from loguru import logger
import requests
import json
import uuid
from datetime import datetime

# FIXED IMPORT - use relative import
from ..rabbitmq_service import rabbitmq_service, with_rabbitmq_connection

bp = Blueprint('api', __name__)
AAS_SERVICE_URL = "http://generate_aasx_from_datasheets:5002/api"


@bp.route("/run", methods=["POST"])
@with_rabbitmq_connection
def run_digital_twin():
    try:
        data = request.get_json()
        workflow = data.get('workflow', 'aas_only')
        equipment = data.get('equipment')

        # Generate unique workflow ID
        workflow_id = str(uuid.uuid4())

        # Create workflow message
        workflow_message = {
            "workflow_id": workflow_id,
            "workflow_type": workflow,
            "equipment": equipment,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "initiated"
        }

        # Publish workflow initiation message
        rabbitmq_service.publish_message(
            exchange='digital_twin.workflow',
            routing_key='workflow.status',
            message=workflow_message
        )

        # For immediate response, use async processing
        if workflow == 'aas_only':
            # Direct API call for simple workflows
            response = requests.post(
                f"{AAS_SERVICE_URL}/generate-aas",
                json={"workflow": workflow, "equipment": equipment},
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                logger.success(f"AAS service response: {result}")

                # Update workflow status
                workflow_message.update({
                    "status": "completed",
                    "results": result
                })
                rabbitmq_service.publish_message(
                    exchange='digital_twin.workflow',
                    routing_key='workflow.status',
                    message=workflow_message
                )

                return jsonify({
                    "status": "success",
                    "workflow_id": workflow_id,
                    "message": "Digital Twin executed successfully",
                    "results": result
                })
            else:
                raise Exception(f"AAS service error: {response.text}")

        else:
            # For complex workflows, use message queue
            rabbitmq_service.publish_message(
                exchange='digital_twin.workflow',
                routing_key='aas.creation',
                message=workflow_message
            )

            return jsonify({
                "status": "processing",
                "workflow_id": workflow_id,
                "message": "Workflow started asynchronously",
                "monitor_endpoint": f"/api/workflow/status/{workflow_id}"
            }), 202

    except Exception as e:
        logger.error(f"Error in run_digital_twin: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@bp.route('/workflow/status/<workflow_id>', methods=['GET'])
def get_workflow_status(workflow_id):
    """Endpoint to check workflow status"""
    # In production, you'd query a database or cache for status
    return jsonify({
        "workflow_id": workflow_id,
        "status": "processing",  # Placeholder
        "message": "Implement status tracking database"
    }), 200


@bp.route('/generate-aas', methods=['POST'])
def generate_aas_proxy():
    """Proxy endpoint to directly call AAS service"""
    try:
        data = request.get_json()
        response = requests.post(
            f"{AAS_SERVICE_URL}/generate-aas",
            json=data,
            timeout=30
        )
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logger.error(f"Proxy error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route('/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "rabbitmq_connected": rabbitmq_service.connected
    }), 200