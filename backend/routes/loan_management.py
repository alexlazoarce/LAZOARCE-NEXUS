from flask import Blueprint, request, jsonify
from backend.extensions import db
from backend.models import User, LoanProduct, LoanApplication
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.utils.security import role_required

loan_management_bp = Blueprint('loan_management_bp', __name__, url_prefix='/api')

@loan_management_bp.route('/products', methods=['POST'])
@jwt_required()
@role_required('Administrador General')
def create_loan_product():
    data = request.get_json()
    try:
        new_product = LoanProduct(**data)
        db.session.add(new_product)
        db.session.commit()
        return jsonify({"msg": "Producto de préstamo creado exitosamente", "product_id": new_product.id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@loan_management_bp.route('/products', methods=['GET'])
@jwt_required()
def get_loan_products():
    products = LoanProduct.query.filter_by(is_active=True).all()
    return jsonify([{"id": p.id, "name": p.name} for p in products])

@loan_management_bp.route('/applications', methods=['POST'])
@jwt_required()
def submit_loan_application():
    user_email = get_jwt_identity()
    user = User.query.filter_by(email=user_email).first()
    data = request.get_json()
    try:
        new_application = LoanApplication(user_id=user.id, **data)
        db.session.add(new_application)
        db.session.commit()
        return jsonify({"msg": "Solicitud de préstamo enviada exitosamente.", "application_id": new_application.id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@loan_management_bp.route('/applications/<int:application_id>/status', methods=['PUT'])
@jwt_required()
@role_required('Administrador General')
def update_application_status(application_id):
    application = LoanApplication.query.get_or_404(application_id)
    data = request.get_json()
    application.status = data.get('status')
    db.session.commit()
    return jsonify({"msg": f"Estado de la solicitud {application_id} actualizado a '{application.status}'."})