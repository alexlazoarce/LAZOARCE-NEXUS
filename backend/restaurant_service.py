from .models import db, MenuItem, Table, RestaurantOrder, RestaurantOrderItem
from sqlalchemy.exc import SQLAlchemyError
from flask_jwt_extended import get_jwt_identity

def _get_current_user_info():
    identity = get_jwt_identity()
    return identity.get('tenant_id'), identity.get('user_id')

# --- Menu Item Service ---
def create_menu_item_service(data):
    tenant_id, _ = _get_current_user_info()
    try:
        new_item = MenuItem(tenant_id=tenant_id, **data)
        db.session.add(new_item)
        db.session.commit()
        return {'message': 'Menu item created'}, 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return {'error': str(e)}, 500

def get_menu_items_service():
    tenant_id, _ = _get_current_user_info()
    return [item.__dict__ for item in MenuItem.query.filter_by(tenant_id=tenant_id).all()], 200

# --- Table Service ---
def create_table_service(data):
    tenant_id, _ = _get_current_user_info()
    try:
        new_table = Table(tenant_id=tenant_id, **data)
        db.session.add(new_table)
        db.session.commit()
        return {'message': 'Table created'}, 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return {'error': str(e)}, 500

def get_tables_service():
    tenant_id, _ = _get_current_user_info()
    return [table.__dict__ for table in Table.query.filter_by(tenant_id=tenant_id).all()], 200

# --- Order Service ---
def create_order_service(data):
    tenant_id, user_id = _get_current_user_info()
    try:
        new_order = RestaurantOrder(tenant_id=tenant_id, table_id=data['table_id'], waiter_id=user_id)
        db.session.add(new_order)
        # Cambiar estado de la mesa
        table = Table.query.get(data['table_id'])
        if table:
            table.status = 'Ocupada'
        db.session.commit()
        return {'message': 'Order created', 'order_id': new_order.id}, 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return {'error': str(e)}, 500

def add_item_to_order_service(order_id, data):
    tenant_id, _ = _get_current_user_info()
    try:
        order = RestaurantOrder.query.filter_by(id=order_id, tenant_id=tenant_id).first()
        menu_item = MenuItem.query.filter_by(id=data['menu_item_id'], tenant_id=tenant_id).first()
        if not order or not menu_item:
            return {'error': 'Order or Menu Item not found'}, 404

        new_order_item = RestaurantOrderItem(
            order_id=order_id,
            menu_item_id=data['menu_item_id'],
            quantity=data.get('quantity', 1),
            price=menu_item.price,
            notes=data.get('notes'),
            tenant_id=tenant_id
        )
        order.total_amount += new_order_item.quantity * new_order_item.price
        db.session.add(new_order_item)
        db.session.commit()
        return {'message': 'Item added to order'}, 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return {'error': str(e)}, 500
