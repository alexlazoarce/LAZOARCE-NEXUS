from .models import db, ServiceJob, JobQuote, JobInvoice
from sqlalchemy.exc import SQLAlchemyError
from flask_jwt_extended import get_jwt_identity

def _get_current_user_info():
    identity = get_jwt_identity()
    return identity.get('tenant_id'), identity.get('user_id')

# --- Service Job Service ---
def create_service_job_service(data):
    tenant_id, _ = _get_current_user_info()
    try:
        new_job = ServiceJob(tenant_id=tenant_id, **data)
        db.session.add(new_job)
        db.session.commit()
        return {'message': 'Service job created'}, 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return {'error': str(e)}, 500

def get_service_jobs_service():
    tenant_id, _ = _get_current_user_info()
    return [job.__dict__ for job in ServiceJob.query.filter_by(tenant_id=tenant_id).all()], 200

# --- Job Quote Service ---
def create_job_quote_service(job_id, data):
    tenant_id, _ = _get_current_user_info()
    try:
        job = ServiceJob.query.filter_by(id=job_id, tenant_id=tenant_id).first()
        if not job:
            return {'error': 'Job not found'}, 404

        new_quote = JobQuote(tenant_id=tenant_id, job_id=job_id, **data)
        db.session.add(new_quote)
        db.session.commit()
        return {'message': 'Quote created'}, 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return {'error': str(e)}, 500

# --- Job Invoice Service ---
def create_job_invoice_service(job_id, data):
    tenant_id, _ = _get_current_user_info()
    try:
        job = ServiceJob.query.filter_by(id=job_id, tenant_id=tenant_id).first()
        if not job:
            return {'error': 'Job not found'}, 404

        new_invoice = JobInvoice(tenant_id=tenant_id, job_id=job_id, **data)
        job.status = 'Facturado' # Update job status
        db.session.add(new_invoice)
        db.session.commit()
        return {'message': 'Invoice created'}, 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return {'error': str(e)}, 500
