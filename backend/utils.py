from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt

def role_required(required_role):
    """
    Decorador para restringir el acceso a rutas basado en el rol del usuario,
    leyendo el rol desde los claims adicionales del token.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            # get_jwt() devuelve el payload completo del token decodificado
            claims = get_jwt()
            user_role = claims.get('role')

            allowed_roles = []
            if isinstance(required_role, list):
                allowed_roles = required_role
            else:
                allowed_roles = [required_role]

            if user_role not in allowed_roles:
                return jsonify({"msg": f"Acceso restringido. Se requiere uno de los siguientes roles: {', '.join(allowed_roles)}"}), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator