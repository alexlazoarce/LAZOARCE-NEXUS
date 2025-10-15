from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

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

    applications = db.relationship('LoanApplication', backref='applicant', lazy=True)
    communication_logs = db.relationship('CommunicationLog', backref='user', lazy='dynamic')
    audit_logs = db.relationship('AuditLog', backref='user', lazy='dynamic')
    tickets = db.relationship('Ticket', backref='created_by_user', lazy='dynamic', foreign_keys='Ticket.user_id')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class LoanProduct(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    min_amount = db.Column(db.Float, nullable=False)
    max_amount = db.Column(db.Float, nullable=False)
    interest_rate = db.Column(db.Float, nullable=False) # Annual interest rate
    commission_rate = db.Column(db.Float, nullable=False, default=0.01) # Monthly commission rate
    term_months = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    applications = db.relationship('LoanApplication', backref='product', lazy=True)

    # Timestamps
    application_date = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    decision_date = db.Column(db.DateTime, nullable=True)

    # Link to the accounting entry for disbursement
    disbursement_entry_id = db.Column(db.Integer, db.ForeignKey('journal_entry.id'), nullable=True)
    disbursement_entry = db.relationship('JournalEntry', foreign_keys=[disbursement_entry_id])


    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'min_amount': self.min_amount,
            'max_amount': self.max_amount,
            'interest_rate': self.interest_rate,
            'commission_rate': self.commission_rate,
            'term_months': self.term_months,
            'is_active': self.is_active
        }

class LoanApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('loan_product.id'), nullable=False)

    amount_requested = db.Column(db.Float, nullable=False)
    term_months = db.Column(db.Integer, nullable=False)
    commission_calculation_method = db.Column(db.String(1), nullable=False) # 'A', 'B', or 'C'

    status = db.Column(db.String(20), nullable=False, default='Pendiente') # e.g., Pendiente, Aprobada, Rechazada, Desembolsada

    # Calculated fields to be stored
    monthly_payment = db.Column(db.Float, nullable=True)
    total_payment = db.Column(db.Float, nullable=True)

    # Timestamps
    application_date = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    decision_date = db.Column(db.DateTime, nullable=True) # Approval or rejection date

    payments = db.relationship('Payment', backref='application', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'applicant_name': self.applicant.full_name,
            'product_id': self.product_id,
            'product_name': self.product.name,
            'amount_requested': self.amount_requested,
            'term_months': self.term_months,
            'commission_calculation_method': self.commission_calculation_method,
            'status': self.status,
            'monthly_payment': self.monthly_payment,
            'total_payment': self.total_payment,
            'application_date': self.application_date.isoformat() if self.application_date else None,
            'decision_date': self.decision_date.isoformat() if self.decision_date else None,
        }

# --- Accounting Models ---

class Account(db.Model):
    """Represents a single account in the chart of accounts."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    # e.g., 'Asset', 'Liability', 'Equity', 'Revenue', 'Expense'
    category = db.Column(db.String(50), nullable=False)
    # Normal balance: 'Debit' or 'Credit'
    normal_balance = db.Column(db.String(10), nullable=False)

    transactions = db.relationship('Transaction', backref='account', lazy=True)

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'category': self.category}

class JournalEntry(db.Model):
    """Represents a single, balanced accounting entry (a collection of transactions)."""
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    description = db.Column(db.String(255), nullable=False)
    transactions = db.relationship('Transaction', backref='journal_entry', lazy='dynamic', cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'description': self.description,
            'transactions': [t.to_dict() for t in self.transactions]
        }

class Transaction(db.Model):
    """Represents a single debit or credit in a journal entry."""
    id = db.Column(db.Integer, primary_key=True)
    journal_entry_id = db.Column(db.Integer, db.ForeignKey('journal_entry.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    # 'Debit' or 'Credit'
    type = db.Column(db.String(10), nullable=False)
    amount = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {
            'account_name': self.account.name,
            'type': self.type,
            'amount': self.amount
        }

# --- HR / Payroll Models ---

class Employee(db.Model):
    """Represents an employee of the company."""
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    salary = db.Column(db.Float, nullable=False) # Monthly salary
    hire_date = db.Column(db.Date, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Personal Information for payroll
    dui = db.Column(db.String(20), nullable=True, unique=True)
    nit = db.Column(db.String(20), nullable=True, unique=True)
    isss_number = db.Column(db.String(20), nullable=True, unique=True)
    afp_number = db.Column(db.String(20), nullable=True, unique=True)

    payslips = db.relationship('PaySlip', backref='employee', lazy=True)
    assigned_tickets = db.relationship('Ticket', backref='assigned_employee', lazy='dynamic', foreign_keys='Ticket.assigned_to_id')

    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'position': self.position,
            'salary': self.salary,
            'hire_date': self.hire_date.isoformat() if self.hire_date else None,
            'is_active': self.is_active,
            'dui': self.dui,
            'nit': self.nit,
            'isss_number': self.isss_number,
            'afp_number': self.afp_number,
        }

class PayrollLog(db.Model):
    """Represents a record of a payroll run for a specific period."""
    id = db.Column(db.Integer, primary_key=True)
    period_start_date = db.Column(db.Date, nullable=False)
    period_end_date = db.Column(db.Date, nullable=False)
    execution_date = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    total_paid = db.Column(db.Float, nullable=False)

    payslips = db.relationship('PaySlip', backref='payroll_log', lazy=True)

class PaySlip(db.Model):
    """Represents an individual employee's payslip for a specific payroll period."""
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    payroll_log_id = db.Column(db.Integer, db.ForeignKey('payroll_log.id'), nullable=False)

    gross_salary = db.Column(db.Float, nullable=False)
    isss_deduction = db.Column(db.Float, nullable=False)
    afp_deduction = db.Column(db.Float, nullable=False)
    renta_deduction = db.Column(db.Float, nullable=False)
    net_salary = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'employee_name': self.employee.full_name,
            'gross_salary': self.gross_salary,
            'isss_deduction': self.isss_deduction,
            'afp_deduction': self.afp_deduction,
            'renta_deduction': self.renta_deduction,
            'net_salary': self.net_salary,
        }

