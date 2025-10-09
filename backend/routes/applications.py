from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from ..extensions import db
from ..models import User, LoanApplication, LoanProduct, Loan
from ..utils import role_required

applications_bp = Blueprint('applications_bp', __name__, url_prefix='/api/applications')

@applications_bp.route('', methods=['POST'])
@jwt_required()
def submit_loan_application():
    """Permite a un usuario logueado enviar una solicitud de préstamo."""
    user_email = get_jwt_identity()
    user = User.query.filter_by(email=user_email).first()
    if not user:
        return jsonify({"msg": "Usuario no encontrado"}), 404

    data = request.get_json()
    try:
        product_id = int(data['product_id'])
        requested_amount = float(data['requested_amount'])
        requested_term = int(data['requested_term'])

        product = LoanProduct.query.get(product_id)
        if not product or not product.is_active:
            return jsonify({"msg": "Producto de préstamo no válido o inactivo."}), 400

        if not (product.min_amount <= requested_amount <= product.max_amount):
            return jsonify({"msg": f"El monto solicitado debe estar entre {product.min_amount} y {product.max_amount}."}), 400

        new_application = LoanApplication(
            user_id=user.id,
            product_id=product_id,
            requested_amount=requested_amount,
            requested_term=requested_term,
            status='Solicitud Recibida'
        )
        db.session.add(new_application)
        db.session.commit()
        return jsonify({"msg": "Solicitud de préstamo enviada exitosamente.", "application_id": new_application.id}), 201

    except (KeyError, ValueError):
        return jsonify({"msg": "Datos inválidos o incompletos."}), 400

@applications_bp.route('', methods=['GET'])
@jwt_required()
def get_loan_applications():
    """
    Obtiene las solicitudes de préstamo.
    - Clientes ven solo sus solicitudes.
    - Admins/Ejecutivos ven todas las solicitudes.
    """
    user_email = get_jwt_identity()
    claims = get_jwt()
    user_role = claims.get('role')

    if user_role in ['Administrador General', 'Ejecutivo de Crédito', 'Super Administrador']:
        applications = LoanApplication.query.order_by(LoanApplication.application_date.desc()).all()
    else:
        user = User.query.filter_by(email=user_email).first()
        if not user:
            return jsonify({"msg": "Usuario no encontrado"}), 404
        applications = LoanApplication.query.filter_by(user_id=user.id).order_by(LoanApplication.application_date.desc()).all()

    return jsonify([{
        "id": app.id,
        "applicant_email": app.applicant.email,
        "product_name": app.product.name,
        "requested_amount": app.requested_amount,
        "requested_term": app.requested_term,
        "status": app.status,
        "application_date": app.application_date.isoformat()
    } for app in applications])

@applications_bp.route('/<int:application_id>/status', methods=['PUT'])
@jwt_required()
@role_required('Administrador General')
def update_application_status(application_id):
    """
    Actualiza el estado de una solicitud de préstamo.
    Si el estado es 'Aprobada', crea un nuevo registro de Préstamo.
    """
    application = LoanApplication.query.get_or_404(application_id)
    data = request.get_json()

    new_status = data.get('status')
    if not new_status:
        return jsonify({"msg": "El campo 'status' es requerido."}), 400

    if application.status == 'Aprobada' and new_status == 'Aprobada':
        return jsonify({"msg": "Esta solicitud ya fue aprobada y tiene un préstamo asociado."}), 400

    application.status = new_status
    message = f"Estado de la solicitud {application_id} actualizado a '{new_status}'."

    if new_status == 'Aprobada':
        existing_loan = Loan.query.filter_by(application_id=application.id).first()
        if existing_loan:
            return jsonify({"msg": "Error: Ya existe un préstamo asociado a esta solicitud."}), 409

        product = application.product
        new_loan = Loan(
            application_id=application.id,
            loan_amount=application.requested_amount,
            interest_rate=product.default_interest_rate,
            term=application.requested_term,
            status='Activo'
        )
        db.session.add(new_loan)
        db.session.flush()
        message += f" Préstamo con ID {new_loan.id} creado exitosamente."

    db.session.commit()

    return jsonify({"msg": message})