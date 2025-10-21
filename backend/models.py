"""
MODELOS DE BASE DE DATOS - SISTEMA INTEGRADO LAZO ARCE (FUSIONADO)

Versión: 2.1 | Multi-tenant | Integración de Firma Electrónica y Payroll Avanzado

"""

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta
from sqlalchemy import func, Boolean, DateTime, Float, Integer, String, Text, ForeignKey, Date, UniqueConstraint
from sqlalchemy.orm import relationship, backref
from sqlalchemy.dialects.postgresql import JSONB

# Inicializar SQLAlchemy (Debe ser inicializado en el app factory)
db = SQLAlchemy()

# === TABLAS INTERMEDIAS (Many-to-Many) ===

user_roles = db.Table('user_roles',
    db.Column('user_id', Integer, ForeignKey('user.id'), primary_key=True),
    db.Column('role_id', Integer, ForeignKey('role.id'), primary_key=True),
    schema='public'
)

# === MODELOS DE SEGURIDAD Y TENANTS (Manteniendo la estructura 2.0) ===

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

class User(db.Model):
    """Usuarios con autenticación y perfil completo"""
    __tablename__ = 'user'
    
    id = db.Column(Integer, primary_key=True)
    email = db.Column(String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(String(256), nullable=False)
    
    # Campos fusionados del HEAD (para acceso directo)
    full_name = db.Column(String(120), nullable=True) # Se usa el campo del HEAD
    dui = db.Column(String(20), unique=True, nullable=True, index=True)
    nit = db.Column(String(20), unique=True, nullable=True, index=True)
    
    is_active = db.Column(Boolean, default=True)
    last_login = db.Column(DateTime)
    created_at = db.Column(DateTime, default=func.current_timestamp())
    
    # Relaciones de la versión 2.0
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    role_id = db.Column(Integer, ForeignKey('role.id'), nullable=False)  # Rol principal
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
    """Perfil detallado de cliente (Versión 2.0 para datos extensos)"""
    __tablename__ = 'client_profile'
    
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(Integer, ForeignKey('user.id'), unique=True, nullable=False)
    
    full_name = db.Column(String(120))
    phone_number = db.Column(String(20))
    secondary_phone = db.Column(String(20))
    address = db.Column(Text)
    birth_date = db.Column(Date)
    occupation = db.Column(String(100))
    monthly_income = db.Column(Float)
    
    # Otras relaciones, etc.


# --- MODELOS DE PRÉSTAMOS (Fusionando LoanProduct y ProductoCredito) ---

class LoanProduct(db.Model):
    """Productos de préstamo configurables (Base 2.0, campos del HEAD)"""
    __tablename__ = 'loan_product'
    
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(100), nullable=False, index=True)
    description = db.Column(Text)
    
    # Campos de ProductoCredito/HEAD
    loan_type = db.Column(String(50), nullable=True) # 'Personal', 'Grupal', etc. (del HEAD)
    tasa_interes_anual = db.Column(Float, nullable=False) # Tasa ANUAL (del HEAD)
    comision_apertura = db.Column(Float, default=0.0)
    comision_administracion = db.Column(Float, default=0.0)
    seguro = db.Column(Float, default=0.0)
    plazo_maximo = db.Column(Integer, nullable=True)
    
    min_amount = db.Column(Float, nullable=False, default=0.0)
    max_amount = db.Column(Float, nullable=False, default=0.0)
    
    # OPCIONES DE CÁLCULO (del HEAD)
    comisiones_generan_intereses = db.Column(Boolean, default=False)
    comisiones_se_agregan_capital = db.Column(Boolean, default=False)
    comisiones_se_descuentan_capital = db.Column(Boolean, default=True)
    aplicar_tea = db.Column(Boolean, default=True)
    
    # Estado y tenant (Base 2.0)
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    is_active = db.Column(Boolean, default=True)
    created_at = db.Column(DateTime, default=func.current_timestamp())
    
    applications = db.relationship('LoanApplication', backref='product', lazy='dynamic')
    __table_args__ = (UniqueConstraint('name', 'tenant_id', name='_loan_product_tenant_uc'),)

class LoanApplication(db.Model):
    """Solicitudes de préstamo (Base 2.0, campos del HEAD)"""
    __tablename__ = 'loan_application'
    
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(Integer, ForeignKey('user.id'), nullable=False, index=True)
    product_id = db.Column(Integer, ForeignKey('loan_product.id'), nullable=False, index=True)
    
    amount_requested = db.Column(Float, nullable=False)
    term_months = db.Column(Integer, nullable=False) # En meses
    
    status = db.Column(String(50), default='Solicitud Recibida', nullable=False) # Solicitud, Análisis, Aprobación, Desembolsado...
    application_date = db.Column(DateTime, default=func.current_timestamp())
    
    # Campos calculados (del 2.0)
    monthly_payment = db.Column(Float, nullable=True)
    total_payment = db.Column(Float, nullable=True)
    tea_calculada = db.Column(Float, nullable=True)
    
    # Relación contable (del 2.0)
    disbursement_entry_id = db.Column(Integer, ForeignKey('journal_entry.id'), nullable=True)
    disbursement_entry = db.relationship('JournalEntry', foreign_keys=[disbursement_entry_id], backref='disbursed_application', uselist=False)


