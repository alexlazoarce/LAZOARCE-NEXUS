from models import db, LoanApplication

# En un sistema real, esto podría interactuar con un servicio de firma electrónica como DocuSign o similar.
# Por ahora, simularemos la lógica.

def request_electronic_signature(application_id):
    """
    Simula el inicio de un proceso de firma electrónica.
    """
    application = LoanApplication.query.get_or_404(application_id)

    # Lógica para enviar el documento a un servicio de firma...
    print(f"Iniciando proceso de firma electrónica para la solicitud {application_id}.")

    application.signature_status = 'EN_PROCESO_ELECTRONICO'
    db.session.commit()

    # Devuelve una URL de firma simulada
    return f"https://simulador-firma.com/sign/{application.id}"

def handle_manual_upload(application_id, file_url):
    """
    Maneja la carga de un documento firmado manualmente.
    """
    application = LoanApplication.query.get_or_404(application_id)

    application.signature_status = 'FIRMADO_MANUAL'
    application.signed_document_url = file_url
    db.session.commit()

    print(f"Documento firmado manualmente cargado para la solicitud {application_id} en {file_url}.")
    return {"message": "Documento cargado, pendiente de validación."}

def validate_manual_signature(application_id):
    """
    Permite a un administrador validar una firma manual.
    """
    application = LoanApplication.query.get_or_404(application_id)

    if application.signature_status != 'FIRMADO_MANUAL':
        raise ValueError("La solicitud no está en estado de firma manual para ser validada.")

    application.signature_status = 'VALIDADO'
    db.session.commit()

    print(f"Firma manual para la solicitud {application_id} ha sido validada.")
    return {"message": "Firma validada exitosamente."}