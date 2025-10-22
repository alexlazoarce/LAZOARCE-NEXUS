from .models import db, ConstructionProject, BudgetItem, ProgressReport, Certification, RFI, Milestone
from sqlalchemy.exc import SQLAlchemyError
from flask_jwt_extended import get_jwt_identity, get_jwt # Importamos get_jwt
from datetime import date

def _get_current_user_info():
    """Extrae tenant_id y user_id de las claims del JWT."""
    # Usamos get_jwt() para acceder a todas las claims
    claims = get_jwt()
    tenant_id = claims.get('tenant_id')
    user_id = claims.get('user_id') # Asumimos que user_id está en las claims
    # Si user_id no estuviera, podríamos buscarlo usando get_jwt_identity() (ej. email)
    # user_identity = get_jwt_identity()
    return tenant_id, user_id

# --- Servicio de Proyectos de Construcción ---
def create_construction_project_service(data):
    """Crea un nuevo proyecto de construcción."""
    tenant_id, user_id = _get_current_user_info()
    if not tenant_id:
        return {'error': 'Información del tenant ausente en el token'}, 400
    try:
        # Validar y convertir fechas
        start_date_obj = date.fromisoformat(data['start_date']) if data.get('start_date') else None
        end_date_obj = date.fromisoformat(data['end_date']) if data.get('end_date') else None

        new_project = ConstructionProject(
            tenant_id=tenant_id,
            manager_id=user_id, # Asignamos al creador como manager por defecto
            name=data['name'],
            location=data.get('location'),
            start_date=start_date_obj,
            end_date=end_date_obj,
            budget=float(data.get('budget', 0.0)) # Aseguramos que sea float
        )
        db.session.add(new_project)
        db.session.commit()
        # Asumimos que el modelo tiene un método .to_dict()
        return {'message': 'Proyecto de construcción creado exitosamente', 'project': new_project.to_dict()}, 201
    except (SQLAlchemyError, ValueError, KeyError, TypeError) as e: # Capturamos más errores potenciales
        db.session.rollback()
        # Considera loggear el error 'e' para depuración
        print(f"Error creando proyecto: {e}") # Log simple
        return {'error': f'No se pudo crear el proyecto: {str(e)}'}, 500

def get_construction_projects_service():
    """Obtiene todos los proyectos de construcción para el tenant actual."""
    tenant_id, _ = _get_current_user_info()
    if not tenant_id:
        return {'error': 'Información del tenant ausente en el token'}, 400
    try:
        projects = ConstructionProject.query.filter_by(tenant_id=tenant_id).order_by(ConstructionProject.name).all()
        return [p.to_dict() for p in projects], 200
    except SQLAlchemyError as e:
        # Loggear error 'e'
        print(f"Error obteniendo proyectos: {e}")
        return {'error': f'Error de base de datos: {str(e)}'}, 500

def get_construction_project_details_service(project_id):
    """Obtiene los detalles completos de un proyecto específico."""
    tenant_id, _ = _get_current_user_info()
    if not tenant_id:
        return {'error': 'Información del tenant ausente en el token'}, 400
    try:
        project = ConstructionProject.query.filter_by(id=project_id, tenant_id=tenant_id).first()
        if not project:
            return {'error': 'Proyecto no encontrado'}, 404

        details = project.to_dict()
        # Agregamos listas de elementos relacionados, manejando si están vacías
        details['budget_items'] = [item.to_dict() for item in project.budget_items or []]
        details['progress_reports'] = [report.to_dict() for report in project.progress_reports or []]
        details['certifications'] = [cert.to_dict() for cert in project.certifications or []]
        details['rfis'] = [rfi.to_dict() for rfi in project.rfis or []] # Asumiendo rfi.to_dict()
        details['milestones'] = [m.to_dict() for m in project.milestones or []] # Asumiendo m.to_dict()

        return details, 200
    except SQLAlchemyError as e:
        # Loggear error 'e'
        print(f"Error obteniendo detalles del proyecto {project_id}: {e}")
        return {'error': f'Error de base de datos: {str(e)}'}, 500

# --- Servicio de Partidas Presupuestarias ---
def add_budget_item_service(project_id, data):
    """Agrega una partida presupuestaria a un proyecto."""
    tenant_id, _ = _get_current_user_info()
    if not tenant_id:
        return {'error': 'Información del tenant ausente en el token'}, 400
    try:
        # Verificamos que el proyecto exista y pertenezca al tenant
        project = ConstructionProject.query.filter_by(id=project_id, tenant_id=tenant_id).first()
        if not project:
            return {'error': 'Proyecto no encontrado'}, 404

        new_item = BudgetItem(
            tenant_id=tenant_id,
            project_id=project_id,
            name=data['name'],
            code=data.get('code'),
            amount=float(data['amount']) # Aseguramos float
        )
        db.session.add(new_item)
        db.session.commit()
        return {'message': 'Partida presupuestaria agregada exitosamente', 'item': new_item.to_dict()}, 201
    except (SQLAlchemyError, ValueError, KeyError, TypeError) as e:
        db.session.rollback()
        print(f"Error agregando partida: {e}")
        return {'error': f'No se pudo agregar la partida: {str(e)}'}, 500

