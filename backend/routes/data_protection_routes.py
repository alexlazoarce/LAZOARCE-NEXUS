"""
backend/routes/data_protection_routes.py

Rutas para el Módulo de Protección de Datos (LAN-DPR2).
"""
from flask import Blueprint, request, jsonify
from ..services.jwt_service import get_current_tenant_id, get_current_user
from ..data_protection_service import data_protection_service

data_protection_bp = Blueprint('data_protection_bp', __name__)

# --- Rutas de Solicitudes de Protección de Datos ---
@data_protection_bp.route('/requests', methods=['GET', 'POST'])
def handle_requests():
    tenant_id = get_current_tenant_id()
    user = get_current_user()
    if request.method == 'POST':
        data = request.json
        dpr = data_protection_service.create_request(tenant_id, user.id, data['request_type'])
        return jsonify({'id': dpr.id, 'status': dpr.status}), 201

    requests = data_protection_service.get_requests(tenant_id)
    return jsonify([{'id': r.id, 'type': r.request_type, 'status': r.status} for r in requests])

@data_protection_bp.route('/requests/<int:request_id>/process', methods=['POST'])
def process_request(request_id):
    tenant_id = get_current_tenant_id()
    result = data_protection_service.process_request(tenant_id, request_id)
    if result:
        return jsonify({'message': 'Solicitud procesada exitosamente', 'data': result}), 200
    return jsonify({'message': 'Solicitud no encontrada o no se pudo procesar'}), 404
