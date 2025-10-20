"""
Rutas de la API para el Módulo de Contabilidad (NEXUS-BOOKS).
"""
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from backend import accounting_service

accounting_bp = Blueprint('accounting_bp', __name__, url_prefix='/api/accounting')

def _is_authorized():
    """Helper to check for Admin or Contador roles."""
    claims = get_jwt()
    user_roles = claims.get('roles', [])
    return 'Admin' in user_roles or 'Contador' in user_roles

@accounting_bp.route('/journal', methods=['GET'])
@jwt_required()
def get_journal_entries():
    if not _is_authorized():
        return jsonify({"message": "Acceso no autorizado"}), 403
    entries = accounting_service.get_journal_entries_service()
    return jsonify([entry.to_dict() for entry in entries])

@accounting_bp.route('/general-ledger', methods=['GET'])
@jwt_required()
def get_general_ledger():
    if not _is_authorized():
        return jsonify({"message": "Acceso no autorizado"}), 403
    ledger = accounting_service.get_general_ledger_service()
    return jsonify(ledger)

@accounting_bp.route('/trial-balance', methods=['GET'])
@jwt_required()
def get_trial_balance():
    if not _is_authorized():
        return jsonify({"message": "Acceso no autorizado"}), 403
    report = accounting_service.get_trial_balance_service()
    return jsonify(report)

@accounting_bp.route('/balance-sheet', methods=['GET'])
@jwt_required()
def get_balance_sheet():
    if not _is_authorized():
        return jsonify({"message": "Acceso no autorizado"}), 403
    report = accounting_service.get_balance_sheet_service()
    return jsonify(report)

@accounting_bp.route('/income-statement', methods=['GET'])
@jwt_required()
def get_income_statement():
    if not _is_authorized():
        return jsonify({"message": "Acceso no autorizado"}), 403
    report = accounting_service.get_income_statement_service()
    return jsonify(report)
