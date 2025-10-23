"""
backend/cleaning_service.py

Servicio para el Módulo de Gestión de Limpieza (LAN-CLN7).
"""
from .models import db, CleaningService, CleaningOrder, CleaningOrderItem, CleaningSupply, User
from sqlalchemy.exc import IntegrityError

class CleaningServiceManager:

    def create_service(self, tenant_id, data):
        service = CleaningService(
            name=data['name'],
            description=data.get('description'),
            pricing_method=data['pricing_method'],
            price=data['price'],
            tenant_id=tenant_id
        )
        db.session.add(service)
        db.session.commit()
        return service

    def get_services(self, tenant_id):
        return CleaningService.query.filter_by(tenant_id=tenant_id).all()

    def create_order(self, tenant_id, customer_id, items_data, scheduled_date):
        order = CleaningOrder(
            customer_id=customer_id,
            tenant_id=tenant_id,
            scheduled_date=scheduled_date,
            total_amount=0 # Se calculará después
        )
        db.session.add(order)
        db.session.flush() # Para obtener el ID de la orden

        total = 0
        for item_data in items_data:
            service = CleaningService.query.get(item_data['service_id'])
            price = service.price * item_data.get('quantity', 0)
            total += price

            order_item = CleaningOrderItem(
                order_id=order.id,
                service_id=item_data['service_id'],
                description=item_data.get('description'),
                quantity=item_data.get('quantity'),
                price=price,
                tenant_id=tenant_id
            )
            db.session.add(order_item)

        order.total_amount = total
        db.session.commit()
        return order

    def get_orders(self, tenant_id):
        return CleaningOrder.query.filter_by(tenant_id=tenant_id).all()

    def update_order_status(self, tenant_id, order_id, status):
        order = CleaningOrder.query.filter_by(id=order_id, tenant_id=tenant_id).first()
        if order:
            order.status = status
            db.session.commit()
        return order

    def create_supply(self, tenant_id, data):
        supply = CleaningSupply(
            name=data['name'],
            stock_level=data.get('stock_level', 0),
            unit=data.get('unit'),
            tenant_id=tenant_id
        )
        db.session.add(supply)
        db.session.commit()
        return supply

    def get_supplies(self, tenant_id):
        return CleaningSupply.query.filter_by(tenant_id=tenant_id).all()

cleaning_service = CleaningServiceManager()