# --- Servicio de Reportes de Avance ---
def add_progress_report_service(project_id, data):
    """Agrega un reporte de avance a un proyecto."""
    tenant_id, user_id = _get_current_user_info()
    if not tenant_id:
        return {'error': 'Información del tenant ausente en el token'}, 400
    try:
        project = ConstructionProject.query.filter_by(id=project_id, tenant_id=tenant_id).first()
        if not project:
            return {'error': 'Proyecto no encontrado'}, 404

        report_date_obj = date.fromisoformat(data['report_date'])

        new_report = ProgressReport(
            tenant_id=tenant_id,
            project_id=project_id,
            reported_by_id=user_id,
            report_date=report_date_obj,
            percentage_complete=float(data['percentage_complete']), # Aseguramos float
            notes=data.get('notes')
        )
        db.session.add(new_report)
        db.session.commit()
        return {'message': 'Reporte de avance agregado exitosamente', 'report': new_report.to_dict()}, 201
    except (SQLAlchemyError, ValueError, KeyError, TypeError) as e:
        db.session.rollback()
        print(f"Error agregando reporte de avance: {e}")
        return {'error': f'No se pudo agregar el reporte: {str(e)}'}, 500

# --- Servicio de Certificaciones ---
def create_certification_service(project_id, data):
    """Crea una nueva certificación para un proyecto."""
    tenant_id, user_id = _get_current_user_info() # user_id por si se aprueba al crear
    if not tenant_id:
        return {'error': 'Información del tenant ausente en el token'}, 400
    try:
        project = ConstructionProject.query.filter_by(id=project_id, tenant_id=tenant_id).first()
        if not project:
            return {'error': 'Proyecto no encontrado'}, 404

        certification_date_obj = date.fromisoformat(data['certification_date'])

        new_certification = Certification(
            tenant_id=tenant_id,
            project_id=project_id,
            certification_date=certification_date_obj,
            amount=float(data['amount']), # Aseguramos float
            description=data.get('description'),
            status='Pendiente' # Estado inicial por defecto
            # approved_by_id=None # Se asigna en otro paso/ruta de aprobación
        )
        db.session.add(new_certification)
        db.session.commit()
        return {'message': 'Certificación creada exitosamente', 'certification': new_certification.to_dict()}, 201
    except (SQLAlchemyError, ValueError, KeyError, TypeError) as e:
        db.session.rollback()
        print(f"Error creando certificación: {e}")
        return {'error': f'No se pudo crear la certificación: {str(e)}'}, 500

def get_certifications_for_project_service(project_id):
    """Obtiene todas las certificaciones para un proyecto."""
    tenant_id, _ = _get_current_user_info()
    if not tenant_id:
        return {'error': 'Información del tenant ausente en el token'}, 400
    try:
        certifications = Certification.query.filter_by(project_id=project_id, tenant_id=tenant_id).order_by(Certification.certification_date).all()
        return [c.to_dict() for c in certifications], 200
    except SQLAlchemyError as e:
        print(f"Error obteniendo certificaciones: {e}")
        return {'error': f'Error de base de datos: {str(e)}'}, 500

# --- Servicio RFI ---
def create_rfi_service(project_id, data):
    """Crea un nuevo Request for Information (RFI)."""
    tenant_id, user_id = _get_current_user_info()
    if not tenant_id:
        return {'error': 'Información del tenant ausente en el token'}, 400
    try:
        project = ConstructionProject.query.filter_by(id=project_id, tenant_id=tenant_id).first()
        if not project:
            return {'error': 'Proyecto no encontrado'}, 404

        new_rfi = RFI(
            tenant_id=tenant_id,
            project_id=project_id,
            created_by_id=user_id,
            subject=data['subject'],
            question=data['question'],
            status='Abierto' # Estado inicial
        )
        db.session.add(new_rfi)
        db.session.commit()
        return {'message': 'RFI creado exitosamente', 'rfi_id': new_rfi.id}, 201
    except (SQLAlchemyError, KeyError) as e:
        db.session.rollback()
        print(f"Error creando RFI: {e}")
        return {'error': f'No se pudo crear el RFI: {str(e)}'}, 500

# --- Servicio Hitos de Facturación ---
def create_milestone_service(project_id, data):
    """Crea un nuevo hito de facturación."""
    tenant_id, _ = _get_current_user_info()
    if not tenant_id:
        return {'error': 'Información del tenant ausente en el token'}, 400
    try:
        project = ConstructionProject.query.filter_by(id=project_id, tenant_id=tenant_id).first()
        if not project:
            return {'error': 'Proyecto no encontrado'}, 404

        due_date_obj = date.fromisoformat(data['due_date']) if data.get('due_date') else None

        new_milestone = Milestone(
            tenant_id=tenant_id,
            project_id=project_id,
            name=data['name'],
            due_date=due_date_obj,
            amount=float(data['amount']), # Aseguramos float
            status='Pendiente' # Estado inicial
        )
        db.session.add(new_milestone)
        db.session.commit()
        return {'message': 'Hito creado exitosamente', 'milestone_id': new_milestone.id}, 201
    except (SQLAlchemyError, ValueError, KeyError, TypeError) as e:
        db.session.rollback()
        print(f"Error creando hito: {e}")
        return {'error': f'No se pudo crear el hito: {str(e)}'}, 500