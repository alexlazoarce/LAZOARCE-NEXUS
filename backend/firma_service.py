from models import db, LoanApplication

def request_electronic_signature(application_id):
    """Simulates initiating an electronic signature process."""
    application = LoanApplication.query.get_or_404(application_id)
    application.signature_status = 'EN_PROCESO_ELECTRONICO'
    db.session.commit()
    return f"https://simulador-firma.com/sign/{application.id}"

def handle_manual_upload(application_id, file_url):
    """Handles the upload of a manually signed document."""
    application = LoanApplication.query.get_or_404(application_id)
    application.signature_status = 'FIRMADO_MANUAL'
    application.signed_document_url = file_url
    db.session.commit()
    return {"message": "Documento cargado, pendiente de validación."}

def validate_manual_signature(application_id):
    """Allows an admin to validate a manual signature."""
    application = LoanApplication.query.get_or_404(application_id)
    if application.signature_status != 'FIRMADO_MANUAL':
        raise ValueError("La solicitud no está en estado de firma manual para ser validada.")
    application.signature_status = 'VALIDADO'
    db.session.commit()
    return {"message": "Firma validada exitosamente."}