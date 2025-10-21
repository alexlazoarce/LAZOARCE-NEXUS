from .models import db, Student, Course, Enrollment, Grade, User
from sqlalchemy.exc import SQLAlchemyError
from flask_jwt_extended import get_jwt_identity
from datetime import date

def _get_current_user_info():
    """Extrae el tenant_id y user_id de la identidad del JWT."""
    identity = get_jwt_identity()
    return identity.get('tenant_id'), identity.get('user_id')

# --- Student Service ---
def create_student_service(data):
    tenant_id, _ = _get_current_user_info()
    try:
        new_student = Student(
            tenant_id=tenant_id,
            full_name=data['full_name'],
            student_code=data.get('student_code')
        )
        db.session.add(new_student)
        db.session.commit()
        return {'message': 'Student created', 'student': new_student.to_dict()}, 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return {'error': str(e)}, 500

def get_students_service():
    tenant_id, _ = _get_current_user_info()
    students = Student.query.filter_by(tenant_id=tenant_id).all()
    return [s.to_dict() for s in students], 200

# --- Course Service ---
def create_course_service(data):
    tenant_id, _ = _get_current_user_info()
    try:
        new_course = Course(
            tenant_id=tenant_id,
            name=data['name'],
            course_code=data.get('course_code'),
            teacher_id=data.get('teacher_id')
        )
        db.session.add(new_course)
        db.session.commit()
        return {'message': 'Course created', 'course': new_course.to_dict()}, 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return {'error': str(e)}, 500

def get_courses_service():
    tenant_id, _ = _get_current_user_info()
    courses = Course.query.filter_by(tenant_id=tenant_id).all()
    return [c.to_dict() for c in courses], 200

# --- Enrollment Service ---
def enroll_student_service(data):
    tenant_id, _ = _get_current_user_info()
    try:
        # Validations
        student = Student.query.filter_by(id=data['student_id'], tenant_id=tenant_id).first()
        course = Course.query.filter_by(id=data['course_id'], tenant_id=tenant_id).first()
        if not student or not course:
            return {'error': 'Student or Course not found'}, 404

        existing_enrollment = Enrollment.query.filter_by(student_id=data['student_id'], course_id=data['course_id']).first()
        if existing_enrollment:
            return {'error': 'Student is already enrolled in this course'}, 409

        new_enrollment = Enrollment(
            tenant_id=tenant_id,
            student_id=data['student_id'],
            course_id=data['course_id']
        )
        db.session.add(new_enrollment)
        db.session.commit()
        return {'message': 'Enrollment successful'}, 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return {'error': str(e)}, 500

# --- Grade Service ---
def add_grade_service(enrollment_id, data):
    tenant_id, _ = _get_current_user_info()
    try:
        enrollment = Enrollment.query.filter_by(id=enrollment_id, tenant_id=tenant_id).first()
        if not enrollment:
            return {'error': 'Enrollment not found'}, 404

        new_grade = Grade(
            tenant_id=tenant_id,
            enrollment_id=enrollment_id,
            grade_name=data['grade_name'],
            score=data['score']
        )
        db.session.add(new_grade)
        db.session.commit()
        # Opcional: Recalcular nota final
        # update_final_grade(enrollment_id)
        return {'message': 'Grade added successfully'}, 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return {'error': str(e)}, 500
