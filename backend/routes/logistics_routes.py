from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.logistics_service import (
    create_vehicle_service, get_vehicles_service,
    create_driver_service, get_drivers_service,
    create_route_service, get_routes_service,
    add_delivery_to_route_service
)

logistics_bp = Blueprint('logistics_bp', __name__, url_prefix='/api/logistics')

# --- Vehicle Routes ---
@logistics_bp.route('/vehicles', methods=['POST'])
@jwt_required()
def create_vehicle():
    data = request.get_json()
    response, status_code = create_vehicle_service(data)
    return jsonify(response), status_code

@logistics_bp.route('/vehicles', methods=['GET'])
@jwt_required()
def get_vehicles():
    response, status_code = get_vehicles_service()
    return jsonify(response), status_code

# --- Driver Routes ---
@logistics_bp.route('/drivers', methods=['POST'])
@jwt_required()
def create_driver():
    data = request.get_json()
    response, status_code = create_driver_service(data)
    return jsonify(response), status_code

@logistics_bp.route('/drivers', methods=['GET'])
@jwt_required()
def get_drivers():
    response, status_code = get_drivers_service()
    return jsonify(response), status_code

# --- Route Routes ---
@logistics_bp.route('/routes', methods=['POST'])
@jwt_required()
def create_route():
    data = request.get_json()
    response, status_code = create_route_service(data)
    return jsonify(response), status_code

@logistics_bp.route('/routes', methods=['GET'])
@jwt_required()
def get_routes():
    response, status_code = get_routes_service()
    return jsonify(response), status_code

# --- Delivery Routes ---
@logistics_bp.route('/routes/<int:route_id>/deliveries', methods=['POST'])
@jwt_required()
def add_delivery_to_route(route_id):
    data = request.get_json()
    response, status_code = add_delivery_to_route_service(route_id, data)
    return jsonify(response), status_code
