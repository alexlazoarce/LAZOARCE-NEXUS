from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

from werkzeug.security import generate_password_hash, check_password_hash

# Initialize the database extension instance.
# This will be connected to the Flask app in the main app.py file.
db = SQLAlchemy()

# --- USER AND ROLE MODELS ---

class Role(db.Model):
    """
    Represents user roles (e.g., 'Admin', 'Contador', 'Cliente').
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    users = db.relationship('User', backref='role', lazy=True)

    def __repr__(self):
        return f'<Role {self.name}>'

class User(db.Model):
    """
    Represents a user of the system.
    """
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    dui = db.Column(db.String(20), nullable=True, unique=True)
    nit = db.Column(db.String(20), nullable=True, unique=True)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)
    loan_applications = db.relationship('LoanApplication', back_populates='applicant', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    employee_profile = db.relationship('Employee', backref='user', uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<User {self.email}>'

# --- HR & PAYROLL MODELS ---

class Employee(db.Model):
    """
    Stores employee-specific data, linked to a User account.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    position = db.Column(db.String(100), nullable=False)
    base_salary = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    payslips = db.relationship('PaySlip', backref='employee', lazy=True)

    def __repr__(self):
        return f'<Employee {self.user.full_name if self.user else self.id}>'

class PayrollLog(db.Model):
    """
    Represents a record of a payroll run for a specific period.
    """
    id = db.Column(db.Integer, primary_key=True)
    period_name = db.Column(db.String(100), nullable=False) # e.g., "Enero 2025"
    pay_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    creator = db.relationship('User', backref='created_payrolls')
    payslips = db.relationship('PaySlip', backref='payroll_log', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<PayrollLog {self.period_name}>'

class PaySlip(db.Model):
    """
    Stores the detailed calculation for a single employee for a single payroll period.
    """
    id = db.Column(db.Integer, primary_key=True)
    payroll_log_id = db.Column(db.Integer, db.ForeignKey('payroll_log.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)

    # Salary components
    gross_salary = db.Column(db.Float, nullable=False)

    # Deductions
    afp_employee = db.Column(db.Float, nullable=False)
    isss_employee = db.Column(db.Float, nullable=False)
    renta_tax = db.Column(db.Float, nullable=False)

    # Final amounts
    net_salary = db.Column(db.Float, nullable=False)

    # Employer contributions (for accounting purposes)
    afp_employer = db.Column(db.Float, nullable=False)
    isss_employer = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<PaySlip for Employee ID: {self.employee_id}>'

# --- LOAN MODELS ---

class LoanProduct(db.Model):
    """
    Defines a specific type of loan that the company offers.
    e.g., 'Personal Loan', 'Mortgage'
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    min_amount = db.Column(db.Float, nullable=False)
    max_amount = db.Column(db.Float, nullable=False)
    interest_rate = db.Column(db.Float, nullable=False) # Annual interest rate
    term_months = db.Column(db.Integer, nullable=False) # Default term in months
    # Defines how commission is calculated: 'A' (on principal), 'B' (on interest), 'C' (on principal + interest)
    commission_type = db.Column(db.String(1), default='A', nullable=False)
    admin_commission_rate = db.Column(db.Float, default=0.0, nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<LoanProduct {self.name}>'

class LoanApplication(db.Model):
    """
    Represents a loan application submitted by a user.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('loan_product.id'), nullable=False)
    requested_amount = db.Column(db.Float, nullable=False)
    requested_term = db.Column(db.Integer, nullable=False) # Term in months
    # Status can be 'Solicitud', 'Aprobado', 'Rechazado', 'Desembolsado'
    status = db.Column(db.String(50), default='Solicitud', nullable=False)
    application_date = db.Column(db.DateTime, default=datetime.utcnow)

    # Fields for signature tracking
    # PENDIENTE, EN_PROCESO_ELECTRONICO, FIRMADO_MANUAL, VALIDADO
    signature_status = db.Column(db.String(50), default='PENDIENTE', nullable=False)
    signed_document_url = db.Column(db.String(255), nullable=True)

    # Explicitly define the bidirectional relationship with User
    applicant = db.relationship('User', back_populates='loan_applications')
    product = db.relationship('LoanProduct')
    payments = db.relationship('Payment', backref='application', lazy='dynamic')

    def __repr__(self):
        return f'<LoanApplication ID: {self.id} - Status: {self.status}>'

class Payment(db.Model):
    """
    Represents a payment made towards a loan application.
    """
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('loan_application.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    # The user who recorded the payment (e.g., a collector or admin)
    recorded_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    recorder = db.relationship('User', backref=db.backref('recorded_payments', lazy=True))

    def __repr__(self):
        return f'<Payment ID: {self.id} for App ID: {self.application_id} - Amount: {self.amount}>'


# --- ACCOUNTING MODELS ---

class Account(db.Model):
    """
    Represents an account in the chart of accounts.
    e.g., '1101 - Caja', '4101 - Ingresos por Intereses'
    """
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    # Type can be 'Activo', 'Pasivo', 'Patrimonio', 'Ingreso', 'Gasto'
    account_type = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f'<Account {self.code} - {self.name}>'

class Transaction(db.Model):
    """
    Represents a single financial transaction, which groups multiple journal entries.
    e.g., "Disbursement of loan #123", "Payroll for Jan 2025"
    """
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    description = db.Column(db.String(255), nullable=False)
    # A transaction is the parent of multiple journal entries (debits/credits)
    entries = db.relationship('JournalEntry', backref='transaction', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Transaction {self.id} - {self.description}>'

class JournalEntry(db.Model):
    """
    Represents a single entry (a debit or a credit) in the accounting journal.
    Part of a double-entry bookkeeping system. Each entry belongs to a transaction.
    """
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    # For a balanced transaction, sum of debits must equal sum of credits across all its entries.
    debit = db.Column(db.Float, nullable=False, default=0.0)
    credit = db.Column(db.Float, nullable=False, default=0.0)

    # Relationship to easily get account details from an entry
    account = db.relationship('Account')

    def __repr__(self):
        return f'<JournalEntry {self.id} - Account: {self.account_id} Debit: {self.debit} Credit: {self.credit}>'