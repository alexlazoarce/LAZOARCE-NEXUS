import uuid
from datetime import datetime
from .models import db, Employee, AttendanceRecord

def generate_qr_code_token_for_employee(employee_id):
    """
    Generates a unique QR code token for an employee and saves it.
    If a token already exists, it returns the existing one.
    """
    employee = Employee.query.get_or_404(employee_id)
    if not employee.qr_code_token:
        employee.qr_code_token = str(uuid.uuid4())
        db.session.commit()
    return employee.qr_code_token

def record_attendance(qr_code_token, event_type):
    """
    Records a new attendance event (Entrada or Salida) for the employee
    associated with the given QR code token.
    """
    employee = Employee.query.filter_by(qr_code_token=qr_code_token).first_or_404()

    # Simple validation: prevent two consecutive 'Entrada' or 'Salida'
    last_record = AttendanceRecord.query.filter_by(employee_id=employee.id).order_by(AttendanceRecord.timestamp.desc()).first()
    if last_record and last_record.event_type == event_type:
        raise ValueError(f"El último registro ya es una '{event_type}'. No se puede duplicar el evento.")

    new_record = AttendanceRecord(
        tenant_id=employee.tenant_id,
        employee_id=employee.id,
        event_type=event_type,
        timestamp=datetime.utcnow()
    )
    db.session.add(new_record)
    return new_record

def get_attendance_history(employee_id):
    """
    Retrieves the attendance history for a given employee.
    """
    return AttendanceRecord.query.filter_by(employee_id=employee_id).order_by(AttendanceRecord.timestamp.desc()).all()