# --- CRM Models ---

class Lead(db.Model):
    """Represents a potential customer (a lead)."""
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(20), nullable=True)

    # e.g., 'Nuevo', 'Contactado', 'Calificado', 'No Calificado'
    status = db.Column(db.String(50), nullable=False, default='Nuevo')
    # e.g., 'Referencia', 'Web', 'Campaña Publicitaria'
    source = db.Column(db.String(100), nullable=True)

    notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    # Optional: Assign a lead to a specific employee
    # assigned_to_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=True)
    # assigned_to = db.relationship('Employee')
    communication_logs = db.relationship('CommunicationLog', backref='lead', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'status': self.status,
            'source': self.source,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

class CommunicationLog(db.Model):
    """Represents a single interaction with a lead or client."""
    id = db.Column(db.Integer, primary_key=True)

    # Can be linked to a lead, a user, or both if the lead was converted
    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    # The employee who logged the communication
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    employee = db.relationship('Employee')

    # e.g., 'Llamada', 'Email', 'Reunión'
    type = db.Column(db.String(50), nullable=False)
    notes = db.Column(db.Text, nullable=False)

    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

    def to_dict(self):
        return {
            'id': self.id,
            'employee_name': self.employee.full_name,
            'type': self.type,
            'notes': self.notes,
            'timestamp': self.timestamp.isoformat(),
        }

# --- Collections Models ---

class Payment(db.Model):
    """Represents a payment made towards a loan."""
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('loan_application.id'), nullable=False)
    amount_paid = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.Date, nullable=False)

    # e.g., 'Cuota', 'Abono a Capital', 'Cancelación'
    type = db.Column(db.String(50), nullable=False, default='Cuota')

    # The employee who registered the payment
    registered_by_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    registered_by = db.relationship('Employee')

    # Link to the accounting entry for this payment
    journal_entry_id = db.Column(db.Integer, db.ForeignKey('journal_entry.id'), nullable=True)
    journal_entry = db.relationship('JournalEntry')

    def to_dict(self):
        return {
            'id': self.id,
            'application_id': self.application_id,
            'amount_paid': self.amount_paid,
            'payment_date': self.payment_date.isoformat(),
            'type': self.type,
            'registered_by': self.registered_by.full_name,
        }

# --- Notifications Models ---

class NotificationTemplate(db.Model):
    """Stores templates for emails or other notifications."""
    id = db.Column(db.Integer, primary_key=True)
    # A unique, code-friendly identifier, e.g., 'loan-approved'
    slug = db.Column(db.String(50), unique=True, nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False) # Can contain placeholders like {customer_name}
    type = db.Column(db.String(20), nullable=False, default='Email') # 'Email', 'SMS', etc.

    def to_dict(self):
        return {
            'id': self.id,
            'slug': self.slug,
            'subject': self.subject,
            'body': self.body,
            'type': self.type,
        }

