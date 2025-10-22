"""
backend/routes/school_management_routes.py

Rutas para el Módulo de Gestión Escolar (LAN-SCH6).
"""
from flask import Blueprint, request, jsonify
from ..services.jwt_service import get_current_tenant_id
from ..school_management_service import school_management_service

school_management_bp = Blueprint('school_management_bp', __name__)

# --- Rutas de Estudiantes ---
@school_management_bp.route('/students', methods=['GET'])
def get_students():
    tenant_id = get_current_tenant_id()
    students = school_management_service.get_students(tenant_id)
    return jsonify([s.to_dict() for s in students])

@school_management_bp.route('/students', methods=['POST'])
def create_student():
    data = request.json
    tenant_id = get_current_tenant_id()
    student = school_management_service.create_student(tenant_id, data)
    if student:
        return jsonify(student.to_dict()), 201
    return jsonify({'message': 'El estudiante ya existe o los datos son inválidos'}), 400

# --- Rutas de Cursos ---
@school_management_bp.route('/courses', methods=['GET'])
def get_courses():
    tenant_id = get_current_tenant_id()
    courses = school_management_service.get_courses(tenant_id)
    return jsonify([c.to_dict() for c in courses])

@school_management_bp.route('/courses', methods=['POST'])
def create_course():
    data = request.json
    tenant_id = get_current_tenant_id()
    course = school_management_service.create_course(tenant_id, data)
    if course:
        return jsonify(course.to_dict()), 201
    return jsonify({'message': 'El curso ya existe o los datos son inválidos'}), 400

# --- Rutas de Inscripciones ---
@school_management_bp.route('/enrollments', methods=['POST'])
def enroll_student():
    data = request.json
    tenant_id = get_current_tenant_id()
    enrollment, error = school_management_service.enroll_student(tenant_id, data['student_id'], data['course_id'])
    if error:
        return jsonify({'message': error}), 400
    return jsonify({'message': 'Inscripción exitosa'}), 201

@school_management_bp.route('/students/<int:student_id>/enrollments', methods=['GET'])
def get_student_enrollments(student_id):
    tenant_id = get_current_tenant_id()
    enrollments = school_management_service.get_student_enrollments(tenant_id, student_id)
    # Aquí sería bueno devolver más detalles de la inscripción
    return jsonify([{'course_id': e.course_id, 'final_grade': e.final_grade} for e in enrollments])

# --- Rutas de Calificaciones ---
@school_management_bp.route('/enrollments/<int:enrollment_id>/grades', methods=['POST'])
def add_grade(enrollment_id):
    data = request.json
    tenant_id = get_current_tenant_id()
    grade, error = school_management_service.add_grade(tenant_id, enrollment_id, data)
    if error:
        return jsonify({'message': error}), 404
    return jsonify({'message': 'Calificación añadida exitosamente'}), 201

# --- Rutas de Pagos ---
@school_management_bp.route('/students/<int:student_id>/payments', methods=['POST'])
def add_payment(student_id):
    data = request.json
    tenant_id = get_current_tenant_id()
    payment, error = school_management_service.add_tuition_payment(tenant_id, student_id, data)
    if error:
        return jsonify({'message': error}), 404
    return jsonify({'message': 'Pago registrado exitosamente'}), 201

@school_management_bp.route('/students/<int:student_id>/payments', methods=['GET'])
def get_payments(student_id):
    tenant_id = get_current_tenant_id()
    payments = school_management_service.get_student_payments(tenant_id, student_id)
    return jsonify([{'amount': p.amount, 'date': p.payment_date.isoformat(), 'concept': p.concept} for p in payments])
