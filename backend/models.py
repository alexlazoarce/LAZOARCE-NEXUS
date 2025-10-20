from flask_sqlalchemy import SQLAlchemy

from werkzeug.security import generate_password_hash, check_password_hash

from datetime import datetime, date

from sqlalchemy import func, Boolean, DateTime, Float, Integer, String, Text

from sqlalchemy.orm import relationship, backref

from sqlalchemy import ForeignKey

# Inicializar SQLAlchemy

db = SQLAlchemy()

# Tabla intermedia para relaciones many-to-many

mailing_list_members = db.Table('mailing_list_members',

    db.Column('mailing_list_id', Integer, ForeignKey('mailing_list.id'), primary_key=True),

    db.Column('user_id', Integer, ForeignKey('user.id'), primary_key=True)

)

# Tabla intermedia para roles de usuario (many-to-many)

user_roles = db.Table('user_roles',

    db.Column('user_id', Integer, ForeignKey('user.id'), primary_key=True),

    db.Column('role_id', Integer, ForeignKey('role.id'), primary_key=True)

)

# --- MODELOS DE SEGURIDAD Y USUARIOS ---

class Role(db.Model):

    __tablename__ = 'role'

    

    id = db.Column(Integer, primary_key=True)

    name = db.Column(String(80), unique=True, nullable=False, index=True)

    

    # Relaciones

    users = db.relationship('User', secondary=user_roles, back_populates='roles')

    

    def __repr__(self):

        return f'<Role {self.name}>'

    

    def to_dict(self):

        return {'id': self.id, 'name': self.name}

class User(db.Model):

    __tablename__ = 'user'

    

    id = db.Column(Integer, primary_key=True)

    email = db.Column(String(120), unique=True, nullable=False, index=True)

    password_hash = db.Column(String(256), nullable=False)

    full_name = db.Column(String(120), nullable=True)

    dui = db.Column(String(20), unique=True, nullable=True)

    nit = db.Column(String(20), unique=True, nullable=True)

    is_active = db.Column(Boolean, default=True)

    last_login = db.Column(DateTime)

    

    # Relaciones

    role_id = db.Column(Integer, ForeignKey('role.id'), nullable=False)  # Rol principal

    roles = db.relationship('Role', secondary=user_roles, back_populates='users')  # Roles adicionales

    profile = db.relationship('ClientProfile', backref='user', uselist=False)

    applications = db.relationship('LoanApplication', backref='applicant', lazy=True)

    communication_logs = db.relationship('CommunicationLog', backref='user', lazy='dynamic')

    audit_logs = db.relationship('AuditLog', backref='user', lazy='dynamic')

    tickets = db.relationship('Ticket', foreign_keys='[Ticket.user_id]', backref='created_by_user', lazy='dynamic')

    subscriptions = db.relationship('Subscription', backref='user', lazy=True)

    mailing_lists = db.relationship('MailingList', secondary=mailing_list_members, lazy='dynamic', 

                                   backref=db.backref('members', lazy=True))

    

    # Métodos de seguridad

    def set_password(self, password):

        self.password_hash = generate_password_hash(password)

    

    def check_password(self, password):

        return check_password_hash(self.password_hash, password)

    

    @property

    def role(self):

        return Role.query.get(self.role_id)

    

    def has_role(self, *role_names):

        """Verifica si el usuario tiene alguno de los roles especificados"""

        return any(role.name in role_names for role in self.roles) or self.role.name in role_names

    

    def to_dict(self):

        return {

            'id': self.id,

            'email': self.email,

            'full_name': self.full_name,

            'dui': self.dui,

            'nit': self.nit,

            'is_active': self.is_active,

            'roles': [role.name for role in self.roles],

            'primary_role': self.role.name if self.role else None

        }

    

    def __repr__(self):

        return f'<User {self.email}>'

class ClientProfile(db.Model):

    __tablename__ = 'client_profile'

    

    id = db.Column(Integer, primary_key=True)

    user_id = db.Column(Integer, ForeignKey('user.id'), unique=True, nullable=False)

    full_name = db.Column(String(120))

    phone_number = db.Column(String(20))

    address = db.Column(Text)

    birth_date = db.Column(Date)

    

    def to_dict(self):

        return {

            'id': self.id,

            'full_name': self.full_name,

            'phone_number': self.phone_number,

            'address': self.address,

            'birth_date': self.birth_date.isoformat() if self.birth_date else None

        }

# --- MODELOS DE PRÉSTAMOS ---

