"""

MODELOS DE BASE DE DATOS - SISTEMA INTEGRADO LAZO ARCE

Versión: 2.0 | Multi-tenant | Production-ready

"""

from flask_sqlalchemy import SQLAlchemy

from werkzeug.security import generate_password_hash, check_password_hash

from datetime import datetime, date, timedelta

from sqlalchemy import func, Boolean, DateTime, Float, Integer, String, Text, ForeignKey

from sqlalchemy.orm import relationship, backref

from sqlalchemy.dialects.postgresql import JSONB

# Inicializar SQLAlchemy

db = SQLAlchemy()

# === TABLAS INTERMEDIAS (Many-to-Many) ===

user_roles = db.Table('user_roles',

    db.Column('user_id', Integer, ForeignKey('user.id'), primary_key=True),

    db.Column('role_id', Integer, ForeignKey('role.id'), primary_key=True),

    schema='public'

)

mailing_list_members = db.Table('mailing_list_members',

    db.Column('mailing_list_id', Integer, ForeignKey('mailing_list.id'), primary_key=True),

    db.Column('user_id', Integer, ForeignKey('user.id'), primary_key=True),

    schema='public'

)

# === MODELOS DE SEGURIDAD Y TENANTS ===

class Tenant(db.Model):

    """Multi-tenant support - Empresas/Organizaciones"""

    __tablename__ = 'tenant'

    

    id = db.Column(Integer, primary_key=True)

    company_name = db.Column(String(100), unique=True, nullable=False, index=True)

    company_code = db.Column(String(20), unique=True, nullable=False)

    domain = db.Column(String(100), unique=True)

    is_active = db.Column(Boolean, default=True)

    created_at = db.Column(DateTime, default=func.current_timestamp())

    

    # Configuración específica del tenant

    config = db.Column(JSONB, default=dict)

    

    # Relaciones

    users = db.relationship('User', backref='tenant', lazy='dynamic')

    roles = db.relationship('Role', backref='tenant', lazy='dynamic')

    loan_products = db.relationship('LoanProduct', backref='tenant', lazy='dynamic')

    

    def to_dict(self):

        return {

            'id': self.id,

            'company_name': self.company_name,

            'company_code': self.company_code,

            'domain': self.domain,

            'is_active': self.is_active,

            'created_at': self.created_at.isoformat() if self.created_at else None

        }

    

    def __repr__(self):

        return f'<Tenant {self.company_name}>'

class Role(db.Model):

    """Roles de usuario con soporte multi-tenant"""

    __tablename__ = 'role'

    

    id = db.Column(Integer, primary_key=True)

    name = db.Column(String(80), nullable=False, index=True)

    description = db.Column(String(255))

    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)

    is_active = db.Column(Boolean, default=True)

    

    # Relaciones

    users = db.relationship('User', secondary=user_roles, back_populates='roles')

    

    def to_dict(self):

        return {

            'id': self.id,

            'name': self.name,

            'description': self.description,

            'tenant_id': self.tenant_id,

            'is_active': self.is_active

        }

    

    def __repr__(self):

        return f'<Role {self.name}>'

class User(db.Model):

    """Usuarios con autenticación y perfil completo"""

    __tablename__ = 'user'

    

    id = db.Column(Integer, primary_key=True)

    email = db.Column(String(120), unique=True, nullable=False, index=True)

    password_hash = db.Column(String(256), nullable=False)

    full_name = db.Column(String(120), nullable=False)

    

    # Datos legales (El Salvador)

    dui = db.Column(String(20), unique=True, nullable=True, index=True)

    nit = db.Column(String(20), unique=True, nullable=True, index=True)

    

    is_active = db.Column(Boolean, default=True)

    last_login = db.Column(DateTime)

    created_at = db.Column(DateTime, default=func.current_timestamp())

    

    # Relaciones

    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)

    role_id = db.Column(Integer, ForeignKey('role.id'), nullable=False)  # Rol principal

    roles = db.relationship('Role', secondary=user_roles, back_populates='users')

    

    # Perfiles relacionados

    profile = db.relationship('ClientProfile', backref='user', uselist=False)

    employee = db.relationship('Employee', backref='user', uselist=False)

    

    # Relaciones de negocio

    applications = db.relationship('LoanApplication', backref='applicant', lazy='dynamic')

    payments = db.relationship('Payment', foreign_keys='Payment.paid_by_id', backref='paid_by')

    audit_logs = db.relationship('AuditLog', backref='user', lazy='dynamic')

    

    # Métodos de seguridad

    def set_password(self, password):

        self.password_hash = generate_password_hash(password)

    

    def check_password(self, password):

        return check_password_hash(self.password_hash, password)

    

    @property

    def role(self):

        return Role.query.get(self.role_id)

    

    def has_role(self, *role_names):

        """Verifica si tiene alguno de los roles especificados"""

        return (self.role and self.role.name in role_names) or \

               any(role.name in role_names for role in self.roles)

    

    def to_dict(self, include_private=False):

        base_dict = {

            'id': self.id,

            'email': self.email,

            'full_name': self.full_name,

            'dui': self.dui,

            'nit': self.nit,

            'is_active': self.is_active,

            'tenant_id': self.tenant_id,

            'roles': [role.name for role in self.roles],

            'primary_role': self.role.name if self.role else None,

            'created_at': self.created_at.isoformat() if self.created_at else None

        }

        

        if include_private:

            base_dict.update({

                'last_login': self.last_login.isoformat() if self.last_login else None

            })

        

        return base_dict

    

    def __repr__(self):

        return f'<User {self.email}>'

