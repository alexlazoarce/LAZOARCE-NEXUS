from flask_jwt_extended import get_jwt_identity, get_jwt
from ..models import User

def get_current_user():
    user_identity = get_jwt_identity()
    return User.query.filter_by(email=user_identity).first()

def get_current_tenant_id():
    claims = get_jwt()
    return claims.get('tenant_id')
