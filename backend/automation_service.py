# backend/automation_service.py
import requests
import os
from backend.models import db, N8nWorkflow, N8nCredential

# For now, we'll assume a single, managed n8n instance.
# These would be in environment variables in a real deployment.
N8N_API_URL = os.environ.get("N8N_API_URL", "http://localhost:5678") # Default for local dev
N8N_API_KEY = os.environ.get("N8N_API_KEY")

def save_workflow(tenant_id, name, trigger_event, workflow_json):
    """Saves or updates a workflow for a tenant."""
    workflow = N8nWorkflow.query.filter_by(tenant_id=tenant_id, name=name).first()
    if workflow:
        workflow.trigger_event = trigger_event
        workflow.workflow_json = workflow_json
    else:
        workflow = N8nWorkflow(
            tenant_id=tenant_id,
            name=name,
            trigger_event=trigger_event,
            workflow_json=workflow_json
        )
        db.session.add(workflow)
    db.session.commit()
    return workflow

def get_workflows(tenant_id):
    """Retrieves all workflows for a tenant."""
    return N8nWorkflow.query.filter_by(tenant_id=tenant_id).all()

def trigger_workflow(event_type, payload):
    """
    Finds and triggers the appropriate n8n workflow based on an event.
    This is the core of LAN-AGT5.
    """
    # Identify the tenant from the payload. This is crucial.
    # For a WhatsApp message, this might be the 'To' number.
    # This is a placeholder for a more robust tenant identification logic.
    tenant_id = payload.get('tenant_id')
    if not tenant_id:
        print(f"AUTOMATION ERROR: No se pudo identificar al inquilino para el evento {event_type}")
        return {"status": "error", "message": "Tenant not identified"}

    workflow = N8nWorkflow.query.filter_by(
        tenant_id=tenant_id,
        trigger_event=event_type,
        is_active=True
    ).first()

    if not workflow:
        print(f"AUTOMATION INFO: No hay un flujo de trabajo activo para el evento '{event_type}' en el inquilino {tenant_id}")
        return {"status": "ignored", "message": "No active workflow for this event"}

    # In a real system, you'd find the correct webhook URL from the workflow_json or have a dedicated one.
    # For this simulation, we'll assume a generic webhook that can receive data.
    # The actual n8n workflow would need to be designed to handle this.
    webhook_url = f"{N8N_API_URL}/webhook/lazoarce-nexus-trigger"

    headers = {
        "Content-Type": "application/json",
        # n8n can be secured in multiple ways, e.g. API key in header
        "X-N8N-API-KEY": N8N_API_KEY
    }

    # Pass the original payload, enriched with context
    enriched_payload = {
        "event_type": event_type,
        "tenant_id": tenant_id,
        "original_payload": payload
    }

    try:
        response = requests.post(webhook_url, json=enriched_payload, headers=headers, timeout=10)
        response.raise_for_status()
        print(f"AUTOMATION SUCCESS: Flujo de trabajo para '{event_type}' en inquilino {tenant_id} disparado exitosamente.")
        return {"status": "success", "message": "Workflow triggered"}
    except requests.exceptions.RequestException as e:
        print(f"AUTOMATION ERROR: Fallo al disparar el flujo de trabajo para '{event_type}' en inquilino {tenant_id}. Error: {e}")
        return {"status": "error", "message": str(e)}

# Credential management would go here (encrypting/decrypting values)
# For now, we'll omit the complexity of encryption.
def save_credential(tenant_id, name, value):
    """Saves a credential for a tenant."""
    # In a real implementation, 'value' would be encrypted before saving.
    encrypted_value = value # Placeholder

    cred = N8nCredential(
        tenant_id=tenant_id,
        name=name,
        encrypted_value=encrypted_value
    )
    db.session.add(cred)
    db.session.commit()
    return cred
