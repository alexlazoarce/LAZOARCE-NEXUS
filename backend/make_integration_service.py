# backend/make_integration_service.py
import requests
import os
from backend.models import db, MakeScenario, MakeConnection

# These would be environment variables, specific to the Make.com integration.
MAKE_API_URL = os.environ.get("MAKE_API_URL", "https://api.make.com/v2")
MAKE_API_TOKEN = os.environ.get("MAKE_API_TOKEN") # The master token for the LAZOARCE organization

def save_scenario(tenant_id, name, scenario_blueprint):
    """Saves or updates a Make.com scenario for a tenant."""
    scenario = MakeScenario.query.filter_by(tenant_id=tenant_id, name=name).first()
    if scenario:
        scenario.scenario_blueprint = scenario_blueprint
    else:
        scenario = MakeScenario(
            tenant_id=tenant_id,
            name=name,
            scenario_blueprint=scenario_blueprint
        )
        db.session.add(scenario)
    db.session.commit()
    # In a real integration, you would probably need to call the Make API
    # here to create or update the scenario in your Make.com organization.
    return scenario

def get_scenarios(tenant_id):
    """Retrieves all Make.com scenarios for a tenant."""
    return MakeScenario.query.filter_by(tenant_id=tenant_id).all()

def run_scenario(tenant_id, scenario_id, payload):
    """
    Triggers a specific Make.com scenario via its webhook.

    This assumes the scenario in Make.com starts with a "Webhook" module,
    which provides a unique URL to receive data.
    """
    scenario = MakeScenario.query.filter_by(id=scenario_id, tenant_id=tenant_id).first_or_404()

    if not scenario.is_active:
        return {"status": "ignored", "message": "Scenario is not active."}

    # The webhook URL should be part of the scenario_blueprint or stored separately.
    # We are extracting it from a hypothetical 'webhookUrl' key in the blueprint.
    webhook_url = scenario.scenario_blueprint.get('webhookUrl')
    if not webhook_url:
        msg = f"MAKE ERROR: No se encontró la URL del webhook en el blueprint del escenario '{scenario.name}'."
        print(msg)
        return {"status": "error", "message": msg}

    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status() # Will raise an exception for 4xx/5xx responses
        print(f"MAKE SUCCESS: Escenario '{scenario.name}' para el inquilino {tenant_id} disparado exitosamente.")
        return {"status": "success", "message": "Scenario triggered"}
    except requests.exceptions.RequestException as e:
        print(f"MAKE ERROR: Fallo al disparar el escenario '{scenario.name}'. Error: {e}")
        return {"status": "error", "message": str(e)}

# Similar to the n8n service, credential management would be handled here.
def save_connection(tenant_id, name, credentials):
    """Saves a Make.com connection's credentials for a tenant."""
    # 'credentials' would be a JSON object that is then encrypted.
    encrypted_credentials = str(credentials) # Placeholder for encryption

    conn = MakeConnection(
        tenant_id=tenant_id,
        name=name,
        encrypted_credentials=encrypted_credentials
    )
    db.session.add(conn)
    db.session.commit()
    return conn
