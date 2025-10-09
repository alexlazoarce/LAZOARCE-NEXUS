import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import create_access_token, JWTManager, jwt_required, get_jwt_identity, verify_jwt_in_request
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from functools import wraps
from datetime import datetime
from io import BytesIO
from flask import make_response

# Módulos locales
from loan_calculator import generate_amortization_table
from pdf_generator import create_contract_pdf
# Los servicios se importarán localmente para evitar dependencias circulares

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
    def __repr__(self): return f'<Role {self.name}>'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)
    full_name = db.Column(db.String(120), nullable=True)
    dui = db.Column(db.String(20), nullable=True, unique=True)
    nit = db.Column(db.String(20), nullable=True, unique=True)
    loan_applications = db.relationship('LoanApplication', backref='applicant', lazy=True)
    employee_profile = db.relationship('Employee', backref='user', uselist=False, cascade="all, delete-orphan")
    def set_password(self, password): self.password_hash = generate_password_hash(password)
    def check_password(self, password): return check_password_hash(self.password_hash, password)
    def __repr__(self): return f'<User {self.email}>'

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    position = db.Column(db.String(100), nullable=False)
    base_salary = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    payslips = db.relationship('PaySlip', backref='employee', lazy=True)
    def __repr__(self): return f'<Employee {self.user.full_name}>'

class LoanProduct(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    loan_type = db.Column(db.String(50), nullable=False)
    min_amount = db.Column(db.Float, nullable=False)
    max_amount = db.Column(db.Float, nullable=False)
    default_interest_rate = db.Column(db.Float, nullable=False)
    default_admin_commission = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    applications = db.relationship('LoanApplication', backref='product', lazy=True)
    def __repr__(self): return f'<LoanProduct {self.name}>'

class LoanApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('loan_product.id'), nullable=False)
    requested_amount = db.Column(db.Float, nullable=False)
    requested_term = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), default='Solicitud', nullable=False)
    application_date = db.Column(db.DateTime, default=datetime.utcnow)
    payments = db.relationship('Payment', backref='application', lazy=True)
    def __repr__(self): return f'<LoanApplication ID: {self.id} - Status: {self.status}>'

class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    account_type = db.Column(db.String(50), nullable=False)
    def __repr__(self): return f'<Account {self.code} - {self.name}>'

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    description = db.Column(db.String(255), nullable=False)
    entries = db.relationship('JournalEntry', backref='transaction', lazy=True, cascade="all, delete-orphan")

class JournalEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    debit = db.Column(db.Float, nullable=False, default=0.0)
    credit = db.Column(db.Float, nullable=False, default=0.0)
    account = db.relationship('Account')

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('loan_application.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    payment_method = db.Column(db.String(50), nullable=False, default='Deposito')
    recorded_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recorder = db.relationship('User')
    def __repr__(self): return f'<Payment ID: {self.id} - Amount: {self.amount} ({self.payment_method})>'

class PayrollLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    period_name = db.Column(db.String(100), nullable=False)
    pay_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    creator = db.relationship('User')
    payslips = db.relationship('PaySlip', backref='payroll_log', lazy=True, cascade="all, delete-orphan")
    def __repr__(self): return f'<PayrollLog {self.period_name}>'

class PaySlip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    payroll_log_id = db.Column(db.Integer, db.ForeignKey('payroll_log.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    gross_salary = db.Column(db.Float, nullable=False)
    afp_employee = db.Column(db.Float, nullable=False)
    isss_employee = db.Column(db.Float, nullable=False)
    renta_tax = db.Column(db.Float, nullable=False)
    net_salary = db.Column(db.Float, nullable=False)
    afp_employer = db.Column(db.Float, nullable=False)
    isss_employer = db.Column(db.Float, nullable=False)
    def __repr__(self): return f'<PaySlip for Employee ID: {self.employee_id} - Period: {self.payroll_log.period_name}>'

# --- DECORADORES ---
def role_required(required_roles):
    if not isinstance(required_roles, list): required_roles = [required_roles]
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user = User.query.filter_by(email=get_jwt_identity()).first()
            if not user or user.role.name not in required_roles:
                return jsonify({"msg": "Acceso no autorizado para este rol"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator

# --- RUTAS DE LA API ---
@app.route('/api/applications/<int:application_id>/status', methods=['PUT'])
@jwt_required()
@role_required('Administrador General')
def update_application_status(application_id):
    from accounting_service import create_journal_entry
    application = LoanApplication.query.get_or_404(application_id)
    data = request.get_json()
    new_status = data.get('status')
    if not new_status:
        return jsonify({"msg": "El campo 'status' es requerido."}), 400
    original_status = application.status
    if original_status == new_status:
        return jsonify({"msg": f"La solicitud ya se encuentra en el estado '{new_status}'."})
    application.status = new_status
    if new_status == 'Desembolsado':
        try:
            entries = [{'account_code': '1201', 'debit': application.requested_amount, 'credit': 0}, {'account_code': '1102', 'debit': 0, 'credit': application.requested_amount}]
            description = f"Desembolso de prestamo ID: {application.id}"
            create_journal_entry(description, entries)
            print(f"Asiento de diario creado para el desembolso del prestamo {application.id}")
        except Exception as e:
            db.session.rollback()
            return jsonify({"msg": f"Error al crear el asiento contable: {str(e)}"}), 500
    db.session.commit()
    return jsonify({"msg": f"Estado de la solicitud {application_id} actualizado a '{new_status}'."})

@app.route('/api/applications/<int:application_id>/payments', methods=['POST'])
@jwt_required()
@role_required(['Cobrador', 'Administrador General'])
def record_payment(application_id):
    from accounting_service import create_journal_entry
    application = LoanApplication.query.get_or_404(application_id)
    user_email = get_jwt_identity()
    recorder = User.query.filter_by(email=user_email).first_or_404()
    data = request.get_json()
    amount = data.get('amount')
    payment_method = data.get('payment_method', 'Deposito')
    if not amount or not isinstance(amount, (int, float)) or amount <= 0:
        return jsonify({"msg": "Se requiere un monto de pago válido."}), 400
    if payment_method not in ['Efectivo', 'Deposito']:
        return jsonify({"msg": "El método de pago no es válido."}), 400
    debit_account_code = '1101' if payment_method == 'Efectivo' else '1102'
    try:
        new_payment = Payment(application_id=application.id, amount=amount, payment_method=payment_method, recorded_by_user_id=recorder.id)
        db.session.add(new_payment)
        entries = [{'account_code': debit_account_code, 'debit': amount, 'credit': 0}, {'account_code': '1201', 'debit': 0, 'credit': amount}]
        description = f"Pago de {payment_method} recibido para prestamo ID: {application.id}"
        create_journal_entry(description, entries)
        db.session.commit()
        print(f"Pago de ${amount} ({payment_method}) registrado para el prestamo {application.id}")
        return jsonify({"msg": "Pago registrado exitosamente."}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": f"Error al registrar el pago: {str(e)}"}), 500

@app.route('/api/payroll/calculate', methods=['POST'])
@jwt_required()
@role_required('Administrador General')
def run_payroll_calculation():
    from payroll_service import calculate_payslip_details
    user_email = get_jwt_identity()
    creator = User.query.filter_by(email=user_email).first_or_404()
    data = request.get_json()
    period_name = data.get('period_name')
    if not period_name:
        return jsonify({"msg": "El nombre del período es requerido."}), 400
    try:
        payroll_log = PayrollLog(period_name=period_name, created_by_user_id=creator.id)
        db.session.add(payroll_log)
        employees = Employee.query.filter_by(is_active=True).all()
        for emp in employees:
            payslip_details = calculate_payslip_details(emp.base_salary)
            new_payslip = PaySlip(payroll_log=payroll_log, employee_id=emp.id, **payslip_details)
            db.session.add(new_payslip)
        db.session.commit()
        return jsonify({"msg": f"Planilla '{period_name}' calculada exitosamente para {len(employees)} empleados.", "payroll_log_id": payroll_log.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": f"Error al calcular la planilla: {str(e)}"}), 500

# ... (el resto de las rutas y el código de inicialización permanece igual) ...
# (Se omite por brevedad, pero está presente en el archivo real)
if __name__ == '__main__':
    # ... (código de inicialización) ...
    pass