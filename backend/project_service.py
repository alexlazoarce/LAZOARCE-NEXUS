"""
Servicio para el Módulo de Gestión de Proyectos (LAN-PR0)
"""
from .models import db, Project, Task, User
from datetime import date

def get_projects_for_tenant(tenant_id):
    """Obtiene todos los proyectos para un tenant."""
    return Project.query.filter_by(tenant_id=tenant_id).order_by(Project.name).all()

def create_project(name, description, budget, start_date, end_date, manager_id, tenant_id):
    """Crea un nuevo proyecto."""
    if not name:
        raise ValueError("El nombre del proyecto es requerido.")

    project = Project(
        name=name,
        description=description,
        budget=budget,
        start_date=start_date,
        end_date=end_date,
        manager_id=manager_id,
        tenant_id=tenant_id
    )
    db.session.add(project)
    db.session.commit()
    return project

def get_project_details(project_id, tenant_id):
    """Obtiene los detalles de un proyecto, incluyendo sus tareas."""
    return Project.query.filter_by(id=project_id, tenant_id=tenant_id).first_or_404()

def create_task(project_id, title, description, due_date, assigned_to_id, tenant_id):
    """Crea una nueva tarea dentro de un proyecto."""
    if not title:
        raise ValueError("El título de la tarea es requerido.")

    # Asegurarse de que el proyecto existe y pertenece al tenant
    project = get_project_details(project_id, tenant_id)

    task = Task(
        project_id=project.id,
        title=title,
        description=description,
        due_date=due_date,
        assigned_to_id=assigned_to_id,
        tenant_id=tenant_id
    )
    db.session.add(task)
    db.session.commit()
    return task

def update_task_status(task_id, status, tenant_id):
    """Actualiza el estado de una tarea."""
    task = Task.query.filter_by(id=task_id, tenant_id=tenant_id).first_or_404()

    valid_statuses = ['Pendiente', 'En Progreso', 'Completada']
    if status not in valid_statuses:
        raise ValueError(f"Estado no válido. Use uno de: {', '.join(valid_statuses)}")

    task.status = status
    db.session.commit()
    return task

def get_tasks_for_project(project_id, tenant_id):
    """Obtiene todas las tareas de un proyecto."""
    project = get_project_details(project_id, tenant_id)
    return project.tasks.all()
