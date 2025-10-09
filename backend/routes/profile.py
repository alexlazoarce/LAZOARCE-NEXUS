from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models import User, ClientProfile

profile_bp = Blueprint('profile_bp', __name__, url_prefix='/api')

@profile_bp.route('/profile', methods=['POST'])
@jwt_required()
def create_or_update_profile():
    """
    Crea o actualiza el perfil de un cliente.
    El usuario debe estar autenticado.
    """
    user_email = get_jwt_identity()
    user = User.query.filter_by(email=user_email).first()

    if not user:
        return jsonify({"msg": "Usuario no encontrado"}), 404

    profile = ClientProfile.query.filter_by(user_id=user.id).first()
    data = request.get_json()

    if not data or 'full_name' not in data:
        return jsonify({"msg": "El campo 'full_name' es requerido."}), 400

    if profile:
        profile.full_name = data.get('full_name', profile.full_name)
        profile.phone_number = data.get('phone_number', profile.phone_number)
        profile.address = data.get('address', profile.address)
        msg = "Perfil actualizado exitosamente."
        status_code = 200
    else:
        profile = ClientProfile(
            user_id=user.id,
            full_name=data['full_name'],
            phone_number=data.get('phone_number'),
            address=data.get('address')
        )
        db.session.add(profile)
        msg = "Perfil creado exitosamente."
        status_code = 201

    db.session.commit()
    return jsonify({"msg": msg}), status_code

@profile_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """
    Obtiene el perfil del usuario autenticado.
    """
    user_email = get_jwt_identity()
    user = User.query.filter_by(email=user_email).first()

    if not user:
        return jsonify({"msg": "Usuario no encontrado"}), 404

    profile = ClientProfile.query.filter_by(user_id=user.id).first()

    if not profile:
        return jsonify({"msg": "Este usuario aún no tiene un perfil."}), 404

    return jsonify({
        "full_name": profile.full_name,
        "phone_number": profile.phone_number,
        "address": profile.address,
        "email": user.email
    }), 200