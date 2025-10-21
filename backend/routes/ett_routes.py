"""
Rutas de la API para el Módulo ETT (Empresa de Trabajo Temporal).
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.services import ett_service

ett_bp = Blueprint('ett_bp', __name__, url_prefix='/api/ett')

# Rutas para Empresas Cliente (ClientCompany)

@ett_bp.route('/client_companies', methods=['POST'])
@jwt_required()
def create_client_company():
    """Crea una nueva empresa cliente."""
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({'message': 'El nombre de la empresa es requerido'}), 400

    company, error = ett_service.create_client_company(data)
    if error:
        return jsonify({'message': 'Error al crear la empresa cliente', 'error': error}), 500

    return jsonify(company.to_dict()), 201

@ett_bp.route('/client_companies', methods=['GET'])
@jwt_required()
def get_all_client_companies():
    """Obtiene todas las empresas cliente."""
    companies = ett_service.get_all_client_companies()
    return jsonify([company.to_dict() for company in companies]), 200

@ett_bp.route('/client_companies/<int:company_id>', methods=['GET'])
@jwt_required()
def get_client_company_by_id(company_id):
    """Obtiene una empresa cliente por su ID."""
    company = ett_service.get_client_company_by_id(company_id)
    if not company:
        return jsonify({'message': 'Empresa cliente no encontrada'}), 404
    return jsonify(company.to_dict()), 200

@ett_bp.route('/client_companies/<int:company_id>', methods=['PUT'])
@jwt_required()
def update_client_company(company_id):
    """Actualiza una empresa cliente."""
    data = request.get_json()
    company, error = ett_service.update_client_company(company_id, data)

    if error:
        return jsonify({'message': error}), 404 if "no encontrada" in error else 500

    return jsonify(company.to_dict()), 200

# Rutas para Asignaciones Temporales (TemporaryAssignment)

@ett_bp.route('/assignments', methods=['POST'])
@jwt_required()
def create_assignment():
    """Crea una nueva asignación temporal."""
    data = request.get_json()
    required_fields = ['employee_id', 'client_company_id', 'start_date', 'end_date', 'assignment_salary']
    if not all(field in data for field in required_fields):
        return jsonify({'message': 'Faltan campos requeridos'}), 400

    assignment, error = ett_service.create_assignment(data)
    if error:
        return jsonify({'message': 'Error al crear la asignación', 'error': error}), 500

    return jsonify(assignment.to_dict()), 201

@ett_bp.route('/assignments', methods=['GET'])
@jwt_required()
def get_all_assignments():
    """Obtiene todas las asignaciones."""
    assignments = ett_service.get_all_assignments()
    return jsonify([a.to_dict() for a in assignments]), 200

@ett_bp.route('/assignments/<int:assignment_id>', methods=['GET'])
@jwt_required()
def get_assignment_by_id(assignment_id):
    """Obtiene una asignación por su ID."""
    assignment = ett_service.get_assignment_by_id(assignment_id)
    if not assignment:
        return jsonify({'message': 'Asignación no encontrada'}), 404
    return jsonify(assignment.to_dict()), 200

@ett_bp.route('/assignments/<int:assignment_id>', methods=['PUT'])
@jwt_required()
def update_assignment(assignment_id):
    """Actualiza una asignación."""
    data = request.get_json()
    assignment, error = ett_service.update_assignment(assignment_id, data)

    if error:
        return jsonify({'message': error}), 404 if "no encontrada" in error else 500

    return jsonify(assignment.to_dict()), 200

@ett_bp.route('/assignments/<int:assignment_id>', methods=['DELETE'])
@jwt_required()
def deactivate_assignment(assignment_id):
    """Desactiva una asignación."""
    assignment, error = ett_service.deactivate_assignment(assignment_id)

    if error:
        return jsonify({'message': error}), 404 if "no encontrada" in error else 500

    return jsonify({'message': 'Asignación desactivada exitosamente'}), 200

@ett_bp.route('/employees/<int:employee_id>/assignments', methods=['GET'])
@jwt_required()
def get_assignments_for_employee(employee_id):
    """Obtiene todas las asignaciones de un empleado."""
    assignments = ett_service.get_assignments_for_employee(employee_id)
    return jsonify([a.to_dict() for a in assignments]), 200

@ett_bp.route('/client_companies/<int:company_id>/assignments', methods=['GET'])
@jwt_required()
def get_assignments_for_client_company(company_id):
    """Obtiene todas las asignaciones para una empresa cliente."""
    assignments = ett_service.get_assignments_for_client_company(company_id)
    return jsonify([a.to_dict() for a in assignments]), 200
