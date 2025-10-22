from .models import db, ConstructionProject, BudgetItem, ProgressReport, Certification, RFI, Milestone
from sqlalchemy.exc import SQLAlchemyError
from flask_jwt_extended import get_jwt_identity
from datetime import date

def _get_current_user_info():
    """Extrae el tenant_id y user_id de la identidad del JWT."""
    identity = get_jwt_identity()
    return identity.get('tenant_id'), identity.get('user_id')

# --- Construction Project Service ---
def create_construction_project_service(data):
    tenant_id, user_id = _get_current_user_info()
    try:
        new_project = ConstructionProject(
            tenant_id=tenant_id,
            manager_id=user_id,
            name=data['name'],
            location=data.get('location'),
            start_date=date.fromisoformat(data['start_date']) if data.get('start_date') else None,
            end_date=date.fromisoformat(data['end_date']) if data.get('end_date') else None,
            budget=data.get('budget', 0.0)
        )
        db.session.add(new_project)
        db.session.commit()
        return {'message': 'Construction project created successfully', 'project': new_project.to_dict()}, 201
    except (SQLAlchemyError, ValueError) as e:
        db.session.rollback()
        return {'error': str(e)}, 500

def get_construction_projects_service():
    tenant_id, _ = _get_current_user_info()
    try:
        projects = ConstructionProject.query.filter_by(tenant_id=tenant_id).all()
        return [p.to_dict() for p in projects], 200
    except SQLAlchemyError as e:
        return {'error': str(e)}, 500

def get_construction_project_details_service(project_id):
    tenant_id, _ = _get_current_user_info()
    try:
        project = ConstructionProject.query.filter_by(id=project_id, tenant_id=tenant_id).first()
        if not project:
            return {'error': 'Project not found'}, 404
        details = project.to_dict()
        details['budget_items'] = [item.to_dict() for item in project.budget_items]
        details['progress_reports'] = [report.to_dict() for report in project.progress_reports]
        return details, 200
    except SQLAlchemyError as e:
        return {'error': str(e)}, 500

# --- Budget Item Service ---
def add_budget_item_service(project_id, data):
    tenant_id, _ = _get_current_user_info()
    try:
        project = ConstructionProject.query.filter_by(id=project_id, tenant_id=tenant_id).first()
        if not project:
            return {'error': 'Project not found'}, 404
        new_item = BudgetItem(
            tenant_id=tenant_id,
            project_id=project_id,
            name=data['name'],
            code=data.get('code'),
            amount=data['amount']
        )
        db.session.add(new_item)
        db.session.commit()
        return {'message': 'Budget item added successfully', 'item': new_item.to_dict()}, 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return {'error': str(e)}, 500

# --- Progress Report Service ---
def add_progress_report_service(project_id, data):
    tenant_id, user_id = _get_current_user_info()
    try:
        project = ConstructionProject.query.filter_by(id=project_id, tenant_id=tenant_id).first()
        if not project:
            return {'error': 'Project not found'}, 404
        new_report = ProgressReport(
            tenant_id=tenant_id,
            project_id=project_id,
            reported_by_id=user_id,
            report_date=date.fromisoformat(data['report_date']),
            percentage_complete=data['percentage_complete'],
            notes=data.get('notes')
        )
        db.session.add(new_report)
        db.session.commit()
        return {'message': 'Progress report added successfully', 'report': new_report.to_dict()}, 201
    except (SQLAlchemyError, ValueError) as e:
        db.session.rollback()
        return {'error': str(e)}, 500

# --- Certification Service ---
def create_certification_service(project_id, data):
    tenant_id, _ = _get_current_user_info()
    try:
        project = ConstructionProject.query.filter_by(id=project_id, tenant_id=tenant_id).first()
        if not project:
            return {'error': 'Project not found'}, 404
        new_certification = Certification(
            tenant_id=tenant_id,
            project_id=project_id,
            certification_date=date.fromisoformat(data['certification_date']),
            amount=data['amount'],
            description=data.get('description')
        )
        db.session.add(new_certification)
        db.session.commit()
        return {'message': 'Certification created successfully', 'certification': new_certification.to_dict()}, 201
    except (SQLAlchemyError, ValueError) as e:
        db.session.rollback()
        return {'error': str(e)}, 500

def get_certifications_for_project_service(project_id):
    tenant_id, _ = _get_current_user_info()
    try:
        certifications = Certification.query.filter_by(project_id=project_id, tenant_id=tenant_id).all()
        return [c.to_dict() for c in certifications], 200
    except SQLAlchemyError as e:
        return {'error': str(e)}, 500

# --- RFI Service ---
def create_rfi_service(project_id, data):
    tenant_id, user_id = _get_current_user_info()
    try:
        new_rfi = RFI(
            tenant_id=tenant_id,
            project_id=project_id,
            created_by_id=user_id,
            subject=data['subject'],
            question=data['question']
        )
        db.session.add(new_rfi)
        db.session.commit()
        return {'message': 'RFI created'}, 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return {'error': str(e)}, 500

# --- Milestone Service ---
def create_milestone_service(project_id, data):
    tenant_id, _ = _get_current_user_info()
    try:
        new_milestone = Milestone(
            tenant_id=tenant_id,
            project_id=project_id,
            name=data['name'],
            due_date=date.fromisoformat(data['due_date']) if data.get('due_date') else None,
            amount=data['amount']
        )
        db.session.add(new_milestone)
        db.session.commit()
        return {'message': 'Milestone created'}, 201
    except (SQLAlchemyError, ValueError) as e:
        db.session.rollback()
        return {'error': str(e)}, 500