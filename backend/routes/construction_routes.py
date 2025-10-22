from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
# Asumiendo que backend.construction_service existe y contiene estas funciones
from backend.construction_service import (
    create_construction_project_service, get_construction_projects_service,
    get_construction_project_details_service, add_budget_item_service,
    add_progress_report_service, create_certification_service,
    get_certifications_for_project_service, create_rfi_service, create_milestone_service
)

construction_bp = Blueprint('construction_bp', __name__, url_prefix='/api/construction')

# --- Rutas de Proyectos ---

@construction_bp.route('/projects', methods=['POST'])
@jwt_required()
def create_project():
    data = request.get_json()
    # Asegúrate que el servicio devuelva una tupla (response_data, status_code)
    response, status_code = create_construction_project_service(data)
    return jsonify(response), status_code

@construction_bp.route('/projects', methods=['GET'])
@jwt_required()
def get_projects():
    response, status_code = get_construction_projects_service()
    return jsonify(response), status_code

@construction_bp.route('/projects/<int:project_id>', methods=['GET'])
@jwt_required()
def get_project_details(project_id):
    response, status_code = get_construction_project_details_service(project_id)
    return jsonify(response), status_code

# --- Rutas de Partidas Presupuestarias ---

@construction_bp.route('/projects/<int:project_id>/budget_items', methods=['POST'])
@jwt_required()
def add_budget_item(project_id):
    data = request.get_json()
    response, status_code = add_budget_item_service(project_id, data)
    return jsonify(response), status_code

# --- Rutas de Reportes de Avance ---

@construction_bp.route('/projects/<int:project_id>/progress_reports', methods=['POST'])
@jwt_required()
def add_progress_report(project_id):
    data = request.get_json()
    response, status_code = add_progress_report_service(project_id, data)
    return jsonify(response), status_code

# --- Rutas de Certificaciones ---

@construction_bp.route('/projects/<int:project_id>/certifications', methods=['POST'])
@jwt_required()
def create_certification(project_id):
    data = request.get_json()
    response, status_code = create_certification_service(project_id, data)
    return jsonify(response), status_code

@construction_bp.route('/projects/<int:project_id>/certifications', methods=['GET'])
@jwt_required()
def get_certifications(project_id):
    response, status_code = get_certifications_for_project_service(project_id)
    return jsonify(response), status_code

# --- Rutas de RFI ---
@construction_bp.route('/projects/<int:project_id>/rfis', methods=['POST'])
@jwt_required()
def create_rfi(project_id):
    data = request.get_json()
    response, status_code = create_rfi_service(project_id, data)
    return jsonify(response), status_code

# --- Rutas de Hitos ---
@construction_bp.route('/projects/<int:project_id>/milestones', methods=['POST'])
@jwt_required()
def create_milestone(project_id):
    data = request.get_json()
    response, status_code = create_milestone_service(project_id, data)
    return jsonify(response), status_code