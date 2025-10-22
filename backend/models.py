from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
from sqlalchemy import func, Boolean, Date, DateTime, Float, Integer, String, Text, ForeignKey, UniqueConstraint, CheckConstraint
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

channel_members = db.Table('messaging_channel_members',
    db.Column('channel_id', Integer, ForeignKey('messaging_channel.id'), primary_key=True),
    db.Column('user_id', Integer, ForeignKey('user.id'), primary_key=True),
    schema='public'
)

# === MODELOS DE SEGURIDAD Y TENANTS ===
class Tenant(db.Model):
    """Soporte Multi-tenant - Empresas/Organizaciones"""
    __tablename__ = 'tenant'
    id = db.Column(Integer, primary_key=True)
    company_name = db.Column(String(100), unique=True, nullable=False, index=True)
    company_code = db.Column(String(20), unique=True, nullable=False)
    domain = db.Column(String(100), unique=True, nullable=True) # Domain puede ser opcional
    is_active = db.Column(Boolean, default=True)
    created_at = db.Column(DateTime, default=func.current_timestamp())
    config = db.Column(JSONB, default=dict)
    users = db.relationship('User', backref='tenant', lazy='dynamic', cascade="all, delete-orphan")
    roles = db.relationship('Role', backref='tenant', lazy='dynamic', cascade="all, delete-orphan")
    loan_products = db.relationship('LoanProduct', backref='tenant', lazy='dynamic', cascade="all, delete-orphan")
    def __repr__(self):
        return f'<Tenant {self.company_name}>'

class Role(db.Model):
    """Roles de usuario con soporte multi-tenant"""
    __tablename__ = 'role'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(80), nullable=False, index=True)
    description = db.Column(String(255), nullable=True)
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    is_active = db.Column(Boolean, default=True)
    users = db.relationship('User', secondary=user_roles, back_populates='roles_m2m')
    __table_args__ = (UniqueConstraint('name', 'tenant_id', name='_role_name_tenant_uc'),)
    def __repr__(self):
        return f'<Role {self.name}>'

class User(db.Model):
    """Usuarios con autenticación y perfil completo"""
    __tablename__ = 'user'
    id = db.Column(Integer, primary_key=True)
    email = db.Column(String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(String(256), nullable=False)
    full_name = db.Column(String(120), nullable=True)
    dui = db.Column(String(20), unique=True, nullable=True, index=True)
    nit = db.Column(String(20), unique=True, nullable=True, index=True)
    is_active = db.Column(Boolean, default=True)
    last_login = db.Column(DateTime, nullable=True)
    created_at = db.Column(DateTime, default=func.current_timestamp())
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    role_id = db.Column(Integer, ForeignKey('role.id'), nullable=True) # Hacer role_id opcional si se usa M2M
    roles_m2m = db.relationship('Role', secondary=user_roles, back_populates='users')
    profile = db.relationship('ClientProfile', backref='user', uselist=False, cascade="all, delete-orphan")
    employee = db.relationship('Employee', backref='user', uselist=False, cascade="all, delete-orphan")
    applications = db.relationship('LoanApplication', backref='applicant', lazy='dynamic', cascade="all, delete-orphan")
    audit_logs = db.relationship('AuditLog', backref='user', lazy='dynamic', cascade="all, delete-orphan")
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    @property
    def role(self): # Propiedad para acceder al rol directo si existe
        return db.session.get(Role, self.role_id) if self.role_id else None
    def __repr__(self):
        return f'<User {self.email}>'

class ClientProfile(db.Model):
    """Perfil detallado de cliente (puede aplicar a User o Contact)"""
    __tablename__ = 'client_profile'
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(Integer, ForeignKey('user.id'), unique=True, nullable=True) # Opcional si el perfil es para un Contacto CRM
    contact_id = db.Column(Integer, ForeignKey('crm_contact.id'), unique=True, nullable=True) # Opcional si el perfil es para un User
    full_name = db.Column(String(120), nullable=True) # Puede diferir del User.full_name
    phone_number = db.Column(String(20))
    secondary_phone = db.Column(String(20), nullable=True)
    address = db.Column(Text, nullable=True)
    birth_date = db.Column(Date, nullable=True)
    occupation = db.Column(String(100), nullable=True)
    employer = db.Column(String(100), nullable=True)
    monthly_income = db.Column(Float, nullable=True)
    reference_name = db.Column(String(120), nullable=True)
    reference_phone = db.Column(String(20), nullable=True)
    # Check constraint to ensure it links to either user or contact, but not both? Or maybe allow both?
    # __table_args__ = (CheckConstraint('(user_id IS NOT NULL AND contact_id IS NULL) OR (user_id IS NULL AND contact_id IS NOT NULL)', name='_client_profile_link_check'),)

# --- MODELOS DE PRÉSTAMOS ---
class LoanProduct(db.Model):
    """Productos de préstamo configurables"""
    __tablename__ = 'loan_product'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(100), nullable=False, index=True)
    description = db.Column(Text, nullable=True)
    loan_type = db.Column(String(50), nullable=True)
    tasa_interes_anual = db.Column(Float, nullable=False)
    plazo_maximo = db.Column(Integer, nullable=True)
    min_amount = db.Column(Float, nullable=False, default=0.0)
    max_amount = db.Column(Float, nullable=False, default=0.0)
    comision_apertura = db.Column(Float, default=0.0)
    comision_administracion = db.Column(Float, default=0.0)
    seguro = db.Column(Float, default=0.0)
    comisiones_generan_intereses = db.Column(Boolean, default=False)
    comisiones_se_agregan_capital = db.Column(Boolean, default=False)
    comisiones_se_descuentan_capital = db.Column(Boolean, default=True)
    aplicar_tea = db.Column(Boolean, default=True)
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    is_active = db.Column(Boolean, default=True)
    created_at = db.Column(DateTime, default=func.current_timestamp())
    applications = db.relationship('LoanApplication', backref='product', lazy='dynamic', cascade="all, delete-orphan")
    __table_args__ = (UniqueConstraint('name', 'tenant_id', name='_loan_product_tenant_uc'),)

