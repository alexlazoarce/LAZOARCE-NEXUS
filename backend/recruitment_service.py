from backend.models import db, JobVacancy, Candidate, Application
from flask_jwt_extended import get_jwt_identity

def get_current_tenant_id():
    # This is a placeholder. In a real multi-tenant app, you'd get this from the user's session or JWT.
    # For now, we'll assume a default tenant or derive it from the user.
    # Let's assume the JWT identity contains info that can lead to the tenant.
    # For simplicity, returning a default value.
    user_email = get_jwt_identity()
    # This logic assumes a User model exists with email and tenant_id fields.
    # from backend.models import User
    # user = User.query.filter_by(email=user_email).first()
    # return user.tenant_id if user else 1
    return 1 # Fallback for now

def create_job_vacancy(data):
    """Creates a new job vacancy."""
    tenant_id = get_current_tenant_id()
    user_id = data.get('created_by_id') # Assuming this is passed in securely

    new_vacancy = JobVacancy(
        tenant_id=tenant_id,
        title=data['title'],
        description=data['description'],
        created_by_id=user_id
    )
    db.session.add(new_vacancy)
    db.session.commit()
    return new_vacancy

def get_all_vacancies():
    """Retrieves all job vacancies for the current tenant."""
    tenant_id = get_current_tenant_id()
    return JobVacancy.query.filter_by(tenant_id=tenant_id).all()

def create_candidate_and_apply(vacancy_id, candidate_data):
    """Creates a new candidate and an application for a specific job vacancy."""
    tenant_id = get_current_tenant_id()

    # Check if candidate already exists
    candidate = Candidate.query.filter_by(email=candidate_data['email'], tenant_id=tenant_id).first()

    if not candidate:
        candidate = Candidate(
            tenant_id=tenant_id,
            full_name=candidate_data['full_name'],
            email=candidate_data['email'],
            phone=candidate_data.get('phone'),
            resume_url=candidate_data.get('resume_url')
        )
        db.session.add(candidate)
        # We need to commit here to get the candidate ID for the application
        db.session.commit()

    # Create the application
    application = Application(
        tenant_id=tenant_id,
        candidate_id=candidate.id,
        job_vacancy_id=vacancy_id
    )
    db.session.add(application)
    db.session.commit()
    return application

def get_applications_for_vacancy(vacancy_id):
    """Gets all applications for a specific job vacancy."""
    tenant_id = get_current_tenant_id()
    # Ensure the vacancy belongs to the tenant before showing applications
    vacancy = JobVacancy.query.filter_by(id=vacancy_id, tenant_id=tenant_id).first_or_404()
    return Application.query.filter_by(job_vacancy_id=vacancy.id).all()

def update_application_status(application_id, status):
    """Updates the status of an application."""
    tenant_id = get_current_tenant_id()
    application = Application.query.filter_by(id=application_id, tenant_id=tenant_id).first_or_404()

    valid_statuses = ['Nuevo', 'Revisión', 'Entrevista', 'Oferta', 'Contratado', 'Rechazado']
    if status not in valid_statuses:
        raise ValueError(f"Invalid status. Must be one of {valid_statuses}")

    application.status = status
    db.session.commit()
    return application
