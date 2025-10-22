from .models import db, ConstructionProject, BudgetItem, ProgressReport, Certification, RFI, Milestone
from sqlalchemy.exc import SQLAlchemyError
from flask_jwt_extended import get_jwt_identity, get_jwt # Added get_jwt
from datetime import date

def _get_current_user_info():
    """Extrae tenant_id y user_id de las claims del JWT."""
    # Updated to get claims from get_jwt() which is more standard
    claims = get_jwt()
    tenant_id = claims.get('tenant_id')
    user_id = claims.get('user_id') # Assuming user_id is in claims, adjust if identity() is used directly for user_id
    # Fallback if user_id not in claims, might use identity (e.g., email) to lookup user
    # if not user_id:
    #    user_identity = get_jwt_identity()
    #    # Logic to get user_id from user_identity if needed
    return tenant_id, user_id

# --- Construction Project Service ---
def create_construction_project_service(data):
    tenant_id, user_id = _get_current_user_info()
    if not tenant_id:
         return {'error': 'Tenant information missing in token'}, 400
    try:
        start_date_obj = date.fromisoformat(data['start_date']) if data.get('start_date') else None
        end_date_obj = date.fromisoformat(data['end_date']) if data.get('end_date') else None

        new_project = ConstructionProject(
            tenant_id=tenant_id,
            manager_id=user_id, # Assigning creator as manager by default
            name=data['name'],
            location=data.get('location'),
            start_date=start_date_obj,
            end_date=end_date_obj,
            budget=float(data.get('budget', 0.0)) # Ensure budget is float
        )
        db.session.add(new_project)
        db.session.commit()
        # Assuming .to_dict() method exists on the model
        return {'message': 'Construction project created successfully', 'project': new_project.to_dict()}, 201
    except (SQLAlchemyError, ValueError, KeyError) as e:
        db.session.rollback()
        # Log the error e
        return {'error': f'Failed to create project: {str(e)}'}, 500

def get_construction_projects_service():
    tenant_id, _ = _get_current_user_info()
    if not tenant_id:
         return {'error': 'Tenant information missing in token'}, 400
    try:
        projects = ConstructionProject.query.filter_by(tenant_id=tenant_id).all()
        # Assuming .to_dict() method exists on the model
        return [p.to_dict() for p in projects], 200
    except SQLAlchemyError as e:
        # Log the error e
        return {'error': f'Database error: {str(e)}'}, 500

def get_construction_project_details_service(project_id):
    tenant_id, _ = _get_current_user_info()
    if not tenant_id:
         return {'error': 'Tenant information missing in token'}, 400
    try:
        project = ConstructionProject.query.filter_by(id=project_id, tenant_id=tenant_id).first()
        if not project:
            return {'error': 'Project not found'}, 404

        # Assuming .to_dict() method exists on models
        details = project.to_dict()
        details['budget_items'] = [item.to_dict() for item in project.budget_items or []] # Handle potential None
        details['progress_reports'] = [report.to_dict() for report in project.progress_reports or []] # Handle potential None
        # Add Certifications, RFIs, Milestones if needed
        details['certifications'] = [cert.to_dict() for cert in Certification.query.filter_by(project_id=project_id, tenant_id=tenant_id).all()]
        details['rfis'] = [{'id': rfi.id, 'subject': rfi.subject, 'status': rfi.status} for rfi in RFI.query.filter_by(project_id=project_id, tenant_id=tenant_id).all()]
        details['milestones'] = [{'id': m.id, 'name': m.name, 'amount': m.amount, 'status': m.status} for m in Milestone.query.filter_by(project_id=project_id, tenant_id=tenant_id).all()]

        return details, 200
    except SQLAlchemyError as e:
        # Log the error e
        return {'error': f'Database error: {str(e)}'}, 500

# --- Budget Item Service ---
def add_budget_item_service(project_id, data):
    tenant_id, _ = _get_current_user_info()
    if not tenant_id:
         return {'error': 'Tenant information missing in token'}, 400
    try:
        # Verify project exists and belongs to the tenant
        project = ConstructionProject.query.filter_by(id=project_id, tenant_id=tenant_id).first()
        if not project:
            return {'error': 'Project not found'}, 404

        new_item = BudgetItem(
            tenant_id=tenant_id,
            project_id=project_id,
            name=data['name'],
            code=data.get('code'),
            amount=float(data['amount']) # Ensure amount is float
        )
        db.session.add(new_item)
        db.session.commit()
        # Assuming .to_dict() method exists
        return {'message': 'Budget item added successfully', 'item': new_item.to_dict()}, 201
    except (SQLAlchemyError, ValueError, KeyError) as e:
        db.session.rollback()
        # Log the error e
        return {'error': f'Failed to add budget item: {str(e)}'}, 500

