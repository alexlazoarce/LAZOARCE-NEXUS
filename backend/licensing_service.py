# backend/licensing_service.py

import uuid
from backend.models import db, Tenant
from backend import subscription_service

def generate_license_key_for_tenant(tenant_id):
    """
    Generates a unique license key for an on-premise tenant.
    """
    tenant = Tenant.query.get(tenant_id)
    if not tenant:
        raise ValueError(f"Inquilino con ID '{tenant_id}' no encontrado.")

    if tenant.deployment_type != 'on-premise':
        raise ValueError("Las claves de licencia solo se pueden generar para inquilinos 'on-premise'.")

    # Generate a unique key and assign it to the tenant
    new_key = f"LAN-LIC-{uuid.uuid4().hex.upper()}"
    tenant.license_key = new_key
    db.session.commit()

    return new_key

def validate_license_key(license_key):
    """
    Validates a license key and returns the list of active module subscriptions.
    This is the function that on-premise instances will call.
    """
    if not license_key:
        return {"is_valid": False, "error": "No se proporcionó ninguna clave de licencia."}

    tenant = Tenant.query.filter_by(license_key=license_key, is_active=True).first()

    if not tenant:
        return {"is_valid": False, "error": "Clave de licencia inválida o inquilino inactivo."}

    # If the key is valid, get the tenant's active subscriptions
    subscriptions = subscription_service.get_tenant_subscriptions(tenant.id)

    active_modules = [
        sub['module_code'] for sub in subscriptions if sub['status'] == 'active'
    ]

    return {
        "is_valid": True,
        "tenant_name": tenant.company_name,
        "active_modules": active_modules
    }

def simulate_on_premise_startup_check(license_key):
    """
    A simulation function to demonstrate how an on-premise instance would
    use the validation service.
    """
    print(f"--- SIMULACIÓN DE ARRANQUE ON-PREMISE ---")
    print(f"Verificando la clave de licencia: {license_key[:12]}...")

    validation_result = validate_license_key(license_key)

    if validation_result["is_valid"]:
        print(f"Validación exitosa para el inquilino: {validation_result['tenant_name']}")
        print("Módulos activos habilitados:")
        for module_code in validation_result['active_modules']:
            print(f"  - {module_code}")
    else:
        print(f"Error de validación: {validation_result['error']}")
        print("La aplicación no puede continuar. Por favor, contacte a soporte.")

    print("--- FIN DE LA SIMULACIÓN ---")
    return validation_result