class LoanProduct(db.Model):

    __tablename__ = 'loan_product'

    

    id = db.Column(Integer, primary_key=True)

    name = db.Column(String(100), unique=True, nullable=False, index=True)

    min_amount = db.Column(Float, nullable=False, default=0.0)

    max_amount = db.Column(Float, nullable=False, default=0.0)

    interest_rate = db.Column(Float, nullable=False, default=0.0)  # Tasa anual %

    commission_rate = db.Column(Float, nullable=False, default=0.01)

    term_months = db.Column(Integer, nullable=False, default=12)

    is_active = db.Column(Boolean, default=True)

    

    # Campos avanzados de cálculo

    comision_apertura = db.Column(Float, default=0.0)

    comision_administracion = db.Column(Float, default=0.0)

    seguro = db.Column(Float, default=0.0)

    comisiones_se_descuentan_capital = db.Column(Boolean, default=True)

    aplicar_tea = db.Column(Boolean, default=True)

    

    # Timestamps

    created_at = db.Column(DateTime, default=func.current_timestamp())

    updated_at = db.Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())

    

    # Relaciones

    applications = db.relationship('LoanApplication', backref='product', lazy=True)

    

    def to_dict(self):

        return {

            'id': self.id,

            'name': self.name,

            'min_amount': self.min_amount,

            'max_amount': self.max_amount,

            'interest_rate': self.interest_rate,

            'commission_rate': self.commission_rate,

            'term_months': self.term_months,

            'is_active': self.is_active,

            **{k: v for k, v in self.__dict__.items() if k.startswith('comision_') or k.startswith('seguro')}

        }

    

    def __repr__(self):

        return f'<LoanProduct {self.name}>'

class LoanApplication(db.Model):

    __tablename__ = 'loan_application'

    

    id = db.Column(Integer, primary_key=True)

    user_id = db.Column(Integer, ForeignKey('user.id'), nullable=False, index=True)

    product_id = db.Column(Integer, ForeignKey('loan_product.id'), nullable=False, index=True)

    

    amount_requested = db.Column(Float, nullable=False)

    term_months = db.Column(Integer, nullable=False)

    commission_calculation_method = db.Column(String(1), default='A')  # A, B, C

    

    # Campos calculados

    monthly_payment = db.Column(Float, nullable=True)

    total_payment = db.Column(Float, nullable=True)

    tea_calculada = db.Column(Float, nullable=True)

    

    status = db.Column(String(20), nullable=False, default='Pendiente', index=True)

    

    # Timestamps

    application_date = db.Column(DateTime, default=func.current_timestamp(), index=True)

    decision_date = db.Column(DateTime, nullable=True)

    

    # Relación contable

    disbursement_entry_id = db.Column(Integer, ForeignKey('journal_entry.id'), nullable=True)

    disbursement_entry = db.relationship('JournalEntry', foreign_keys=[disbursement_entry_id])

    

    # Relaciones

    payments = db.relationship('Payment', backref='application', lazy='dynamic', 

                              cascade="all, delete-orphan")

    

    def to_dict(self):

        return {

            'id': self.id,

            'user_id': self.user_id,

            'applicant_name': self.applicant.full_name if self.applicant else None,

            'product_id': self.product_id,

            'product_name': self.product.name if self.product else None,

            'amount_requested': self.amount_requested,

            'term_months': self.term_months,

            'status': self.status,

            'monthly_payment': self.monthly_payment,

            'total_payment': self.total_payment,

            'application_date': self.application_date.isoformat() if self.application_date else None,

            'decision_date': self.decision_date.isoformat() if self.decision_date else None

        }

    

    def __repr__(self):

        return f'<LoanApplication {self.id} - {self.status}>'

# --- MODELOS CONTABLES ---

class Account(db.Model):

    __tablename__ = 'account'

    

    id = db.Column(Integer, primary_key=True)

    account_code = db.Column(String(20), unique=True, nullable=False, index=True)

    name = db.Column(String(100), unique=True, nullable=False)

    category = db.Column(String(50), nullable=False)  # Asset, Liability, Equity, Revenue, Expense

    normal_balance = db.Column(String(10), nullable=False)  # Debit, Credit

    account_type = db.Column(String(50))

    account_class = db.Column(String(100))

    is_active = db.Column(Boolean, default=True)

    

    # Relaciones

    transactions = db.relationship('Transaction', backref='account', lazy=True)

    

    def to_dict(self):

        return {

            'id': self.id,

            'account_code': self.account_code,

            'name': self.name,

            'category': self.category,

            'normal_balance': self.normal_balance,

            'is_active': self.is_active

        }

    

    def __repr__(self):

        return f'<Account {self.account_code} - {self.name}>'

