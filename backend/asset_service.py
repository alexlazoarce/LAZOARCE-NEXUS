"""
Servicio para el Módulo de Activos Fijos (LAN-AFX4)
"""
from .models import db, FixedAsset, DepreciationEntry
from datetime import date
from dateutil.relativedelta import relativedelta

def get_assets_for_tenant(tenant_id):
    """Obtiene todos los activos fijos para un tenant."""
    return FixedAsset.query.filter_by(tenant_id=tenant_id).order_by(FixedAsset.name).all()

def create_asset(name, description, purchase_date, purchase_cost, useful_life, salvage_value, tenant_id):
    """Crea un nuevo activo fijo."""
    if not all([name, purchase_date, purchase_cost, useful_life is not None]):
        raise ValueError("Nombre, fecha de compra, costo y vida útil son requeridos.")

    asset = FixedAsset(
        name=name,
        description=description,
        purchase_date=purchase_date,
        purchase_cost=purchase_cost,
        useful_life=useful_life,
        salvage_value=salvage_value,
        tenant_id=tenant_id
    )
    db.session.add(asset)
    db.session.commit()
    return asset

def get_asset_details(asset_id, tenant_id):
    """Obtiene los detalles de un activo, incluyendo su depreciación."""
    return FixedAsset.query.filter_by(id=asset_id, tenant_id=tenant_id).first_or_404()

def calculate_monthly_depreciation(asset_id, tenant_id):
    """Calcula y registra la depreciación para un mes. (Ejemplo simple)"""
    asset = get_asset_details(asset_id, tenant_id)

    if asset.depreciation_method == 'linea_recta':
        depreciable_cost = asset.purchase_cost - asset.salvage_value
        monthly_depreciation = depreciable_cost / asset.useful_life

        # Determinar para qué mes calcular
        last_entry = DepreciationEntry.query.filter_by(asset_id=asset.id).order_by(DepreciationEntry.entry_date.desc()).first()

        if last_entry:
            next_date = last_entry.entry_date + relativedelta(months=1)
        else:
            # Primer día del mes siguiente a la compra
            next_date = (asset.purchase_date + relativedelta(months=1)).replace(day=1)

        # No depreciar más allá de la vida útil
        end_of_life = asset.purchase_date + relativedelta(months=asset.useful_life)
        if next_date > end_of_life:
            raise ValueError("El activo ha completado su ciclo de depreciación.")

        entry = DepreciationEntry(
            asset_id=asset.id,
            entry_date=next_date,
            amount=monthly_depreciation,
            tenant_id=tenant_id
        )
        db.session.add(entry)
        db.session.commit()
        return entry
    else:
        raise NotImplementedError(f"Método de depreciación '{asset.depreciation_method}' no implementado.")

def get_asset_book_value(asset_id, tenant_id):
    """Calcula el valor en libros de un activo en una fecha determinada."""
    asset = get_asset_details(asset_id, tenant_id)

    total_depreciation = db.session.query(db.func.sum(DepreciationEntry.amount))\
                                   .filter_by(asset_id=asset.id).scalar() or 0

    return asset.purchase_cost - total_depreciation
