from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.material_service import (
    create_material_service, get_materials_service, update_material_stock_service,
    create_material_request_service, get_material_requests_service, update_material_request_status_service
)

material_bp = Blueprint('material_bp', __name__, url_prefix='/api/materials')

# --- Material Routes ---

@material_bp.route('/', methods=['POST'])
@jwt_required()
def create_material():
    # Solo roles de admin pueden crear materiales
    roles = get_jwt_identity().get('roles', [])
    if 'Administrador General' not in roles:
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.get_json()
    response, status_code = create_material_service(data)
    return jsonify(response), status_code

@material_bp.route('/', methods=['GET'])
@jwt_required()
def get_materials():
    response, status_code = get_materials_service()
    return jsonify(response), status_code

@material_bp.route('/<int:material_id>/stock', methods=['PUT'])
@jwt_required()
def update_material_stock(material_id):
    # Solo roles de admin pueden ajustar stock manualmente
    roles = get_jwt_identity().get('roles', [])
    if 'Administrador General' not in roles:
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.get_json()
    response, status_code = update_material_stock_service(material_id, data)
    return jsonify(response), status_code

# --- Material Request Routes ---

@material_bp.route('/requests', methods=['POST'])
@jwt_required()
def create_material_request():
    data = request.get_json()
    response, status_code = create_material_request_service(data)
    return jsonify(response), status_code

@material_bp.route('/requests', methods=['GET'])
@jwt_required()
def get_material_requests():
    # Los admins ven todas, los demás solo las suyas (lógica en el frontend)
    status = request.args.get('status')
    response, status_code = get_material_requests_service(status)
    return jsonify(response), status_code

@material_bp.route('/requests/<int:request_id>/status', methods=['PUT'])
@jwt_required()
def update_material_request_status(request_id):
    # Solo admins pueden aprobar/rechazar/entregar
    roles = get_jwt_identity().get('roles', [])
    if 'Administrador General' not in roles:
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.get_json()
    response, status_code = update_material_request_status_service(request_id, data)
    return jsonify(response), status_code
