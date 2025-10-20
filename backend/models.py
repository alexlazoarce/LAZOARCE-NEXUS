from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import MetaData

convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)
db = SQLAlchemy(metadata=metadata)

# --- Core Tenant & Subscription Models ---

class Tenant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(120), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    deployment_type = db.Column(db.String(50), default='SaaS', nullable=False) # SaaS or On-Premise
    license_key = db.Column(db.String(100), unique=True, nullable=True)
    roles = db.relationship('Role', backref='tenant', lazy=True, cascade="all, delete-orphan")
    subscriptions = db.relationship('TenantSubscription', backref='tenant', lazy=True, cascade="all, delete-orphan")

class SystemModule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    module_code = db.Column(db.String(20), unique=True, nullable=False) # e.g., LAN-GP1
    module_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)

class TenantSubscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    module_id = db.Column(db.Integer, db.ForeignKey('system_module.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False, default=db.func.current_date())
    end_date = db.Column(db.Date, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    is_trial = db.Column(db.Boolean, default=False)
    module = db.relationship('SystemModule')
    __table_args__ = (db.UniqueConstraint('tenant_id', 'module_id'),)


# --- Tenant-Specific Foundational Models ---

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    users = db.relationship('User', backref='role', lazy=True)
    __table_args__ = (db.UniqueConstraint('name', 'tenant_id'),)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)
    full_name = db.Column(db.String(120), nullable=True)
    dui = db.Column(db.String(20), nullable=True)
    nit = db.Column(db.String(20), nullable=True)
    tenant = db.relationship('Tenant', backref='users')
    __table_args__ = (db.UniqueConstraint('email', 'tenant_id'),)

    def set_password(self, password): self.password_hash = generate_password_hash(password)
    def check_password(self, password): return check_password_hash(self.password_hash, password)

# --- Accounting Module (LAN-BKS1) ---

class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False) # Activo, Pasivo, Patrimonio, Ingreso, Gasto
    normal_balance = db.Column(db.String(10), nullable=False) # Debit or Credit
    __table_args__ = (db.UniqueConstraint('name', 'tenant_id'),)

class JournalEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    description = db.Column(db.String(255), nullable=False)
    transactions = db.relationship('Transaction', backref='journal_entry', lazy='dynamic', cascade="all, delete-orphan")

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    journal_entry_id = db.Column(db.Integer, db.ForeignKey('journal_entry.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    type = db.Column(db.String(10), nullable=False) # debit or credit
    amount = db.Column(db.Float, nullable=False)
    account = db.relationship('Account')

class TaxType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False) # e.g., IVA, ISR
    rate = db.Column(db.Float, nullable=False)
    country_code = db.Column(db.String(3), nullable=False)
    __table_args__ = (db.UniqueConstraint('name', 'country_code', 'tenant_id'),)

# --- Loan Management Module (LAN-GP1) ---

class LoanProduct(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    min_amount = db.Column(db.Float, nullable=False)
    max_amount = db.Column(db.Float, nullable=False)
    interest_rate = db.Column(db.Float, nullable=False) # Annual
    commission_rate = db.Column(db.Float, nullable=False, default=0.0)
    term_months = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    __table_args__ = (db.UniqueConstraint('name', 'tenant_id'),)

class LoanApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    applicant = db.relationship('User')
    product_id = db.Column(db.Integer, db.ForeignKey('loan_product.id'), nullable=False)
    product = db.relationship('LoanProduct')
    amount_requested = db.Column(db.Float, nullable=False)
    term_months = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Pendiente') # Pendiente, Aprobado, Desembolsado, Rechazado, Pagado
    application_date = db.Column(db.Date, nullable=False, default=db.func.current_date())
    decision_date = db.Column(db.Date, nullable=True)
    disbursement_date = db.Column(db.Date, nullable=True)
    monthly_payment = db.Column(db.Float, nullable=True)
    total_payment = db.Column(db.Float, nullable=True)
    contract_id = db.Column(db.String(100), nullable=True)
    signature_image = db.Column(db.Text, nullable=True)
    signed_at = db.Column(db.DateTime, nullable=True)

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('loan_application.id'), nullable=False)
    application = db.relationship('LoanApplication', backref='payments')
    amount_paid = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.Date, nullable=False)
    journal_entry_id = db.Column(db.Integer, db.ForeignKey('journal_entry.id'), nullable=True)


# --- HR Modules ---

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # Link to a user account
    user = db.relationship('User', backref='employee_profile')
    full_name = db.Column(db.String(120), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    salary = db.Column(db.Float, nullable=False)
    hire_date = db.Column(db.Date, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    country_code = db.Column(db.String(3), nullable=False, default='SV') # SV, GT, HN
    qr_code_token = db.Column(db.String(255), unique=True, nullable=True) # For LAN-AT5

class AbsenceRequest(db.Model): # LAN-V1A
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    employee = db.relationship('Employee', backref='absence_requests')
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default='Pending', nullable=False) # Pending, Approved, Rejected

class JobVacancy(db.Model): # LAN-REC7
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    is_open = db.Column(db.Boolean, default=True)

class Candidate(db.Model): # LAN-REC7
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    resume_url = db.Column(db.String(255), nullable=True)
    __table_args__ = (db.UniqueConstraint('email', 'tenant_id'),)

class Application(db.Model): # LAN-REC7
    id = db.Column(db.Integer, primary_key=True)
    vacancy_id = db.Column(db.Integer, db.ForeignKey('job_vacancy.id'), nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'), nullable=False)
    application_date = db.Column(db.Date, default=db.func.current_date())
    status = db.Column(db.String(50), default='Received') # Received, Interviewing, Offered, Hired, Rejected
    vacancy = db.relationship('JobVacancy', backref='applications')
    candidate = db.relationship('Candidate', backref='applications')

class AttendanceRecord(db.Model): # LAN-AT5
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    employee = db.relationship('Employee', backref='attendance_records')
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    record_type = db.Column(db.String(10), nullable=False) # 'entry' or 'exit'

# --- Onboarding Module (LAN-OBD2) ---
class OnboardingTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    steps = db.relationship('OnboardingStep', backref='template', lazy='dynamic', cascade="all, delete-orphan")

class OnboardingStep(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey('onboarding_template.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    order = db.Column(db.Integer, nullable=False)

class EmployeeOnboarding(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    employee = db.relationship('Employee', backref='onboarding_process')
    template_id = db.Column(db.Integer, db.ForeignKey('onboarding_template.id'), nullable=False)
    completed_steps = db.Column(db.JSON, default=dict) # {step_id: completed_date}
    status = db.Column(db.String(50), default='In Progress') # In Progress, Completed

# --- Document Management (LAN-GD2) ---

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_by = db.relationship('User')
    latest_version_id = db.Column(db.Integer, nullable=True) # Self-referential FK after DocumentVersion is defined

class DocumentVersion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=False)
    document = db.relationship('Document', backref='versions', foreign_keys=[document_id])
    version_number = db.Column(db.Integer, nullable=False)
    file_path = db.Column(db.String(512), nullable=False) # Path in storage
    uploaded_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    uploaded_by = db.relationship('User')

# --- E-Invoicing (LAN-FE2) & Recurring Billing (LAN-BIL9) ---

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    customer = db.relationship('User')
    issue_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='Draft') # Draft, Sent, Paid, Void
    items = db.relationship('InvoiceItem', backref='invoice', lazy='dynamic', cascade="all, delete-orphan")

class InvoiceItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total = db.Column(db.Float, nullable=False)

class SubscriptionPlan(db.Model): # LAN-BIL9
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    billing_cycle = db.Column(db.String(20)) # e.g., 'monthly', 'yearly'
    __table_args__ = (db.UniqueConstraint('name', 'tenant_id'),)

class Subscription(db.Model): # LAN-BIL9
    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('subscription_plan.id'), nullable=False)
    plan = db.relationship('SubscriptionPlan')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User')
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    is_active = db.Column(db.Boolean, default=True)

# --- Bank Reconciliation (LAN-CB7) ---

class BankAccountStatement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    account_number = db.Column(db.String(50), nullable=False)
    statement_date = db.Column(db.Date, nullable=False)
    transactions = db.relationship('BankTransaction', backref='statement', lazy='dynamic', cascade="all, delete-orphan")

class BankTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    statement_id = db.Column(db.Integer, db.ForeignKey('bank_account_statement.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    is_reconciled = db.Column(db.Boolean, default=False)
    journal_entry_id = db.Column(db.Integer, db.ForeignKey('journal_entry.id'), nullable=True)

# --- Expense Management (LAN-EXP3) ---
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    employee = db.relationship('Employee')
    date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), default='Submitted') # Submitted, Approved, Reimbursed, Rejected
    journal_entry_id = db.Column(db.Integer, db.ForeignKey('journal_entry.id'), nullable=True)

# --- Automation Modules (LAN-N8N1, LAN-MKE1) ---
class N8nWorkflow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    webhook_url = db.Column(db.String(512), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)

class N8nCredential(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    api_key = db.Column(db.String(255), nullable=False) # Encrypted
    n8n_instance_url = db.Column(db.String(255), nullable=False)

class MakeScenario(db.Model): # LAN-MKE1
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    webhook_url = db.Column(db.String(512), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)

class MakeConnection(db.Model): # LAN-MKE1
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    api_key = db.Column(db.String(255), nullable=False) # Encrypted

# --- Electronic Signature (LAN-FEV8) ---
class SignatureRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=False)
    document = db.relationship('Document')
    signer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    signer = db.relationship('User')
    status = db.Column(db.String(50), default='Pending') # Pending, Signed, Rejected
    signature_data = db.Column(db.Text, nullable=True)
    signed_at = db.Column(db.DateTime, nullable=True)

# --- Vertical Modules (LAN-GYM1, LAN-BAR1, LAN-ET2) ---

class GymMembershipPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    duration_days = db.Column(db.Integer, nullable=False)

class GymMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    user = db.relationship('User')
    plan_id = db.Column(db.Integer, db.ForeignKey('gym_membership_plan.id'), nullable=False)
    plan = db.relationship('GymMembershipPlan')
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)

class GymClass(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    instructor = db.Column(db.String(100), nullable=False)
    schedule = db.Column(db.DateTime, nullable=False)
    max_capacity = db.Column(db.Integer, nullable=False)

class ClassAttendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('gym_class.id'), nullable=False)
    gym_class = db.relationship('GymClass', backref='attendees')
    member_id = db.Column(db.Integer, db.ForeignKey('gym_member.id'), nullable=False)
    member = db.relationship('GymMember', backref='classes_attended')
    check_in_time = db.Column(db.DateTime, default=db.func.current_timestamp())


class Stylist(db.Model): # LAN-BAR1
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    is_available = db.Column(db.Boolean, default=True)

class Appointment(db.Model): # LAN-BAR1
    id = db.Column(db.Integer, primary_key=True)
    stylist_id = db.Column(db.Integer, db.ForeignKey('stylist.id'), nullable=False)
    stylist = db.relationship('Stylist', backref='appointments')
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    customer = db.relationship('User')
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    service = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), default='Scheduled') # Scheduled, Completed, Cancelled

class ClientCompany(db.Model): # LAN-ET2
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    contact_person = db.Column(db.String(120), nullable=True)

class TemporaryAssignment(db.Model): # LAN-ET2
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    employee = db.relationship('Employee')
    client_company_id = db.Column(db.Integer, db.ForeignKey('client_company.id'), nullable=False)
    client_company = db.relationship('ClientCompany')
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    hourly_rate = db.Column(db.Float, nullable=False)

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
    user = db.relationship('User', backref='audit_logs')
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
    assignee = db.relationship('Employee', backref='tasks')
