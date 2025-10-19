from datetime import date, timedelta
from .models import db, AbsenceRequest, Employee

# --- Constantes para el cálculo de vacaciones (Ejemplo para El Salvador) ---
# 15 días de vacaciones pagadas después de 1 año de trabajo.
# Proporcional para períodos menores.
VACATION_DAYS_PER_YEAR = 15

def get_vacation_balance(employee_id):
    """
    Calcula el saldo de días de vacaciones para un empleado.
    """
    employee = Employee.query.get_or_404(employee_id)

    # Calcular años de servicio
    years_of_service = (date.today() - employee.hire_date).days / 365.25

    # Calcular días de vacaciones ganados
    earned_vacation_days = int(years_of_service * VACATION_DAYS_PER_YEAR)

    # Calcular días de vacaciones ya tomados
    taken_vacation_days = db.session.query(db.func.sum(AbsenceRequest.end_date - AbsenceRequest.start_date + timedelta(days=1))).\
        filter(
            AbsenceRequest.employee_id == employee_id,
            AbsenceRequest.absence_type == 'Vacaciones',
            AbsenceRequest.status == 'Aprobada'
        ).scalar() or 0

    return earned_vacation_days - taken_vacation_days

def create_absence_request(employee_id, tenant_id, absence_type, start_date, end_date, comments):
    """
    Crea una nueva solicitud de ausencia.
    """
    if start_date > end_date:
        raise ValueError("La fecha de inicio no puede ser posterior a la fecha de fin.")

    # Check if the employee has enough vacation days
    if absence_type == 'Vacaciones':
        requested_days = (end_date - start_date).days + 1
        available_days = get_vacation_balance(employee_id)
        if requested_days > available_days:
            raise ValueError(f"No tienes suficientes días de vacaciones disponibles. Solicitados: {requested_days}, Disponibles: {available_days}")

    new_request = AbsenceRequest(
        tenant_id=tenant_id,
        employee_id=employee_id,
        absence_type=absence_type,
        start_date=start_date,
        end_date=end_date,
        comments=comments,
        status='Pendiente'
    )
    db.session.add(new_request)
    return new_request

def approve_absence_request(request_id, approver_id):
    """
    Aprueba una solicitud de ausencia.
    """
    absence_request = AbsenceRequest.query.get_or_404(request_id)
    if absence_request.status != 'Pendiente':
        raise ValueError("La solicitud ya ha sido procesada.")

    absence_request.status = 'Aprobada'
    absence_request.approved_by_id = approver_id
    return absence_request

def reject_absence_request(request_id, approver_id, comments):
    """
    Rechaza una solicitud de ausencia.
    """
    absence_request = AbsenceRequest.query.get_or_404(request_id)
    if absence_request.status != 'Pendiente':
        raise ValueError("La solicitud ya ha sido procesada.")

    absence_request.status = 'Rechazada'
    absence_request.approved_by_id = approver_id
    absence_request.comments = f"Rechazada: {comments}"
    return absence_request

def get_absence_requests_for_employee(employee_id):
    """
    Retrieves all absence requests for a given employee.
    """
    return AbsenceRequest.query.filter_by(employee_id=employee_id).order_by(AbsenceRequest.start_date.desc()).all()
