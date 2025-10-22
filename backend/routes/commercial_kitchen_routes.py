from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.commercial_kitchen_service import (
    create_kitchen_space_service,
    create_booking_service,
    create_haccp_log_service
)

commercial_kitchen_bp = Blueprint('commercial_kitchen_bp', __name__, url_prefix='/api/commercial-kitchen')

# --- Kitchen Space Routes ---
@commercial_kitchen_bp.route('/spaces', methods=['POST'])
@jwt_required()
def create_kitchen_space():
    data = request.get_json()
    response, status_code = create_kitchen_space_service(data)
    return jsonify(response), status_code

# --- Kitchen Booking Routes ---
@commercial_kitchen_bp.route('/bookings', methods=['POST'])
@jwt_required()
def create_booking():
    data = request.get_json()
    response, status_code = create_booking_service(data)
    return jsonify(response), status_code

# --- HACCP Log Routes ---
@commercial_kitchen_bp.route('/haccp-logs', methods=['POST'])
@jwt_required()
def create_haccp_log():
    data = request.get_json()
    response, status_code = create_haccp_log_service(data)
    return jsonify(response), status_code
