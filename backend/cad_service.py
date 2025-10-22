"""
backend/cad_service.py

Servicio para el Módulo de Creación de Planos (LAN-CAD).
"""
from .models import db, CADProject, CADFile, CADLayer, CollaborationSession, User
from sqlalchemy.exc import IntegrityError
import secrets

class CADService:

    def create_project(self, tenant_id, user_id, data):
        project = CADProject(
            name=data['name'],
            description=data.get('description'),
            tenant_id=tenant_id,
            created_by_id=user_id
        )
        db.session.add(project)
        db.session.commit()
        return project

    def get_projects(self, tenant_id):
        return CADProject.query.filter_by(tenant_id=tenant_id).all()

    def add_file_to_project(self, tenant_id, project_id, data):
        # En una implementación real, aquí se manejaría la subida del archivo.
        # Por ahora, simulamos la creación del registro.
        cad_file = CADFile(
            project_id=project_id,
            filename=data['filename'],
            file_format=data.get('file_format'),
            storage_path=f"uploads/cad/{secrets.token_hex(8)}/{data['filename']}", # Ruta simulada
            tenant_id=tenant_id
        )
        db.session.add(cad_file)
        db.session.commit()
        return cad_file

    def get_files_for_project(self, tenant_id, project_id):
        return CADFile.query.filter_by(tenant_id=tenant_id, project_id=project_id).all()

    def add_layer_to_file(self, tenant_id, file_id, data):
        layer = CADLayer(
            file_id=file_id,
            name=data['name'],
            color=data.get('color', '#FFFFFF'),
            is_visible=data.get('is_visible', True),
            tenant_id=tenant_id
        )
        db.session.add(layer)
        db.session.commit()
        return layer

    def get_layers_for_file(self, tenant_id, file_id):
        return CADLayer.query.filter_by(tenant_id=tenant_id, file_id=file_id).all()

    def start_collaboration_session(self, tenant_id, file_id, user_ids):
        session = CollaborationSession(
            file_id=file_id,
            session_token=secrets.token_urlsafe(16),
            tenant_id=tenant_id,
        )

        participants = User.query.filter(User.id.in_(user_ids)).all()
        for user in participants:
            session.participants.append(user)

        db.session.add(session)
        db.session.commit()
        return session

    def end_collaboration_session(self, tenant_id, session_id):
        session = CollaborationSession.query.filter_by(id=session_id, tenant_id=tenant_id).first()
        if session:
            session.is_active = False
            session.end_time = db.func.now()
            db.session.commit()
        return session

cad_service = CADService()
