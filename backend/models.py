from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    users = db.relationship('User', backref='role', lazy=True)

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
    recorded_payments = db.relationship('Payment', backref='recorder', lazy=True, foreign_keys='Payment.recorded_by_user_id')
    created_payrolls = db.relationship('PayrollLog', backref='creator', lazy=True, foreign_keys='PayrollLog.created_by_user_id')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    position = db.Column(db.String(100), nullable=False)
    base_salary = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    payslips = db.relationship('PaySlip', backref='employee', lazy=True)

class PayrollLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    period_name = db.Column(db.String(100), nullable=False)
    pay_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    payslips = db.relationship('PaySlip', backref='payroll_log', lazy=True, cascade="all, delete-orphan")

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

class LoanProduct(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    min_amount = db.Column(db.Float, nullable=False)
    max_amount = db.Column(db.Float, nullable=False)
    interest_rate = db.Column(db.Float, nullable=False)
    term_months = db.Column(db.Integer, nullable=False)
    commission_type = db.Column(db.String(1), default='A', nullable=False)
    admin_commission_rate = db.Column(db.Float, default=0.0, nullable=False)
    is_active = db.Column(db.Boolean, default=True)

class LoanApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('loan_product.id'), nullable=False)
    requested_amount = db.Column(db.Float, nullable=False)
    requested_term = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), default='Solicitud', nullable=False)
    application_date = db.Column(db.DateTime, default=datetime.utcnow)
    signature_status = db.Column(db.String(50), default='PENDIENTE', nullable=False)
    signed_document_url = db.Column(db.String(255), nullable=True)

    product = db.relationship('LoanProduct')
    payments = db.relationship('Payment', backref='application', lazy='dynamic')

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('loan_application.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    recorded_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    account_type = db.Column(db.String(50), nullable=False)

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