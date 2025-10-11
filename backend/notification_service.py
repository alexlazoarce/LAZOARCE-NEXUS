from .models import db, User, NotificationTemplate

def send_notification(user_id, template_slug, data={}):
    """
    Renders and "sends" a notification to a user based on a template.
    In this version, "sending" means printing to the console.

    :param user_id: The ID of the user to notify.
    :param template_slug: The slug of the NotificationTemplate to use.
    :param data: A dictionary of context data to fill in the template.
    """
    user = User.query.get(user_id)
    template = NotificationTemplate.query.filter_by(slug=template_slug).first()

    if not user:
        print(f"ERROR de Notificación: Usuario con ID {user_id} no encontrado.")
        return
    if not template:
        print(f"ERROR de Notificación: Plantilla con slug '{template_slug}' no encontrada.")
        return

    # Prepare context data
    context = {
        'customer_name': user.full_name,
        'customer_email': user.email,
        **data # Merge external data
    }

    # Render subject and body
    subject = template.subject
    body = template.body
    for key, value in context.items():
        subject = subject.replace(f'{{{key}}}', str(value))
        body = body.replace(f'{{{key}}}', str(value))

    # "Send" the notification
    print("--- SIMULANDO ENVÍO DE NOTIFICACIÓN ---")
    print(f"Tipo: {template.type}")
    print(f"Para: {user.email}")
    print(f"Asunto: {subject}")
    print("--- Cuerpo ---")
    print(body)
    print("---------------------------------------")

    return True # Indicate success