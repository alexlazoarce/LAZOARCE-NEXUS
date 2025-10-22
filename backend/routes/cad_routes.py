"""
backend/routes/cad_routes.py

Rutas para el Módulo de Creación de Planos (LAN-CAD).
"""
from flask import Blueprint, request, jsonify
from ..services.jwt_service import get_current_tenant_id, get_current_user
from ..cad_service import cad_service

cad_bp = Blueprint('cad_bp', __name__)

# --- Rutas de Proyectos CAD ---
@cad_bp.route('/projects', methods=['GET', 'POST'])
def handle_projects():
    tenant_id = get_current_tenant_id()
    user = get_current_user()

    if request.method == 'POST':
        data = request.json
        project = cad_service.create_project(tenant_id, user.id, data)
        return jsonify({'id': project.id, 'name': project.name}), 201

    projects = cad_service.get_projects(tenant_id)
    return jsonify([{'id': p.id, 'name': p.name, 'description': p.description} for p in projects])

# --- Rutas de Archivos CAD ---
@cad_bp.route('/projects/<int:project_id>/files', methods=['GET', 'POST'])
def handle_files(project_id):
    tenant_id = get_current_tenant_id()
    if request.method == 'POST':
        data = request.json
        cad_file = cad_service.add_file_to_project(tenant_id, project_id, data)
        return jsonify({'id': cad_file.id, 'filename': cad_file.filename}), 201

    files = cad_service.get_files_for_project(tenant_id, project_id)
    return jsonify([{'id': f.id, 'filename': f.filename, 'version': f.version} for f in files])

# --- Rutas de Capas ---
@cad_bp.route('/files/<int:file_id>/layers', methods=['GET', 'POST'])
def handle_layers(file_id):
    tenant_id = get_current_tenant_id()
    if request.method == 'POST':
        data = request.json
        layer = cad_service.add_layer_to_file(tenant_id, file_id, data)
        return jsonify({'id': layer.id, 'name': layer.name}), 201

    layers = cad_service.get_layers_for_file(tenant_id, file_id)
    return jsonify([{'id': l.id, 'name': l.name, 'color': l.color, 'is_visible': l.is_visible} for l in layers])

# --- Rutas de Colaboración ---
@cad_bp.route('/files/<int:file_id>/collaboration/start', methods=['POST'])
def start_session(file_id):
    tenant_id = get_current_tenant_id()
    data = request.json
    user_ids = data.get('user_ids', [])
    session = cad_service.start_collaboration_session(tenant_id, file_id, user_ids)
    return jsonify({'session_token': session.session_token}), 201

@cad_bp.route('/collaboration/<int:session_id>/end', methods=['POST'])
def end_session(session_id):
    tenant_id = get_current_tenant_id()
    session = cad_service.end_collaboration_session(tenant_id, session_id)
    if session:
        return jsonify({'message': 'Sesión finalizada.'}), 200
    return jsonify({'message': 'Sesión no encontrada.'}), 404
