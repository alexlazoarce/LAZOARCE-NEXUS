"""
backend/routes/controller_routes.py

Rutas para el Módulo de Contraloría (LAN-C7N).
"""
from flask import Blueprint, request, jsonify
from ..services.jwt_service import get_current_tenant_id
from ..controller_service import controller_service

controller_bp = Blueprint('controller_bp', __name__)

# --- Rutas de Controles Internos ---
@controller_bp.route('/controls', methods=['GET', 'POST'])
def handle_controls():
    tenant_id = get_current_tenant_id()
    if request.method == 'POST':
        data = request.json
        control = controller_service.create_internal_control(tenant_id, data)
        return jsonify({'id': control.id, 'name': control.name}), 201

    controls = controller_service.get_internal_controls(tenant_id)
    return jsonify([{'id': c.id, 'name': c.name, 'type': c.control_type} for c in controls])

# --- Rutas de Reportes de Auditoría ---
@controller_bp.route('/reports', methods=['GET', 'POST'])
def handle_reports():
    tenant_id = get_current_tenant_id()
    if request.method == 'POST':
        data = request.json
        report = controller_service.create_audit_report(tenant_id, data)
        return jsonify({'id': report.id, 'title': report.title}), 201

    reports = controller_service.get_audit_reports(tenant_id)
    return jsonify([{'id': r.id, 'title': r.title, 'area': r.audit_area} for r in reports])
