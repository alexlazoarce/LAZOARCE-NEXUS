from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from ..extensions import db
from ..models import LoanProduct
from ..utils import role_required

products_bp = Blueprint('products_bp', __name__, url_prefix='/api/products')

@products_bp.route('', methods=['POST'])
@jwt_required()
@role_required('Administrador General')
def create_loan_product():
    """Crea un nuevo producto de préstamo."""
    data = request.get_json()
    try:
        new_product = LoanProduct(
            name=data['name'],
            loan_type=data['loan_type'],
            min_amount=float(data['min_amount']),
            max_amount=float(data['max_amount']),
            default_interest_rate=float(data['default_interest_rate']),
            default_admin_commission=float(data['default_admin_commission'])
        )
        db.session.add(new_product)
        db.session.commit()
        return jsonify({"msg": "Producto de préstamo creado exitosamente", "product_id": new_product.id}), 201
    except (KeyError, ValueError):
        return jsonify({"msg": "Datos inválidos o incompletos."}), 400

@products_bp.route('', methods=['GET'])
@jwt_required()
def get_loan_products():
    """Obtiene todos los productos de préstamo activos."""
    products = LoanProduct.query.filter_by(is_active=True).all()
    return jsonify([{
        "id": p.id, "name": p.name, "loan_type": p.loan_type,
        "min_amount": p.min_amount, "max_amount": p.max_amount,
        "default_interest_rate": p.default_interest_rate,
        "default_admin_commission": p.default_admin_commission
    } for p in products])

@products_bp.route('/<int:product_id>', methods=['PUT'])
@jwt_required()
@role_required('Administrador General')
def update_loan_product(product_id):
    """Actualiza un producto de préstamo existente."""
    product = LoanProduct.query.get_or_404(product_id)
    data = request.get_json()
    try:
        product.name = data.get('name', product.name)
        product.loan_type = data.get('loan_type', product.loan_type)
        product.min_amount = float(data.get('min_amount', product.min_amount))
        product.max_amount = float(data.get('max_amount', product.max_amount))
        product.default_interest_rate = float(data.get('default_interest_rate', product.default_interest_rate))
        product.default_admin_commission = float(data.get('default_admin_commission', product.default_admin_commission))
        db.session.commit()
        return jsonify({"msg": "Producto actualizado exitosamente."})
    except ValueError:
        return jsonify({"msg": "Datos inválidos."}), 400

@products_bp.route('/<int:product_id>', methods=['DELETE'])
@jwt_required()
@role_required('Administrador General')
def deactivate_loan_product(product_id):
    """Desactiva un producto de préstamo (soft delete)."""
    product = LoanProduct.query.get_or_404(product_id)
    product.is_active = False
    db.session.commit()
    return jsonify({"msg": "Producto desactivado exitosamente."})