class ClientProfile(db.Model):

    """Perfil detallado de cliente"""

    __tablename__ = 'client_profile'

    

    id = db.Column(Integer, primary_key=True)

    user_id = db.Column(Integer, ForeignKey('user.id'), unique=True, nullable=False)

    

    # Datos personales

    full_name = db.Column(String(120))

    phone_number = db.Column(String(20))

    secondary_phone = db.Column(String(20))

    address = db.Column(Text)

    birth_date = db.Column(Date)

    

    # Datos profesionales

    occupation = db.Column(String(100))

    employer = db.Column(String(100))

    monthly_income = db.Column(Float)

    

    # Referencias

    reference_name = db.Column(String(120))

    reference_phone = db.Column(String(20))

    

    def to_dict(self):

        return {

            'id': self.id,

            'full_name': self.full_name,

            'phone_number': self.phone_number,

            'address': self.address,

            'birth_date': self.birth_date.isoformat() if self.birth_date else None,

            'monthly_income': self.monthly_income

        }

# === MODELOS DE PRÉSTAMOS ===

class LoanProduct(db.Model):

    """Productos de préstamo configurables"""

    __tablename__ = 'loan_product'

    

    id = db.Column(Integer, primary_key=True)

    name = db.Column(String(100), unique=True, nullable=False, index=True)

    description = db.Column(Text)

    

    # Límites y condiciones

    min_amount = db.Column(Float, nullable=False, default=0.0)

    max_amount = db.Column(Float, nullable=False, default=0.0)

    interest_rate = db.Column(Float, nullable=False)  # Tasa anual %

    commission_rate = db.Column(Float, nullable=False, default=0.0)

    term_months = db.Column(Integer, nullable=False, default=12)

    

    # Comisiones y costos

    comision_apertura = db.Column(Float, default=0.0)  # % o monto fijo

    comision_administracion = db.Column(Float, default=0.0)  # Mensual

    seguro = db.Column(Float, default=0.0)  # Mensual

    

    # Configuración de cálculo

    comisiones_generan_intereses = db.Column(Boolean, default=False)

    comisiones_se_agregan_capital = db.Column(Boolean, default=False)

    comisiones_se_descuentan_capital = db.Column(Boolean, default=True)

    aplicar_tea = db.Column(Boolean, default=True)

    

    # Estado y tenant

    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)

    is_active = db.Column(Boolean, default=True)

    

    # Timestamps

    created_at = db.Column(DateTime, default=func.current_timestamp())

    updated_at = db.Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())

    

    # Relaciones

    applications = db.relationship('LoanApplication', backref='product', lazy='dynamic')

    

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

            'tenant_id': self.tenant_id,

            'created_at': self.created_at.isoformat() if self.created_at else None,

            # Campos de configuración

            **{k: v for k, v in self.__dict__.items() 

               if k.startswith(('comision_', 'seguro', 'aplicar_'))}

        }

    

    def __repr__(self):

        return f'<LoanProduct {self.name}>'

