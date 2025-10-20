# backend/document_service.py
import os
import werkzeug
from backend.models import db, Document, DocumentVersion

# Define the base upload folder. In a real app, this should be configurable and likely
# point to a cloud storage bucket (S3, GCS, etc.).
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_tenant_upload_path(tenant_id):
    """Creates a dedicated upload folder for a tenant if it doesn't exist."""
    path = os.path.join(UPLOAD_FOLDER, str(tenant_id))
    os.makedirs(path, exist_ok=True)
    return path

def list_documents(tenant_id):
    """Lists all documents for a given tenant."""
    return Document.query.filter_by(tenant_id=tenant_id).order_by(Document.filename).all()

def upload_new_document(tenant_id, user_id, file, description):
    """Handles the initial upload of a new document."""
    if not file or file.filename == '':
        raise ValueError("No se seleccionó ningún archivo.")

    filename = werkzeug.utils.secure_filename(file.filename)

    # Check if a document with this name already exists for the tenant
    if Document.query.filter_by(tenant_id=tenant_id, filename=filename).first():
        raise ValueError(f"Ya existe un documento con el nombre '{filename}'. Use la opción de subir nueva versión.")

    tenant_path = get_tenant_upload_path(tenant_id)

    document = Document(
        tenant_id=tenant_id,
        filename=filename,
        description=description
    )
    db.session.add(document)
    db.session.commit() # Commit to get the document ID

    # Now create the first version
    version_number = 1
    version_filename = f"{document.id}_v{version_number}_{filename}"
    filepath = os.path.join(tenant_path, version_filename)
    file.save(filepath)

    new_version = DocumentVersion(
        document_id=document.id,
        version_number=version_number,
        filepath=filepath,
        uploaded_by_id=user_id
    )
    db.session.add(new_version)

    # Set the latest version on the parent document
    document.latest_version_id = new_version.id

    db.session.commit()
    return document

def upload_new_version(tenant_id, user_id, document_id, file):
    """Handles the upload of a new version of an existing document."""
    document = Document.query.filter_by(id=document_id, tenant_id=tenant_id).first_or_404()

    if not file or file.filename == '':
        raise ValueError("No se seleccionó ningún archivo.")

    filename = werkzeug.utils.secure_filename(file.filename)
    if filename != document.filename:
        raise ValueError("El nombre del archivo de la nueva versión debe coincidir con el original.")

    tenant_path = get_tenant_upload_path(tenant_id)

    # Determine the next version number
    last_version = DocumentVersion.query.filter_by(document_id=document.id).order_by(DocumentVersion.version_number.desc()).first()
    new_version_number = (last_version.version_number + 1) if last_version else 1

    version_filename = f"{document.id}_v{new_version_number}_{filename}"
    filepath = os.path.join(tenant_path, version_filename)
    file.save(filepath)

    new_version = DocumentVersion(
        document_id=document.id,
        version_number=new_version_number,
        filepath=filepath,
        uploaded_by_id=user_id
    )
    db.session.add(new_version)

    document.latest_version_id = new_version.id # Update the current version pointer

    db.session.commit()
    return new_version

def get_document_version(tenant_id, version_id):
    """Retrieves a specific document version to be downloaded."""
    version = DocumentVersion.query.get_or_404(version_id)
    document = Document.query.filter_by(id=version.document_id, tenant_id=tenant_id).first_or_404()
    return version
