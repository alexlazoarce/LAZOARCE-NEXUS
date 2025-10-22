from .models import db, KitchenSpace, KitchenBooking, HACCPLog
from sqlalchemy.exc import SQLAlchemyError
from flask_jwt_extended import get_jwt_identity
from datetime import datetime

def _get_current_user_info():
    identity = get_jwt_identity()
    return identity.get('tenant_id'), identity.get('user_id')

# --- Kitchen Space Service ---
def create_kitchen_space_service(data):
    tenant_id, _ = _get_current_user_info()
    try:
        new_space = KitchenSpace(tenant_id=tenant_id, **data)
        db.session.add(new_space)
        db.session.commit()
        return {'message': 'Kitchen space created'}, 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return {'error': str(e)}, 500

# --- Kitchen Booking Service ---
def create_booking_service(data):
    tenant_id, user_id = _get_current_user_info()
    try:
        space = KitchenSpace.query.get(data['space_id'])
        if not space or not space.is_available:
            return {'error': 'Space not available'}, 400

        start_time = datetime.fromisoformat(data['start_time'])
        end_time = datetime.fromisoformat(data['end_time'])
        duration_hours = (end_time - start_time).total_seconds() / 3600
        total_cost = duration_hours * space.hourly_rate if space.hourly_rate else 0

        new_booking = KitchenBooking(
            tenant_id=tenant_id,
            user_id=user_id,
            space_id=data['space_id'],
            start_time=start_time,
            end_time=end_time,
            total_cost=total_cost
        )
        db.session.add(new_booking)
        db.session.commit()
        return {'message': 'Booking created'}, 201
    except (SQLAlchemyError, ValueError) as e:
        db.session.rollback()
        return {'error': str(e)}, 500

# --- HACCP Log Service ---
def create_haccp_log_service(data):
    tenant_id, user_id = _get_current_user_info()
    try:
        new_log = HACCPLog(
            tenant_id=tenant_id,
            verified_by_id=user_id,
            control_point=data['control_point'],
            measurement=data['measurement'],
            is_compliant=data['is_compliant'],
            corrective_action=data.get('corrective_action')
        )
        db.session.add(new_log)
        db.session.commit()
        return {'message': 'HACCP log created'}, 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return {'error': str(e)}, 500
