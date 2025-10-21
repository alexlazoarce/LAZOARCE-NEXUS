from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.education_service import (
    create_student_service, get_students_service,
    create_course_service, get_courses_service,
    enroll_student_service, add_grade_service
)

education_bp = Blueprint('education_bp', __name__, url_prefix='/api/education')

# --- Student Routes ---
@education_bp.route('/students', methods=['POST'])
@jwt_required()
def create_student():
    data = request.get_json()
    response, status_code = create_student_service(data)
    return jsonify(response), status_code

@education_bp.route('/students', methods=['GET'])
@jwt_required()
def get_students():
    response, status_code = get_students_service()
    return jsonify(response), status_code

# --- Course Routes ---
@education_bp.route('/courses', methods=['POST'])
@jwt_required()
def create_course():
    data = request.get_json()
    response, status_code = create_course_service(data)
    return jsonify(response), status_code

@education_bp.route('/courses', methods=['GET'])
@jwt_required()
def get_courses():
    response, status_code = get_courses_service()
    return jsonify(response), status_code

# --- Enrollment Routes ---
@education_bp.route('/enrollments', methods=['POST'])
@jwt_required()
def enroll_student():
    data = request.get_json()
    response, status_code = enroll_student_service(data)
    return jsonify(response), status_code

# --- Grade Routes ---
@education_bp.route('/enrollments/<int:enrollment_id>/grades', methods=['POST'])
@jwt_required()
def add_grade(enrollment_id):
    data = request.get_json()
    response, status_code = add_grade_service(enrollment_id, data)
    return jsonify(response), status_code
