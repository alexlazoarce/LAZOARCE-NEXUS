"""
backend/routes/laundry_routes.py

Rutas para el Módulo de Gestión de Lavandería (LAN-LDR3).
"""
from flask import Blueprint, request, jsonify
from ..services.jwt_service import get_current_tenant_id, get_current_user
from ..laundry_service import laundry_service

laundry_bp = Blueprint('laundry_bp', __name__)

# --- Rutas de Servicios de Lavandería ---
@laundry_bp.route('/services', methods=['GET', 'POST'])
def handle_services():
    tenant_id = get_current_tenant_id()
    if request.method == 'POST':
        data = request.json
        service = laundry_service.create_service(tenant_id, data)
        return jsonify({'id': service.id, 'name': service.name}), 201

    services = laundry_service.get_services(tenant_id)
    return jsonify([{'id': s.id, 'name': s.name, 'price': s.price} for s in services])

# --- Rutas de Órdenes de Lavandería ---
@laundry_bp.route('/orders', methods=['GET', 'POST'])
def handle_orders():
    tenant_id = get_current_tenant_id()
    user = get_current_user()

    if request.method == 'POST':
        data = request.json
        order = laundry_service.create_order(tenant_id, user.id, data['items'])
        return jsonify({'id': order.id, 'total_amount': order.total_amount}), 201

    orders = laundry_service.get_orders(tenant_id)
    return jsonify([{'id': o.id, 'status': o.status, 'total': o.total_amount} for o in orders])

@laundry_bp.route('/orders/<int:order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    tenant_id = get_current_tenant_id()
    data = request.json
    order = laundry_service.update_order_status(tenant_id, order_id, data['status'])
    if order:
        return jsonify({'id': order.id, 'new_status': order.status}), 200
    return jsonify({'message': 'Orden no encontrada'}), 404

# --- Rutas de Insumos de Lavandería ---
@laundry_bp.route('/supplies', methods=['GET', 'POST'])
def handle_supplies():
    tenant_id = get_current_tenant_id()
    if request.method == 'POST':
        data = request.json
        supply = laundry_service.create_supply(tenant_id, data)
        return jsonify({'id': supply.id, 'name': supply.name}), 201

    supplies = laundry_service.get_supplies(tenant_id)
    return jsonify([{'id': s.id, 'name': s.name, 'stock': s.stock_level} for s in supplies])
