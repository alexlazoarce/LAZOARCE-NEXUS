"""
teaching_service.py - Service layer for the Teaching Management module (LAN-TCH1).
"""
from datetime import datetime
from .models import db, TeachingAssignment, StudentSubmission, Course, Student
from .services.jwt_service import get_current_tenant_id

def create_assignment(data):
    """Creates a new assignment for a course."""
    tenant_id = get_current_tenant_id()
    course = Course.query.filter_by(id=data.get('course_id'), tenant_id=tenant_id).first()
    if not course:
        raise ValueError("Course not found for the current tenant.")

    new_assignment = TeachingAssignment(
        course_id=data['course_id'],
        title=data['title'],
        description=data.get('description'),
        due_date=data.get('due_date'),
        max_points=data.get('max_points'),
        tenant_id=tenant_id
    )
    db.session.add(new_assignment)
    db.session.commit()
    return new_assignment

def get_assignments_for_course(course_id):
    """Retrieves all assignments for a specific course."""
    tenant_id = get_current_tenant_id()
    return TeachingAssignment.query.filter_by(course_id=course_id, tenant_id=tenant_id).all()

def get_assignment_by_id(assignment_id):
    """Retrieves a single assignment by its ID."""
    tenant_id = get_current_tenant_id()
    return TeachingAssignment.query.filter_by(id=assignment_id, tenant_id=tenant_id).first()

def create_submission(data):
    """Creates a new student submission for an assignment."""
    tenant_id = get_current_tenant_id()

    # Verify assignment and student exist for the tenant
    assignment = TeachingAssignment.query.filter_by(id=data.get('assignment_id'), tenant_id=tenant_id).first()
    if not assignment:
        raise ValueError("Assignment not found for the current tenant.")

    student = Student.query.filter_by(id=data.get('student_id'), tenant_id=tenant_id).first()
    if not student:
        raise ValueError("Student not found for the current tenant.")

    # Check for existing submission
    existing_submission = StudentSubmission.query.filter_by(
        assignment_id=data['assignment_id'],
        student_id=data['student_id'],
        tenant_id=tenant_id
    ).first()
    if existing_submission:
        raise ValueError("A submission for this assignment by this student already exists.")

    new_submission = StudentSubmission(
        assignment_id=data['assignment_id'],
        student_id=data['student_id'],
        content=data.get('content'),
        file_path=data.get('file_path'),
        submission_date=datetime.utcnow(),
        tenant_id=tenant_id
    )
    db.session.add(new_submission)
    db.session.commit()
    return new_submission

def get_submissions_for_assignment(assignment_id):
    """Retrieves all submissions for a specific assignment."""
    tenant_id = get_current_tenant_id()
    return StudentSubmission.query.filter_by(assignment_id=assignment_id, tenant_id=tenant_id).all()

def grade_submission(submission_id, grade, feedback):
    """Grades a student's submission."""
    tenant_id = get_current_tenant_id()
    submission = StudentSubmission.query.filter_by(id=submission_id, tenant_id=tenant_id).first()
    if not submission:
        raise ValueError("Submission not found for the current tenant.")

    submission.grade = grade
    submission.feedback = feedback
    db.session.commit()
    return submission
