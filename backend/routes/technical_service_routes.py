from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.technical_service import (
    create_service_job_service, get_service_jobs_service,
    create_job_quote_service, create_job_invoice_service
)

technical_service_bp = Blueprint('technical_service_bp', __name__, url_prefix='/api/technical-services')

# --- Service Job Routes ---
@technical_service_bp.route('/jobs', methods=['POST'])
@jwt_required()
def create_service_job():
    data = request.get_json()
    response, status_code = create_service_job_service(data)
    return jsonify(response), status_code

@technical_service_bp.route('/jobs', methods=['GET'])
@jwt_required()
def get_service_jobs():
    response, status_code = get_service_jobs_service()
    return jsonify(response), status_code

# --- Job Quote Routes ---
@technical_service_bp.route('/jobs/<int:job_id>/quotes', methods=['POST'])
@jwt_required()
def create_job_quote(job_id):
    data = request.get_json()
    response, status_code = create_job_quote_service(job_id, data)
    return jsonify(response), status_code

# --- Job Invoice Routes ---
@technical_service_bp.route('/jobs/<int:job_id>/invoices', methods=['POST'])
@jwt_required()
def create_job_invoice(job_id):
    data = request.get_json()
    response, status_code = create_job_invoice_service(job_id, data)
    return jsonify(response), status_code
