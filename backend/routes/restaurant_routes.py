from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.restaurant_service import (
    create_menu_item_service, get_menu_items_service,
    create_table_service, get_tables_service,
    create_order_service, add_item_to_order_service
)

restaurant_bp = Blueprint('restaurant_bp', __name__, url_prefix='/api/restaurant')

# --- Menu Item Routes ---
@restaurant_bp.route('/menu-items', methods=['POST'])
@jwt_required()
def create_menu_item():
    data = request.get_json()
    response, status_code = create_menu_item_service(data)
    return jsonify(response), status_code

@restaurant_bp.route('/menu-items', methods=['GET'])
@jwt_required()
def get_menu_items():
    response, status_code = get_menu_items_service()
    return jsonify(response), status_code

# --- Table Routes ---
@restaurant_bp.route('/tables', methods=['POST'])
@jwt_required()
def create_table():
    data = request.get_json()
    response, status_code = create_table_service(data)
    return jsonify(response), status_code

@restaurant_bp.route('/tables', methods=['GET'])
@jwt_required()
def get_tables():
    response, status_code = get_tables_service()
    return jsonify(response), status_code

# --- Order Routes ---
@restaurant_bp.route('/orders', methods=['POST'])
@jwt_required()
def create_order():
    data = request.get_json()
    response, status_code = create_order_service(data)
    return jsonify(response), status_code

@restaurant_bp.route('/orders/<int:order_id>/items', methods=['POST'])
@jwt_required()
def add_item_to_order(order_id):
    data = request.get_json()
    response, status_code = add_item_to_order_service(order_id, data)
    return jsonify(response), status_code
