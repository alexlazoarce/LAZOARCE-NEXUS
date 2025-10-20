"""
Rutas de la API para el Módulo de Facturación (LAN-FE2).
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from backend.services import invoicing_service
from backend import accounting_service
from backend.models import Invoice

invoicing_bp = Blueprint('invoicing_bp', __name__, url_prefix='/api/invoicing')

def _is_authorized():
    """Helper to check for Admin or Contador roles."""
    claims = get_jwt()
    user_roles = claims.get('roles', [])
    return 'Admin' in user_roles or 'Contador' in user_roles

@invoicing_bp.route('/invoices', methods=['POST'])
@jwt_required()
def create_invoice():
    if not _is_authorized():
        return jsonify({"message": "Acceso no autorizado"}), 403

    data = request.get_json()
    if not data or 'customer_name' not in data or 'items' not in data:
        return jsonify({"message": "Datos de factura incompletos."}), 400

    invoice, error = invoicing_service.create_invoice_service(data)

    if error:
        return jsonify({"message": "Error al crear la factura", "error": error}), 500

    return jsonify(invoice.to_dict()), 201

@invoicing_bp.route('/invoices/<int:invoice_id>/taxes', methods=['GET'])
@jwt_required()
def get_invoice_taxes(invoice_id):
    if not _is_authorized():
        return jsonify({"message": "Acceso no autorizado"}), 403

    invoice = Invoice.query.get_or_404(invoice_id)

    # country_code can be dynamic in a multi-tenant setup
    # For now, we'll use 'SV' as the default
    country_code = request.args.get('country_code', 'SV')

    try:
        tax_details = accounting_service.calculate_taxes_for_invoice(invoice, country_code)
        return jsonify(tax_details), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
