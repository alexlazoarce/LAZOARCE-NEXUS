"""
NEXUS-FEV: Firma Electrónica Avanzada Service
Placeholder for signature logic.
"""

def request_signature(document_id, signer_data):
    """
    Simulates requesting a signature for a document.
    In a real implementation, this would call an external e-signature provider API.
    """
    print(f"[FIRMA SERVICE] Solicitando firma para el documento {document_id} por parte de {signer_data['name']} ({signer_data['email']})")
    # Simulate a provider's signature request ID
    signature_request_id = f"sig_req_{document_id}_{signer_data['email']}"
    return {
        "status": "pending",
        "signature_request_id": signature_request_id,
        "message": "Signature request sent to provider."
    }

def get_signature_status(signature_request_id):
    """
    Simulates checking the status of a signature request.
    """
    print(f"[FIRMA SERVICE] Verificando estado de la solicitud de firma {signature_request_id}")
    # In a real scenario, you'd poll your provider's API.
    # Here we'll just simulate a "completed" status for demonstration.
    return {
        "status": "completed",
        "signed_document_url": f"/api/documents/signed/{signature_request_id}.pdf"
    }
