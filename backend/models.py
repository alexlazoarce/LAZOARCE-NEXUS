"""
MODELOS DE BASE DE DATOS - SISTEMA INTEGRADO LAZO ARCE (FUSIONADO FINAL)

Versión: 2.1 | Multi-tenant | Integración de Firma Electrónica, Payroll y Módulos LAN

"""

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta
from sqlalchemy import func, Boolean, Date, DateTime, Float, Integer, String, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, backref
from sqlalchemy.dialects.postgresql import JSONB, JSON

# Inicializar SQLAlchemy (Debe ser inicializado en el app factory)
db = SQLAlchemy()

# === TABLAS INTERMEDIAS (Many-to-Many) ===

user_roles = db.Table('user_roles',
    db.Column('user_id', Integer, ForeignKey('user.id'), primary_key=True),
    db.Column('role_id', Integer, ForeignKey('role.id'), primary_key=True),
    schema='public'
)

# Se incluye mailing_list_members del 2.0 (asumiendo que MailingList existe en el módulo)
mailing_list_members = db.Table('mailing_list_members',
    db.Column('mailing_list_id', Integer, ForeignKey('mailing_list.id'), primary_key=True),
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
    domain = db.Column(String(100), unique=True)
    is_active = db.Column(Boolean, default=True)
    created_at = db.Column(DateTime, default=func.current_timestamp())
    config = db.Column(JSONB, default=dict)

    users = db.relationship('User', backref='tenant', lazy='dynamic')
    roles = db.relationship('Role', backref='tenant', lazy='dynamic')
    loan_products = db.relationship('LoanProduct', backref='tenant', lazy='dynamic')

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

    users = db.relationship('User', secondary=user_roles, back_populates='roles')
    __table_args__ = (UniqueConstraint('name', 'tenant_id', name='_role_name_tenant_uc'),)

    def __repr__(self):
        return f'<Role {self.name}>'

class User(db.Model):
    """Usuarios con autenticación y perfil completo"""
    __tablename__ = 'user'

    id = db.Column(Integer, primary_key=True)
    email = db.Column(String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(String(256), nullable=False)

    # Campos de perfil/legales (fusionados del 2.0 y HEAD)
    full_name = db.Column(String(120), nullable=True)
    dui = db.Column(String(20), unique=True, nullable=True, index=True)
    nit = db.Column(String(20), unique=True, nullable=True, index=True)

    is_active = db.Column(Boolean, default=True)
    last_login = db.Column(DateTime)
    created_at = db.Column(DateTime, default=func.current_timestamp())

    # Relaciones
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    role_id = db.Column(Integer, ForeignKey('role.id'), nullable=False)
    roles = db.relationship('Role', secondary=user_roles, back_populates='users')

    profile = db.relationship('ClientProfile', backref='user', uselist=False)
    employee = db.relationship('Employee', backref='user', uselist=False)
    applications = db.relationship('LoanApplication', backref='applicant', lazy='dynamic')
    audit_logs = db.relationship('AuditLog', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def role(self):
        return Role.query.get(self.role_id)

    def __repr__(self):
        return f'<User {self.email}>'

class ClientProfile(db.Model):
    """Perfil detallado de cliente (Versión 2.0)"""
    __tablename__ = 'client_profile'

    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(Integer, ForeignKey('user.id'), unique=True, nullable=False)

    full_name = db.Column(String(120))
    phone_number = db.Column(String(20))
    secondary_phone = db.Column(String(20))
    address = db.Column(Text)
    birth_date = db.Column(Date)

    occupation = db.Column(String(100))
    employer = db.Column(String(100)) # Del 2.0
    monthly_income = db.Column(Float)

    # Campos de referencias del 2.0
    reference_name = db.Column(String(120))
    reference_phone = db.Column(String(20))


# --- MODELOS DE PRÉSTAMOS ---

class LoanProduct(db.Model):
    """Productos de préstamo configurables (Fusión de LoanProduct y ProductoCredito)"""
    __tablename__ = 'loan_product'

    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(100), nullable=False, index=True)
    description = db.Column(Text)

    # Campos de ProductoCredito (HEAD)
    loan_type = db.Column(String(50), nullable=True)
    tasa_interes_anual = db.Column(Float, nullable=False)
    plazo_maximo = db.Column(Integer, nullable=True)

    # Límites (unificados)
    min_amount = db.Column(Float, nullable=False, default=0.0)
    max_amount = db.Column(Float, nullable=False, default=0.0)

    # Comisiones y costos (unificados)
    comision_apertura = db.Column(Float, default=0.0)
    comision_administracion = db.Column(Float, default=0.0)
    seguro = db.Column(Float, default=0.0)

    # Configuración de cálculo
    comisiones_generan_intereses = db.Column(Boolean, default=False)
    comisiones_se_agregan_capital = db.Column(Boolean, default=False)
    comisiones_se_descuentan_capital = db.Column(Boolean, default=True)
    aplicar_tea = db.Column(Boolean, default=True)

    # Estado y tenant
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    is_active = db.Column(Boolean, default=True)
    created_at = db.Column(DateTime, default=func.current_timestamp())

    applications = db.relationship('LoanApplication', backref='product', lazy='dynamic')
    __table_args__ = (UniqueConstraint('name', 'tenant_id', name='_loan_product_tenant_uc'),)

    def __repr__(self):
        return f'<LoanProduct {self.name}>'

class LoanApplication(db.Model):
    """Solicitudes de préstamo"""
    __tablename__ = 'loan_application'

    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(Integer, ForeignKey('user.id'), nullable=False, index=True)
    product_id = db.Column(Integer, ForeignKey('loan_product.id'), nullable=False, index=True)

    amount_requested = db.Column(Float, nullable=False)
    term_months = db.Column(Integer, nullable=False)

    # Campos de estado y cálculo
    status = db.Column(String(50), default='Solicitud Recibida', nullable=False)
    application_date = db.Column(DateTime, default=func.current_timestamp())
    monthly_payment = db.Column(Float, nullable=True)
    total_payment = db.Column(Float, nullable=True)
    tea_calculada = db.Column(Float, nullable=True)

    # Relación contable
    disbursement_entry_id = db.Column(Integer, ForeignKey('journal_entry.id'), nullable=True)
    disbursement_entry = db.relationship('JournalEntry', foreign_keys=[disbursement_entry_id], backref='disbursed_application', uselist=False)

    # Relaciones de pagos (del 2.0)
    payments = db.relationship('Payment', backref='application', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<LoanApplication {self.id} - {self.status}>'


# --- MODELOS CONTABLES ---

class Account(db.Model):
    """Plan de cuentas contable"""
    __tablename__ = 'account'

    id = db.Column(Integer, primary_key=True)
    account_code = db.Column(String(20), unique=True, nullable=False, index=True)
    name = db.Column(String(100), nullable=False)

    category = db.Column(String(50), nullable=False)  # Asset, Liability, Equity, Revenue, Expense
    normal_balance = db.Column(String(10), nullable=False)  # Debit, Credit
    account_type = db.Column(String(50), nullable=True)

    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    is_active = db.Column(Boolean, default=True)

    transactions = db.relationship('Transaction', backref='account', lazy='dynamic')
    __table_args__ = (UniqueConstraint('account_code', 'tenant_id', name='_account_code_tenant_uc'),)

    def __repr__(self):
        return f'<Account {self.account_code} - {self.name}>'

class JournalEntry(db.Model):
    """Asiento contable (Encabezado)"""
    __tablename__ = 'journal_entry'

    id = db.Column(Integer, primary_key=True)
    date = db.Column(DateTime, default=func.current_timestamp(), index=True)
    description = db.Column(String(500), nullable=False)
    reference = db.Column(String(100), nullable=True)
    created_by_id = db.Column(Integer, ForeignKey('user.id'), nullable=True)

    is_posted = db.Column(Boolean, default=False)
    posted_at = db.Column(DateTime)

    transactions = db.relationship('Transaction', backref='journal_entry', lazy='dynamic', cascade="all, delete-orphan")
    created_by = db.relationship('User', backref='created_journal_entries', foreign_keys=[created_by_id])

class Transaction(db.Model):
    """Movimiento contable individual (Detalle)"""
    __tablename__ = 'transaction'

    id = db.Column(Integer, primary_key=True)
    journal_entry_id = db.Column(Integer, ForeignKey('journal_entry.id'), nullable=False, index=True)
    account_id = db.Column(Integer, ForeignKey('account.id'), nullable=False, index=True)

    type = db.Column(String(10), nullable=False)  # Debit, Credit
    amount = db.Column(Float, nullable=False, default=0.0)

    account = db.relationship('Account')

    def __repr__(self):
        return f'<Transaction {self.id} - {self.type} {self.amount}>'

# --- MODELOS DE RECURSOS HUMANOS / PAYROLL ---

class Employee(db.Model):
    """Empleados y personal"""
    __tablename__ = 'employee'

    id = db.Column(Integer, primary_key=True)
    full_name = db.Column(String(120), nullable=False, index=True)
    position = db.Column(String(100), nullable=True)
    salary = db.Column(Float, default=0.0) # Salario base

    employee_type = db.Column(String(20), default='interno')
    hire_date = db.Column(Date, nullable=True)
    is_active = db.Column(Boolean, default=True)

    user_id = db.Column(Integer, ForeignKey('user.id'), unique=True, nullable=True)
    payslips = db.relationship('PaySlip', backref='employee', lazy='dynamic')

    # Datos legales del 2.0 (se mantienen para Employee)
    dui = db.Column(String(20), unique=True, index=True)
    nit = db.Column(String(20), unique=True, index=True)
    isss_number = db.Column(String(20), unique=True)
    afp_number = db.Column(String(20), unique=True)

    def __repr__(self):
        return f'<Employee {self.full_name}>'

class PaySlip(db.Model):
    """Planillas de pago (Fusión de PaySlip y Planilla)"""
    __tablename__ = 'payslip'

    id = db.Column(Integer, primary_key=True)
    employee_id = db.Column(Integer, ForeignKey('employee.id'), nullable=False, index=True)

    # Campos del 2.0 (Periodo)
    period_start = db.Column(Date, nullable=True)
    period_end = db.Column(Date, nullable=True)
    payment_date = db.Column(Date, nullable=True)

    # Campos de Planilla (HEAD)
    base_salary = db.Column(Float, nullable=False)
    isss_employee = db.Column(Float, nullable=False)
    afp_employee = db.Column(Float, nullable=False)
    renta = db.Column(Float, nullable=False)
    net_salary = db.Column(Float, nullable=False)

    fecha_calculo = db.Column(DateTime, default=func.current_timestamp())

    # Campos del 2.0 (Estado y Totales)
    gross_salary = db.Column(Float, nullable=True)
    total_deductions = db.Column(Float, nullable=True)
    is_paid = db.Column(Boolean, default=False)
    paid_at = db.Column(DateTime)

# --- MODELOS DE FIRMA ELECTRÓNICA Y CONTRATOS ---

class Cliente(db.Model):
    """Perfil específico de Cliente (Del HEAD)"""
    __tablename__ = 'cliente'

    id = db.Column(db.Integer, primary_key=True)
    nombre_completo = db.Column(db.String(200), nullable=False)
    dui = db.Column(db.String(12), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    telefono = db.Column(db.String(20), nullable=False)
    direccion = db.Column(db.String(255), nullable=False)
    estado = db.Column(db.String(20), default='PENDIENTE', nullable=False)

    contrato_integracion_id = db.Column(db.String(50), db.ForeignKey('contrato_integracion.contrato_id'))
    firma_electronica_id = db.Column(db.String(50), db.ForeignKey('firma_electronica.firma_id'))

    __table_args__ = (UniqueConstraint('dui'), UniqueConstraint('email'))

class ContratoIntegracion(db.Model):
    """Contrato de Integración y Documentos (Del HEAD)"""
    __tablename__ = 'contrato_integracion'

    id = db.Column(db.Integer, primary_key=True)
    contrato_id = db.Column(db.String(50), unique=True, nullable=False)
    cliente_dui = db.Column(db.String(12), nullable=False)
    cliente_nombre = db.Column(db.String(200), nullable=False)
    contrato_html = db.Column(db.Text, nullable=False)

    estado = db.Column(db.String(50), default="PENDIENTE_FIRMA")
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_firma = db.Column(db.DateTime)

    tipo_firma = db.Column(db.String(20))
    documento_firmado_url = db.Column(db.String(255))

    __table_args__ = (UniqueConstraint('contrato_id'),)


class FirmaElectronica(db.Model):
    """Registro de Firma Electrónica (Del HEAD)"""
    __tablename__ = 'firma_electronica'

    id = db.Column(db.Integer, primary_key=True)
    firma_id = db.Column(db.String(50), unique=True, nullable=False)
    documento_id = db.Column(db.String(50), nullable=False)
    cliente_dui = db.Column(db.String(12), nullable=False)
    hash_documento = db.Column(db.String(64), nullable=False)
    fecha_firma = db.Column(db.DateTime, nullable=False)

    hash_biometrico = db.Column(db.String(64))
    score_confianza = db.Column(db.Float)
    metodo_validacion = db.Column(db.String(50))

    __table_args__ = (UniqueConstraint('firma_id'),)

class CertificadoValidacion(db.Model):
    """Certificado de Validación de Firma (Del HEAD)"""
    __tablename__ = 'certificado_validacion'

    id = db.Column(db.Integer, primary_key=True)
    certificado_id = db.Column(db.String(50), unique=True, nullable=False)
    firma_id = db.Column(db.String(50), nullable=False)
    documento_id = db.Column(db.String(50), nullable=False)
    cliente_dui = db.Column(db.String(12), nullable=False)
    pdf_certificado = db.Column(db.Text)
    fecha_generacion = db.Column(db.DateTime, default=datetime.utcnow)
    valido_hasta = db.Column(db.DateTime)


# --- MODELOS DE MÓDULOS EXTENDIDOS (MailingList, Recruitment, Gym, Automation, Docs) ---
# Se asume que estos modelos se definirán y usarán fuera del scope de este archivo,
# pero se necesita un placeholder para que las tablas intermedias y las relaciones funcionen.

class MailingList(db.Model):
    __tablename__ = 'mailing_list'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(100), nullable=False)
    members = db.relationship('User', secondary=mailing_list_members, backref='mailing_lists')
    # ... otros campos (tenant_id, etc.)

# Se asume la existencia de los modelos de Recruitment, Gym, Automation, Docs, etc. aquí...


# --- MODELOS PARA EDUCACIÓN (LAN-SCH6) ---

class Student(db.Model):
    """Registro de un estudiante."""
    __tablename__ = 'education_student'
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(Integer, ForeignKey('user.id'), nullable=True, unique=True)
    full_name = db.Column(String(200), nullable=False)
    student_code = db.Column(String(50), unique=True)
    admission_status = db.Column(String(50), default='Aplicante', index=True) # Aplicante, Admitido, Rechazado
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)

    enrollments = db.relationship('Enrollment', backref='student', lazy='dynamic')
    payments = db.relationship('TuitionPayment', backref='student', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'student_code': self.student_code,
            'admission_status': self.admission_status
        }

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


# --- MODELOS PARA GESTIÓN UNIVERSITARIA (LAN-UNV8) ---

class DegreeProgram(db.Model):
    """Planes de estudio o carreras universitarias."""
    __tablename__ = 'university_degree_program'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(200), nullable=False)
    faculty = db.Column(String(150)) # Facultad
    credits_required = db.Column(Integer)
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)