class LoanApplication(db.Model):
    """Solicitudes de préstamo"""
    __tablename__ = 'loan_application'
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(Integer, ForeignKey('user.id'), nullable=False, index=True)
    product_id = db.Column(Integer, ForeignKey('loan_product.id'), nullable=False, index=True)
    amount_requested = db.Column(Float, nullable=False)
    term_months = db.Column(Integer, nullable=False)
    status = db.Column(String(50), default='Solicitud Recibida', nullable=False)
    application_date = db.Column(DateTime, default=func.current_timestamp())
    monthly_payment = db.Column(Float, nullable=True)
    total_payment = db.Column(Float, nullable=True)
    tea_calculada = db.Column(Float, nullable=True)
    disbursement_entry_id = db.Column(Integer, ForeignKey('journal_entry.id'), nullable=True)
    disbursement_entry = db.relationship('JournalEntry', foreign_keys=[disbursement_entry_id], backref='disbursed_application', uselist=False)
    payments = db.relationship('Payment', backref='application', lazy='dynamic', cascade="all, delete-orphan")

class Payment(db.Model):
    """Pagos de un préstamo"""
    __tablename__ = 'payment'
    id = db.Column(Integer, primary_key=True)
    loan_application_id = db.Column(Integer, ForeignKey('loan_application.id'), nullable=False, index=True) # Added index
    amount = db.Column(Float, nullable=False)
    payment_date = db.Column(DateTime, default=func.current_timestamp(), index=True) # Added index

# --- MODELOS CONTABLES ---
class Account(db.Model):
    """Plan de cuentas contable"""
    __tablename__ = 'account'
    id = db.Column(Integer, primary_key=True)
    account_code = db.Column(String(20), nullable=False, index=True)
    name = db.Column(String(100), nullable=False)
    category = db.Column(String(50), nullable=False) # Activo, Pasivo, Patrimonio, Ingreso, Gasto
    normal_balance = db.Column(String(10), nullable=False) # debit, credit
    account_type = db.Column(String(50), nullable=True) # Detalle, Control
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    is_active = db.Column(Boolean, default=True)
    transactions = db.relationship('Transaction', backref='account', lazy='dynamic', cascade="all, delete-orphan")
    __table_args__ = (UniqueConstraint('account_code', 'tenant_id', name='_account_code_tenant_uc'),)

class JournalEntry(db.Model):
    """Asiento contable (Encabezado)"""
    __tablename__ = 'journal_entry'
    id = db.Column(Integer, primary_key=True)
    date = db.Column(DateTime, default=func.current_timestamp(), index=True)
    description = db.Column(String(500), nullable=False)
    reference = db.Column(String(100), nullable=True)
    created_by_id = db.Column(Integer, ForeignKey('user.id'), nullable=True)
    is_posted = db.Column(Boolean, default=False, index=True) # Added index
    posted_at = db.Column(DateTime, nullable=True)
    transactions = db.relationship('Transaction', backref='journal_entry', lazy='dynamic', cascade="all, delete-orphan")
    created_by = db.relationship('User', backref='created_journal_entries', foreign_keys=[created_by_id])

