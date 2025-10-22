from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.field_service import (
    create_field_task_service, get_field_tasks_service,
    create_task_report_service
)

field_bp = Blueprint('field_bp', __name__, url_prefix='/api/field-ops')

# --- Field Task Routes ---
@field_bp.route('/tasks', methods=['POST'])
@jwt_required()
def create_field_task():
    data = request.get_json()
    response, status_code = create_field_task_service(data)
    return jsonify(response), status_code

@field_bp.route('/tasks', methods=['GET'])
@jwt_required()
def get_field_tasks():
    response, status_code = get_field_tasks_service()
    return jsonify(response), status_code

# --- Task Report Routes ---
@field_bp.route('/tasks/<int:task_id>/reports', methods=['POST'])
@jwt_required()
def create_task_report(task_id):
    data = request.get_json()
    response, status_code = create_task_report_service(task_id, data)
    return jsonify(response), status_code
