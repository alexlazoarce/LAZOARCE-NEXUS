"""
teaching_routes.py - API routes for the Teaching Management module (LAN-TCH1).
"""
from flask import Blueprint, request, jsonify
from backend.services.jwt_service import jwt_required, get_current_user
from backend import teaching_service

teaching_bp = Blueprint('teaching_bp', __name__, url_prefix='/api/teaching')

@teaching_bp.route('/assignments', methods=['POST'])
@jwt_required
def create_assignment():
    """Create a new assignment."""
    data = request.get_json()
    # Assuming the user creating the assignment has the authority (e.g., teacher, admin)
    # Further role-based access control could be added here.
    try:
        new_assignment = teaching_service.create_assignment(data)
        return jsonify({'message': 'Assignment created successfully', 'assignment_id': new_assignment.id}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

@teaching_bp.route('/courses/<int:course_id>/assignments', methods=['GET'])
@jwt_required
def get_assignments_for_course(course_id):
    """Get all assignments for a course."""
    try:
        assignments = teaching_service.get_assignments_for_course(course_id)
        return jsonify([{'id': a.id, 'title': a.title, 'due_date': a.due_date} for a in assignments]), 200
    except Exception as e:
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

@teaching_bp.route('/assignments/<int:assignment_id>', methods=['GET'])
@jwt_required
def get_assignment(assignment_id):
    """Get a single assignment by ID."""
    try:
        assignment = teaching_service.get_assignment_by_id(assignment_id)
        if not assignment:
            return jsonify({'error': 'Assignment not found'}), 404
        return jsonify({
            'id': assignment.id,
            'title': assignment.title,
            'description': assignment.description,
            'due_date': assignment.due_date,
            'max_points': assignment.max_points
        }), 200
    except Exception as e:
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

@teaching_bp.route('/submissions', methods=['POST'])
@jwt_required
def create_submission():
    """Create a new student submission."""
    data = request.get_json()
    try:
        new_submission = teaching_service.create_submission(data)
        return jsonify({'message': 'Submission created successfully', 'submission_id': new_submission.id}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

@teaching_bp.route('/assignments/<int:assignment_id>/submissions', methods=['GET'])
@jwt_required
def get_submissions_for_assignment(assignment_id):
    """Get all submissions for an assignment."""
    try:
        submissions = teaching_service.get_submissions_for_assignment(assignment_id)
        return jsonify([{'id': s.id, 'student_id': s.student_id, 'submission_date': s.submission_date, 'grade': s.grade} for s in submissions]), 200
    except Exception as e:
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

@teaching_bp.route('/submissions/<int:submission_id>/grade', methods=['PUT'])
@jwt_required
def grade_submission(submission_id):
    """Grade a student submission."""
    data = request.get_json()
    grade = data.get('grade')
    feedback = data.get('feedback')
    if grade is None:
        return jsonify({'error': 'Grade is required'}), 400

    try:
        updated_submission = teaching_service.grade_submission(submission_id, grade, feedback)
        return jsonify({'message': 'Submission graded successfully', 'submission_id': updated_submission.id}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500
