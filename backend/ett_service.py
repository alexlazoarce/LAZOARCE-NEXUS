from models import db, ClientCompany, TemporaryAssignment
from datetime import datetime

def add_client_company(name, contact_person, contact_email):
    """Adds a new client company."""
    if not name or not contact_email:
        raise ValueError("Name and contact email are required.")

    new_company = ClientCompany(
        name=name,
        contact_person=contact_person,
        contact_email=contact_email
    )
    db.session.add(new_company)
    db.session.commit()
    return new_company

def get_all_client_companies():
    """Returns all client companies."""
    return ClientCompany.query.all()

def add_temporary_assignment(employee_id, client_company_id, start_date_str, end_date_str, hourly_rate):
    """Adds a new temporary assignment."""
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        raise ValueError("Invalid date format. Please use YYYY-MM-DD.")

    if not all([employee_id, client_company_id, start_date, end_date, hourly_rate]):
         raise ValueError("Missing required fields for temporary assignment.")

    new_assignment = TemporaryAssignment(
        employee_id=employee_id,
        client_company_id=client_company_id,
        start_date=start_date,
        end_date=end_date,
        hourly_rate=hourly_rate
    )
    db.session.add(new_assignment)
    db.session.commit()
    return new_assignment

def get_assignments_for_employee(employee_id):
    """Gets all temporary assignments for a specific employee."""
    return TemporaryAssignment.query.filter_by(employee_id=employee_id).all()

def get_active_assignments():
    """Gets all active temporary assignments."""
    today = datetime.utcnow().date()
    return TemporaryAssignment.query.filter(
        TemporaryAssignment.start_date <= today,
        TemporaryAssignment.end_date >= today
    ).all()
