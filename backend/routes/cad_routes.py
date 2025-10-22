"""
backend/routes/cad_routes.py
Rutas para el Módulo de Creación de Planos (LAN-CAD).
"""
from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from .. import cad_service
from ..models import User
from ..services.jwt_service import get_current_tenant_id, get_current_user

cad_bp = Blueprint('cad_bp', __name__)

@cad_bp.before_request
@jwt_required()
def before_request():
    """
    Protects all routes in this blueprint and extracts tenant_id from the JWT token.
    The tenant_id is stored in Flask's application context `g`.
    """
    identity = get_jwt_identity()
    # It is assumed the JWT identity is a dictionary containing 'tenant_id'
    g.tenant_id = identity.get('tenant_id')
    g.user_id = identity.get('user_id')
    if not g.tenant_id or not g.user_id:
        # Using a consistent error message
        return jsonify({"msg": "Missing or incomplete user identity in token"}), 400

# === CAD Project Routes ===
@cad_bp.route('/projects', methods=['GET', 'POST'])
def handle_projects():
    """Gets all CAD projects or creates a new one for the current tenant."""
    tenant_id = get_current_tenant_id() or g.tenant_id
    user_id = g.user_id
    
    if request.method == 'POST':
        data = request.get_json()
        if not data or not data.get('name'):
            return jsonify({"msg": "Project name is required"}), 400
        project, error = cad_service.create_project(
            tenant_id=tenant_id,
            user_id=user_id,
            data=data
        )
        if error:
            return jsonify({"msg": "Failed to create project", "details": error}), 500
        return jsonify({'id': project.id, 'name': project.name, 'description': project.description}), 201
    
    projects = cad_service.get_projects(tenant_id)
    return jsonify([{'id': p.id, 'name': p.name, 'description': p.description} for p in projects]), 200

# === CAD File Routes ===
@cad_bp.route('/projects/<int:project_id>/files', methods=['GET', 'POST'])
def handle_files(project_id):
    """Gets all files or adds a new file to a CAD project."""
    tenant_id = get_current_tenant_id() or g.tenant_id
    
    if request.method == 'POST':
        data = request.get_json()
        if not data or not data.get('filename') or not data.get('file_format'):
            return jsonify({"msg": "Filename and file format are required"}), 400
        cad_file, error = cad_service.add_file_to_project(
            tenant_id=tenant_id,
            project_id=project_id,
            data=data
        )
        if error:
            return jsonify({"msg": error}), 404
        return jsonify({'id': cad_file.id, 'filename': cad_file.filename}), 201
    
    files = cad_service.get_files_for_project(tenant_id, project_id)
    return jsonify([{'id': f.id, 'filename': f.filename, 'version': getattr(f, 'version', None)} for f in files]), 200

# === CAD Layer Routes ===
@cad_bp.route('/files/<int:file_id>/layers', methods=['GET', 'POST'])
def handle_layers(file_id):
    """Gets all layers or adds a new layer to a CAD file."""
    tenant_id = get_current_tenant_id() or g.tenant_id
    
    if request.method == 'POST':
        data = request.get_json()
        if not data or not data.get('name'):
            return jsonify({"msg": "Layer name is required"}), 400
        layer, error = cad_service.add_layer_to_file(
            tenant_id=tenant_id,
            file_id=file_id,
            data=data
        )
        if error:
            return jsonify({"msg": error}), 404
        return jsonify({'id': layer.id, 'name': layer.name}), 201
    
    layers = cad_service.get_layers_for_file(tenant_id, file_id)
    return jsonify([{'id': l.id, 'name': l.name, 'color': l.color, 'is_visible': l.is_visible} for l in layers]), 200

# === Collaboration Session Routes ===
@cad_bp.route('/files/<int:file_id>/sessions', methods=['POST'])
def start_session(file_id):
    """Starts a collaboration session for a file."""
    tenant_id = get_current_tenant_id() or g.tenant_id
    data = request.get_json()
    user_ids = data.get('user_ids', []) if data else []
    session, error = cad_service.start_collaboration_session(
        tenant_id=tenant_id,
        file_id=file_id,
        user_ids=user_ids
    )
    if error:
        return jsonify({"msg": error}), 404
    return jsonify({'session_id': session.id, 'session_token': session.session_token}), 201

@cad_bp.route('/sessions/<int:session_id>/participants', methods=['POST'])
def add_participant(session_id):
    """Adds a participant to a session."""
    tenant_id = get_current_tenant_id() or g.tenant_id
    data = request.get_json()
    if not data or not data.get('user_id'):
        return jsonify({"msg": "User ID is required"}), 400
    session, error = cad_service.add_participant_to_session(
        session_id=session_id,
        user_id=data['user_id'],
        tenant_id=tenant_id
    )
    if error:
        return jsonify({"msg": error}), 404
    return jsonify({"msg": "Participant added successfully"}), 200

@cad_bp.route('/collaboration/<int:session_id>/end', methods=['POST'])
def end_session(session_id):
    """Ends a collaboration session."""
    tenant_id = get_current_tenant_id() or g.tenant_id
    session = cad_service.end_collaboration_session(tenant_id, session_id)
    if session:
        return jsonify({'message': 'Sesión finalizada.'}), 200
    return jsonify({'message': 'Sesión no encontrada.'}), 404
 