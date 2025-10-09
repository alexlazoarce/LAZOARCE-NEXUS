from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import db

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
    profile = db.relationship('ClientProfile', backref='user', uselist=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email}>'

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

    def __repr__(self):
        return f'<LoanProduct {self.name}>'

class LoanApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('loan_product.id'), nullable=False)
    requested_amount = db.Column(db.Float, nullable=False)
    requested_term = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), default='Solicitud', nullable=False)
    application_date = db.Column(db.DateTime, default=datetime.utcnow)
    loan = db.relationship('Loan', backref='application', uselist=False, lazy=True)

    def __repr__(self):
        return f'<LoanApplication ID: {self.id} - Status: {self.status}>'

class ClientProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    full_name = db.Column(db.String(150), nullable=False)
    phone_number = db.Column(db.String(20))
    address = db.Column(db.String(250))

    def __repr__(self):
        return f'<ClientProfile for User ID: {self.user_id}>'

class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('loan_application.id'), nullable=False, unique=True)
    loan_amount = db.Column(db.Float, nullable=False)
    interest_rate = db.Column(db.Float, nullable=False)
    term = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), default='Activo', nullable=False)
    disbursement_date = db.Column(db.DateTime, default=datetime.utcnow)
    payments = db.relationship('Payment', backref='loan', lazy='dynamic')

    def __repr__(self):
        return f'<Loan ID: {self.id} - Status: {self.status}>'

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.Integer, db.ForeignKey('loan.id'), nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50))

    def __repr__(self):
        return f'<Payment ID: {self.id} for Loan ID: {self.loan_id}>'