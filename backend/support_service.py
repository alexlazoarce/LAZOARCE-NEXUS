"""
Servicio para el Módulo de Soporte Técnico (LAN-SOP1)
"""
from .models import db, Ticket, TicketUpdate, User

def get_tickets_for_tenant(tenant_id, user_role=None, user_id=None):
    """Obtiene tickets para un tenant, filtrando por rol de usuario."""
    query = Ticket.query.filter_by(tenant_id=tenant_id)

    # Si el usuario no es admin/soporte, solo ve sus propios tickets
    if user_role not in ['Administrador General', 'Soporte']:
        query = query.filter_by(created_by_id=user_id)

    return query.order_by(Ticket.updated_at.desc()).all()

def create_ticket(subject, description, priority, tenant_id, user_id):
    """Crea un nuevo ticket de soporte."""
    if not subject or not description:
        raise ValueError("El asunto y la descripción son requeridos.")

    ticket = Ticket(
        subject=subject,
        description=description,
        priority=priority,
        tenant_id=tenant_id,
        created_by_id=user_id
    )
    db.session.add(ticket)
    db.session.commit()
    return ticket

def get_ticket_details(ticket_id, tenant_id):
    """Obtiene los detalles de un ticket, incluyendo sus actualizaciones."""
    return Ticket.query.filter_by(id=ticket_id, tenant_id=tenant_id).first_or_404()

def add_ticket_update(ticket_id, user_id, comment):
    """Añade un comentario o actualización a un ticket."""
    if not comment:
        raise ValueError("El comentario no puede estar vacío.")

    # La validación de que el usuario puede ver el ticket se hace en la ruta
    ticket = Ticket.query.get_or_404(ticket_id)

    update = TicketUpdate(
        ticket_id=ticket.id,
        user_id=user_id,
        comment=comment
    )
    db.session.add(update)

    # Actualizar el timestamp del ticket principal para que aparezca primero
    ticket.updated_at = db.func.current_timestamp()

    db.session.commit()
    return update

def assign_ticket(ticket_id, assign_to_user_id, tenant_id):
    """Asigna un ticket a un miembro del personal de soporte."""
    ticket = get_ticket_details(ticket_id, tenant_id)
    assignee = User.query.filter_by(id=assign_to_user_id, tenant_id=tenant_id).first_or_404()

    # Aquí se podría verificar que el 'assignee' tiene rol de Soporte

    ticket.assigned_to_id = assignee.id
    db.session.commit()
    return ticket

def change_ticket_status(ticket_id, status, tenant_id):
    """Cambia el estado de un ticket."""
    ticket = get_ticket_details(ticket_id, tenant_id)

    valid_statuses = ['Abierto', 'En Progreso', 'Cerrado']
    if status not in valid_statuses:
        raise ValueError(f"Estado no válido. Use uno de: {', '.join(valid_statuses)}")

    ticket.status = status
    db.session.commit()
    return ticket
