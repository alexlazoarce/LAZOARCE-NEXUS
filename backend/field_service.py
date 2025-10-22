from .models import db, FieldTask, TaskReport
from sqlalchemy.exc import SQLAlchemyError
from flask_jwt_extended import get_jwt_identity

def _get_current_user_info():
    identity = get_jwt_identity()
    return identity.get('tenant_id'), identity.get('user_id')

# --- Field Task Service ---
def create_field_task_service(data):
    tenant_id, _ = _get_current_user_info()
    try:
        new_task = FieldTask(tenant_id=tenant_id, **data)
        db.session.add(new_task)
        db.session.commit()
        return {'message': 'Field task created'}, 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return {'error': str(e)}, 500

def get_field_tasks_service():
    tenant_id, _ = _get_current_user_info()
    return [task.__dict__ for task in FieldTask.query.filter_by(tenant_id=tenant_id).all()], 200

# --- Task Report Service ---
def create_task_report_service(task_id, data):
    tenant_id, user_id = _get_current_user_info()
    try:
        task = FieldTask.query.filter_by(id=task_id, tenant_id=tenant_id).first()
        if not task:
            return {'error': 'Task not found'}, 404

        new_report = TaskReport(
            tenant_id=tenant_id,
            task_id=task_id,
            created_by_id=user_id,
            **data
        )
        db.session.add(new_report)
        db.session.commit()
        return {'message': 'Task report created'}, 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return {'error': str(e)}, 500
