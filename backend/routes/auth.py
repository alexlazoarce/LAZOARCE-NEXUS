from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, get_jwt
from ..extensions import db
from ..models import User, Role

auth_bp = Blueprint('auth_bp', __name__, url_prefix='/api')

@auth_bp.route('/register', methods=['POST'])
def register():
    """Endpoint para registrar un nuevo usuario."""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    role_name = data.get('role', 'Cliente')

    if not email or not password:
        return jsonify({"msg": "Email y contraseña son requeridos"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"msg": "El email ya está registrado"}), 400

    role = Role.query.filter_by(name=role_name).first()
    if not role:
        return jsonify({"msg": f"El rol '{role_name}' no es válido"}), 400

    new_user = User(email=email, role_id=role.id)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"msg": "Usuario creado exitosamente"}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    """Endpoint para iniciar sesión y obtener un token JWT."""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"msg": "Email y contraseña son requeridos"}), 400

    user = User.query.filter_by(email=email).first()

    if user and user.check_password(password):
        # La identidad es el email (string), y el rol va en los claims adicionales
        identity = user.email
        additional_claims = {"role": user.role.name}
        access_token = create_access_token(identity=identity, additional_claims=additional_claims)
        return jsonify(access_token=access_token)

    return jsonify({"msg": "Credenciales inválidas"}), 401