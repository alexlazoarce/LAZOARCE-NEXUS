"""
NEXUS-ET2: Empresa de Trabajo Temporal Service
"""
from .models import db, Employee, ClientCompany, TemporaryAssignment
from . import payroll_service
from datetime import date

def create_client_company(data):
    """Creates a new client company."""
    if ClientCompany.query.filter_by(name=data['name']).first():
        raise ValueError("Una empresa cliente con ese nombre ya existe.")

    new_company = ClientCompany(
        name=data['name'],
        contact_person=data.get('contact_person'),
        contact_email=data.get('contact_email'),
        phone_number=data.get('phone_number')
    )
    db.session.add(new_company)
    return new_company

def create_temporary_worker(data):
    """Creates a new employee with type 'temporal'."""
    if Employee.query.filter_by(dui=data['dui']).first():
        raise ValueError("Un empleado con ese DUI ya existe.")

    new_worker = Employee(
        full_name=data['full_name'],
        employee_type='temporal',
        dui=data.get('dui'),
        nit=data.get('nit'),
        isss_number=data.get('isss_number'),
        afp_number=data.get('afp_number'),
        country_code=data.get('country_code', 'SV'), # Default to SV if not provided
        is_active=True
    )
    db.session.add(new_worker)
    return new_worker

def create_assignment(data):
    """Assigns a temporary worker to a client company."""
    worker = Employee.query.get_or_404(data['employee_id'])
    if worker.employee_type != 'temporal':
        raise ValueError("Solo los empleados de tipo 'temporal' pueden ser asignados.")

    company = ClientCompany.query.get_or_404(data['client_company_id'])

    new_assignment = TemporaryAssignment(
        employee_id=worker.id,
        client_company_id=company.id,
        project_name=data.get('project_name'),
        position_in_client=data['position_in_client'],
        start_date=date.fromisoformat(data['start_date']),
        end_date=date.fromisoformat(data['end_date']) if data.get('end_date') else None,
        assignment_salary=float(data['assignment_salary'])
    )
    db.session.add(new_assignment)
    return new_assignment

def calculate_payroll_for_assignment(assignment_id):
    """
    Calculates a payslip for a single temporary assignment.
    """
    assignment = TemporaryAssignment.query.get_or_404(assignment_id)
    if not assignment.is_active:
        raise ValueError("No se puede calcular la nómina para una asignación inactiva.")

    # Reuse the regional payroll service, passing the worker's country code
    payslip_details = payroll_service.calculate_payslip_details(
        assignment.assignment_salary,
        assignment.employee.country_code
    )

    return {
        "assignment_id": assignment.id,
        "employee_name": assignment.employee.full_name,
        "client_company": assignment.client_company.name,
        "period": f"{date.today():%Y-%m}",
        "payslip": payslip_details
    }