class LoanApplication(db.Model):

    """Solicitudes de préstamo"""

    __tablename__ = 'loan_application'

    

    id = db.Column(Integer, primary_key=True)

    

    # Relaciones principales

    user_id = db.Column(Integer, ForeignKey('user.id'), nullable=False, index=True)

    product_id = db.Column(Integer, ForeignKey('loan_product.id'), nullable=False, index=True)

    

    # Datos de la solicitud

    amount_requested = db.Column(Float, nullable=False)

    term_months = db.Column(Integer, nullable=False)

    commission_calculation_method = db.Column(String(1), default='A')  # A, B, C

    

    # Campos calculados (se actualizan al aprobar)

    monthly_payment = db.Column(Float, nullable=True)

    total_payment = db.Column(Float, nullable=True)

    tea_calculada = db.Column(Float, nullable=True)

    

    # Estado del workflow

    status = db.Column(String(20), nullable=False, default='Pendiente', index=True)

    # Pendiente, En revisión, Aprobado, Rechazado, Desembolsado, Cancelado

    

    # Timestamps

    application_date = db.Column(DateTime, default=func.current_timestamp(), index=True)

    decision_date = db.Column(DateTime, nullable=True)

    disbursement_date = db.Column(Date, nullable=True)

    

    # Relaciones contables

    disbursement_entry_id = db.Column(Integer, ForeignKey('journal_entry.id'), nullable=True)

    disbursement_entry = db.relationship('JournalEntry', foreign_keys=[disbursement_entry_id])

    

    # Relaciones

    payments = db.relationship('Payment', backref='application', 

                              lazy='dynamic', cascade="all, delete-orphan")

    

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

# === MODELOS CONTABLES ===

class Account(db.Model):

    """Plan de cuentas contable"""

    __tablename__ = 'account'

    

    id = db.Column(Integer, primary_key=True)

    account_code = db.Column(String(20), unique=True, nullable=False, index=True)

    name = db.Column(String(100), unique=True, nullable=False)

    

    # Clasificación contable

    category = db.Column(String(50), nullable=False)  # Asset, Liability, Equity, Revenue, Expense

    normal_balance = db.Column(String(10), nullable=False)  # Debit, Credit

    

    # Detalles adicionales

    account_type = db.Column(String(50))  # Corriente, No corriente, etc.

    account_class = db.Column(String(100))

    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)

    is_active = db.Column(Boolean, default=True)

    

    # Relaciones

    transactions = db.relationship('Transaction', backref='account', lazy='dynamic')

    

    def to_dict(self):

        return {

            'id': self.id,

            'account_code': self.account_code,

            'name': self.name,

            'category': self.category,

            'normal_balance': self.normal_balance,

            'tenant_id': self.tenant_id,

            'is_active': self.is_active

        }

    

    def __repr__(self):

        return f'<Account {self.account_code} - {self.name}>'

class JournalEntry(db.Model):

    """Asiento contable"""

    __tablename__ = 'journal_entry'

    

    id = db.Column(Integer, primary_key=True)

    date = db.Column(DateTime, default=func.current_timestamp(), index=True)

    description = db.Column(String(500), nullable=False)

    reference = db.Column(String(100))  # Factura, contrato, etc.

    created_by_id = db.Column(Integer, ForeignKey('user.id'), nullable=False)

    

    # Estado

    is_posted = db.Column(Boolean, default=False)

    posted_at = db.Column(DateTime)

    

    # Relaciones

    transactions = db.relationship('Transaction', backref='journal_entry', 

                                  lazy='dynamic', cascade="all, delete-orphan")

    created_by = db.relationship('User')

    

    @property

    def total_debit(self):

        return sum(t.amount for t in self.transactions.filter_by(type='Debit').all())

    

    @property

    def total_credit(self):

        return sum(t.amount for t in self.transactions.filter_by(type='Credit').all())

    

    @property

    def is_balanced(self):

        return self.total_debit == self.total_credit

    

    def post(self):

        """Publica el asiento contable"""

        if not self.is_balanced:

            raise ValueError("El asiento debe estar balanceado")

        

        self.is_posted = True

        self.posted_at = func.current_timestamp()

    

    def to_dict(self):

        return {

            'id': self.id,

            'date': self.date.isoformat() if self.date else None,

            'description': self.description,

            'reference': self.reference,

            'is_posted': self.is_posted,

            'total_debit': self.total_debit,

            'total_credit': self.total_credit,

            'is_balanced': self.is_balanced,

            'transactions': [t.to_dict() for t in self.transactions.all()]

        }

