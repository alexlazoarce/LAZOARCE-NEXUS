# backend/barbershop_service.py
from datetime import datetime
from backend.models import db, Stylist, Appointment

def add_stylist(tenant_id, data):
    """Adds a new stylist for a tenant."""
    new_stylist = Stylist(
        tenant_id=tenant_id,
        name=data['name'],
        specialty=data.get('specialty'),
        is_active=data.get('is_active', True)
    )
    db.session.add(new_stylist)
    db.session.commit()
    return new_stylist

def get_stylists(tenant_id):
    """Retrieves all active stylists for a tenant."""
    return Stylist.query.filter_by(tenant_id=tenant_id, is_active=True).all()

def book_appointment(tenant_id, data):
    """Books a new appointment."""
    # Ensure stylist exists and belongs to the tenant
    stylist = Stylist.query.filter_by(id=data['stylist_id'], tenant_id=tenant_id, is_active=True).first_or_404()

    appointment_time = datetime.fromisoformat(data['appointment_time'])

    # Basic validation: Prevent booking in the past
    if appointment_time < datetime.now():
        raise ValueError("No se puede agendar una cita en el pasado.")

    # More complex logic could be added here to check for overlapping appointments for the stylist.

    new_appointment = Appointment(
        tenant_id=tenant_id,
        stylist_id=stylist.id,
        client_name=data['client_name'],
        client_phone=data['client_phone'],
        client_email=data.get('client_email'),
        appointment_time=appointment_time,
        booking_fee=data.get('booking_fee', 0.0)
    )
    db.session.add(new_appointment)
    db.session.commit()
    return new_appointment

def get_appointments_for_day(tenant_id, date):
    """Retrieves all appointments for a specific day."""
    start_of_day = datetime.combine(date, datetime.min.time())
    end_of_day = datetime.combine(date, datetime.max.time())

    return Appointment.query.filter(
        Appointment.tenant_id == tenant_id,
        Appointment.appointment_time >= start_of_day,
        Appointment.appointment_time <= end_of_day
    ).order_by(Appointment.appointment_time).all()

def cancel_appointment(tenant_id, appointment_id):
    """Cancels an appointment."""
    appointment = Appointment.query.filter_by(id=appointment_id, tenant_id=tenant_id).first_or_404()

    if appointment.status in ['completed', 'cancelled']:
        raise ValueError(f"La cita ya está en estado '{appointment.status}'.")

    appointment.status = 'cancelled'

    # Optional: Add logic here for refunds if a booking_fee was paid.

    db.session.commit()
    return appointment
