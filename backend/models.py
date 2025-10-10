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

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email}>'


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