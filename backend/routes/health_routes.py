from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.health_service import (
    create_patient_record_service, get_patient_records_service,
    create_appointment_service, get_appointments_service,
    create_prescription_service, create_lab_order_service
)

health_bp = Blueprint('health_bp', __name__, url_prefix='/api/health')

# --- Patient Record Routes ---

@health_bp.route('/patients', methods=['POST'])
@jwt_required()
def create_patient():
    data = request.get_json()
    response, status_code = create_patient_record_service(data)
    return jsonify(response), status_code

@health_bp.route('/patients', methods=['GET'])
@jwt_required()
def get_patients():
    response, status_code = get_patient_records_service()
    return jsonify(response), status_code

# --- Appointment Routes ---

@health_bp.route('/appointments', methods=['POST'])
@jwt_required()
def create_appointment():
    data = request.get_json()
    response, status_code = create_appointment_service(data)
    return jsonify(response), status_code

@health_bp.route('/appointments', methods=['GET'])
@jwt_required()
def get_appointments():
    filters = {
        'doctor_id': request.args.get('doctor_id'),
        'patient_id': request.args.get('patient_id'),
        'date': request.args.get('date')
    }
    active_filters = {k: v for k, v in filters.items() if v}
    response, status_code = get_appointments_service(active_filters)
    return jsonify(response), status_code

# --- Prescription and Lab Order Routes ---

@health_bp.route('/appointments/<int:appointment_id>/prescriptions', methods=['POST'])
@jwt_required()
def create_prescription(appointment_id):
    data = request.get_json()
    response, status_code = create_prescription_service(appointment_id, data)
    return jsonify(response), status_code

@health_bp.route('/appointments/<int:appointment_id>/lab_orders', methods=['POST'])
@jwt_required()
def create_lab_order(appointment_id):
    data = request.get_json()
    response, status_code = create_lab_order_service(appointment_id, data)
    return jsonify(response), status_code
