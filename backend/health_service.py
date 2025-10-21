from .models import db, PatientRecord, MedicalAppointment, Prescription, LabOrder, User
from sqlalchemy.exc import SQLAlchemyError
from flask_jwt_extended import get_jwt_identity
from datetime import datetime

def _get_current_user_info():
    """Extrae el tenant_id y user_id de la identidad del JWT."""
    identity = get_jwt_identity()
    return identity.get('tenant_id'), identity.get('user_id')

# --- Patient Record Service ---

def create_patient_record_service(data):
    tenant_id, _ = _get_current_user_info()
    try:
        new_patient = PatientRecord(
            tenant_id=tenant_id,
            full_name=data['full_name'],
            birth_date=datetime.fromisoformat(data['birth_date']).date() if data.get('birth_date') else None,
            medical_history_summary=data.get('medical_history_summary'),
            user_id=data.get('user_id'),
            contact_id=data.get('contact_id')
        )
        db.session.add(new_patient)
        db.session.commit()
        return {'message': 'Patient record created successfully', 'patient': new_patient.to_dict()}, 201
    except (SQLAlchemyError, ValueError) as e:
        db.session.rollback()
        return {'error': str(e)}, 500

def get_patient_records_service():
    tenant_id, _ = _get_current_user_info()
    try:
        patients = PatientRecord.query.filter_by(tenant_id=tenant_id).all()
        return [p.to_dict() for p in patients], 200
    except SQLAlchemyError as e:
        return {'error': str(e)}, 500

# --- Medical Appointment Service ---

def create_appointment_service(data):
    tenant_id, _ = _get_current_user_info()
    try:
        # Validar que el paciente y el doctor existen y pertenecen al tenant
        patient = PatientRecord.query.filter_by(id=data['patient_id'], tenant_id=tenant_id).first()
        doctor = User.query.filter_by(id=data['doctor_id'], tenant_id=tenant_id).first()
        if not patient or not doctor:
            return {'error': 'Patient or Doctor not found'}, 404

        new_appointment = MedicalAppointment(
            tenant_id=tenant_id,
            patient_id=data['patient_id'],
            doctor_id=data['doctor_id'],
            appointment_time=datetime.fromisoformat(data['appointment_time']),
            reason=data.get('reason')
        )
        db.session.add(new_appointment)
        db.session.commit()
        return {'message': 'Appointment created successfully', 'appointment': new_appointment.to_dict()}, 201
    except (SQLAlchemyError, ValueError) as e:
        db.session.rollback()
        return {'error': str(e)}, 500

def get_appointments_service(filters=None):
    tenant_id, _ = _get_current_user_info()
    try:
        query = MedicalAppointment.query.filter_by(tenant_id=tenant_id)
        if filters:
            if filters.get('doctor_id'):
                query = query.filter_by(doctor_id=filters['doctor_id'])
            if filters.get('patient_id'):
                query = query.filter_by(patient_id=filters['patient_id'])
            if filters.get('date'):
                # Filtrar por día, ignorando la hora
                filter_date = datetime.fromisoformat(filters['date']).date()
                query = query.filter(db.func.date(MedicalAppointment.appointment_time) == filter_date)

        appointments = query.order_by(MedicalAppointment.appointment_time.asc()).all()
        return [a.to_dict() for a in appointments], 200
    except (SQLAlchemyError, ValueError) as e:
        return {'error': str(e)}, 500

# --- Prescription and Lab Order Services ---

def create_prescription_service(appointment_id, data):
    tenant_id, _ = _get_current_user_info()
    try:
        appointment = MedicalAppointment.query.filter_by(id=appointment_id, tenant_id=tenant_id).first()
        if not appointment:
            return {'error': 'Appointment not found'}, 404

        new_prescription = Prescription(
            tenant_id=tenant_id,
            appointment_id=appointment_id,
            medication_details=data['medication_details']
        )
        db.session.add(new_prescription)
        db.session.commit()
        return {'message': 'Prescription created successfully'}, 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return {'error': str(e)}, 500

def create_lab_order_service(appointment_id, data):
    tenant_id, _ = _get_current_user_info()
    try:
        appointment = MedicalAppointment.query.filter_by(id=appointment_id, tenant_id=tenant_id).first()
        if not appointment:
            return {'error': 'Appointment not found'}, 404

        new_lab_order = LabOrder(
            tenant_id=tenant_id,
            appointment_id=appointment_id,
            test_details=data['test_details']
        )
        db.session.add(new_lab_order)
        db.session.commit()
        return {'message': 'Lab order created successfully'}, 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return {'error': str(e)}, 500
