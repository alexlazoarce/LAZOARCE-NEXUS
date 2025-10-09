from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from ..loan_calculator import generate_amortization_table
from ..extensions import db
from ..models import Loan, Payment

loans_bp = Blueprint('loans_bp', __name__, url_prefix='/api/loans')

@loans_bp.route('/simulate', methods=['POST'])
@jwt_required()
def simulate_loan():
    """Endpoint para simular un préstamo y obtener la tabla de amortización."""
    data = request.get_json()

    capital = data.get('capital_solicitado')
    meses = data.get('meses')
    tasa_interes = data.get('tasa_interes_mensual')

    if not all([capital, meses, tasa_interes]):
        return jsonify({"msg": "Los parámetros 'capital_solicitado', 'meses', y 'tasa_interes_mensual' son requeridos."}), 400

    try:
        capital = float(capital)
        meses = int(meses)
        tasa_interes = float(tasa_interes)
        com_admin = float(data.get('comision_administracion', 0))
        com_iniciales = float(data.get('comisiones_iniciales', 0))
    except (ValueError, TypeError):
        return jsonify({"msg": "Parámetros inválidos. Asegúrese de que los valores sean numéricos."}), 400

    commission_method = data.get('commission_method', 'no_interest')

    if commission_method not in ['no_interest', 'add_to_capital', 'subtract_from_capital']:
        return jsonify({"msg": "El valor de 'commission_method' no es válido."}), 400

    resultado = generate_amortization_table(
        capital_solicitado=capital,
        meses=meses,
        tasa_interes_mensual=tasa_interes,
        comision_administracion=com_admin,
        comisiones_iniciales=com_iniciales,
        commission_method=commission_method
    )

    if not resultado or not resultado.get("amortization_table"):
        return jsonify({"msg": "No se pudo generar la tabla de amortización con los parámetros proporcionados."}), 500

    return jsonify(resultado)

@loans_bp.route('/<int:loan_id>/payments', methods=['POST'])
@jwt_required()
def record_payment(loan_id):
    """Registra un nuevo pago para un préstamo específico."""
    loan = Loan.query.get_or_404(loan_id)

    if loan.status != 'Activo':
        return jsonify({"msg": f"No se pueden registrar pagos para un préstamo que no está 'Activo'. Estado actual: {loan.status}"}), 400

    data = request.get_json()
    amount = data.get('amount')
    payment_method = data.get('payment_method')

    if not amount or not isinstance(amount, (int, float)) or amount <= 0:
        return jsonify({"msg": "El campo 'amount' es requerido y debe ser un número positivo."}), 400

    new_payment = Payment(
        loan_id=loan_id,
        amount=float(amount),
        payment_method=payment_method
    )
    db.session.add(new_payment)
    db.session.commit()

    return jsonify({"msg": "Pago registrado exitosamente.", "payment_id": new_payment.id}), 201

@loans_bp.route('/<int:loan_id>/payments', methods=['GET'])
@jwt_required()
def get_payments_for_loan(loan_id):
    """Obtiene el historial de pagos para un préstamo específico."""
    loan = Loan.query.get_or_404(loan_id)

    payments = loan.payments.order_by(Payment.payment_date.desc()).all()

    return jsonify([{
        "id": p.id,
        "payment_date": p.payment_date.isoformat(),
        "amount": p.amount,
        "payment_method": p.payment_method
    } for p in payments])