# --- Auditing Models ---

class AuditLog(db.Model):
    """Logs critical actions performed in the system."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False) # e.g., 'LOAN_STATUS_CHANGED'
    details = db.Column(db.Text, nullable=True) # e.g., 'Loan 123 status changed from Pending to Approved'
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

    def to_dict(self):
        return {
            'id': self.id,
            'user_email': self.user.email,
            'action': self.action,
            'details': self.details,
            'timestamp': self.timestamp.isoformat(),
        }

class Opportunity(db.Model):
    """Represents a sales opportunity or a deal."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)

    # The value of the potential deal
    amount = db.Column(db.Float, nullable=True)

    # e.g., 'Calificación', 'Propuesta', 'Negociación', 'Ganada', 'Perdida'
    stage = db.Column(db.String(50), nullable=False, default='Calificación')

    close_date = db.Column(db.Date, nullable=True)

    # Link to the original lead and the converted user/client
    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'), nullable=True)
    lead = db.relationship('Lead')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    client = db.relationship('User')

    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'amount': self.amount,
            'stage': self.stage,
            'close_date': self.close_date.isoformat() if self.close_date else None,
            'client_name': self.client.full_name if self.client else (self.lead.full_name if self.lead else None)
        }

# --- Marketing Models ---

mailing_list_members = db.Table('mailing_list_members',
    db.Column('mailing_list_id', db.Integer, db.ForeignKey('mailing_list.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

class MailingList(db.Model):
    """Represents a list of users for marketing campaigns."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)

    members = db.relationship('User', secondary=mailing_list_members, lazy='dynamic',
                              backref=db.backref('mailing_lists', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'member_count': self.members.count()
        }

class Campaign(db.Model):
    """Represents a marketing email campaign."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    subject = db.Column(db.String(255), nullable=False)

    # e.g., 'Draft', 'Scheduled', 'Sent'
    status = db.Column(db.String(50), nullable=False, default='Draft')

    mailing_list_id = db.Column(db.Integer, db.ForeignKey('mailing_list.id'), nullable=False)
    mailing_list = db.relationship('MailingList')

    template_id = db.Column(db.Integer, db.ForeignKey('notification_template.id'), nullable=False)
    template = db.relationship('NotificationTemplate')

    sent_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'subject': self.subject,
            'status': self.status,
            'mailing_list_name': self.mailing_list.name,
            'template_slug': self.template.slug,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
        }

# --- Helpdesk / Ticketing Models ---

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(255), nullable=False)

    # e.g., 'Abierto', 'En Progreso', 'Cerrado'
    status = db.Column(db.String(50), nullable=False, default='Abierto')
    # e.g., 'Baja', 'Normal', 'Alta'
    priority = db.Column(db.String(50), nullable=False, default='Normal')

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=True)

    comments = db.relationship('TicketComment', backref='ticket', lazy='dynamic', cascade="all, delete-orphan")

    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    def to_dict(self):
        return {
            'id': self.id,
            'subject': self.subject,
            'status': self.status,
            'priority': self.priority,
            'created_by': self.created_by_user.full_name,
            'assigned_to': self.assigned_employee.full_name if self.assigned_employee else 'Sin asignar',
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

class TicketComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # User who made the comment
    comment_text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

    def to_dict(self):
        commenter = User.query.get(self.user_id)
        return {
            'id': self.id,
            'commenter_name': commenter.full_name,
            'comment_text': self.comment_text,
            'timestamp': self.timestamp.isoformat()
        }

# --- Firma Electrónica (FEV) Models ---

class SignatureRequest(db.Model):
    """Tracks the status of an electronic signature request."""
    id = db.Column(db.Integer, primary_key=True)

    # Link to the document being signed, e.g., a loan application contract
    loan_application_id = db.Column(db.Integer, db.ForeignKey('loan_application.id'), nullable=False)
    loan_application = db.relationship('LoanApplication', backref='signature_requests')

    # ID from the external signature provider
    provider_request_id = db.Column(db.String(255), unique=True, nullable=False)

    # Status: 'pending', 'completed', 'failed', 'expired'
    status = db.Column(db.String(50), nullable=False, default='pending')

    signer_email = db.Column(db.String(120), nullable=False)

    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    def to_dict(self):
        return {
            'id': self.id,
            'loan_application_id': self.loan_application_id,
            'status': self.status,
            'signer_email': self.signer_email,
            'provider_request_id': self.provider_request_id,
            'created_at': self.created_at.isoformat(),
        }