"""
Servicio para el Módulo de Formularios (LAN-FRM5)
"""
import uuid
from .models import db, Form, FormSubmission

def get_forms_for_tenant(tenant_id):
    """Obtiene todos los formularios para un tenant."""
    return Form.query.filter_by(tenant_id=tenant_id).order_by(Form.name).all()

def create_form(name, description, fields, tenant_id, user_id):
    """Crea un nuevo formulario."""
    if not name or not fields:
        raise ValueError("El nombre y la definición de campos son requeridos.")

    # Aquí se podría añadir una validación más robusta de la estructura de 'fields'

    form = Form(
        name=name,
        description=description,
        fields=fields,
        public_token=str(uuid.uuid4()),
        tenant_id=tenant_id,
        created_by_id=user_id
    )
    db.session.add(form)
    db.session.commit()
    return form

def get_form_by_token(token):
    """Obtiene la definición de un formulario por su token público."""
    return Form.query.filter_by(public_token=token).first_or_404()

def submit_form(form_token, submission_data):
    """Guarda los datos de un envío de formulario."""
    form = get_form_by_token(form_token)

    # Validación simple: verificar que todos los campos requeridos están presentes
    required_fields = {field['name'] for field in form.fields if field.get('required', False)}
    submitted_fields = set(submission_data.keys())

    if not required_fields.issubset(submitted_fields):
        missing = required_fields - submitted_fields
        raise ValueError(f"Faltan campos requeridos: {', '.join(missing)}")

    submission = FormSubmission(
        form_id=form.id,
        data=submission_data,
        tenant_id=form.tenant_id
    )
    db.session.add(submission)
    db.session.commit()

    # Aquí se podría disparar una notificación (ej. al CRM)

    return submission

def get_submissions_for_form(form_id, tenant_id):
    """Obtiene todos los envíos para un formulario específico."""
    # Asegurarse de que el formulario pertenece al tenant
    form = Form.query.filter_by(id=form_id, tenant_id=tenant_id).first_or_404()
    return FormSubmission.query.filter_by(form_id=form.id).order_by(FormSubmission.submitted_at.desc()).all()
