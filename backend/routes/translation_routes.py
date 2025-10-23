"""
backend/routes/translation_routes.py

Rutas para el Módulo de Gestión de Traducción (LAN-TRN5).
"""
from flask import Blueprint, request, jsonify
from ..services.jwt_service import get_current_tenant_id
from ..translation_service import translation_service

translation_bp = Blueprint('translation_bp', __name__)

# --- Rutas de Proyectos de Traducción ---
@translation_bp.route('/projects', methods=['GET', 'POST'])
def handle_projects():
    tenant_id = get_current_tenant_id()
    if request.method == 'POST':
        data = request.json
        project = translation_service.create_project(tenant_id, data)
        return jsonify({'id': project.id, 'name': project.name}), 201

    projects = translation_service.get_projects(tenant_id)
    return jsonify([{'id': p.id, 'name': p.name, 'status': p.status} for p in projects])

# --- Rutas de Documentos de Traducción ---
@translation_bp.route('/projects/<int:project_id>/documents', methods=['GET', 'POST'])
def handle_documents(project_id):
    tenant_id = get_current_tenant_id()
    if request.method == 'POST':
        data = request.json
        document = translation_service.add_document_to_project(tenant_id, project_id, data)
        return jsonify({'id': document.id, 'file_path': document.file_path}), 201

    documents = translation_service.get_documents_for_project(tenant_id, project_id)
    return jsonify([{'id': d.id, 'file_path': d.file_path} for d in documents])

# --- Rutas de Tareas de Traducción ---
@translation_bp.route('/projects/<int:project_id>/tasks', methods=['GET', 'POST'])
def handle_tasks(project_id):
    tenant_id = get_current_tenant_id()
    if request.method == 'POST':
        data = request.json
        task = translation_service.create_task(tenant_id, project_id, data)
        return jsonify({'id': task.id, 'task_type': task.task_type}), 201

    tasks = translation_service.get_tasks_for_project(tenant_id, project_id)
    return jsonify([{'id': t.id, 'task_type': t.task_type, 'status': t.status} for t in tasks])
