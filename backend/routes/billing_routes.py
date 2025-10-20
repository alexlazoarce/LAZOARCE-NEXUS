"""
Rutas de la API para el Módulo de Facturación Recurrente (LAN-BIL9).
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from backend.services import billing_service

billing_bp = Blueprint('billing_bp', __name__, url_prefix='/api/billing')

def _is_admin():
    """Helper to check for Admin role."""
    claims = get_jwt()
    user_roles = claims.get('roles', [])
    return 'Admin' in user_roles

@billing_bp.route('/subscriptions', methods=['POST'])
@jwt_required()
def create_subscription():
    if not _is_admin():
        return jsonify({"message": "Acceso no autorizado"}), 403

    data = request.get_json()
    if not data or 'user_id' not in data or 'plan_id' not in data:
        return jsonify({"message": "Datos de suscripción incompletos."}), 400

    subscription, error = billing_service.create_subscription_service(data)

    if error:
        return jsonify({"message": "Error al crear la suscripción", "error": error}), 500

    return jsonify(subscription.to_dict()), 201

@billing_bp.route('/subscriptions/<int:subscription_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_subscription(subscription_id):
    if not _is_admin():
        return jsonify({"message": "Acceso no autorizado"}), 403

    subscription, error = billing_service.cancel_subscription_service(subscription_id)

    if error:
        return jsonify({"message": "Error al cancelar la suscripción", "error": error}), 500

    return jsonify(subscription.to_dict()), 200

@billing_bp.route('/process-invoices', methods=['POST'])
@jwt_required()
def process_invoices():
    if not _is_admin():
        return jsonify({"message": "Acceso no autorizado"}), 403

    result = billing_service.process_recurring_invoices_service()

    if result['errors']:
        return jsonify({
            "message": f"Proceso completado con errores. {result['processed_count']} facturas generadas.",
            "errors": result['errors']
        }), 500

    return jsonify({
        "message": f"Proceso completado exitosamente. {result['processed_count']} facturas generadas."
    }), 200
