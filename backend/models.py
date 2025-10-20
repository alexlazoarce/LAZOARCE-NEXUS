from flask_sqlalchemy import SQLAlchemy

from werkzeug.security import generate_password_hash, check_password_hash

from datetime import datetime, date

from sqlalchemy import func

from sqlalchemy.orm import relationship

# Inicializar SQLAlchemy

db = SQLAlchemy()

# Tabla intermedia para MailingList

mailing_list_members = db.Table('mailing_list_members',

    db.Column('mailing_list_id', db.Integer, db.ForeignKey('mailing_list.id'), primary_key=True),

    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)

)

# --- MODELOS DE SEGURIDAD Y USUARIOS ---

class Role(db.Model):

    __tablename__ = 'role'

    

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(80), unique=True, nullable=False)

    

    # Relaciones

    users = db.relationship('User', backref='role', lazy=True)

    

    def __repr__(self):

        return f'<Role {self.name}>'

    

    def to_dict(self):

        return {'id': self.id, 'name': self.name}

class User(db.Model):

    __tablename__ = 'user'

    

    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(db.String(120), unique=True, nullable=False, index=True)

    password_hash = db.Column(db.String(256), nullable=False)

    full_name = db.Column(db.String(120), nullable=True)

    dui = db.Column(db.String(20), nullable=True, unique=True)

    nit = db.Column(db.String(20), nullable=True, unique=True)

    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False, index=True)

    

    # Relaciones principales

    applications = db.relationship('LoanApplication', backref='applicant', lazy=True)

    communication_logs = db.relationship('CommunicationLog', backref='user', lazy='dynamic')

    audit_logs = db.relationship('AuditLog', backref='user', lazy='dynamic')

    tickets = db.relationship('Ticket', foreign_keys='[Ticket.user_id]', backref='created_by_user', lazy='dynamic')

    subscriptions = db.relationship('Subscription', backref='user', lazy=True)

    mailing_lists = db.relationship('MailingList', secondary=mailing_list_members, lazy='dynamic', backref=db.backref('members', lazy=True))

    

    # Métodos de seguridad

    def set_password(self, password):

        self.password_hash = generate_password_hash(password)

    

    def check_password(self, password):

        return check_password_hash(self.password_hash, password)

    

    def to_dict(self):

        return {

            'id': self.id,

            'email': self.email,

            'full_name': self.full_name,

            'dui': self.dui,

            'nit': self.nit,

            'role': self.role.name if self.role else None

        }

    

    def __repr__(self):

        return f'<User {self.email}>'

# --- MODELOS DE PRÉSTAMOS ---

class LoanProduct(db.Model):

    __tablename__ = 'loan_product'

    

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False, unique=True)

    min_amount = db.Column(db.Float, nullable=False, default=0.0)

    max_amount = db.Column(db.Float, nullable=False, default=0.0)

    interest_rate = db.Column(db.Float, nullable=False, default=0.0)  # Tasa anual %

    commission_rate = db.Column(db.Float, nullable=False, default=0.01)  # Comisión %

    term_months = db.Column(db.Integer, nullable=False, default=12)

    is_active = db.Column(db.Boolean, default=True)

    

    # Campos para calculadora de préstamos

    comision_apertura = db.Column(db.Float, default=0.0)

    comision_administracion = db.Column(db.Float, default=0.0)

    seguro = db.Column(db.Float, default=0.0)

    comisiones_se_descuentan_capital = db.Column(db.Boolean, default=True)

    comisiones_se_agregan_capital = db.Column(db.Boolean, default=False)

    aplicar_tea = db.Column(db.Boolean, default=True)

    

    # Timestamps

    created_at = db.Column(db.DateTime, default=func.current_timestamp())

    updated_at = db.Column(db.DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())

    

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

            'comision_apertura': self.comision_apertura,

            'comision_administracion': self.comision_administracion,

            'seguro': self.seguro

        }

    

    def __repr__(self):

        return f'<LoanProduct {self.name}>'

class LoanApplication(db.Model):

    __tablename__ = 'loan_application'

    

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)

    product_id = db.Column(db.Integer, db.ForeignKey('loan_product.id'), nullable=False, index=True)

    

    amount_requested = db.Column(db.Float, nullable=False)

    term_months = db.Column(db.Integer, nullable=False)

    commission_calculation_method = db.Column(db.String(1), default='A')  # A, B, C

    

    # Campos calculados

    monthly_payment = db.Column(db.Float, nullable=True)

    total_payment = db.Column(db.Float, nullable=True)

    tea_calculada = db.Column(db.Float, nullable=True)  # TEA %

    

    status = db.Column(db.String(20), nullable=False, default='Pendiente', index=True)

    

    # Timestamps

    application_date = db.Column(db.DateTime, default=func.current_timestamp(), index=True)

    decision_date = db.Column(db.DateTime, nullable=True)

    

    # Relación contable

    disbursement_entry_id = db.Column(db.Integer, db.ForeignKey('journal_entry.id'), nullable=True)

    disbursement_entry = db.relationship('JournalEntry', foreign_keys=[disbursement_entry_id])

    

    # Relaciones

    payments = db.relationship('Payment', backref='application', lazy='dynamic', cascade="all, delete-orphan")

    

    def to_dict(self):

        return {

            'id': self.id,

            'user_id': self.user_id,

            'applicant_name': self.applicant.full_name if self.applicant else None,

            'product_id': self.product_id,

            'product_name': self.product.name if self.product else None,

            'amount_requested': self.amount_requested,

            'term_months': self.term_months,

            'commission_calculation_method': self.commission_calculation_method,

            'status': self.status,

            'monthly_payment': self.monthly_payment,

            'total_payment': self.total_payment,

            'tea_calculada': self.tea_calculada,

            'application_date': self.application_date.isoformat() if self.application_date else None,

            'decision_date': self.decision_date.isoformat() if self.decision_date else None

        }

    

    def __repr__(self):

        return f'<LoanApplication {self.id} - {self.status}>'

# --- MODELOS CONTABLES (NUEVO SISTEMA) ---

class Account(db.Model):

    __tablename__ = 'account'

    

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), unique=True, nullable=False)

    category = db.Column(db.String(50), nullable=False)  # Asset, Liability, Equity, Revenue, Expense

    normal_balance = db.Column(db.String(10), nullable=False)  # Debit, Credit

    account_code = db.Column(db.String(20), unique=True)

    account_type = db.Column(db.String(50))

    account_class = db.Column(db.String(100))

    

    # Relaciones

    transactions = db.relationship('Transaction', backref='account', lazy=True)

    

    def to_dict(self):

        return {

            'id': self.id,

            'name': self.name,

            'account_code': self.account_code,

            'category': self.category,

            'normal_balance': self.normal_balance

        }

    

    def __repr__(self):

        return f'<Account {self.name}>'

class JournalEntry(db.Model):

    __tablename__ = 'journal_entry'

    

    id = db.Column(db.Integer, primary_key=True)

    date = db.Column(db.DateTime, default=func.current_timestamp(), index=True)

    description = db.Column(db.String(500), nullable=False)

    reference = db.Column(db.String(100), nullable=True)

    

    # Relaciones

    transactions = db.relationship('Transaction', backref='journal_entry', 

                                 lazy='dynamic', cascade="all, delete-orphan")

    

    def to_dict(self):

        return {

            'id': self.id,

            'date': self.date.isoformat() if self.date else None,

            'description': self.description,

            'reference': self.reference,

            'transactions': [t.to_dict() for t in self.transactions.all()]

        }

    

    def __repr__(self):

        return f'<JournalEntry {self.id}>'

class Transaction(db.Model):

    __tablename__ = 'transaction'

    

    id = db.Column(db.Integer, primary_key=True)

    journal_entry_id = db.Column(db.Integer, db.ForeignKey('journal_entry.id'), 

                               nullable=False, index=True)

    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False, index=True)

    type = db.Column(db.String(10), nullable=False)  # Debit, Credit

    amount = db.Column(db.Float, nullable=False, default=0.0)

    

    def to_dict(self):

        return {

            'id': self.id,

            'account_name': self.account.name if self.account else None,

            'type': self.type,

            'amount': self.amount

        }

    

    def __repr__(self):

        return f'<Transaction {self.id} - {self.type} {self.amount}>'

# --- MODELOS DE RECURSOS HUMANOS ---

class Employee(db.Model):

    __tablename__ = 'employee'

    

    id = db.Column(db.Integer, primary_key=True)

    full_name = db.Column(db.String(120), nullable=False)

    employee_type = db.Column(db.String(20), default='interno')  # interno, temporal

    position = db.Column(db.String(100), nullable=True)

    salary = db.Column(db.Float, default=0.0)

    hire_date = db.Column(db.Date, nullable=True)

    is_active = db.Column(db.Boolean, default=True)

    

    # Datos personales

    country_code = db.Column(db.String(2), default='SV')

    dui = db.Column(db.String(20), unique=True)

    nit = db.Column(db.String(20), unique=True)

    isss_number = db.Column(db.String(20), unique=True)

    afp_number = db.Column(db.String(20), unique=True)

    

    # Relaciones

    payslips = db.relationship('PaySlip', backref='employee', lazy=True)

    payments_registered = db.relationship('Payment', foreign_keys='Payment.registered_by_id', 

                                        backref='registered_by', lazy='dynamic')

    assigned_tickets = db.relationship('Ticket', foreign_keys='Ticket.assigned_to_id',

                                     backref='assigned_employee', lazy='dynamic')

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

# --- MODELOS ET2 (EMPRESA DE TRABAJO TEMPORAL) ---

class ClientCompany(db.Model):

    __tablename__ = 'client_company'

    

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(150), unique=True, nullable=False)

    contact_person = db.Column(db.String(120))

    contact_email = db.Column(db.String(120))

    phone_number = db.Column(db.String(20))

    

    # Relaciones

    assignments = db.relationship('TemporaryAssignment', backref='client_company', lazy='dynamic')

    

    def to_dict(self):

        return {

            'id': self.id,

            'name': self.name,

            'contact_person': self.contact_person,

            'contact_email': self.contact_email,

            'phone_number': self.phone_number

        }

    

    def __repr__(self):

        return f'<ClientCompany {self.name}>'

class TemporaryAssignment(db.Model):

    __tablename__ = 'temporary_assignment'

    

    id = db.Column(db.Integer, primary_key=True)

    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False, index=True)

    client_company_id = db.Column(db.Integer, db.ForeignKey('client_company.id'), nullable=False, index=True)

    

    project_name = db.Column(db.String(150))

    position_in_client = db.Column(db.String(100), nullable=False)

    start_date = db.Column(db.Date, nullable=False, index=True)

    end_date = db.Column(db.Date, nullable=True)

    assignment_salary = db.Column(db.Float, nullable=False)

    is_active = db.Column(db.Boolean, default=True)

    

    created_at = db.Column(db.DateTime, default=func.current_timestamp())

    

    def to_dict(self):

        return {

            'id': self.id,

            'employee_name': self.employee.full_name if self.employee else None,

            'client_company_name': self.client_company.name if self.client_company else None,

            'project_name': self.project_name,

            'position_in_client': self.position_in_client,

            'start_date': self.start_date.isoformat(),

            'end_date': self.end_date.isoformat() if self.end_date else None,

            'assignment_salary': self.assignment_salary,

            'is_active': self.is_active

        }

    

    def __repr__(self):

        return f'<TemporaryAssignment {self.id}>'

# --- MODELOS DE NÓMINA ---

class PayrollLog(db.Model):

    __tablename__ = 'payroll_log'

    

    id = db.Column(db.Integer, primary_key=True)

    period_start_date = db.Column(db.Date, nullable=False, index=True)

    period_end_date = db.Column(db.Date, nullable=False, index=True)

    execution_date = db.Column(db.DateTime, default=func.current_timestamp())

    total_paid = db.Column(db.Float, default=0.0)

    

    # Relación contable

    journal_entry_id = db.Column(db.Integer, db.ForeignKey('journal_entry.id'), nullable=True)

    journal_entry = db.relationship('JournalEntry')

    

    # Relaciones

    payslips = db.relationship('PaySlip', backref='payroll_log', lazy=True)

    

    def to_dict(self):

        return {

            'id': self.id,

            'period_start_date': self.period_start_date.isoformat(),

            'period_end_date': self.period_end_date.isoformat(),

            'execution_date': self.execution_date.isoformat() if self.execution_date else None,

            'total_paid': self.total_paid

        }

class PaySlip(db.Model):

    __tablename__ = 'payslip'

    

    id = db.Column(db.Integer, primary_key=True)

    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)

    payroll_log_id = db.Column(db.Integer, db.ForeignKey('payroll_log.id'), nullable=False)

    

    gross_salary = db.Column(db.Float, nullable=False)

    isss_deduction = db.Column(db.Float, default=0.0)

    afp_deduction = db.Column(db.Float, default=0.0)

    renta_deduction = db.Column(db.Float, default=0.0)

    net_salary = db.Column(db.Float, nullable=False)

    

    def to_dict(self):

        return {

            'id': self.id,

            'employee_name': self.employee.full_name if self.employee else None,

            'gross_salary': self.gross_salary,

            'isss_deduction': self.isss_deduction,

            'afp_deduction': self.afp_deduction,

            'renta_deduction': self.renta_deduction,

            'net_salary': self.net_salary

        }

# --- MODELOS CRM ---

class Lead(db.Model):

    __tablename__ = 'lead'

    

    id = db.Column(db.Integer, primary_key=True)

    full_name = db.Column(db.String(120), nullable=False)

    email = db.Column(db.String(120))

    phone = db.Column(db.String(20))

    

    status = db.Column(db.String(50), default='Nuevo')

    source = db.Column(db.String(100))

    notes = db.Column(db.Text)

    

    created_at = db.Column(db.DateTime, default=func.current_timestamp())

    updated_at = db.Column(db.DateTime, default=func.current_timestamp(), 

                          onupdate=func.current_timestamp())

    

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

    

    id = db.Column(db.Integer, primary_key=True)

    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'), nullable=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)

    

    type = db.Column(db.String(50), nullable=False)  # Llamada, Email, Reunión

    notes = db.Column(db.Text, nullable=False)

    timestamp = db.Column(db.DateTime, default=func.current_timestamp())

    

    def to_dict(self):

        return {

            'id': self.id,

            'employee_name': self.employee.full_name if self.employee else None,

            'type': self.type,

            'notes': self.notes,

            'timestamp': self.timestamp.isoformat() if self.timestamp else None

        }

class Opportunity(db.Model):

    __tablename__ = 'opportunity'

    

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(255), nullable=False)

    amount = db.Column(db.Float)

    stage = db.Column(db.String(50), default='Calificación')

    close_date = db.Column(db.Date)

    

    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'), nullable=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    

    created_at = db.Column(db.DateTime, default=func.current_timestamp())

    updated_at = db.Column(db.DateTime, default=func.current_timestamp(), 

                          onupdate=func.current_timestamp())

    

    # Relaciones

    client = db.relationship('User')

    

    def to_dict(self):

        return {

            'id': self.id,

            'name': self.name,

            'amount': self.amount,

            'stage': self.stage,

            'close_date': self.close_date.isoformat() if self.close_date else None,

            'client_name': self.client.full_name if self.client else (self.lead.full_name if self.lead else None)

        }

# --- MODELOS DE COBRANZA (NUEVO SISTEMA) ---

class Payment(db.Model):

    __tablename__ = 'payment'

    

    id = db.Column(db.Integer, primary_key=True)

    application_id = db.Column(db.Integer, db.ForeignKey('loan_application.id'), 

                             nullable=False, index=True)

    amount_paid = db.Column(db.Float, nullable=False)

    payment_date = db.Column(db.Date, nullable=False, index=True)

    type = db.Column(db.String(50), default='Cuota')  # Cuota, Abono, Cancelación

    

    registered_by_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)

    

    # Relación contable

    journal_entry_id = db.Column(db.Integer, db.ForeignKey('journal_entry.id'), nullable=True)

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

# --- MODELOS DE NOTIFICACIONES ---

class NotificationTemplate(db.Model):

    __tablename__ = 'notification_template'

    

    id = db.Column(db.Integer, primary_key=True)

    slug = db.Column(db.String(50), unique=True, nullable=False)

    subject = db.Column(db.String(255), nullable=False)

    body = db.Column(db.Text, nullable=False)

    type = db.Column(db.String(20), default='Email')  # Email, SMS

    

    def to_dict(self):

        return {

            'id': self.id,

            'slug': self.slug,

            'subject': self.subject,

            'body': self.body,

            'type': self.type

        }

# --- MODELOS DE AUDITORÍA ---

class AuditLog(db.Model):

    __tablename__ = 'audit_log'

    

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)

    action = db.Column(db.String(100), nullable=False)

    details = db.Column(db.Text)

    timestamp = db.Column(db.DateTime, default=func.current_timestamp(), index=True)

    

    def to_dict(self):

        return {

            'id': self.id,

            'user_email': self.user.email if self.user else None,

            'action': self.action,

            'details': self.details,

            'timestamp': self.timestamp.isoformat() if self.timestamp else None

        }

# --- MODELOS DE MARKETING ---

class MailingList(db.Model):

    __tablename__ = 'mailing_list'

    

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), unique=True, nullable=False)

    description = db.Column(db.String(255))

    

    def to_dict(self):

        return {

            'id': self.id,

            'name': self.name,

            'description': self.description,

            'member_count': self.members.count()

        }

class Campaign(db.Model):

    __tablename__ = 'campaign'

    

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(150), nullable=False)

    subject = db.Column(db.String(255), nullable=False)

    status = db.Column(db.String(50), default='Draft')

    

    mailing_list_id = db.Column(db.Integer, db.ForeignKey('mailing_list.id'), nullable=False)

    template_id = db.Column(db.Integer, db.ForeignKey('notification_template.id'), nullable=False)

    

    sent_at = db.Column(db.DateTime)

    

    # Relaciones

    mailing_list = db.relationship('MailingList')

    template = db.relationship('NotificationTemplate')

    

    def to_dict(self):

        return {

            'id': self.id,

            'name': self.name,

            'subject': self.subject,

            'status': self.status,

            'mailing_list_name': self.mailing_list.name if self.mailing_list else None,

            'template_slug': self.template.slug if self.template else None,

            'sent_at': self.sent_at.isoformat() if self.sent_at else None

        }

# --- MODELOS DE HELP DESK ---

class Ticket(db.Model):

    __tablename__ = 'ticket'

    

    id = db.Column(db.Integer, primary_key=True)

    subject = db.Column(db.String(255), nullable=False)

    status = db.Column(db.String(50), default='Abierto')

    priority = db.Column(db.String(50), default='Normal')

    

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)

    assigned_to_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=True, index=True)

    

    created_at = db.Column(db.DateTime, default=func.current_timestamp())

    updated_at = db.Column(db.DateTime, default=func.current_timestamp(), 

                          onupdate=func.current_timestamp())

    

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

    

    id = db.Column(db.Integer, primary_key=True)

    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    comment_text = db.Column(db.Text, nullable=False)

    timestamp = db.Column(db.DateTime, default=func.current_timestamp())

    

    def to_dict(self):

        commenter = User.query.get(self.user_id)

        return {

            'id': self.id,

            'commenter_name': commenter.full_name if commenter else 'Usuario eliminado',

            'comment_text': self.comment_text,

            'timestamp': self.timestamp.isoformat() if self.timestamp else None

        }

# --- MODELOS DE FACTURACIÓN ---

class Invoice(db.Model):

    __tablename__ = 'invoice'

    

    id = db.Column(db.Integer, primary_key=True)

    customer_name = db.Column(db.String(200), nullable=False)

    customer_nit = db.Column(db.String(20), nullable=False)

    total_amount = db.Column(db.Float, nullable=False)

    status = db.Column(db.String(20), default='draft')

    

    issue_date = db.Column(db.DateTime, default=func.current_timestamp())

    

    # Relación contable

    journal_entry_id = db.Column(db.Integer, db.ForeignKey('journal_entry.id'), nullable=True)

    journal_entry = db.relationship('JournalEntry')

    

    # Relaciones

    items = db.relationship('InvoiceItem', backref='invoice', 

                          lazy='dynamic', cascade="all, delete-orphan")

    

    def to_dict(self):

        return {

            'id': self.id,

            'customer_name': self.customer_name,

            'customer_nit': self.customer_nit,

            'total_amount': self.total_amount,

            'status': self.status,

            'issue_date': self.issue_date.isoformat() if self.issue_date else None

        }

