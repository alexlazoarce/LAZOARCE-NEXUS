"""
backend/routes/cleaning_routes.py

Rutas para el Módulo de Gestión de Limpieza (LAN-CLN7).
"""
from flask import Blueprint, request, jsonify
from ..services.jwt_service import get_current_tenant_id, get_current_user
from ..cleaning_service import cleaning_service

cleaning_bp = Blueprint('cleaning_bp', __name__)

# --- Rutas de Servicios de Limpieza ---
@cleaning_bp.route('/services', methods=['GET', 'POST'])
def handle_services():
    tenant_id = get_current_tenant_id()
    if request.method == 'POST':
        data = request.json
        service = cleaning_service.create_service(tenant_id, data)
        return jsonify({'id': service.id, 'name': service.name}), 201

    services = cleaning_service.get_services(tenant_id)
    return jsonify([{'id': s.id, 'name': s.name, 'price': s.price} for s in services])

# --- Rutas de Órdenes de Limpieza ---
@cleaning_bp.route('/orders', methods=['GET', 'POST'])
def handle_orders():
    tenant_id = get_current_tenant_id()
    user = get_current_user()

    if request.method == 'POST':
        data = request.json
        order = cleaning_service.create_order(tenant_id, user.id, data['items'], data['scheduled_date'])
        return jsonify({'id': order.id, 'total_amount': order.total_amount}), 201

    orders = cleaning_service.get_orders(tenant_id)
    return jsonify([{'id': o.id, 'status': o.status, 'total': o.total_amount} for o in orders])

@cleaning_bp.route('/orders/<int:order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    tenant_id = get_current_tenant_id()
    data = request.json
    order = cleaning_service.update_order_status(tenant_id, order_id, data['status'])
    if order:
        return jsonify({'id': order.id, 'new_status': order.status}), 200
    return jsonify({'message': 'Orden no encontrada'}), 404

# --- Rutas de Insumos de Limpieza ---
@cleaning_bp.route('/supplies', methods=['GET', 'POST'])
def handle_supplies():
    tenant_id = get_current_tenant_id()
    if request.method == 'POST':
        data = request.json
        supply = cleaning_service.create_supply(tenant_id, data)
        return jsonify({'id': supply.id, 'name': supply.name}), 201

    supplies = cleaning_service.get_supplies(tenant_id)
    return jsonify([{'id': s.id, 'name': s.name, 'stock': s.stock_level} for s in supplies])