class JournalEntry(db.Model):

    __tablename__ = 'journal_entry'

    

    id = db.Column(Integer, primary_key=True)

    date = db.Column(DateTime, default=func.current_timestamp(), index=True)

    description = db.Column(String(500), nullable=False)

    reference = db.Column(String(100))

    created_by_id = db.Column(Integer, ForeignKey('user.id'))

    

    # Relaciones

    transactions = db.relationship('Transaction', backref='journal_entry', 

                                  lazy='dynamic', cascade="all, delete-orphan")

    created_by = db.relationship('User')

    

    @property

    def total_debit(self):

        return sum(t.amount for t in self.transactions if t.type == 'Debit')

    

    @property

    def total_credit(self):

        return sum(t.amount for t in self.transactions if t.type == 'Credit')

    

    @property

    def is_balanced(self):

        return self.total_debit == self.total_credit

    

    def to_dict(self):

        return {

            'id': self.id,

            'date': self.date.isoformat() if self.date else None,

            'description': self.description,

            'reference': self.reference,

            'total_debit': self.total_debit,

            'total_credit': self.total_credit,

            'is_balanced': self.is_balanced,

            'transactions': [t.to_dict() for t in self.transactions.all()]

        }

class Transaction(db.Model):

    __tablename__ = 'transaction'

    

    id = db.Column(Integer, primary_key=True)

    journal_entry_id = db.Column(Integer, ForeignKey('journal_entry.id'), nullable=False, index=True)

    account_id = db.Column(Integer, ForeignKey('account.id'), nullable=False, index=True)

    type = db.Column(String(10), nullable=False)  # Debit, Credit

    amount = db.Column(Float, nullable=False, default=0.0)

    

    def to_dict(self):

        return {

            'id': self.id,

            'account_code': self.account.account_code if self.account else None,

            'account_name': self.account.name if self.account else None,

            'type': self.type,

            'amount': self.amount

        }

    

    def __repr__(self):

        return f'<Transaction {self.id} - {self.type} {self.amount}>'

# --- MODELOS DE RECURSOS HUMANOS ---

class Employee(db.Model):

    __tablename__ = 'employee'

    

    id = db.Column(Integer, primary_key=True)

    full_name = db.Column(String(120), nullable=False, index=True)

    employee_type = db.Column(String(20), default='interno')  # interno, temporal

    position = db.Column(String(100))

    salary = db.Column(Float, default=0.0)

    hire_date = db.Column(Date, nullable=True)

    termination_date = db.Column(Date, nullable=True)

    is_active = db.Column(Boolean, default=True)

    

    # Datos legales (El Salvador)

    dui = db.Column(String(20), unique=True)

    nit = db.Column(String(20), unique=True)

    isss_number = db.Column(String(20), unique=True)

    afp_number = db.Column(String(20), unique=True)

    

    # Relaciones

    payslips = db.relationship('PaySlip', backref='employee', lazy=True)

    payments_registered = db.relationship('Payment', foreign_keys='Payment.registered_by_id', 

                                         backref='registered_by', lazy='dynamic')

    assignments = db.relationship('TemporaryAssignment', backref='employee', lazy='dynamic')

    communication_logs = db.relationship('CommunicationLog', foreign_keys='CommunicationLog.employee_id', 

                                        backref='employee', lazy='dynamic')

    

    def to_dict(self):

        return {

            'id': self.id,

            'full_name': self.full_name,

            'employee_type': self.employee_type,

            'position': self.position,

            'salary': self.salary,

            'hire_date': self.hire_date.isoformat() if self.hire_date else None,

            'is_active': self.is_active,

            'dui': self.dui,

            'nit': self.nit

        }

    

    def __repr__(self):

        return f'<Employee {self.full_name}>'

# --- MODELOS CRM ---

