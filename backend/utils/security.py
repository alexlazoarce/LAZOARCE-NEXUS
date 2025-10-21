from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt

def role_required(required_role):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            user_role = claims.get('role')

            allowed_roles = [required_role] if not isinstance(required_role, list) else required_role

            if user_role not in allowed_roles:
                return jsonify({"msg": f"Acceso restringido. Se requiere uno de los siguientes roles: {', '.join(allowed_roles)}"}), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator