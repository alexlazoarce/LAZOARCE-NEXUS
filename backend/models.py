from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# --- Core Tenant Model ---

class Tenant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(120), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    roles = db.relationship('Role', backref='tenant', lazy=True)

    def to_dict(self):
        return {'id': self.id, 'company_name': self.company_name, 'is_active': self.is_active}

# --- Tenant-Specific Models ---

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    users = db.relationship('User', backref='role', lazy=True)
    __table_args__ = (db.UniqueConstraint('name', 'tenant_id'),)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    tenant = db.relationship('Tenant')
    email = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)
    full_name = db.Column(db.String(120), nullable=True)
    dui = db.Column(db.String(20), nullable=True)
    nit = db.Column(db.String(20), nullable=True)
    __table_args__ = (db.UniqueConstraint('email', 'tenant_id'),)

    applications = db.relationship('LoanApplication', backref='applicant', lazy='dynamic')
    communication_logs = db.relationship('CommunicationLog', backref='user', lazy='dynamic')
    audit_logs = db.relationship('AuditLog', backref='user', lazy='dynamic')

    def set_password(self, password): self.password_hash = generate_password_hash(password)
    def check_password(self, password): return check_password_hash(self.password_hash, password)

class LoanProduct(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    tenant = db.relationship('Tenant')
    name = db.Column(db.String(100), nullable=False)
    min_amount = db.Column(db.Float, nullable=False)
    max_amount = db.Column(db.Float, nullable=False)
    interest_rate = db.Column(db.Float, nullable=False)
    commission_rate = db.Column(db.Float, nullable=False, default=0.01)
    term_months = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    applications = db.relationship('LoanApplication', backref='product', lazy=True)
    __table_args__ = (db.UniqueConstraint('name', 'tenant_id'),)

class LoanApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('loan_product.id'), nullable=False)
    amount_requested = db.Column(db.Float, nullable=False)
    term_months = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Pendiente')
    application_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    decision_date = db.Column(db.DateTime, nullable=True)
    disbursement_date = db.Column(db.DateTime, nullable=True)
    monthly_payment = db.Column(db.Float, nullable=True)
    total_payment = db.Column(db.Float, nullable=True)
    commission_calculation_method = db.Column(db.String(50), default='Al Inicio', nullable=False)
    signature_image = db.Column(db.Text, nullable=True)
    signed_at = db.Column(db.DateTime, nullable=True)
    contract_id = db.Column(db.String(100), nullable=True) # To store a reference to the generated contract
    payments = db.relationship('Payment', backref='application', lazy='dynamic')

class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    normal_balance = db.Column(db.String(10), nullable=False)
    transactions = db.relationship('Transaction', backref='account', lazy=True)
    __table_args__ = (db.UniqueConstraint('name', 'tenant_id'),)

class JournalEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    description = db.Column(db.String(255), nullable=False)
    transactions = db.relationship('Transaction', backref='journal_entry', lazy='dynamic', cascade="all, delete-orphan")

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    journal_entry_id = db.Column(db.Integer, db.ForeignKey('journal_entry.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    type = db.Column(db.String(10), nullable=False)
    amount = db.Column(db.Float, nullable=False)

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=True) # Can be nullable if not all employees are users
    position = db.Column(db.String(100), nullable=False)
    salary = db.Column(db.Float, nullable=False)
    hire_date = db.Column(db.Date, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    qr_code_token = db.Column(db.String(255), nullable=True, unique=True)
    tasks = db.relationship('Task', backref='assignee', lazy='dynamic')

# --- Attendance Models (LAN-AT5) ---

class AttendanceRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    employee = db.relationship('Employee')
    timestamp = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    event_type = db.Column(db.String(50), nullable=False) # 'Entrada' or 'Salida'

class Lead(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    status = db.Column(db.String(50), nullable=False, default='Nuevo')
    communication_logs = db.relationship('CommunicationLog', backref='lead', lazy='dynamic')

class CommunicationLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    employee = db.relationship('Employee')
    type = db.Column(db.String(50), nullable=False)
    notes = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    application_id = db.Column(db.Integer, db.ForeignKey('loan_application.id'), nullable=False)
    amount_paid = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.Date, nullable=False)
    registered_by_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    journal_entry_id = db.Column(db.Integer, db.ForeignKey('journal_entry.id'), nullable=True)

class NotificationTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=True) # Can be global (tenant_id=NULL)
    slug = db.Column(db.String(50), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)
    __table_args__ = (db.UniqueConstraint('slug', 'tenant_id'),)

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

class Opportunity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    stage = db.Column(db.String(50), nullable=False, default='Calificación')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    client = db.relationship('User')

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    tasks = db.relationship('Task', backref='project', lazy='dynamic', cascade="all, delete-orphan")

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    assignee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=True)

# --- Bank Reconciliation Models (LAN-CB7) ---

class BankAccountStatement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False) # The internal bank account
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    start_balance = db.Column(db.Float, nullable=False)
    end_balance = db.Column(db.Float, nullable=False)
    uploaded_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    status = db.Column(db.String(50), default='Pending', nullable=False) # Pending, In Progress, Completed
    transactions = db.relationship('BankTransaction', backref='statement', lazy='dynamic', cascade="all, delete-orphan")

class BankTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    statement_id = db.Column(db.Integer, db.ForeignKey('bank_account_statement.id'), nullable=False)
    transaction_date = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(50), nullable=False) # Debit or Credit
    status = db.Column(db.String(50), default='Unreconciled', nullable=False) # Unreconciled, Reconciled, Mismatch
    journal_entry_id = db.Column(db.Integer, db.ForeignKey('journal_entry.id'), nullable=True) # Link to the reconciled entry

# --- Absence Management Models (LAN-V1A) ---

class AbsenceRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    employee = db.relationship('Employee')
    absence_type = db.Column(db.String(50), nullable=False) # E.g., 'Vacaciones', 'Enfermedad', 'Personal'
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(50), default='Pendiente', nullable=False) # Pendiente, Aprobada, Rechazada
    approved_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # User who approved/rejected
    approved_by = db.relationship('User')
    comments = db.Column(db.Text, nullable=True)

# --- Onboarding Models (LAN-OBD2) ---

class OnboardingTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    steps = db.relationship('OnboardingStep', backref='template', lazy='dynamic', cascade="all, delete-orphan")

class OnboardingStep(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey('onboarding_template.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    order = db.Column(db.Integer, nullable=False)
    step_type = db.Column(db.String(50), nullable=False) # E.g., 'Documento', 'Formulario', 'Firma'
    resource_link = db.Column(db.String(255), nullable=True) # Link to a form or document template

class EmployeeOnboarding(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    employee = db.relationship('Employee')
    template_id = db.Column(db.Integer, db.ForeignKey('onboarding_template.id'), nullable=False)
    template = db.relationship('OnboardingTemplate')
    status = db.Column(db.String(50), default='Pendiente', nullable=False) # Pendiente, En Progreso, Completado
    completed_steps = db.Column(db.JSON, default=[]) # List of completed step IDs

# --- Recruitment Models (LAN-REC7) ---

class JobVacancy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='Abierta', nullable=False) # Abierta, Cerrada
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_by = db.relationship('User')
    applications = db.relationship('Application', backref='job_vacancy', lazy='dynamic')

class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    full_name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(50), nullable=True)
    resume_url = db.Column(db.String(255), nullable=True)
    applications = db.relationship('Application', backref='candidate', lazy='dynamic')
    __table_args__ = (db.UniqueConstraint('email', 'tenant_id'),)

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'), nullable=False)
    job_vacancy_id = db.Column(db.Integer, db.ForeignKey('job_vacancy.id'), nullable=False)
    application_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    status = db.Column(db.String(50), default='Nuevo', nullable=False) # Nuevo, Revisión, Entrevista, Oferta, Contratado, Rechazado