class Transaction(db.Model):
    """Movimiento contable individual (Detalle)"""
    __tablename__ = 'transaction'
    id = db.Column(Integer, primary_key=True)
    journal_entry_id = db.Column(Integer, ForeignKey('journal_entry.id'), nullable=False, index=True)
    account_id = db.Column(Integer, ForeignKey('account.id'), nullable=False, index=True)
    type = db.Column(String(10), nullable=False) # 'debit' or 'credit'
    amount = db.Column(Float, nullable=False, default=0.0)

# --- MODELOS DE RECURSOS HUMANOS / PAYROLL ---
class Employee(db.Model):
    """Empleados y personal"""
    __tablename__ = 'employee'
    id = db.Column(Integer, primary_key=True)
    full_name = db.Column(String(120), nullable=False, index=True)
    position = db.Column(String(100), nullable=True)
    salary = db.Column(Float, default=0.0) # Base salary per period (e.g., monthly)
    employee_type = db.Column(String(20), default='interno') # E.g., interno, externo, contratista
    hire_date = db.Column(Date, nullable=True)
    termination_date = db.Column(Date, nullable=True) # Added termination date
    is_active = db.Column(Boolean, default=True)
    user_id = db.Column(Integer, ForeignKey('user.id'), unique=True, nullable=True) # Link to User if they have system access
    payslips = db.relationship('PaySlip', backref='employee', lazy='dynamic', cascade="all, delete-orphan")
    # National/Tax IDs
    dui = db.Column(String(20), unique=True, index=True, nullable=True)
    nit = db.Column(String(20), unique=True, index=True, nullable=True)
    # Social Security / Pension IDs
    isss_number = db.Column(String(20), unique=True, nullable=True)
    afp_number = db.Column(String(20), unique=True, nullable=True)

class PaySlip(db.Model):
    """Planillas de pago"""
    __tablename__ = 'payslip'
    id = db.Column(Integer, primary_key=True)
    employee_id = db.Column(Integer, ForeignKey('employee.id'), nullable=False, index=True)
    period_start = db.Column(Date, nullable=False, index=True) # Added index
    period_end = db.Column(Date, nullable=False, index=True) # Added index
    payment_date = db.Column(Date, nullable=True) # Date the payment was actually made
    base_salary = db.Column(Float, nullable=False) # Salary for the period before deductions
    gross_salary = db.Column(Float, nullable=True) # Base + Bonuses/Overtime etc.
    # Deductions (example for El Salvador)
    isss_employee = db.Column(Float, nullable=False, default=0.0)
    afp_employee = db.Column(Float, nullable=False, default=0.0)
    renta = db.Column(Float, nullable=False, default=0.0) # Income Tax withheld
    other_deductions = db.Column(Float, default=0.0) # For loans, etc.
    total_deductions = db.Column(Float, nullable=True) # Sum of all deductions
    net_salary = db.Column(Float, nullable=False) # Gross - Deductions
    fecha_calculo = db.Column(DateTime, default=func.current_timestamp()) # When this record was calculated
    is_paid = db.Column(Boolean, default=False, index=True) # Added index
    paid_at = db.Column(DateTime, nullable=True)

# --- MODELOS DE FIRMA ELECTRÓNICA Y CONTRATOS ---
class Cliente(db.Model): ...
class ContratoIntegracion(db.Model): ...
class FirmaElectronica(db.Model): ...
class CertificadoValidacion(db.Model): ...

# --- MODELOS PARA FORMULACIÓN DE CONTRATOS (LAN-F2C) ---
class ContractTemplate(db.Model): ...
class GeneratedContract(db.Model): ...

# --- MODELOS PARA CRM (LAN-CRM3) ---
class Contact(db.Model): ...
class Interaction(db.Model): ...
class Opportunity(db.Model): ...

# --- MODELOS PARA INVENTARIO (LAN-INV9) ---
class Product(db.Model): ...
class StockMovement(db.Model): ...

# --- MODELOS PARA VENTAS (LAN-SLS2) ---
class Quote(db.Model): ...
class SalesOrder(db.Model): ...
class SalesOrderItem(db.Model): ...

# --- MODELOS PARA COMPRAS (LAN-CO1M) ---
class Supplier(db.Model): ...
class PurchaseOrder(db.Model): ...
class PurchaseOrderItem(db.Model): ...

# --- MODELOS PARA CORREO (LAN-MAIL1) ---
class EmailLog(db.Model): ...

# --- MODELOS DE MÓDULOS EXTENDIDOS ---
class MailingList(db.Model): ...

