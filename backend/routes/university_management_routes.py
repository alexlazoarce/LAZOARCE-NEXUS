"""
backend/routes/university_management_routes.py

Rutas para el Módulo de Gestión Universitaria (LAN-UNV8).
"""
from flask import Blueprint, request, jsonify
from ..services.jwt_service import get_current_tenant_id
from ..university_management_service import university_management_service

university_management_bp = Blueprint('university_management_bp', __name__)

# --- Rutas de Admisiones ---
@university_management_bp.route('/students/<int:student_id>/admission-status', methods=['PUT'])
def update_student_admission_status(student_id):
    data = request.json
    tenant_id = get_current_tenant_id()
    student, error = university_management_service.update_student_admission_status(tenant_id, student_id, data['status'])
    if error:
        return jsonify({'message': error}), 400
    return jsonify(student.to_dict())

# --- Rutas de Planes de Estudio ---
@university_management_bp.route('/degree-programs', methods=['GET', 'POST'])
def handle_degree_programs():
    tenant_id = get_current_tenant_id()
    if request.method == 'POST':
        data = request.json
        program = university_management_service.create_degree_program(tenant_id, data)
        return jsonify({'id': program.id, 'name': program.name}), 201

    programs = university_management_service.get_degree_programs(tenant_id)
    return jsonify([{'id': p.id, 'name': p.name, 'faculty': p.faculty} for p in programs])

# --- Rutas de Becas ---
@university_management_bp.route('/scholarships', methods=['GET', 'POST'])
def handle_scholarships():
    tenant_id = get_current_tenant_id()
    if request.method == 'POST':
        data = request.json
        scholarship = university_management_service.create_scholarship(tenant_id, data)
        return jsonify({'id': scholarship.id, 'name': scholarship.name}), 201

    scholarships = university_management_service.get_scholarships(tenant_id)
    return jsonify([{'id': s.id, 'name': s.name, 'amount': s.amount_or_percentage} for s in scholarships])

@university_management_bp.route('/students/<int:student_id>/scholarships', methods=['POST'])
def assign_scholarship(student_id):
    data = request.json
    tenant_id = get_current_tenant_id()
    assignment, error = university_management_service.assign_scholarship_to_student(tenant_id, student_id, data['scholarship_id'])
    if error:
        return jsonify({'message': error}), 400
    return jsonify({'message': 'Beca asignada exitosamente.'}), 201

# --- Rutas de Biblioteca ---
@university_management_bp.route('/library/resources', methods=['GET', 'POST'])
def handle_library_resources():
    tenant_id = get_current_tenant_id()
    if request.method == 'POST':
        data = request.json
        resource = university_management_service.create_library_resource(tenant_id, data)
        return jsonify({'id': resource.id, 'title': resource.title}), 201

    resources = university_management_service.get_library_resources(tenant_id)
    return jsonify([{'id': r.id, 'title': r.title, 'author': r.author} for r in resources])

# --- Rutas de Egresados ---
@university_management_bp.route('/students/<int:student_id>/graduate', methods=['POST'])
def graduate_student(student_id):
    data = request.json
    tenant_id = get_current_tenant_id()
    alumnus, error = university_management_service.graduate_student(tenant_id, student_id, data.get('graduation_date'))
    if error:
        return jsonify({'message': error}), 400
    return jsonify({'message': 'Estudiante marcado como egresado.'}), 200