class InvoiceItem(db.Model):

    __tablename__ = 'invoice_item'

    

    id = db.Column(db.Integer, primary_key=True)

    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)

    description = db.Column(db.String(255), nullable=False)

    quantity = db.Column(db.Float, nullable=False, default=1.0)

    price = db.Column(db.Float, nullable=False)

    

    @property

    def total(self):

        return self.quantity * self.price

# --- MODELOS DE IMPUESTOS ---

class TaxType(db.Model):

    __tablename__ = 'tax_type'

    

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(50), nullable=False)

    rate = db.Column(db.Float, nullable=False)

    country_code = db.Column(db.String(2), nullable=False)

    

    def to_dict(self):

        return {

            'id': self.id,

            'name': self.name,

            'rate': self.rate,

            'country_code': self.country_code

        }

# --- MODELOS DE SUSCRIPCIONES ---

class SubscriptionPlan(db.Model):

    __tablename__ = 'subscription_plan'

    

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), unique=True, nullable=False)

    price = db.Column(db.Float, nullable=False)

    billing_interval = db.Column(db.String(20), default='monthly')

    

    def to_dict(self):

        return {

            'id': self.id,

            'name': self.name,

            'price': self.price,

            'billing_interval': self.billing_interval

        }

class Subscription(db.Model):

    __tablename__ = 'subscription'

    

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    plan_id = db.Column(db.Integer, db.ForeignKey('subscription_plan.id'), nullable=False)

    

    status = db.Column(db.String(20), default='active')

    start_date = db.Column(db.Date, default=func.current_date())

    next_billing_date = db.Column(db.Date, nullable=False)

    

    # Relaciones

    plan = db.relationship('SubscriptionPlan')

    

    def to_dict(self):

        return {

            'id': self.id,

            'plan_name': self.plan.name if self.plan else None,

            'status': self.status,

            'start_date': self.start_date.isoformat() if self.start_date else None,

            'next_billing_date': self.next_billing_date.isoformat() if self.next_billing_date else None

        }

# --- FUNCIONES DE UTILIDAD ---

def create_tables():

    """Crea todas las tablas de la base de datos."""

    db.create_all()

    print("✅ Todas las tablas creadas exitosamente")

def seed_initial_data():

    """Siembra datos iniciales esenciales."""

    with db.app.app_context():

        # Roles

        roles_data = [

            'Super Administrador',

            'Administrador General', 

            'Ejecutivo de Crédito',

            'Cobrador',

            'Contador',

            'Cliente'

        ]

        

        if Role.query.count() == 0:

            for role_name in roles_data:

                role = Role(name=role_name)

                db.session.add(role)

            db.session.commit()

            print(f"✅ {len(roles_data)} roles creados")

        

        # Cuentas contables básicas

        accounts_data = [

            # Activos

            ('1101', 'Caja', 'Asset', 'Debit'),

            ('1102', 'Bancos', 'Asset', 'Debit'),

            ('1201', 'Cuentas por Cobrar Clientes', 'Asset', 'Debit'),

            # Pasivos

            ('2101', 'Retenciones por Pagar', 'Liability', 'Credit'),

            ('2102', 'Sueldos por Pagar', 'Liability', 'Credit'),

            # Patrimonio

            ('3101', 'Capital Social', 'Equity', 'Credit'),

            # Ingresos

            ('4101', 'Ingresos por Intereses', 'Revenue', 'Credit'),

            ('4102', 'Ingresos por Comisiones', 'Revenue', 'Credit'),

            # Gastos

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

        

        # Producto de préstamo por defecto

        if LoanProduct.query.count() == 0:

            default_product = LoanProduct(

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

            db.session.add(default_product)

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

        create_tables()

        seed_initial_data()

    print("🚀 Sistema de modelos listo para usar!")