# --- Progress Report Service ---
def add_progress_report_service(project_id, data):
    tenant_id, user_id = _get_current_user_info()
    if not tenant_id:
         return {'error': 'Tenant information missing in token'}, 400
    try:
        # Verify project exists and belongs to the tenant
        project = ConstructionProject.query.filter_by(id=project_id, tenant_id=tenant_id).first()
        if not project:
            return {'error': 'Project not found'}, 404

        report_date_obj = date.fromisoformat(data['report_date'])

        new_report = ProgressReport(
            tenant_id=tenant_id,
            project_id=project_id,
            reported_by_id=user_id,
            report_date=report_date_obj,
            percentage_complete=float(data['percentage_complete']), # Ensure float
            notes=data.get('notes')
        )
        db.session.add(new_report)
        db.session.commit()
        # Assuming .to_dict() method exists
        return {'message': 'Progress report added successfully', 'report': new_report.to_dict()}, 201
    except (SQLAlchemyError, ValueError, KeyError) as e:
        db.session.rollback()
        # Log the error e
        return {'error': f'Failed to add progress report: {str(e)}'}, 500

# --- Certification Service ---
def create_certification_service(project_id, data):
    tenant_id, user_id = _get_current_user_info() # Get user_id if needed for approved_by
    if not tenant_id:
         return {'error': 'Tenant information missing in token'}, 400
    try:
        # Verify project exists and belongs to the tenant
        project = ConstructionProject.query.filter_by(id=project_id, tenant_id=tenant_id).first()
        if not project:
            return {'error': 'Project not found'}, 404

        certification_date_obj = date.fromisoformat(data['certification_date'])

        new_certification = Certification(
            tenant_id=tenant_id,
            project_id=project_id,
            certification_date=certification_date_obj,
            amount=float(data['amount']), # Ensure float
            description=data.get('description'),
            status='Pendiente' # Default status
            # approved_by_id=user_id # Or set later during approval workflow
        )
        db.session.add(new_certification)
        db.session.commit()
        # Assuming .to_dict() method exists
        return {'message': 'Certification created successfully', 'certification': new_certification.to_dict()}, 201
    except (SQLAlchemyError, ValueError, KeyError) as e:
        db.session.rollback()
        # Log the error e
        return {'error': f'Failed to create certification: {str(e)}'}, 500

def get_certifications_for_project_service(project_id):
    tenant_id, _ = _get_current_user_info()
    if not tenant_id:
         return {'error': 'Tenant information missing in token'}, 400
    try:
        certifications = Certification.query.filter_by(project_id=project_id, tenant_id=tenant_id).all()
        # Assuming .to_dict() method exists
        return [c.to_dict() for c in certifications], 200
    except SQLAlchemyError as e:
        # Log the error e
        return {'error': f'Database error: {str(e)}'}, 500

# --- RFI Service ---
def create_rfi_service(project_id, data):
    tenant_id, user_id = _get_current_user_info()
    if not tenant_id:
         return {'error': 'Tenant information missing in token'}, 400
    try:
        # Verify project exists and belongs to the tenant
        project = ConstructionProject.query.filter_by(id=project_id, tenant_id=tenant_id).first()
        if not project:
            return {'error': 'Project not found'}, 404

        new_rfi = RFI(
            tenant_id=tenant_id,
            project_id=project_id,
            created_by_id=user_id,
            subject=data['subject'],
            question=data['question'],
            status='Abierto' # Default status
        )
        db.session.add(new_rfi)
        db.session.commit()
        # Consider returning the created RFI's ID or dict
        return {'message': 'RFI created successfully', 'rfi_id': new_rfi.id}, 201
    except (SQLAlchemyError, KeyError) as e:
        db.session.rollback()
        # Log the error e
        return {'error': f'Failed to create RFI: {str(e)}'}, 500

# --- Milestone Service ---
def create_milestone_service(project_id, data):
    tenant_id, _ = _get_current_user_info()
    if not tenant_id:
         return {'error': 'Tenant information missing in token'}, 400
    try:
        # Verify project exists and belongs to the tenant
        project = ConstructionProject.query.filter_by(id=project_id, tenant_id=tenant_id).first()
        if not project:
            return {'error': 'Project not found'}, 404

        due_date_obj = date.fromisoformat(data['due_date']) if data.get('due_date') else None

        new_milestone = Milestone(
            tenant_id=tenant_id,
            project_id=project_id,
            name=data['name'],
            due_date=due_date_obj,
            amount=float(data['amount']), # Ensure float
            status='Pendiente' # Default status
        )
        db.session.add(new_milestone)
        db.session.commit()
        # Consider returning the created milestone's ID or dict
        return {'message': 'Milestone created successfully', 'milestone_id': new_milestone.id}, 201
    except (SQLAlchemyError, ValueError, KeyError) as e:
        db.session.rollback()
        # Log the error e
        return {'error': f'Failed to create milestone: {str(e)}'}, 500