class Lead(db.Model):

    __tablename__ = 'lead'

    

    id = db.Column(Integer, primary_key=True)

    full_name = db.Column(String(120), nullable=False, index=True)

    email = db.Column(String(120))

    phone = db.Column(String(20))

    status = db.Column(String(50), default='Nuevo', index=True)

    source = db.Column(String(100))

    notes = db.Column(Text)

    

    created_at = db.Column(DateTime, default=func.current_timestamp(), index=True)

    updated_at = db.Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())

    

    # Relaciones

    communication_logs = db.relationship('CommunicationLog', backref='lead', lazy='dynamic')

    opportunities = db.relationship('Opportunity', backref='lead', lazy=True)

    

    def to_dict(self):

        return {

            'id': self.id,

            'full_name': self.full_name,

            'email': self.email,

            'phone': self.phone,

            'status': self.status,

            'source': self.source,

            'notes': self.notes,

            'created_at': self.created_at.isoformat() if self.created_at else None

        }

class CommunicationLog(db.Model):

    __tablename__ = 'communication_log'

    

    id = db.Column(Integer, primary_key=True)

    lead_id = db.Column(Integer, ForeignKey('lead.id'), nullable=True)

    user_id = db.Column(Integer, ForeignKey('user.id'), nullable=True)

    employee_id = db.Column(Integer, ForeignKey('employee.id'), nullable=False)

    

    type = db.Column(String(50), nullable=False)  # Llamada, Email, WhatsApp, Reunión

    notes = db.Column(Text, nullable=False)

    duration_minutes = db.Column(Integer, default=0)

    

    timestamp = db.Column(DateTime, default=func.current_timestamp(), index=True)

    

    def to_dict(self):

        return {

            'id': self.id,

            'type': self.type,

            'notes': self.notes,

            'duration_minutes': self.duration_minutes,

            'timestamp': self.timestamp.isoformat() if self.timestamp else None,

            'employee_name': self.employee.full_name if self.employee else None

        }

# --- MODELOS DE COBRANZA ---

class Payment(db.Model):

    __tablename__ = 'payment'

    

    id = db.Column(Integer, primary_key=True)

    application_id = db.Column(Integer, ForeignKey('loan_application.id'), nullable=False, index=True)

    amount_paid = db.Column(Float, nullable=False)

    payment_date = db.Column(Date, nullable=False, index=True)

    type = db.Column(String(50), default='Cuota')  # Cuota, Abono, Cancelación Total

    

    registered_by_id = db.Column(Integer, ForeignKey('employee.id'), nullable=False)

    

    # Relación contable

    journal_entry_id = db.Column(Integer, ForeignKey('journal_entry.id'), nullable=True)

    journal_entry = db.relationship('JournalEntry')

    

    def to_dict(self):

        return {

            'id': self.id,

            'application_id': self.application_id,

            'amount_paid': self.amount_paid,

            'payment_date': self.payment_date.isoformat(),

            'type': self.type,

            'registered_by': self.registered_by.full_name if self.registered_by else None

        }

# --- MODELOS DE NOTIFICACIONES Y AUDITORÍA ---

class NotificationTemplate(db.Model):

    __tablename__ = 'notification_template'

    

    id = db.Column(Integer, primary_key=True)

    slug = db.Column(String(50), unique=True, nullable=False, index=True)

    subject = db.Column(String(255), nullable=False)

    body = db.Column(Text, nullable=False)

    type = db.Column(String(20), default='Email')  # Email, SMS, WhatsApp

    

    def to_dict(self):

        return {

            'id': self.id,

            'slug': self.slug,

            'subject': self.subject,

            'body': self.body,

            'type': self.type

        }

class AuditLog(db.Model):

    __tablename__ = 'audit_log'

    

    id = db.Column(Integer, primary_key=True)

    user_id = db.Column(Integer, ForeignKey('user.id'), nullable=False, index=True)

    action = db.Column(String(100), nullable=False, index=True)

    details = db.Column(Text)

    ip_address = db.Column(String(45))

    user_agent = db.Column(String(500))

    

    timestamp = db.Column(DateTime, default=func.current_timestamp(), index=True)

    

    def to_dict(self):

        return {

            'id': self.id,

            'user_email': self.user.email if self.user else None,

            'action': self.action,

            'details': self.details,

            'timestamp': self.timestamp.isoformat() if self.timestamp else None

        }

# --- MODELOS DE HELP DESK ---