class Transaction(db.Model):

    """Movimiento contable individual"""

    __tablename__ = 'transaction'

    

    id = db.Column(Integer, primary_key=True)

    journal_entry_id = db.Column(Integer, ForeignKey('journal_entry.id'), 

                                nullable=False, index=True)

    account_id = db.Column(Integer, ForeignKey('account.id'), 

                          nullable=False, index=True)

    type = db.Column(String(10), nullable=False)  # Debit, Credit

    amount = db.Column(Float, nullable=False, default=0.0)

    

    # Relaciones

    account = db.relationship('Account')

    

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

# === MODELOS DE RECURSOS HUMANOS ===

class Employee(db.Model):

    """Empleados y personal"""

    __tablename__ = 'employee'

    

    id = db.Column(Integer, primary_key=True)

    full_name = db.Column(String(120), nullable=False, index=True)

    employee_type = db.Column(String(20), default='interno')  # interno, temporal, contratista

    position = db.Column(String(100))

    salary = db.Column(Float, default=0.0)

    

    # Fechas

    hire_date = db.Column(Date, nullable=True)

    termination_date = db.Column(Date, nullable=True)

    is_active = db.Column(Boolean, default=True)

    

    # Datos legales (El Salvador)

    dui = db.Column(String(20), unique=True, index=True)

    nit = db.Column(String(20), unique=True, index=True)

    isss_number = db.Column(String(20), unique=True)

    afp_number = db.Column(String(20), unique=True)

    

    # Relaciones

    user_id = db.Column(Integer, ForeignKey('user.id'), unique=True)

    payslips = db.relationship('PaySlip', backref='employee', lazy='dynamic')

    

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

class PaySlip(db.Model):

    """Planillas de pago (Payroll)"""

    __tablename__ = 'payslip'

    

    id = db.Column(Integer, primary_key=True)

    employee_id = db.Column(Integer, ForeignKey('employee.id'), nullable=False, index=True)

    

    # Período

    period_start = db.Column(Date, nullable=False)

    period_end = db.Column(Date, nullable=False)

    payment_date = db.Column(Date, nullable=False)

    

    # Cálculos

    base_salary = db.Column(Float, nullable=False)

    overtime_hours = db.Column(Float, default=0.0)

    overtime_amount = db.Column(Float, default=0.0)

    

    # Deducciones legales (El Salvador)

    isss_employee = db.Column(Float, default=0.0)  # 7.5%

    afp_employee = db.Column(Float, default=0.0)   # 7.25%

    renta = db.Column(Float, default=0.0)          # Impuesto sobre la renta

    

    # Totales

    gross_salary = db.Column(Float, nullable=False)

    total_deductions = db.Column(Float, nullable=False)

    net_salary = db.Column(Float, nullable=False)

    

    # Estado

    is_paid = db.Column(Boolean, default=False)

    paid_at = db.Column(DateTime)

    

    def to_dict(self):

        return {

            'id': self.id,

            'employee_id': self.employee_id,

            'period_start': self.period_start.isoformat(),

            'period_end': self.period_end.isoformat(),

            'base_salary': self.base_salary,

            'gross_salary': self.gross_salary,

            'net_salary': self.net_salary,

            'is_paid': self.is_paid

        }

# === MODELOS DE COBRANZA Y PAGOS ===

class Payment(db.Model):

    """Pagos de préstamos"""

    __tablename__ = 'payment'

    

    id = db.Column(Integer, primary_key=True)

    application_id = db.Column(Integer, ForeignKey('loan_application.id'), 

                              nullable=False, index=True)

    payment_number = db.Column(Integer)  # Cuota #1, #2, etc.

    

    # Monto del pago

    amount_paid = db.Column(Float, nullable=False)

    amount_due = db.Column(Float, nullable=False)  # Cuota esperada

    interest_paid = db.Column(Float, default=0.0)

    principal_paid = db.Column(Float, default=0.0)

    

    # Fechas

    payment_date = db.Column(Date, nullable=False, index=True)

    due_date = db.Column(Date, nullable=False)

    

    # Tipo de pago

    type = db.Column(String(50), default='Cuota')  # Cuota, Abono, Cancelación Total

    

    # Estado

    status = db.Column(String(20), default='Pagado')  # Pagado, Pendiente, Atrasado

    

    # Quién registró el pago

    registered_by_id = db.Column(Integer, ForeignKey('employee.id'), nullable=False)

    

    # Relación contable

    journal_entry_id = db.Column(Integer, ForeignKey('journal_entry.id'), nullable=True)

    journal_entry = db.relationship('JournalEntry')

    

    def to_dict(self):

        return {

            'id': self.id,

            'application_id': self.application_id,

            'payment_number': self.payment_number,

            'amount_paid': self.amount_paid,

            'amount_due': self.amount_due,

            'payment_date': self.payment_date.isoformat(),

            'due_date': self.due_date.isoformat(),

            'type': self.type,

            'status': self.status,

            'registered_by': self.registered_by.full_name if self.registered_by else None

        }

