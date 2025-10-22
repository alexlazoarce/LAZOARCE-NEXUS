from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.tax_service import (
    create_tax_type_service, get_tax_types_service, update_tax_type_service,
    generate_iva_declaration_service, get_tax_declarations_service
)

tax_bp = Blueprint('tax_bp', __name__, url_prefix='/api/tax')

# --- TaxType Routes ---

@tax_bp.route('/types', methods=['POST'])
@jwt_required()
def create_tax_type():
    data = request.get_json()
    response, status_code = create_tax_type_service(data)
    return jsonify(response), status_code

@tax_bp.route('/types', methods=['GET'])
@jwt_required()
def get_tax_types():
    filters = {
        'country_code': request.args.get('country_code'),
        'tax_category': request.args.get('tax_category')
    }
    # Remove None values so we don't filter by them
    active_filters = {k: v for k, v in filters.items() if v is not None}
    response, status_code = get_tax_types_service(active_filters)
    return jsonify(response), status_code

@tax_bp.route('/types/<int:tax_type_id>', methods=['PUT'])
@jwt_required()
def update_tax_type(tax_type_id):
    data = request.get_json()
    response, status_code = update_tax_type_service(tax_type_id, data)
    return jsonify(response), status_code

# --- Tax Declaration Routes ---

@tax_bp.route('/declarations/iva', methods=['POST'])
@jwt_required()
def generate_iva_declaration():
    data = request.get_json()
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    if not start_date or not end_date:
        return jsonify({'error': 'start_date and end_date are required'}), 400

    response, status_code = generate_iva_declaration_service(start_date, end_date)
    return jsonify(response), status_code

@tax_bp.route('/declarations', methods=['GET'])
@jwt_required()
def get_tax_declarations():
    response, status_code = get_tax_declarations_service()
    return jsonify(response), status_code
