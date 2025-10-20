from .models import db, Tenant, SystemModule, TenantSubscription
from datetime import date, timedelta

def create_tenant(name):
    """Creates a new tenant."""
    if Tenant.query.filter_by(name=name).first():
        raise ValueError(f"Tenant '{name}' already exists.")
    new_tenant = Tenant(name=name)
    db.session.add(new_tenant)
    db.session.commit()
    return new_tenant

def get_all_tenants():
    """Retrieves all tenants."""
    return Tenant.query.order_by(Tenant.name).all()

def create_system_module(module_code, name, description=""):
    """Creates a new system module."""
    if SystemModule.query.filter_by(module_code=module_code).first():
        raise ValueError(f"System module '{module_code}' already exists.")
    new_module = SystemModule(module_code=module_code, name=name, description=description)
    db.session.add(new_module)
    db.session.commit()
    return new_module

def get_all_system_modules():
    """Retrieves all system modules."""
    return SystemModule.query.order_by(SystemModule.module_code).all()

def create_subscription(tenant_id, module_id, start_date_iso, end_date_iso=None):
    """Creates a subscription for a tenant to a module."""
    tenant = Tenant.query.get(tenant_id)
    if not tenant:
        raise ValueError(f"Tenant with ID {tenant_id} not found.")

    module = SystemModule.query.get(module_id)
    if not module:
        raise ValueError(f"System module with ID {module_id} not found.")

    start_date = date.fromisoformat(start_date_iso)
    end_date = date.fromisoformat(end_date_iso) if end_date_iso else None

    new_subscription = TenantSubscription(
        tenant_id=tenant_id,
        module_id=module_id,
        start_date=start_date,
        end_date=end_date
    )
    db.session.add(new_subscription)
    db.session.commit()
    return new_subscription

def get_subscriptions_for_tenant(tenant_id):
    """Retrieves all subscriptions for a specific tenant."""
    return TenantSubscription.query.filter_by(tenant_id=tenant_id).all()
