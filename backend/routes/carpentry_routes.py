"""
backend/routes/carpentry_routes.py

Rutas para el Módulo de Gestión de Carpintería (LAN-WOD1).
"""
from flask import Blueprint, request, jsonify
from ..services.jwt_service import get_current_tenant_id
from ..carpentry_service import carpentry_service

carpentry_bp = Blueprint('carpentry_bp', __name__)

# --- Rutas de Proyectos de Carpintería ---
@carpentry_bp.route('/projects', methods=['GET', 'POST'])
def handle_projects():
    tenant_id = get_current_tenant_id()
    if request.method == 'POST':
        data = request.json
        project = carpentry_service.create_project(tenant_id, data)
        return jsonify({'id': project.id, 'name': project.name}), 201

    projects = carpentry_service.get_projects(tenant_id)
    return jsonify([{'id': p.id, 'name': p.name, 'status': p.status} for p in projects])

# --- Rutas de Tareas de Carpintería ---
@carpentry_bp.route('/projects/<int:project_id>/tasks', methods=['GET', 'POST'])
def handle_tasks(project_id):
    tenant_id = get_current_tenant_id()
    if request.method == 'POST':
        data = request.json
        task = carpentry_service.create_task(tenant_id, project_id, data)
        return jsonify({'id': task.id, 'description': task.description}), 201

    tasks = carpentry_service.get_tasks_for_project(tenant_id, project_id)
    return jsonify([{'id': t.id, 'description': t.description, 'status': t.status} for t in tasks])

# --- Rutas de Materiales de Carpintería ---
@carpentry_bp.route('/materials', methods=['GET', 'POST'])
def handle_materials():
    tenant_id = get_current_tenant_id()
    if request.method == 'POST':
        data = request.json
        material = carpentry_service.create_material(tenant_id, data)
        return jsonify({'id': material.id, 'name': material.name}), 201

    materials = carpentry_service.get_materials(tenant_id)
    return jsonify([{'id': m.id, 'name': m.name, 'stock': m.stock_level} for m in materials])
