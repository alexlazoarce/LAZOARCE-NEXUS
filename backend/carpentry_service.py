"""
backend/carpentry_service.py

Servicio para el Módulo de Gestión de Carpintería (LAN-WOD1).
"""
from .models import db, CarpentryProject, CarpentryTask, CarpentryMaterial
from sqlalchemy.exc import IntegrityError

class CarpentryServiceManager:

    def create_project(self, tenant_id, data):
        project = CarpentryProject(
            name=data['name'],
            description=data.get('description'),
            customer_id=data.get('customer_id'),
            budget=data.get('budget'),
            start_date=data.get('start_date'),
            end_date=data.get('end_date'),
            tenant_id=tenant_id
        )
        db.session.add(project)
        db.session.commit()
        return project

    def get_projects(self, tenant_id):
        return CarpentryProject.query.filter_by(tenant_id=tenant_id).all()

    def create_task(self, tenant_id, project_id, data):
        task = CarpentryTask(
            project_id=project_id,
            description=data['description'],
            due_date=data.get('due_date'),
            assigned_to_id=data.get('assigned_to_id'),
            tenant_id=tenant_id
        )
        db.session.add(task)
        db.session.commit()
        return task

    def get_tasks_for_project(self, tenant_id, project_id):
        return CarpentryTask.query.filter_by(tenant_id=tenant_id, project_id=project_id).all()

    def create_material(self, tenant_id, data):
        material = CarpentryMaterial(
            name=data['name'],
            stock_level=data.get('stock_level', 0),
            unit=data.get('unit'),
            cost_per_unit=data.get('cost_per_unit'),
            tenant_id=tenant_id
        )
        db.session.add(material)
        db.session.commit()
        return material

    def get_materials(self, tenant_id):
        return CarpentryMaterial.query.filter_by(tenant_id=tenant_id).all()

carpentry_service = CarpentryServiceManager()