class Scholarship(db.Model):
    """Becas disponibles."""
    __tablename__ = 'university_scholarship'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(200), nullable=False)
    description = db.Column(Text)
    amount_or_percentage = db.Column(Float)
    is_percentage = db.Column(Boolean, default=False)
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)

class StudentScholarship(db.Model):
    """Asignación de becas a estudiantes."""
    __tablename__ = 'university_student_scholarship'
    id = db.Column(Integer, primary_key=True)
    student_id = db.Column(Integer, ForeignKey('education_student.id'), nullable=False)
    scholarship_id = db.Column(Integer, ForeignKey('university_scholarship.id'), nullable=False)
    awarded_date = db.Column(Date, default=date.today)
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)

    student = db.relationship('Student')
    scholarship = db.relationship('Scholarship')
    __table_args__ = (UniqueConstraint('student_id', 'scholarship_id', 'tenant_id', name='_student_scholarship_tenant_uc'),)

class LibraryResource(db.Model):
    """Recursos de la biblioteca digital."""
    __tablename__ = 'university_library_resource'
    id = db.Column(Integer, primary_key=True)
    title = db.Column(String(255), nullable=False)
    author = db.Column(String(150))
    resource_type = db.Column(String(50)) # Libro, Artículo, Tesis
    url_or_identifier = db.Column(String(500))
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)

