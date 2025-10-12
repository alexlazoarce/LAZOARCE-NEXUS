from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import db

# --- MODELOS PRINCIPALES ---
class Role(db.Model):
    __tablename__ = 'role'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    users = db.relationship('User', backref='role', lazy=True)

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)
    loan_applications = db.relationship('LoanApplication', backref='applicant', lazy=True)
    profile = db.relationship('ClientProfile', backref='user', uselist=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class ClientProfile(db.Model):
    __tablename__ = 'client_profile'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    full_name = db.Column(db.String(150), nullable=False)
    phone_number = db.Column(db.String(20))
    address = db.Column(db.String(250))

class LoanProduct(db.Model):
    __tablename__ = 'loan_product'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    min_amount = db.Column(db.Float, nullable=False)
    max_amount = db.Column(db.Float, nullable=False)
    default_interest_rate = db.Column(db.Float, nullable=False)
    applications = db.relationship('LoanApplication', backref='product', lazy=True)

class LoanApplication(db.Model):
    __tablename__ = 'loan_application'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('loan_product.id'), nullable=False)
    requested_amount = db.Column(db.Float, nullable=False)
    requested_term = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), default='Solicitud', nullable=False)
    application_date = db.Column(db.DateTime, default=datetime.utcnow)
    loan = db.relationship('Loan', backref='application', uselist=False)

class Loan(db.Model):
    __tablename__ = 'loan'
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('loan_application.id'), nullable=False, unique=True)
    loan_amount = db.Column(db.Float, nullable=False)
    interest_rate = db.Column(db.Float, nullable=False)
    term = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), default='Aprobado', nullable=False)
    payments = db.relationship('Payment', backref='loan', lazy='dynamic')

class Payment(db.Model):
    __tablename__ = 'payment'
    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.Integer, db.ForeignKey('loan.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)

# --- MODELOS CONTABLES ---
class ChartOfAccounts(db.Model):
    __tablename__ = 'chart_of_accounts'
    id = db.Column(db.Integer, primary_key=True)
    account_code = db.Column(db.String(20), unique=True, nullable=False)
    account_name = db.Column(db.String(200), nullable=False)
    account_type = db.Column(db.String(50), nullable=False)
    account_class = db.Column(db.String(100), nullable=False)
    balance = db.Column(db.Float, default=0.0)

class AccountingEntry(db.Model):
    __tablename__ = 'accounting_entry'
    id = db.Column(db.Integer, primary_key=True)
    entry_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    description = db.Column(db.String(500), nullable=False)
    reference = db.Column(db.String(100))
    loan_id = db.Column(db.Integer, db.ForeignKey('loan.id'))
    payment_id = db.Column(db.Integer, db.ForeignKey('payment.id'))
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    details = db.relationship('EntryDetail', backref='entry', lazy='dynamic', cascade="all, delete-orphan")

class EntryDetail(db.Model):
    __tablename__ = 'entry_detail'
    id = db.Column(db.Integer, primary_key=True)
    entry_id = db.Column(db.Integer, db.ForeignKey('accounting_entry.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('chart_of_accounts.id'), nullable=False)
    debit = db.Column(db.Float, default=0.0)
    credit = db.Column(db.Float, default=0.0)
    account = db.relationship('ChartOfAccounts')

# --- IMPORTAR MODELOS MODULARES ---
from backend.hr.models import Empleado, PrestamoEmpleado, Nomina