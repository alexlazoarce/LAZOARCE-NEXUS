from .models import db, CADProject, CADFile, CADLayer, CollaborationSession, User
from sqlalchemy.exc import SQLAlchemyError
import secrets

def get_all_projects(tenant_id):
    """Obtiene todos los proyectos CAD para un tenant."""
    return CADProject.query.filter_by(tenant_id=tenant_id).all()

def create_project(tenant_id, user_id, name, description):
    """Crea un nuevo proyecto CAD."""
    try:
        project = CADProject(
            name=name,
            description=description,
            tenant_id=tenant_id,
            created_by_id=user_id
        )
        db.session.add(project)
        db.session.commit()
        return project, None
    except SQLAlchemyError as e:
        db.session.rollback()
        return None, str(e)

def add_file_to_project(project_id, filename, file_format, tenant_id):
    """Añade un nuevo archivo a un proyecto CAD."""
    project = CADProject.query.get(project_id)
    if not project or project.tenant_id != tenant_id:
        return None, "Proyecto no encontrado."

    try:
        # Simula el guardado del archivo y obtiene una ruta
        storage_path = f"uploads/{tenant_id}/cad/{project_id}/{filename}"

        cad_file = CADFile(
            project_id=project_id,
            filename=filename,
            file_format=file_format,
            storage_path=storage_path,
            tenant_id=tenant_id
        )
        db.session.add(cad_file)
        db.session.commit()
        return cad_file, None
    except SQLAlchemyError as e:
        db.session.rollback()
        return None, str(e)

def add_layer_to_file(file_id, name, color, tenant_id):
    """Añade una capa a un archivo CAD."""
    cad_file = CADFile.query.get(file_id)
    if not cad_file or cad_file.tenant_id != tenant_id:
        return None, "Archivo no encontrado."

    try:
        layer = CADLayer(
            file_id=file_id,
            name=name,
            color=color,
            is_visible=True,
            tenant_id=tenant_id
        )
        db.session.add(layer)
        db.session.commit()
        return layer, None
    except SQLAlchemyError as e:
        db.session.rollback()
        return None, str(e)

def start_collaboration_session(file_id, tenant_id):
    """Inicia una nueva sesión de colaboración para un archivo."""
    cad_file = CADFile.query.get(file_id)
    if not cad_file or cad_file.tenant_id != tenant_id:
        return None, "Archivo no encontrado."

    try:
        token = secrets.token_hex(16)
        session = CollaborationSession(
            file_id=file_id,
            session_token=token,
            tenant_id=tenant_id
        )
        db.session.add(session)
        db.session.commit()
        return session, None
    except SQLAlchemyError as e:
        db.session.rollback()
        return None, str(e)

def add_participant_to_session(session_id, user_id, tenant_id):
    """Añade un participante a una sesión de colaboración."""
    session = CollaborationSession.query.get(session_id)
    if not session or session.tenant_id != tenant_id:
        return None, "Sesión no encontrada."

    user = User.query.get(user_id)
    if not user or user.tenant_id != tenant_id:
        return None, "Usuario no encontrado."

    try:
        session.participants.append(user)
        db.session.commit()
        return session, None
    except SQLAlchemyError as e:
        db.session.rollback()
        return None, str(e)
