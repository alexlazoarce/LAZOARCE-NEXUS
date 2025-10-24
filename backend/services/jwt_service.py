"""
jwt_service.py - Helper functions for JWT authentication and user/tenant context.
"""
from functools import wraps
from flask import g, jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request, get_jwt
from backend.models import User

def jwt_required(f):
    """
    A decorator to protect routes with JWT. It also loads the current user
    and tenant into the Flask global context `g`.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request()
            claims = get_jwt()
            user_identity = get_jwt_identity()

            # The identity is the user's email
            current_user = User.query.filter_by(email=user_identity).first()
            if not current_user:
                return jsonify({"error": "User not found."}), 404

            g.current_user = current_user
            g.tenant_id = claims.get('tenant_id')

            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({"error": "JWT verification failed", "message": str(e)}), 401

    return decorated_function

def get_current_user():
    """Returns the authenticated user object from the global context."""
    return g.get('current_user', None)

def get_current_tenant_id():
    """
    Returns the tenant_id from the JWT claims stored in the global context.
    This is a simplified approach. In a real application, you might want to
    ensure the tenant exists and is active.
    """
    return g.get('tenant_id', None)
