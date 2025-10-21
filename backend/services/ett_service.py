"""
Servicio para la lógica de negocio del Módulo ETT (Empresa de Trabajo Temporal).
"""
from backend.models import db, Employee, ClientCompany, TemporaryAssignment
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

def create_assignment(data):
    """Crea una nueva asignación temporal."""
    try:
        new_assignment = TemporaryAssignment(
            employee_id=data['employee_id'],
            client_company_id=data['client_company_id'],
            start_date=datetime.strptime(data['start_date'], '%Y-%m-%d').date(),
            end_date=datetime.strptime(data['end_date'], '%Y-%m-%d').date(),
            assignment_salary=data['assignment_salary'],
            is_active=True
        )
        db.session.add(new_assignment)
        db.session.commit()
        return new_assignment, None
    except SQLAlchemyError as e:
        db.session.rollback()
        return None, str(e)
    except KeyError as e:
        return None, f"Falta el campo requerido: {str(e)}"

def get_assignment_by_id(assignment_id):
    """Obtiene una asignación por su ID."""
    return TemporaryAssignment.query.get(assignment_id)

def get_assignments_for_employee(employee_id):
    """Obtiene todas las asignaciones de un empleado."""
    return TemporaryAssignment.query.filter_by(employee_id=employee_id).all()

def get_assignments_for_client_company(client_company_id):
    """Obtiene todas las asignaciones para una empresa cliente."""
    return TemporaryAssignment.query.filter_by(client_company_id=client_company_id).all()

def get_all_assignments():
    """Obtiene todas las asignaciones."""
    return TemporaryAssignment.query.all()

def update_assignment(assignment_id, data):
    """Actualiza una asignación existente."""
    assignment = get_assignment_by_id(assignment_id)
    if not assignment:
        return None, "Asignación no encontrada"

    try:
        if 'start_date' in data:
            assignment.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        if 'end_date' in data:
            assignment.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        if 'assignment_salary' in data:
            assignment.assignment_salary = data['assignment_salary']
        if 'is_active' in data:
            assignment.is_active = data['is_active']

        db.session.commit()
        return assignment, None
    except SQLAlchemyError as e:
        db.session.rollback()
        return None, str(e)

def deactivate_assignment(assignment_id):
    """Desactiva una asignación (soft delete)."""
    assignment = get_assignment_by_id(assignment_id)
    if not assignment:
        return None, "Asignación no encontrada"

    try:
        assignment.is_active = False
        db.session.commit()
        return assignment, None
    except SQLAlchemyError as e:
        db.session.rollback()
        return None, str(e)

# Lógica para ClientCompany
def create_client_company(data):
    """Crea una nueva empresa cliente."""
    try:
        new_company = ClientCompany(
            name=data['name'],
            contact_person=data.get('contact_person'),
            contact_email=data.get('contact_email'),
            contact_phone=data.get('contact_phone')
        )
        db.session.add(new_company)
        db.session.commit()
        return new_company, None
    except SQLAlchemyError as e:
        db.session.rollback()
        return None, str(e)
    except KeyError as e:
        return None, f"Falta el campo requerido: {str(e)}"

def get_client_company_by_id(company_id):
    """Obtiene una empresa cliente por su ID."""
    return ClientCompany.query.get(company_id)

def get_all_client_companies():
    """Obtiene todas las empresas cliente."""
    return ClientCompany.query.all()

def update_client_company(company_id, data):
    """Actualiza una empresa cliente."""
    company = get_client_company_by_id(company_id)
    if not company:
        return None, "Empresa cliente no encontrada"

    try:
        company.name = data.get('name', company.name)
        company.contact_person = data.get('contact_person', company.contact_person)
        company.contact_email = data.get('contact_email', company.contact_email)
        company.contact_phone = data.get('contact_phone', company.contact_phone)
        company.updated_at = datetime.utcnow()

        db.session.commit()
        return company, None
    except SQLAlchemyError as e:
        db.session.rollback()
        return None, str(e)
