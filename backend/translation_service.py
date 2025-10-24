"""
backend/translation_service.py

Servicio para el Módulo de Gestión de Traducción (LAN-TRN5).
"""
from .models import db, TranslationProject, TranslationDocument, TranslationTask
from sqlalchemy.exc import IntegrityError

class TranslationServiceManager:

    def create_project(self, tenant_id, data):
        project = TranslationProject(
            name=data['name'],
            customer_id=data.get('customer_id'),
            source_language=data.get('source_language'),
            target_languages=data.get('target_languages'),
            due_date=data.get('due_date'),
            budget=data.get('budget'),
            tenant_id=tenant_id
        )
        db.session.add(project)
        db.session.commit()
        return project

    def get_projects(self, tenant_id):
        return TranslationProject.query.filter_by(tenant_id=tenant_id).all()

    def add_document_to_project(self, tenant_id, project_id, data):
        document = TranslationDocument(
            project_id=project_id,
            file_path=data['file_path'],
            word_count=data.get('word_count'),
            tenant_id=tenant_id
        )
        db.session.add(document)
        db.session.commit()
        return document

    def get_documents_for_project(self, tenant_id, project_id):
        return TranslationDocument.query.filter_by(tenant_id=tenant_id, project_id=project_id).all()

    def create_task(self, tenant_id, project_id, data):
        task = TranslationTask(
            project_id=project_id,
            document_id=data.get('document_id'),
            translator_id=data.get('translator_id'),
            task_type=data.get('task_type'),
            due_date=data.get('due_date'),
            tenant_id=tenant_id
        )
        db.session.add(task)
        db.session.commit()
        return task

    def get_tasks_for_project(self, tenant_id, project_id):
        return TranslationTask.query.filter_by(tenant_id=tenant_id, project_id=project_id).all()

translation_service = TranslationServiceManager()