class Alumnus(db.Model):
    """Registro de egresados."""
    __tablename__ = 'university_alumnus'
    id = db.Column(Integer, primary_key=True)
    student_id = db.Column(Integer, ForeignKey('education_student.id'), unique=True, nullable=False)
    graduation_date = db.Column(Date)
    contact_email = db.Column(String(120))
    contact_phone = db.Column(String(50))
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)

    student = db.relationship('Student')


class AuditLog(db.Model):
    """Registro de auditoría"""
    __tablename__ = 'audit_log'
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(Integer, ForeignKey('user.id'), nullable=False, index=True)
    action = db.Column(String(100), nullable=False, index=True)
    details = db.Column(Text)
    ip_address = db.Column(String(45))
    user_agent = db.Column(String(500))
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    timestamp = db.Column(DateTime, default=func.current_timestamp(), index=True)

class NotificationTemplate(db.Model):
    """Plantillas de notificación"""
    __tablename__ = 'notification_template'
    id = db.Column(Integer, primary_key=True)
    slug = db.Column(String(50), unique=True, nullable=False, index=True)
    name = db.Column(String(100), nullable=False)
    subject = db.Column(String(255), nullable=False)
    body = db.Column(Text, nullable=False)
    type = db.Column(String(20), default='Email')
    variables = db.Column(JSONB, default=list)
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    is_active = db.Column(Boolean, default=True)
    __table_args__ = (UniqueConstraint('slug', 'tenant_id', name='_notification_template_tenant_uc'),)