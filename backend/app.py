import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import create_access_token, JWTManager, jwt_required, get_jwt_identity, verify_jwt_in_request
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from functools import wraps
from datetime import datetime

# Módulos locales
from loan_calculator import generate_amortization_table

# Cargar variables de entorno
load_dotenv()

# Inicializar la aplicación de Flask
app = Flask(__name__)
CORS(app) # Habilitar CORS

# --- CONFIGURACIÓN ---
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'un-secreto-muy-seguro')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lazoarce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'otro-secreto-muy-seguro')

# --- INICIALIZACIÓN DE EXTENSIONES ---
db = SQLAlchemy(app)
jwt = JWTManager(app)

# --- MODELOS DE BASE DE DATOS ---
class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    users = db.relationship('User', backref='role', lazy=True)

    def __repr__(self):
        return f'<Role {self.name}>'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)
    loan_applications = db.relationship('LoanApplication', backref='applicant', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email}>'

class LoanProduct(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    loan_type = db.Column(db.String(50), nullable=False) # 'Personal', 'Grupal', etc.
    min_amount = db.Column(db.Float, nullable=False)
    max_amount = db.Column(db.Float, nullable=False)
    default_interest_rate = db.Column(db.Float, nullable=False) # Tasa mensual
    default_admin_commission = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    applications = db.relationship('LoanApplication', backref='product', lazy=True)

    def __repr__(self):
        return f'<LoanProduct {self.name}>'

class LoanApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('loan_product.id'), nullable=False)
    requested_amount = db.Column(db.Float, nullable=False)
    requested_term = db.Column(db.Integer, nullable=False) # En meses
    status = db.Column(db.String(50), default='Solicitud', nullable=False) # Solicitud, Análisis, Aprobación, etc.
    application_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<LoanApplication ID: {self.id} - Status: {self.status}>'


# --- DECORADORES DE AUTORIZACIÓN ---
def role_required(required_role):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user_email = get_jwt_identity()
            user = User.query.filter_by(email=user_email).first()
            if not user or user.role.name != required_role:
                return jsonify({"msg": "Acceso no autorizado para este rol"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


# --- RUTAS DE LA API ---
@app.route('/')
def index():
    return jsonify({"message": "Servidor del Sistema de Gestión Financiera en funcionamiento."})

@app.route('/api/register', methods=['POST'])
def register():
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

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify({"msg": "Email y contraseña son requeridos"}), 400
    user = User.query.filter_by(email=email).first()
    if user and user.check_password(password):
        access_token = create_access_token(identity=user.email)
        return jsonify(access_token=access_token)
    return jsonify({"msg": "Credenciales inválidas"}), 401

@app.route('/api/admin/test')
@jwt_required()
@role_required('Administrador General')
def admin_test_route():
    user_email = get_jwt_identity()
    return jsonify(logged_in_as=user_email), 200


# --- API PARA PRODUCTOS DE PRÉSTAMO (CRUD - Solo Admin) ---
@app.route('/api/products', methods=['POST'])
@jwt_required()
@role_required('Administrador General')
def create_loan_product():
    data = request.get_json()
    try:
        new_product = LoanProduct(name=data['name'], loan_type=data['loan_type'], min_amount=float(data['min_amount']), max_amount=float(data['max_amount']), default_interest_rate=float(data['default_interest_rate']), default_admin_commission=float(data['default_admin_commission']))
        db.session.add(new_product)
        db.session.commit()
        return jsonify({"msg": "Producto de préstamo creado exitosamente", "product_id": new_product.id}), 201
    except (KeyError, ValueError):
        return jsonify({"msg": "Datos inválidos o incompletos."}), 400

@app.route('/api/products', methods=['GET'])
@jwt_required()
def get_loan_products():
    products = LoanProduct.query.filter_by(is_active=True).all()
    return jsonify([{"id": p.id, "name": p.name, "loan_type": p.loan_type, "min_amount": p.min_amount, "max_amount": p.max_amount, "default_interest_rate": p.default_interest_rate, "default_admin_commission": p.default_admin_commission} for p in products])

@app.route('/api/products/<int:product_id>', methods=['PUT'])
@jwt_required()
@role_required('Administrador General')
def update_loan_product(product_id):
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

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
@jwt_required()
@role_required('Administrador General')
def deactivate_loan_product(product_id):
    product = LoanProduct.query.get_or_404(product_id)
    product.is_active = False
    db.session.commit()
    return jsonify({"msg": "Producto desactivado exitosamente."})


# --- API PARA SOLICITUDES DE PRÉSTAMO ---
@app.route('/api/applications', methods=['POST'])
@jwt_required()
def submit_loan_application():
    user_email = get_jwt_identity()
    user = User.query.filter_by(email=user_email).first_or_404()
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
        new_application = LoanApplication(user_id=user.id, product_id=product_id, requested_amount=requested_amount, requested_term=requested_term, status='Solicitud Recibida')
        db.session.add(new_application)
        db.session.commit()
        return jsonify({"msg": "Solicitud de préstamo enviada exitosamente.", "application_id": new_application.id}), 201
    except (KeyError, ValueError):
        return jsonify({"msg": "Datos inválidos o incompletos."}), 400

@app.route('/api/applications', methods=['GET'])
@jwt_required()
def get_loan_applications():
    user_email = get_jwt_identity()
    user = User.query.filter_by(email=user_email).first_or_404()
    if user.role.name in ['Administrador General', 'Ejecutivo de Crédito', 'Super Administrador']:
        applications = LoanApplication.query.order_by(LoanApplication.application_date.desc()).all()
    else:
        applications = LoanApplication.query.filter_by(user_id=user.id).order_by(LoanApplication.application_date.desc()).all()
    return jsonify([{"id": app.id, "applicant_email": app.applicant.email, "product_name": app.product.name, "requested_amount": app.requested_amount, "requested_term": app.requested_term, "status": app.status, "application_date": app.application_date.isoformat()} for app in applications])

@app.route('/api/applications/<int:application_id>/status', methods=['PUT'])
@jwt_required()
@role_required('Administrador General')
def update_application_status(application_id):
    application = LoanApplication.query.get_or_404(application_id)
    data = request.get_json()
    new_status = data.get('status')
    if not new_status:
        return jsonify({"msg": "El campo 'status' es requerido."}), 400
    application.status = new_status
    db.session.commit()
    return jsonify({"msg": f"Estado de la solicitud {application_id} actualizado a '{new_status}'."})


@app.route('/api/loans/simulate', methods=['POST'])
@jwt_required()
def simulate_loan():
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
    resultado = generate_amortization_table(capital_solicitado=capital, meses=meses, tasa_interes_mensual=tasa_interes, comision_administracion=com_admin, comisiones_iniciales=com_iniciales, commission_method=commission_method)
    if not resultado or not resultado.get("amortization_table"):
        return jsonify({"msg": "No se pudo generar la tabla de amortización con los parámetros proporcionados."}), 500
    return jsonify(resultado)


# --- FUNCIONES AUXILIARES ---
def initialize_database():
    with app.app_context():
        db.create_all()
        if Role.query.first() is None:
            roles = ['Super Administrador', 'Administrador General', 'Ejecutivo de Crédito', 'Cobrador', 'Contador', 'Cliente']
            for role_name in roles:
                db.session.add(Role(name=role_name))
            db.session.commit()
            print("Base de datos y roles inicializados.")

if __name__ == '__main__':
    initialize_database()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)