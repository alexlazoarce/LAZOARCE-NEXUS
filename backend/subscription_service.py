# backend/subscription_service.py

from datetime import datetime
from backend.models import db, Tenant, SystemModule, TenantSubscription

def has_active_subscription(tenant_id, module_code):
    """
    Checks if a tenant has an active subscription for a specific module.
    """
    module = SystemModule.query.filter_by(module_code=module_code).first()
    if not module:
        # If the module isn't registered in the system, deny access by default.
        return False

    subscription = TenantSubscription.query.filter_by(
        tenant_id=tenant_id,
        module_id=module.id,
        status='active'
    ).first()

    if not subscription:
        return False

    # Check if the subscription has expired
    if subscription.end_date and subscription.end_date < datetime.utcnow():
        # Optional: Add logic here to automatically change the status to 'expired'
        # subscription.status = 'expired'
        # db.session.commit()
        return False

    return True

def get_tenant_subscriptions(tenant_id):
    """
    Retrieves all subscriptions for a given tenant.
    """
    subscriptions = TenantSubscription.query.filter_by(tenant_id=tenant_id).all()
    return [{
        'module_code': sub.module.module_code,
        'module_name': sub.module.name,
        'status': sub.status,
        'start_date': sub.start_date.isoformat(),
        'end_date': sub.end_date.isoformat() if sub.end_date else None,
    } for sub in subscriptions]

def grant_subscription(tenant_id, module_code, end_date=None):
    """
    Grants or updates a subscription for a tenant.
    """
    module = SystemModule.query.filter_by(module_code=module_code).first()
    if not module:
        raise ValueError(f"Módulo del sistema '{module_code}' no encontrado.")

    tenant = Tenant.query.get(tenant_id)
    if not tenant:
        raise ValueError(f"Inquilino con ID '{tenant_id}' no encontrado.")

    subscription = TenantSubscription.query.filter_by(tenant_id=tenant_id, module_id=module.id).first()

    if subscription:
        # Update existing subscription
        subscription.status = 'active'
        subscription.end_date = end_date
    else:
        # Create new subscription
        subscription = TenantSubscription(
            tenant_id=tenant_id,
            module_id=module.id,
            end_date=end_date,
            status='active'
        )
        db.session.add(subscription)

    db.session.commit()
    return subscription

def revoke_subscription(tenant_id, module_code):
    """
    Revokes a tenant's subscription to a module by setting its status to 'cancelled'.
    """
    module = SystemModule.query.filter_by(module_code=module_code).first()
    if not module:
        raise ValueError(f"Módulo del sistema '{module_code}' no encontrado.")

    subscription = TenantSubscription.query.filter_by(
        tenant_id=tenant_id,
        module_id=module.id
    ).first()

    if not subscription:
        raise ValueError(f"No se encontró ninguna suscripción para el inquilino '{tenant_id}' y el módulo '{module_code}'.")

    subscription.status = 'cancelled'
    db.session.commit()
    return subscription

def seed_system_modules():
    """
    Seeds the SystemModule table with the official list of modules.
    Should be called once during database setup.
    """
    # This list should be kept up-to-date with all available modules.
    modules = [
        {'code': 'LAN-GP1', 'name': 'Gestor de Préstamos'},
        {'code': 'LAN-REC7', 'name': 'Recluta'},
        {'code': 'LAN-CB7', 'name': 'Conciliación Bancaria'},
        {'code': 'LAN-BKS1', 'name': 'Libros / Contabilidad'},
        {'code': 'LAN-V1A', 'name': 'Vacaciones y Ausencias'},
        {'code': 'LAN-OBD2', 'name': 'Onboarding Digital'},
        {'code': 'LAN-AT5', 'name': 'Asistencia y Control de Tiempo'},
        {'code': 'LAN-NR4', 'name': 'Nómina Regional'},
        {'code': 'LAN-SUB1', 'name': 'Gestión de Suscripciones'},
        {'code': 'LAN-LIC1', 'name': 'Licenciamiento On-Premise'},
        {'code': 'LAN-GYM1', 'name': 'Gestión de Gimnasios'},
        {'code': 'LAN-BAR1', 'name': 'Gestión de Barberías'},
        {'code': 'LAN-AGT5', 'name': 'Asistente Multifuncional con n8n'},
        {'code': 'LAN-N8N1', 'name': 'Editor de Flujos n8n'},
        {'code': 'LAN-MKE1', 'name': 'Editor de Escenarios Make'},
    ]

    for mod_data in modules:
        exists = SystemModule.query.filter_by(module_code=mod_data['code']).first()
        if not exists:
            new_module = SystemModule(
                module_code=mod_data['code'],
                name=mod_data['name'],
                description=f"Módulo para {mod_data['name']}." # Basic description
            )
            db.session.add(new_module)

    db.session.commit()