class Ticket(db.Model):

    __tablename__ = 'ticket'

    

    id = db.Column(Integer, primary_key=True)

    subject = db.Column(String(255), nullable=False)

    description = db.Column(Text)

    status = db.Column(String(50), default='Abierto', index=True)

    priority = db.Column(String(50), default='Normal')

    

    user_id = db.Column(Integer, ForeignKey('user.id'), nullable=False, index=True)

    assigned_to_id = db.Column(Integer, ForeignKey('employee.id'), nullable=True, index=True)

    

    created_at = db.Column(DateTime, default=func.current_timestamp(), index=True)

    updated_at = db.Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())

    

    # Relaciones

    comments = db.relationship('TicketComment', backref='ticket', 

                              lazy='dynamic', cascade="all, delete-orphan")

    

    def to_dict(self):

        return {

            'id': self.id,

            'subject': self.subject,

            'status': self.status,

            'priority': self.priority,

            'created_by': self.created_by_user.full_name if self.created_by_user else None,

            'assigned_to': self.assigned_employee.full_name if self.assigned_employee else None,

            'created_at': self.created_at.isoformat() if self.created_at else None

        }

class TicketComment(db.Model):

    __tablename__ = 'ticket_comment'

    

    id = db.Column(Integer, primary_key=True)

    ticket_id = db.Column(Integer, ForeignKey('ticket.id'), nullable=False, index=True)

    user_id = db.Column(Integer, ForeignKey('user.id'), nullable=False)

    comment_text = db.Column(Text, nullable=False)

    is_internal = db.Column(Boolean, default=False)

    

    timestamp = db.Column(DateTime, default=func.current_timestamp())

    

    def to_dict(self):

        commenter = User.query.get(self.user_id)

        return {

            'id': self.id,

            'commenter_name': commenter.full_name if commenter else 'Usuario eliminado',

            'commenter_email': commenter.email if commenter else None,

            'comment_text': self.comment_text,

            'is_internal': self.is_internal,

            'timestamp': self.timestamp.isoformat() if self.timestamp else None

        }

# --- FUNCIONES DE UTILIDAD ---

def create_tables(app=None):

    """Crea todas las tablas de la base de datos."""

    if app:

        with app.app_context():

            db.create_all()

    else:

        db.create_all()

    print("✅ Todas las tablas creadas exitosamente")

def seed_initial_data(app=None):

    """Siembra datos iniciales esenciales."""

    if app:

        with app.app_context():

            _seed_data()

    else:

        with db.app.app_context():

            _seed_data()

def _seed_data():

    """Función interna para sembrar datos."""

    

    # Roles

    roles_data = [

        'Super Administrador', 'Administrador General', 'Ejecutivo de Crédito',

        'Cobrador', 'Contador', 'Cliente'

    ]

    

    if Role.query.count() == 0:

        for role_name in roles_data:

            role = Role(name=role_name)

            db.session.add(role)

        db.session.commit()

        print(f"✅ {len(roles_data)} roles creados")

    

    # Cuentas contables

    accounts_data = [

        ('1101', 'Caja', 'Asset', 'Debit'),

        ('1102', 'Bancos', 'Asset', 'Debit'),

        ('1201', 'Cuentas por Cobrar Clientes', 'Asset', 'Debit'),

        ('2101', 'Retenciones por Pagar', 'Liability', 'Credit'),

        ('2102', 'Sueldos por Pagar', 'Liability', 'Credit'),

        ('3101', 'Capital Social', 'Equity', 'Credit'),

        ('4101', 'Ingresos por Intereses', 'Revenue', 'Credit'),

        ('4102', 'Ingresos por Comisiones', 'Revenue', 'Credit'),

        ('5101', 'Sueldos y Salarios', 'Expense', 'Debit')

    ]

    

    if Account.query.count() == 0:

        for code, name, category, normal_balance in accounts_data:

            account = Account(

                account_code=code,

                name=name,

                category=category,

                normal_balance=normal_balance

            )

            db.session.add(account)

        db.session.commit()

        print(f"✅ {len(accounts_data)} cuentas contables creadas")

    

    # Producto por defecto

    if LoanProduct.query.count() == 0:

        product = LoanProduct(

            name="Préstamo Personal Clásico",

            min_amount=1000.0,

            max_amount=50000.0,

            interest_rate=12.0,

            commission_rate=2.0,

            term_months=12,

            comision_apertura=0.02,

            comision_administracion=10.0,

            seguro=5.0

        )

        db.session.add(product)

        db.session.commit()

        print("✅ Producto de préstamo por defecto creado")

    

    print("✅ Datos iniciales sembrados exitosamente")

if __name__ == '__main__':

    from flask import Flask

    

    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///business_system.db'

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    

    db.init_app(app)

    

    with app.app_context():

        create_tables(app)

        seed_initial_data(app)

    

    print("🚀 Sistema de modelos listo para usar!")