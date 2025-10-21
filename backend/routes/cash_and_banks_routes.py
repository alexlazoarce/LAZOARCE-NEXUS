from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.cash_and_banks_service import (
    create_bank_account_service, get_bank_accounts_service,
    create_bank_transaction_service, get_bank_transactions_service,
    create_cash_box_service, get_cash_boxes_service,
    create_cash_transaction_service, get_cash_transactions_for_box_service
)

cash_and_banks_bp = Blueprint('cash_and_banks_bp', __name__, url_prefix='/api/cash_and_banks')

@cash_and_banks_bp.route('/bank_accounts', methods=['POST'])
@jwt_required()
def create_bank_account():
    data = request.get_json()
    response, status_code = create_bank_account_service(data)
    return jsonify(response), status_code

@cash_and_banks_bp.route('/bank_accounts', methods=['GET'])
@jwt_required()
def get_bank_accounts():
    response, status_code = get_bank_accounts_service()
    return jsonify(response), status_code

@cash_and_banks_bp.route('/bank_transactions', methods=['POST'])
@jwt_required()
def create_bank_transaction():
    data = request.get_json()
    response, status_code = create_bank_transaction_service(data)
    return jsonify(response), status_code

@cash_and_banks_bp.route('/bank_transactions/<int:account_id>', methods=['GET'])
@jwt_required()
def get_bank_transactions(account_id):
    response, status_code = get_bank_transactions_service(account_id)
    return jsonify(response), status_code

@cash_and_banks_bp.route('/cash_boxes', methods=['POST'])
@jwt_required()
def create_cash_box():
    data = request.get_json()
    response, status_code = create_cash_box_service(data)
    return jsonify(response), status_code

@cash_and_banks_bp.route('/cash_boxes', methods=['GET'])
@jwt_required()
def get_cash_boxes():
    response, status_code = get_cash_boxes_service()
    return jsonify(response), status_code

@cash_and_banks_bp.route('/cash_transactions', methods=['POST'])
@jwt_required()
def create_cash_transaction():
    data = request.get_json()
    response, status_code = create_cash_transaction_service(data)
    return jsonify(response), status_code

@cash_and_banks_bp.route('/cash_transactions/<int:cash_box_id>', methods=['GET'])
@jwt_required()
def get_cash_transactions_for_box(cash_box_id):
    response, status_code = get_cash_transactions_for_box_service(cash_box_id)
    return jsonify(response), status_code
