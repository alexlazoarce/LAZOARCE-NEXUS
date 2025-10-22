from .models import db, Material, MaterialRequest
from sqlalchemy.exc import SQLAlchemyError
from flask_jwt_extended import get_jwt_identity

def _get_current_user_info():
    """Extrae el tenant_id y user_id de la identidad del JWT."""
    identity = get_jwt_identity()
    return identity.get('tenant_id'), identity.get('user_id')

# --- Material Service ---

def create_material_service(data):
    tenant_id, _ = _get_current_user_info()
    try:
        new_material = Material(
            tenant_id=tenant_id,
            name=data['name'],
            description=data.get('description'),
            unit=data.get('unit'),
            stock=data.get('stock', 0)
        )
        db.session.add(new_material)
        db.session.commit()
        return {'message': 'Material created successfully', 'material': new_material.to_dict()}, 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return {'error': str(e)}, 500

def get_materials_service():
    tenant_id, _ = _get_current_user_info()
    try:
        materials = Material.query.filter_by(tenant_id=tenant_id).all()
        return [m.to_dict() for m in materials], 200
    except SQLAlchemyError as e:
        return {'error': str(e)}, 500

def update_material_stock_service(material_id, data):
    tenant_id, _ = _get_current_user_info()
    try:
        material = Material.query.filter_by(id=material_id, tenant_id=tenant_id).first()
        if not material:
            return {'error': 'Material not found'}, 404

        change = data.get('change', 0)
        material.stock += change

        db.session.commit()
        return {'message': 'Stock updated successfully', 'material': material.to_dict()}, 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return {'error': str(e)}, 500

# --- Material Request Service ---

def create_material_request_service(data):
    tenant_id, user_id = _get_current_user_info()
    try:
        material = Material.query.filter_by(id=data['material_id'], tenant_id=tenant_id).first()
        if not material:
            return {'error': 'Material not found'}, 404

        new_request = MaterialRequest(
            tenant_id=tenant_id,
            requester_id=user_id,
            material_id=data['material_id'],
            quantity=data['quantity'],
            notes=data.get('notes')
        )
        db.session.add(new_request)
        db.session.commit()
        return {'message': 'Material request created successfully', 'request': new_request.to_dict()}, 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return {'error': str(e)}, 500

def get_material_requests_service(status=None):
    tenant_id, _ = _get_current_user_info()
    try:
        query = MaterialRequest.query.filter_by(tenant_id=tenant_id)
        if status:
            query = query.filter_by(status=status)

        requests = query.order_by(MaterialRequest.created_at.desc()).all()
        return [r.to_dict() for r in requests], 200
    except SQLAlchemyError as e:
        return {'error': str(e)}, 500

def update_material_request_status_service(request_id, data):
    tenant_id, user_id = _get_current_user_info()
    new_status = data.get('status')
    if not new_status:
        return {'error': 'Status is required'}, 400

    try:
        request = MaterialRequest.query.filter_by(id=request_id, tenant_id=tenant_id).first()
        if not request:
            return {'error': 'Request not found'}, 404

        # Lógica de aprobación y entrega
        if new_status == 'Aprobada' and request.status == 'Pendiente':
            request.status = 'Aprobada'
            request.approver_id = user_id
            request.approval_notes = data.get('approval_notes')
        elif new_status == 'Rechazada' and request.status == 'Pendiente':
            request.status = 'Rechazada'
            request.approver_id = user_id
            request.approval_notes = data.get('approval_notes')
        elif new_status == 'Entregada' and request.status == 'Aprobada':
            material = request.material
            if material.stock < request.quantity:
                return {'error': 'Insufficient stock to fulfill the request'}, 400

            material.stock -= request.quantity
            request.status = 'Entregada'
        else:
            return {'error': f'Invalid status transition from {request.status} to {new_status}'}, 400

        db.session.commit()
        return {'message': 'Request status updated successfully', 'request': request.to_dict()}, 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return {'error': str(e)}, 500
