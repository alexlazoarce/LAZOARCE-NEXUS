"""
Servicio para el Módulo Firmar (LAN-SGN3)
"""
import uuid
from datetime import datetime
from .models import db, SignableTemplate, SignatureRequest
from . import email_service # Asumimos que podemos notificar por email

def get_templates_for_tenant(tenant_id):
    """Obtiene todas las plantillas de documentos para un tenant."""
    return SignableTemplate.query.filter_by(tenant_id=tenant_id).order_by(SignableTemplate.name).all()

def create_template(name, description, content, tenant_id, user_id):
    """Crea una nueva plantilla de documento."""
    if not name or not content:
        raise ValueError("El nombre y el contenido de la plantilla son requeridos.")

    template = SignableTemplate(
        name=name,
        description=description,
        content=content,
        tenant_id=tenant_id,
        created_by_id=user_id
    )
    db.session.add(template)
    db.session.commit()
    return template

def get_signature_requests(tenant_id):
    """Obtiene todas las solicitudes de firma para un tenant."""
    return SignatureRequest.query.filter_by(tenant_id=tenant_id).order_by(SignatureRequest.created_at.desc()).all()

def create_signature_request(template_id, signer_name, signer_email, data_payload, tenant_id, user_id):
    """Crea una nueva solicitud de firma a partir de una plantilla y datos."""
    template = SignableTemplate.query.get_or_404(template_id)

    # Rellenar la plantilla con los datos del payload
    final_content = template.content
    for key, value in data_payload.items():
        final_content = final_content.replace(f"{{{{{key}}}}}", str(value))

    request = SignatureRequest(
        template_id=template.id,
        signer_name=signer_name,
        signer_email=signer_email,
        final_document_content=final_content,
        unique_token=str(uuid.uuid4()),
        tenant_id=tenant_id,
        created_by_id=user_id
    )
    db.session.add(request)
    db.session.commit()
    return request

def send_signature_request(request_id):
    """Marca una solicitud como enviada y notifica al firmante."""
    req = SignatureRequest.query.get_or_404(request_id)
    if req.status != 'draft':
        raise ValueError("La solicitud solo puede ser enviada si está en estado borrador.")

    req.status = 'sent'
    req.sent_at = datetime.utcnow()

    # Simular envío de correo
    # En una implementación real, aquí se usaría un servicio de correo con plantillas HTML
    subject = f"Solicitud de Firma: {req.template.name}"
    # La URL debería apuntar a una página pública del frontend
    signing_url = f"https://sistema.tuempresa.com/sign/{req.unique_token}"
    body = f"Hola {req.signer_name},\n\nHas recibido una solicitud para firmar un documento. Por favor, haz clic en el siguiente enlace:\n{signing_url}"

    # Usamos el email_service existente (simulado)
    # email_service.send_email(req.signer_email, subject, body, tenant_id=req.tenant_id)
    print(f"EMAIL ENVIADO a {req.signer_email} con URL: {signing_url}")

    db.session.commit()
    return req

def get_request_by_token(token):
    """Obtiene una solicitud de firma por su token único (para la página pública)."""
    return SignatureRequest.query.filter_by(unique_token=token).first_or_404()

def sign_document(token, signature_data):
    """Registra la firma en una solicitud."""
    req = get_request_by_token(token)
    if req.status not in ['sent', 'viewed']:
        raise ValueError("El documento no puede ser firmado en su estado actual.")

    req.status = 'signed'
    req.signed_at = datetime.utcnow()
    req.signature_data = signature_data

    db.session.commit()

    # Aquí se podría notificar al creador de la solicitud

    return req