# === MODELOS DE AUDITORÍA Y NOTIFICACIONES ===

class AuditLog(db.Model):

    """Registro de auditoría"""

    __tablename__ = 'audit_log'

    

    id = db.Column(Integer, primary_key=True)

    user_id = db.Column(Integer, ForeignKey('user.id'), nullable=False, index=True)

    action = db.Column(String(100), nullable=False, index=True)  # LOGIN, LOAN_APPROVED, etc.

    details = db.Column(Text)

    ip_address = db.Column(String(45))

    user_agent = db.Column(String(500))

    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)

    

    timestamp = db.Column(DateTime, default=func.current_timestamp(), index=True)

    

    def to_dict(self):

        return {

            'id': self.id,

            'user_email': self.user.email if self.user else None,

            'action': self.action,

            'details': self.details,

            'ip_address': self.ip_address,

            'timestamp': self.timestamp.isoformat() if self.timestamp else None

        }

class NotificationTemplate(db.Model):

    """Plantillas de notificación"""

    __tablename__ = 'notification_template'

    

    id = db.Column(Integer, primary_key=True)

    slug = db.Column(String(50), unique=True, nullable=False, index=True)

    name = db.Column(String(100), nullable=False)

    subject = db.Column(String(255), nullable=False)

    body = db.Column(Text, nullable=False)

    type = db.Column(String(20), default='Email')  # Email, SMS, WhatsApp, Push

    

    # Variables disponibles: {customer_name}, {amount}, {due_date}

    variables = db.Column(JSONB, default=list)

    

    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)

    is_active = db.Column(Boolean, default=True)

    

    def to_dict(self):

        return {

            'id': self.id,

            'slug': self.slug,

            'name': self.name,

            'subject': self.subject,

            'type': self.type,

            'is_active': self.is_active,

            'variables': self.variables

        }

# === FUNCIONES DE UTILIDAD ===