# --- MODELOS PARA GESTOR DE DOCUMENTOS (LAN-GD2) ---
class Document(db.Model): ...
# DocumentVersion se define al final

# --- MODELOS PARA MENSAJERÍA CORPORATIVA (LAN-C8T) ---
class Channel(db.Model): ...
class Message(db.Model): ...

# --- MODELOS PARA FIRMAR (LAN-SGN3) ---
class SignableTemplate(db.Model): ...
class SignatureRequest(db.Model): ...

# --- MODELOS PARA FORMULARIOS (LAN-FRM5) ---
class Form(db.Model): ...
class FormSubmission(db.Model): ...

# --- MODELOS PARA GESTIÓN DE PROYECTOS (LAN-PR0) ---
class Project(db.Model): ...
class Task(db.Model): ...

# --- MODELOS PARA SOPORTE TÉCNICO (LAN-SOP1) ---
class Ticket(db.Model): ...
class TicketUpdate(db.Model): ...

# --- MODELOS PARA ACTIVOS FIJOS (LAN-AFX4) ---
class FixedAsset(db.Model): ...
class DepreciationEntry(db.Model): ...

# --- MODELOS PARA CAJA Y BANCOS (LAN-CB2) ---
class BankAccount(db.Model): ...
class BankTransaction(db.Model): ...
class CashBox(db.Model): ...
class CashTransaction(db.Model): ...

# --- MODELOS PARA IMPUESTOS (LAN-TAX1) ---
class TaxType(db.Model): ...
class TaxDeclaration(db.Model): ...

# --- MODELOS PARA RECURSOS MATERIALES (LAN-RM1) ---
class Material(db.Model): ...
class MaterialRequest(db.Model): ...

# --- MODELOS PARA OBRAS Y CONSTRUCCIÓN (LAN-OBR5) ---
class ConstructionProject(db.Model): ...
class BudgetItem(db.Model): ...
class ProgressReport(db.Model): ...
class Certification(db.Model): ...
class RFI(db.Model): ...
class Milestone(db.Model): ...

# --- MODELOS PARA SALUD (LAN-H7S) ---
class PatientRecord(db.Model): ...
class MedicalAppointment(db.Model): ...
class Prescription(db.Model): ...
class LabOrder(db.Model): ...

# --- MODELOS PARA EDUCACIÓN (LAN-ED3U & LAN-UNV8) ---
class Student(db.Model): ...
class Course(db.Model): ...
class Enrollment(db.Model): ...
class Grade(db.Model): ...
class TuitionPayment(db.Model): ...
class DegreeProgram(db.Model): ...
class Scholarship(db.Model): ...
class StudentScholarship(db.Model): ...
class LibraryResource(db.Model): ...
class Alumnus(db.Model): ...

# --- MODELOS PARA LOGÍSTICA (LAN-LOG6) ---
class Vehicle(db.Model): ...
class Driver(db.Model): ...
class Route(db.Model): ...
class Delivery(db.Model): ...

# --- MODELOS PARA GESTIÓN DE RESTAURANTES (LAN-RST1) ---
class MenuItem(db.Model): ...
class Table(db.Model): ...
class RestaurantOrder(db.Model): ...
class RestaurantOrderItem(db.Model): ...

# --- MODELOS PARA COCINA COMERCIAL (LAN-KTC4) ---
class KitchenSpace(db.Model): ...
class KitchenBooking(db.Model): ...
class HACCPLog(db.Model): ...

# --- MODELOS PARA OPERACIONES DE CAMPO (LAN-FLD2) ---
class FieldTask(db.Model): ...
class TaskReport(db.Model): ...

# --- MODELOS PARA SERVICIOS TÉCNICOS (LAN-JO1B) ---
class ServiceJob(db.Model): ...
class JobQuote(db.Model): ...
class JobInvoice(db.Model): ...

# --- MODELOS DE AUDITORÍA, NOTIFICACIONES Y VERSIONES (al final) ---
class DocumentVersion(db.Model):
    """Representa una versión específica de un archivo de un documento."""
    __tablename__ = 'document_version'
    id = db.Column(Integer, primary_key=True)
    document_id = db.Column(Integer, ForeignKey('document.id'), nullable=False, index=True)
    version_number = db.Column(Integer, nullable=False)
    filepath = db.Column(String(500), nullable=False) # Path in storage (local or cloud URL)
    file_hash = db.Column(String(128), nullable=True) # SHA-512 or similar hash for integrity check
    uploaded_by_id = db.Column(Integer, ForeignKey('user.id'), nullable=False)
    created_at = db.Column(DateTime, default=func.current_timestamp())
    uploaded_by = db.relationship('User', foreign_keys=[uploaded_by_id], backref='uploaded_document_versions')
    __table_args__ = (UniqueConstraint('document_id', 'version_number', name='_doc_version_uc'),)
    def __repr__(self):
        return f'<DocumentVersion {self.id} (v{self.version_number}) for Document {self.document_id}>'

