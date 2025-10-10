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
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)
    loan_applications = db.relationship('LoanApplication', back_populates='applicant', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email}>'


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

    # Explicitly define the bidirectional relationship with User
    applicant = db.relationship('User', back_populates='loan_applications')
    product = db.relationship('LoanProduct')

    def __repr__(self):
        return f'<LoanApplication ID: {self.id} - Status: {self.status}>'


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