def create_tables(app=None):

    """Crea todas las tablas de la base de datos."""

    if app:

        with app.app_context():

            db.create_all()

            print("✅ Todas las tablas creadas exitosamente")

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

    """Función interna para sembrar datos iniciales."""

    

    # === TENANT POR DEFECTO ===

    if Tenant.query.count() == 0:

        default_tenant = Tenant(

            company_name='LAZOARCE NEXUS',

            company_code='LAZO001',

            domain='lazoarce.com',

            is_active=True

        )

        db.session.add(default_tenant)

        db.session.commit()

        print("✅ Tenant por defecto creado")

    else:

        default_tenant = Tenant.query.first()

    

    # === ROLES ===

    roles_data = [

        ('Super Administrador', 'Acceso total al sistema'),

        ('Administrador General', 'Gestión completa por tenant'),

        ('Ejecutivo de Crédito', 'Aprobación y gestión de préstamos'),

        ('Cobrador', 'Gestión de cobros y morosidad'),

        ('Contador', 'Contabilidad y planillas'),

        ('Cliente', 'Acceso a información personal')

    ]

    

    existing_roles = {role.name for role in Role.query.all()}

    roles_to_create = [

        Role(name=name, description=desc, tenant_id=default_tenant.id)

        for name, desc in roles_data if name not in existing_roles

    ]

    

    if roles_to_create:

        db.session.bulk_save_objects(roles_to_create)

        db.session.commit()

        print(f"✅ {len(roles_to_create)} roles creados")

    

    # === CUENTAS CONTABLES BÁSICAS ===

    accounts_data = [

        ('1101', 'Caja', 'Asset', 'Debit'),

        ('1102', 'Bancos', 'Asset', 'Debit'),

        ('1201', 'Cuentas por Cobrar Clientes', 'Asset', 'Debit'),

        ('2101', 'Retenciones por Pagar ISSS', 'Liability', 'Credit'),

        ('2102', 'Retenciones por Pagar AFP', 'Liability', 'Credit'),

        ('2103', 'Sueldos por Pagar', 'Liability', 'Credit'),

        ('3101', 'Capital Social', 'Equity', 'Credit'),

        ('4101', 'Ingresos por Intereses', 'Revenue', 'Credit'),

        ('4102', 'Ingresos por Comisiones', 'Revenue', 'Credit'),

        ('5101', 'Sueldos y Salarios', 'Expense', 'Debit'),

        ('5102', 'Gastos Administrativos', 'Expense', 'Debit'),

        ('6101', 'Depreciación', 'Expense', 'Debit')

    ]

    

    existing_accounts = {acc.account_code for acc in Account.query.all()}

    accounts_to_create = []

    

    for code, name, category, normal_balance in accounts_data:

        if code not in existing_accounts:

            accounts_to_create.append(Account(

                account_code=code,

                name=name,

                category=category,

                normal_balance=normal_balance,

                tenant_id=default_tenant.id

            ))

    

    if accounts_to_create:

        db.session.bulk_save_objects(accounts_to_create)

        db.session.commit()

        print(f"✅ {len(accounts_to_create)} cuentas contables creadas")

    

    # === PRODUCTO DE PRÉSTAMO POR DEFECTO ===

    if LoanProduct.query.filter_by(tenant_id=default_tenant.id).count() == 0:

        default_product = LoanProduct(

            name="Préstamo Personal Clásico",

            description="Préstamo personal para clientes con buen historial crediticio",

            min_amount=1000.0,

            max_amount=50000.0,

            interest_rate=15.0,  # 15% anual

            commission_rate=2.0,

            term_months=12,

            comision_apertura=0.02,  # 2%

            comision_administracion=10.0,  # $10 mensual

            seguro=5.0,  # $5 mensual

            comisiones_se_descuentan_capital=True,

            aplicar_tea=True,

            tenant_id=default_tenant.id

        )

        db.session.add(default_product)

        db.session.commit()

        print("✅ Producto de préstamo por defecto creado")

    

    # === PLANTILLAS DE NOTIFICACIÓN ===

    templates_data = [

        ('loan-application-received', 'Recibimos tu solicitud de préstamo',

         'Hola {customer_name},\n\nHemos recibido tu solicitud por ${amount}. Te contactaremos pronto.',

         'Email'),

        ('loan-approved', '¡Tu préstamo fue APROBADO! 🎉',

         '¡Felicidades {customer_name}! Tu préstamo por ${amount} ha sido aprobado.\n\nPróximos pasos:\n1. Firma del contrato\n2. Desembolso en 24h',

         'Email'),

        ('payment-reminder', '⏰ Recordatorio de pago',

         'Hola {customer_name},\n\nTe recordamos que vence tu cuota de ${amount} el {due_date}.\n\n¡Paga a tiempo y mantén tu buen historial!',

         'SMS')

    ]

    

    existing_templates = {t.slug for t in NotificationTemplate.query.all()}

    templates_to_create = []

    

    for slug, subject, body, type_ in templates_data:

        if slug not in existing_templates:

            templates_to_create.append(NotificationTemplate(

                slug=slug,

                name=subject,

                subject=subject,

                body=body,

                type=type_,

                variables=['customer_name', 'amount', 'due_date'],

                tenant_id=default_tenant.id

            ))

    

    if templates_to_create:

        db.session.bulk_save_objects(templates_to_create)

        db.session.commit()

        print(f"✅ {len(templates_to_create)} plantillas de notificación creadas")

    

    # === ESTADÍSTICAS FINALES ===

    print("📊 RESUMEN DE DATOS INICIALES:")

    print(f"   👥 Tenants: {Tenant.query.count()}")

    print(f"   🎭 Roles: {Role.query.count()}")

    print(f"   🏦 Cuentas contables: {Account.query.count()}")

    print(f"   💰 Productos de préstamo: {LoanProduct.query.count()}")

    print(f"   📧 Plantillas: {NotificationTemplate.query.count()}")

    print("✅ 🎉 Datos iniciales sembrados exitosamente")

if __name__ == '__main__':

    from flask import Flask

    

    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lazoarce_system.db'

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    

    db.init_app(app)

    

    with app.app_context():

        create_tables(app)

        seed_initial_data(app)

    

    print("🚀 Sistema de modelos listo para usar!")

    print("\n📋 ENDPOINTS DISPONIBLES:")

    print("   GET /api/health")

    print("   POST /api/auth/login")

    print("   GET /api/loans/products")

    print("   POST /api/loans/applications")