class NotificationTemplate(db.Model):
    """Plantillas de notificaciones (email, SMS, in-app)"""
    __tablename__ = 'notification_template'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(150), nullable=False) # Unique name for identification
    subject = db.Column(String(255), nullable=True) # For email subject lines
    content = db.Column(Text, nullable=False) # Template body with placeholders
    type = db.Column(String(50), default='email') # email, sms, in_app
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    created_by_id = db.Column(Integer, ForeignKey('user.id'))
    created_at = db.Column(DateTime, default=func.current_timestamp())
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='created_notification_templates')
    __table_args__ = (UniqueConstraint('name', 'tenant_id', name='_notification_template_name_tenant_uc'),)
    def __repr__(self):
        return f'<NotificationTemplate {self.name}>'


# --- MODELOS PARA EDUCACIÓN (LAN-SCH6) ---

class Student(db.Model):
    """Registro de un estudiante."""
    __tablename__ = 'education_student'
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(Integer, ForeignKey('user.id'), nullable=True, unique=True)
    full_name = db.Column(String(200), nullable=False)
    student_code = db.Column(String(50), unique=True)
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)

    enrollments = db.relationship('Enrollment', backref='student', lazy='dynamic')
    payments = db.relationship('TuitionPayment', backref='student', lazy='dynamic')

    def to_dict(self):
        return {'id': self.id, 'full_name': self.full_name, 'student_code': self.student_code}

class Course(db.Model):
    """Cursos o asignaturas."""
    __tablename__ = 'education_course'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(200), nullable=False)
    course_code = db.Column(String(50), unique=True)
    teacher_id = db.Column(Integer, ForeignKey('user.id')) # El profesor es un usuario
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)

    teacher = db.relationship('User')
    enrollments = db.relationship('Enrollment', backref='course', lazy='dynamic')

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'course_code': self.course_code, 'teacher_name': self.teacher.full_name if self.teacher else 'N/A'}

class Enrollment(db.Model):
    """Inscripción de un estudiante en un curso."""
    __tablename__ = 'education_enrollment'
    id = db.Column(Integer, primary_key=True)
    student_id = db.Column(Integer, ForeignKey('education_student.id'), nullable=False)
    course_id = db.Column(Integer, ForeignKey('education_course.id'), nullable=False)
    enrollment_date = db.Column(Date, default=date.today)
    final_grade = db.Column(Float)
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)

    grades = db.relationship('Grade', backref='enrollment', lazy='dynamic', cascade="all, delete-orphan")
    __table_args__ = (UniqueConstraint('student_id', 'course_id', 'tenant_id', name='_student_course_tenant_uc'),)

class Grade(db.Model):
    """Calificaciones de un estudiante en una inscripción."""
    __tablename__ = 'education_grade'
    id = db.Column(Integer, primary_key=True)
    enrollment_id = db.Column(Integer, ForeignKey('education_enrollment.id'), nullable=False)
    grade_name = db.Column(String(100)) # Ej: "Examen Parcial 1"
    score = db.Column(Float, nullable=False)
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)

class TuitionPayment(db.Model):
    """Pagos de matrícula de un estudiante."""
    __tablename__ = 'education_tuition_payment'
    id = db.Column(Integer, primary_key=True)
    student_id = db.Column(Integer, ForeignKey('education_student.id'), nullable=False)
    amount = db.Column(Float, nullable=False)
    payment_date = db.Column(Date, default=date.today)
    concept = db.Column(String(200)) # Ej: "Matrícula Enero 2025"
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)


class AuditLog(db.Model):
    """Registro de auditoría"""
    __tablename__ = 'audit_log'
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(Integer, ForeignKey('user.id'), nullable=False, index=True) # User performing action
    action = db.Column(String(255), nullable=False) # E.g., 'create_user', 'update_status', 'login'
    entity = db.Column(String(100), nullable=True) # E.g., 'User', 'LoanApplication', 'Product'
    entity_id = db.Column(Integer, nullable=True) # ID of the affected entity
    details = db.Column(JSONB, nullable=True) # Optional: Store old/new values or other context
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    created_at = db.Column(DateTime, default=func.current_timestamp())
    # user definido por backref desde User
    def __repr__(self):
        return f'<AuditLog {self.id} User:{self.user_id} Action:{self.action} on {self.entity}:{self.entity_id}>'