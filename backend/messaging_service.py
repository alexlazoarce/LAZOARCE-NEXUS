"""
Servicio para la Mensajería Corporativa (LAN-C8T)
"""
from .models import db, Channel, Message, User
from sqlalchemy.orm import joinedload

def get_public_channels(tenant_id):
    """Obtiene todos los canales públicos para un tenant."""
    return Channel.query.filter_by(tenant_id=tenant_id, channel_type='public').all()

def create_channel(name, description, channel_type, tenant_id, creator_id):
    """Crea un nuevo canal de mensajería."""
    if not name:
        raise ValueError("El nombre del canal es requerido.")

    new_channel = Channel(
        name=name,
        description=description,
        channel_type=channel_type,
        tenant_id=tenant_id,
        created_by_id=creator_id
    )

    # Si es público, todos pueden acceder. Si es privado, el creador es el primer miembro.
    if channel_type == 'private':
        creator = User.query.get(creator_id)
        if creator:
            new_channel.members.append(creator)

    db.session.add(new_channel)
    db.session.commit()
    return new_channel

def add_user_to_channel(channel_id, user_id):
    """Agrega un usuario a un canal (principalmente para canales privados)."""
    channel = Channel.query.get_or_404(channel_id)
    user = User.query.get_or_404(user_id)

    if user not in channel.members:
        channel.members.append(user)
        db.session.commit()
    return channel

def post_message(channel_id, user_id, content):
    """Publica un nuevo mensaje en un canal."""
    if not content:
        raise ValueError("El contenido del mensaje no puede estar vacío.")

    # Verificar que el usuario tiene acceso al canal (simplificado)
    channel = Channel.query.get_or_404(channel_id)
    # En una implementación real, se verificaría si el usuario es miembro si el canal es privado

    message = Message(
        channel_id=channel_id,
        user_id=user_id,
        content=content,
        tenant_id=channel.tenant_id
    )
    db.session.add(message)
    db.session.commit()
    return message

def get_messages_for_channel(channel_id, limit=50):
    """Obtiene los últimos mensajes de un canal."""
    # Usamos joinedload para cargar el autor del mensaje y evitar N+1 queries
    return Message.query.filter_by(channel_id=channel_id)\
                        .options(joinedload(Message.author))\
                        .order_by(Message.created_at.desc())\
                        .limit(limit)\
                        .all()

def get_user_channels(user_id, tenant_id):
    """Obtiene los canales a los que un usuario pertenece."""
    user = User.query.get_or_404(user_id)
    # Incluye canales públicos y canales privados donde el usuario es miembro.
    public_channels = Channel.query.filter_by(tenant_id=tenant_id, channel_type='public')
    private_channels = user.messaging_channels.filter_by(tenant_id=tenant_id)

    # Unir las dos consultas
    return public_channels.union(private_channels).all()
