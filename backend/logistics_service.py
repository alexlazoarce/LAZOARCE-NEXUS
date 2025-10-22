from .models import db, Vehicle, Driver, Route, Delivery
from sqlalchemy.exc import SQLAlchemyError
from flask_jwt_extended import get_jwt_identity

def _get_current_user_info():
    identity = get_jwt_identity()
    return identity.get('tenant_id'), identity.get('user_id')

# --- Vehicle Service ---
def create_vehicle_service(data):
    tenant_id, _ = _get_current_user_info()
    try:
        new_vehicle = Vehicle(tenant_id=tenant_id, **data)
        db.session.add(new_vehicle)
        db.session.commit()
        return {'message': 'Vehicle created'}, 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return {'error': str(e)}, 500

def get_vehicles_service():
    tenant_id, _ = _get_current_user_info()
    return [v.__dict__ for v in Vehicle.query.filter_by(tenant_id=tenant_id).all()], 200

# --- Driver Service ---
def create_driver_service(data):
    tenant_id, _ = _get_current_user_info()
    try:
        new_driver = Driver(tenant_id=tenant_id, **data)
        db.session.add(new_driver)
        db.session.commit()
        return {'message': 'Driver created'}, 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return {'error': str(e)}, 500

def get_drivers_service():
    tenant_id, _ = _get_current_user_info()
    return [d.__dict__ for d in Driver.query.filter_by(tenant_id=tenant_id).all()], 200

# --- Route Service ---
def create_route_service(data):
    tenant_id, _ = _get_current_user_info()
    try:
        new_route = Route(tenant_id=tenant_id, **data)
        db.session.add(new_route)
        db.session.commit()
        return {'message': 'Route created'}, 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return {'error': str(e)}, 500

def get_routes_service():
    tenant_id, _ = _get_current_user_info()
    return [r.__dict__ for r in Route.query.filter_by(tenant_id=tenant_id).all()], 200

# --- Delivery Service ---
def add_delivery_to_route_service(route_id, data):
    tenant_id, _ = _get_current_user_info()
    try:
        route = Route.query.filter_by(id=route_id, tenant_id=tenant_id).first()
        if not route:
            return {'error': 'Route not found'}, 404

        new_delivery = Delivery(tenant_id=tenant_id, route_id=route_id, **data)
        db.session.add(new_delivery)
        db.session.commit()
        return {'message': 'Delivery added to route'}, 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return {'error': str(e)}, 500