# --- MODELOS CONTABLES (Manteniendo la estructura 2.0) ---
class Account(db.Model):
    """Plan de cuentas contable"""
    __tablename__ = 'account'
    
    id = db.Column(Integer, primary_key=True)
    account_code = db.Column(String(20), unique=True, nullable=False, index=True) # code (HEAD) -> account_code (2.0)
    name = db.Column(String(100), nullable=False)
    
    category = db.Column(String(50), nullable=False)  # Asset, Liability, Equity, Revenue, Expense (del 2.0)
    normal_balance = db.Column(String(10), nullable=False)  # Debit, Credit (del 2.0)
    account_type = db.Column(String(50), nullable=True) # (del HEAD, se mantiene)
    
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    is_active = db.Column(Boolean, default=True)
    
    transactions = db.relationship('Transaction', backref='account', lazy='dynamic')
    __table_args__ = (UniqueConstraint('account_code', 'tenant_id', name='_account_code_tenant_uc'),)

class JournalEntry(db.Model):
    """Asiento contable (Encabezado del 2.0)"""
    __tablename__ = 'journal_entry'
    
    id = db.Column(Integer, primary_key=True)
    date = db.Column(DateTime, default=func.current_timestamp(), index=True)
    description = db.Column(String(500), nullable=False)
    reference = db.Column(String(100), nullable=True)
    created_by_id = db.Column(Integer, ForeignKey('user.id'), nullable=True) # Permitir null para asientos automáticos
    
    is_posted = db.Column(Boolean, default=False)
    posted_at = db.Column(DateTime)
    
    transactions = db.relationship('Transaction', backref='journal_entry', lazy='dynamic', cascade="all, delete-orphan")
    created_by = db.relationship('User', backref='created_journal_entries', foreign_keys=[created_by_id])

class Transaction(db.Model):
    """Movimiento contable individual (Detalle del 2.0)"""
    __tablename__ = 'transaction'
    
    id = db.Column(Integer, primary_key=True)
    journal_entry_id = db.Column(Integer, ForeignKey('journal_entry.id'), nullable=False, index=True)
    account_id = db.Column(Integer, ForeignKey('account.id'), nullable=False, index=True)
    
    type = db.Column(String(10), nullable=False)  # Debit, Credit
    amount = db.Column(Float, nullable=False, default=0.0)
    
    account = db.relationship('Account')
    
    def __repr__(self):
        return f'<Transaction {self.id} - {self.type} {self.amount}>'


# --- MODELOS DE RECURSOS HUMANOS (Fusionando Empleado/Planilla del HEAD con Employee/Payslip del 2.0) ---

class Employee(db.Model):
    """Empleados y personal (Del 2.0, fusionando campos de Empleado del HEAD)"""
    __tablename__ = 'employee'
    
    id = db.Column(Integer, primary_key=True)
    full_name = db.Column(String(120), nullable=False, index=True) # nombre (HEAD) -> full_name (2.0)
    position = db.Column(String(100), nullable=True)
    salary = db.Column(Float, default=0.0) # salario_base (HEAD) -> salary (2.0)
    
    employee_type = db.Column(String(20), default='interno')
    hire_date = db.Column(Date, nullable=True)
    is_active = db.Column(Boolean, default=True)
    
    user_id = db.Column(Integer, ForeignKey('user.id'), unique=True, nullable=True) # Relacion con User
    payslips = db.relationship('PaySlip', backref='employee', lazy='dynamic') # Relacion con Payslip (Planilla)

class PaySlip(db.Model):
    """Planillas de pago (Payroll) (Del 2.0, fusionando Planilla del HEAD)"""
    __tablename__ = 'payslip'
    
    id = db.Column(Integer, primary_key=True)
    employee_id = db.Column(Integer, ForeignKey('employee.id'), nullable=False, index=True)
    
    # Campos de Planilla del HEAD y Payslip del 2.0
    base_salary = db.Column(Float, nullable=False) # salario_base (HEAD)
    isss_employee = db.Column(Float, nullable=False) # isss (HEAD) -> isss_employee (2.0)
    afp_employee = db.Column(Float, nullable=False)  # afp (HEAD) -> afp_employee (2.0)
    renta = db.Column(Float, nullable=False)
    net_salary = db.Column(Float, nullable=False) # salario_neto (HEAD) -> net_salary (2.0)
    
    fecha_calculo = db.Column(DateTime, default=func.current_timestamp()) # del HEAD


# --- MODELOS DE CLIENTES Y FIRMA ELECTRÓNICA (Del HEAD, integrados al Multi-Tenant) ---

class Cliente(db.Model):
    """Perfil específico de Cliente (Del HEAD) - Se puede considerar migrar a ClientProfile"""
    __tablename__ = 'cliente'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre_completo = db.Column(db.String(200), nullable=False)
    dui = db.Column(db.String(12), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    # user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True) # Se podría vincular con User
    
    telefono = db.Column(db.String(20), nullable=False)
    direccion = db.Column(db.String(255), nullable=False)
    estado = db.Column(db.String(20), default='PENDIENTE', nullable=False)
    
    # Relaciones con Contratos y Firmas
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
    
    # Datos de Trazabilidad
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