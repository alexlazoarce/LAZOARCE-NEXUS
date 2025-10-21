"""
Servicio para el Envío de Correos Empresariales (LAN-MAIL1)
"""
import datetime

def send_email(recipient, subject, body, tenant):
    """
    Envía un correo electrónico.
    Por ahora, simula el envío imprimiendo en la consola.
    """

    # Simulación de un log de envío
    print("--- NUEVO CORREO ELECTRÓNICO ---")
    print(f"Fecha: {datetime.datetime.now()}")
    print(f"Tenant: {tenant.company_name}")
    print(f"Destinatario: {recipient}")
    print(f"Asunto: {subject}")
    print("--- Cuerpo del Mensaje ---")
    print(body)
    print("--------------------------")

    # En una implementación real, aquí iría la lógica para conectarse a un servidor SMTP
    # y enviar el correo.

    # La función podría devolver un ID de log o un estado
    return True, "Correo enviado (simulado) exitosamente."
