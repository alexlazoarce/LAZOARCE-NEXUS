from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from .. import cad_service
from ..models import User # User is needed for participant lookup

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

@cad_bp.route('/projects', methods=['GET'])
def get_projects():
    """Gets all CAD projects for the current tenant."""
    projects = cad_service.get_all_projects(g.tenant_id)
    return jsonify([{'id': p.id, 'name': p.name, 'description': p.description} for p in projects]), 200

@cad_bp.route('/projects', methods=['POST'])
def create_project():
    """Creates a new CAD project."""
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({"msg": "Project name is required"}), 400

    project, error = cad_service.create_project(
        tenant_id=g.tenant_id,
        user_id=g.user_id,
        name=data['name'],
        description=data.get('description')
    )
    if error:
        return jsonify({"msg": "Failed to create project", "details": error}), 500

    return jsonify({'id': project.id, 'name': project.name}), 201

# === CAD File Routes ===

@cad_bp.route('/projects/<int:project_id>/files', methods=['POST'])
def add_file(project_id):
    """Adds a file to a CAD project."""
    data = request.get_json()
    if not data or not data.get('filename') or not data.get('file_format'):
        return jsonify({"msg": "Filename and file format are required"}), 400

    cad_file, error = cad_service.add_file_to_project(
        project_id=project_id,
        filename=data['filename'],
        file_format=data['file_format'],
        tenant_id=g.tenant_id
    )

    if error:
        return jsonify({"msg": error}), 404

    return jsonify({'id': cad_file.id, 'filename': cad_file.filename}), 201

# === CAD Layer Routes ===

@cad_bp.route('/files/<int:file_id>/layers', methods=['POST'])
def add_layer(file_id):
    """Adds a layer to a CAD file."""
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({"msg": "Layer name is required"}), 400

    layer, error = cad_service.add_layer_to_file(
        file_id=file_id,
        name=data['name'],
        color=data.get('color', '#FFFFFF'),
        tenant_id=g.tenant_id
    )

    if error:
        return jsonify({"msg": error}), 404

    return jsonify({'id': layer.id, 'name': layer.name}), 201

# === Collaboration Session Routes ===

@cad_bp.route('/files/<int:file_id>/sessions', methods=['POST'])
def start_session(file_id):
    """Starts a collaboration session for a file."""
    session, error = cad_service.start_collaboration_session(file_id, g.tenant_id)
    if error:
        return jsonify({"msg": error}), 404
    return jsonify({'session_id': session.id, 'token': session.session_token}), 201

@cad_bp.route('/sessions/<int:session_id>/participants', methods=['POST'])
def add_participant(session_id):
    """Adds a participant to a session."""
    data = request.get_json()
    if not data or not data.get('user_id'):
        return jsonify({"msg": "User ID is required"}), 400

    session, error = cad_service.add_participant_to_session(
        session_id=session_id,
        user_id=data['user_id'],
        tenant_id=g.tenant_id
    )

    if error:
        return jsonify({"msg": error}), 404

    return jsonify({"msg": "Participant added successfully"}), 200
