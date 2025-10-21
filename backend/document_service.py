"""
Servicio para la Gestión de Documentos (LAN-GD2)
"""
import os
from werkzeug.utils import secure_filename
from flask import current_app
from .models import db, Document, DocumentVersion, User

# --- Funciones del Servicio ---

def get_documents_for_tenant(tenant_id):
    """Obtiene todos los documentos para un tenant específico."""
    return Document.query.filter_by(tenant_id=tenant_id).order_by(Document.updated_at.desc()).all()

def create_document(tenant_id, user_id, file, description):
    """Crea un nuevo documento y su primera versión."""
    if not file or file.filename == '':
        raise ValueError("Se requiere un archivo para crear un documento.")

    filename = secure_filename(file.filename)

    # Crear la entidad del documento lógico
    new_document = Document(
        filename=filename,
        description=description,
        tenant_id=tenant_id,
        created_by_id=user_id
    )
    db.session.add(new_document)
    db.session.flush() # Para obtener el ID del nuevo documento

    # Guardar el archivo y crear la primera versión
    try:
        filepath = _save_file(file, tenant_id, new_document.id)

        new_version = DocumentVersion(
            document_id=new_document.id,
            version_number=1,
            filepath=filepath,
            uploaded_by_id=user_id
        )
        db.session.add(new_version)
        db.session.flush()

        # Actualizar el documento con el ID de la última versión
        new_document.latest_version_id = new_version.id

        db.session.commit()
        return new_document
    except Exception as e:
        db.session.rollback()
        # Aquí se podría añadir lógica para eliminar el archivo si se guardó
        raise e

def add_new_version(document_id, user_id, file):
    """Añade una nueva versión a un documento existente."""
    document = Document.query.get_or_404(document_id)

    if not file or file.filename == '':
        raise ValueError("Se requiere un archivo para añadir una nueva versión.")

    # Determinar el nuevo número de versión
    last_version = DocumentVersion.query.filter_by(document_id=document.id).order_by(DocumentVersion.version_number.desc()).first()
    new_version_number = (last_version.version_number + 1) if last_version else 1

    try:
        filepath = _save_file(file, document.tenant_id, document.id)

        new_version = DocumentVersion(
            document_id=document.id,
            version_number=new_version_number,
            filepath=filepath,
            uploaded_by_id=user_id
        )
        db.session.add(new_version)
        db.session.flush()

        # Actualizar el ID de la última versión en el documento principal
        document.latest_version_id = new_version.id

        db.session.commit()
        return new_version
    except Exception as e:
        db.session.rollback()
        raise e

def get_document_with_versions(document_id):
    """Obtiene un documento y todas sus versiones."""
    return Document.query.get_or_404(document_id)

def get_document_version(version_id):
    """Obtiene una versión específica de un documento."""
    return DocumentVersion.query.get_or_404(version_id)

# --- Funciones de Ayuda ---

def _save_file(file, tenant_id, document_id):
    """Guarda el archivo en una estructura de carpetas organizada."""
    # Define la ruta base de subida
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')

    # Crea una ruta específica para el tenant y el documento para evitar colisiones
    # Ej: uploads/tenant_1/doc_5/
    tenant_doc_path = os.path.join(upload_folder, f"tenant_{tenant_id}", f"doc_{document_id}")
    os.makedirs(tenant_doc_path, exist_ok=True)

    # Guarda el archivo
    filename = secure_filename(file.filename)
    filepath = os.path.join(tenant_doc_path, filename)
    file.save(filepath)

    return filepath
