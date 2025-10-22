"""
backend/cad_service.py
Servicio para el Módulo de Creación de Planos (LAN-CAD).
"""
from .models import db, CADProject, CADFile, CADLayer, CollaborationSession, User
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import secrets

class CADService:
    def get_projects(self, tenant_id):
        """Obtiene todos los proyectos CAD para un tenant."""
        return CADProject.query.filter_by(tenant_id=tenant_id).all()

    def create_project(self, tenant_id, user_id, data):
        """Crea un nuevo proyecto CAD."""
        try:
            project = CADProject(
                name=data['name'],
                description=data.get('description'),
                tenant_id=tenant_id,
                created_by_id=user_id
            )
            db.session.add(project)
            db.session.commit()
            return project, None
        except (SQLAlchemyError, IntegrityError) as e:
            db.session.rollback()
            return None, str(e)

    def add_file_to_project(self, tenant_id, project_id, data):
        """Añade un nuevo archivo a un proyecto CAD."""
        project = CADProject.query.filter_by(id=project_id, tenant_id=tenant_id).first()
        if not project:
            return None, "Proyecto no encontrado."
        try:
            # Simula el guardado del archivo y obtiene una ruta
            storage_path = f"uploads/{tenant_id}/cad/{project_id}/{data['filename']}"
            cad_file = CADFile(
                project_id=project_id,
                filename=data['filename'],
                file_format=data.get('file_format'),
                storage_path=storage_path,
                tenant_id=tenant_id
            )
            db.session.add(cad_file)
            db.session.commit()
            return cad_file, None
        except (SQLAlchemyError, IntegrityError) as e:
            db.session.rollback()
            return None, str(e)

    def get_files_for_project(self, tenant_id, project_id):
        return CADFile.query.filter_by(tenant_id=tenant_id, project_id=project_id).all()

    def add_layer_to_file(self, tenant_id, file_id, data):
        """Añade una capa a un archivo CAD."""
        cad_file = CADFile.query.filter_by(id=file_id, tenant_id=tenant_id).first()
        if not cad_file:
            return None, "Archivo no encontrado."
        try:
            layer = CADLayer(
                file_id=file_id,
                name=data['name'],
                color=data.get('color', '#FFFFFF'),
                is_visible=data.get('is_visible', True),
                tenant_id=tenant_id
            )
            db.session.add(layer)
            db.session.commit()
            return layer, None
        except (SQLAlchemyError, IntegrityError) as e:
            db.session.rollback()
            return None, str(e)

    def get_layers_for_file(self, tenant_id, file_id):
        return CADLayer.query.filter_by(tenant_id=tenant_id, file_id=file_id).all()

    def start_collaboration_session(self, tenant_id, file_id, user_ids=None):
        """Inicia una nueva sesión de colaboración para un archivo."""
        cad_file = CADFile.query.filter_by(id=file_id, tenant_id=tenant_id).first()
        if not cad_file:
            return None, "Archivo no encontrado."
        try:
            token = secrets.token_urlsafe(16)
            session = CollaborationSession(
                file_id=file_id,
                session_token=token,
                tenant_id=tenant_id
            )
            if user_ids:
                participants = User.query.filter(User.id.in_(user_ids)).filter_by(tenant_id=tenant_id).all()
                for user in participants:
                    session.participants.append(user)
            db.session.add(session)
            db.session.commit()
            return session, None
        except (SQLAlchemyError, IntegrityError) as e:
            db.session.rollback()
            return None, str(e)

    def add_participant_to_session(self, session_id, user_id, tenant_id):
        """Añade un participante a una sesión de colaboración."""
        session = CollaborationSession.query.filter_by(id=session_id, tenant_id=tenant_id).first()
        if not session:
            return None, "Sesión no encontrada."
        user = User.query.filter_by(id=user_id, tenant_id=tenant_id).first()
        if not user:
            return None, "Usuario no encontrado."
        try:
            session.participants.append(user)
            db.session.commit()
            return session, None
        except (SQLAlchemyError, IntegrityError) as e:
            db.session.rollback()
            return None, str(e)

    def end_collaboration_session(self, tenant_id, session_id):
        session = CollaborationSession.query.filter_by(id=session_id, tenant_id=tenant_id).first()
        if session:
            session.is_active = False
            session.end_time = db.func.now()
            db.session.commit()
        return session

cad_service = CADService()