from .models import db, TaxType, TaxDeclaration, SalesOrder, PurchaseOrder, SalesOrderItem, PurchaseOrderItem
from sqlalchemy.exc import SQLAlchemyError
from flask_jwt_extended import get_jwt_identity
from datetime import date
from sqlalchemy import func

def _get_tenant_id():
    """Extrae el tenant_id de la identidad del JWT."""
    current_user = get_jwt_identity()
    return current_user.get('tenant_id')

# --- TaxType Service ---

def create_tax_type_service(data):
    tenant_id = _get_tenant_id()
    try:
        new_tax_type = TaxType(
            tenant_id=tenant_id,
            name=data['name'],
            rate=data['rate'],
            country_code=data['country_code'],
            tax_category=data['tax_category']
        )
        db.session.add(new_tax_type)
        db.session.commit()
        return {'message': 'Tax type created successfully', 'tax_type': new_tax_type.to_dict()}, 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return {'error': str(e)}, 500

def get_tax_types_service(filters=None):
    tenant_id = _get_tenant_id()
    try:
        query = TaxType.query.filter_by(tenant_id=tenant_id)
        if filters:
            if 'country_code' in filters:
                query = query.filter_by(country_code=filters['country_code'])
            if 'tax_category' in filters:
                query = query.filter_by(tax_category=filters['tax_category'])

        tax_types = query.all()
        return [tt.to_dict() for tt in tax_types], 200
    except SQLAlchemyError as e:
        return {'error': str(e)}, 500

def update_tax_type_service(tax_type_id, data):
    tenant_id = _get_tenant_id()
    try:
        tax_type = TaxType.query.filter_by(id=tax_type_id, tenant_id=tenant_id).first()
        if not tax_type:
            return {'error': 'Tax type not found'}, 404

        tax_type.name = data.get('name', tax_type.name)
        tax_type.rate = data.get('rate', tax_type.rate)
        tax_type.country_code = data.get('country_code', tax_type.country_code)
        tax_type.tax_category = data.get('tax_category', tax_type.tax_category)
        tax_type.is_active = data.get('is_active', tax_type.is_active)

        db.session.commit()
        return {'message': 'Tax type updated successfully', 'tax_type': tax_type.to_dict()}, 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return {'error': str(e)}, 500

# --- Tax Declaration Service ---

def generate_iva_declaration_service(start_date_str, end_date_str):
    tenant_id = _get_tenant_id()
    user_id = get_jwt_identity().get('user_id')

    try:
        start_date = date.fromisoformat(start_date_str)
        end_date = date.fromisoformat(end_date_str)

        # 1. Calcular IVA Débito (de Ventas)
        total_debitos = db.session.query(func.sum(SalesOrderItem.total_price)).join(SalesOrder).\
            filter(
                SalesOrder.tenant_id == tenant_id,
                SalesOrder.status.in_(['Confirmada', 'Completada']),
                SalesOrder.order_date.between(start_date, end_date)
            ).scalar() or 0

        # Asumiendo una tasa de IVA estándar del 13% para SV (esto debería ser más dinámico)
        iva_rate = 0.13
        iva_debito = total_debitos * iva_rate

        # 2. Calcular IVA Crédito (de Compras)
        total_creditos = db.session.query(func.sum(PurchaseOrderItem.total_price)).join(PurchaseOrder).\
            filter(
                PurchaseOrder.tenant_id == tenant_id,
                PurchaseOrder.status == 'Recibida',
                PurchaseOrder.order_date.between(start_date, end_date)
            ).scalar() or 0

        iva_credito = total_creditos * iva_rate

        # 3. Calcular impuesto a pagar
        impuesto_a_pagar = iva_debito - iva_credito

        declaration_data = {
            'total_ventas_gravadas': float(total_debitos),
            'iva_debito': float(iva_debito),
            'total_compras_gravadas': float(total_creditos),
            'iva_credito': float(iva_credito),
            'impuesto_resultante': float(impuesto_a_pagar)
        }

        new_declaration = TaxDeclaration(
            tenant_id=tenant_id,
            generated_by_id=user_id,
            declaration_type='IVA Mensual',
            period_start=start_date,
            period_end=end_date,
            calculated_data=declaration_data,
            status='Borrador'
        )

        db.session.add(new_declaration)
        db.session.commit()

        return {'message': 'IVA declaration generated successfully', 'declaration': new_declaration.to_dict()}, 201

    except (ValueError, TypeError) as e:
        return {'error': f'Invalid date format: {e}'}, 400
    except SQLAlchemyError as e:
        db.session.rollback()
        return {'error': str(e)}, 500

def get_tax_declarations_service():
    tenant_id = _get_tenant_id()
    try:
        declarations = TaxDeclaration.query.filter_by(tenant_id=tenant_id).order_by(TaxDeclaration.period_start.desc()).all()
        return [d.to_dict() for d in declarations], 200
    except SQLAlchemyError as e:
        return {'error': str(e)}, 500
