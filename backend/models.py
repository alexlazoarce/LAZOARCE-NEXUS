"""
MODELOS DE BASE DE DATOS - SISTEMA INTEGRADO LAZO ARCE (FUSIONADO FINAL)
Versión: 2.1 | Multi-tenant | Integración de Firma Electrónica, Payroll y Módulos LAN
"""

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
from sqlalchemy import func, Boolean, Date, DateTime, Float, Integer, String, Text, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship, backref
# Se asume que estás usando PostgreSQL para JSONB; si es SQLite/MySQL, cambia a Text o JSON.
from sqlalchemy.dialects.postgresql import JSONB

# Inicializar SQLAlchemy (Debe ser inicializado en el app factory)
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
    """Soporte Multi-tenant - Empresas/Organizaciones"""
    __tablename__ = 'tenant'

    id = db.Column(Integer, primary_key=True)
    company_name = db.Column(String(100), unique=True, nullable=False, index=True)
    company_code = db.Column(String(20), unique=True, nullable=False)
    domain = db.Column(String(100), unique=True)
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
    description = db.Column(String(255))
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
    last_login = db.Column(DateTime)
    created_at = db.Column(DateTime, default=func.current_timestamp())

    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    role_id = db.Column(Integer, ForeignKey('role.id'), nullable=False)

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
    def role(self):
        return db.session.get(Role, self.role_id)

    def __repr__(self):
        return f'<User {self.email}>'

class ClientProfile(db.Model):
    """Perfil detallado de cliente"""
    __tablename__ = 'client_profile'
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(Integer, ForeignKey('user.id'), unique=True, nullable=False)
    full_name = db.Column(String(120))
    phone_number = db.Column(String(20))
    secondary_phone = db.Column(String(20))
    address = db.Column(Text)
    birth_date = db.Column(Date)
    occupation = db.Column(String(100))
    employer = db.Column(String(100))
    monthly_income = db.Column(Float)
    reference_name = db.Column(String(120))
    reference_phone = db.Column(String(20))


# --- MODELOS DE PRÉSTAMOS ---

class LoanProduct(db.Model):
    """Productos de préstamo configurables"""
    __tablename__ = 'loan_product'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(100), nullable=False, index=True)
    description = db.Column(Text)
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
    loan_application_id = db.Column(Integer, ForeignKey('loan_application.id'), nullable=False)
    amount = db.Column(Float, nullable=False)
    payment_date = db.Column(DateTime, default=func.current_timestamp())


# --- MODELOS CONTABLES ---

class Account(db.Model):
    """Plan de cuentas contable"""
    __tablename__ = 'account'
    id = db.Column(Integer, primary_key=True)
    account_code = db.Column(String(20), nullable=False, index=True)
    name = db.Column(String(100), nullable=False)
    category = db.Column(String(50), nullable=False)
    normal_balance = db.Column(String(10), nullable=False)
    account_type = db.Column(String(50), nullable=True)
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
    type = db.Column(String(10), nullable=False)
    amount = db.Column(Float, nullable=False, default=0.0)


# --- MODELOS DE RECURSOS HUMANOS / PAYROLL ---

class Employee(db.Model):
    """Empleados y personal"""
    __tablename__ = 'employee'
    id = db.Column(Integer, primary_key=True)
    full_name = db.Column(String(120), nullable=False, index=True)
    position = db.Column(String(100), nullable=True)
    salary = db.Column(Float, default=0.0)
    employee_type = db.Column(String(20), default='interno')
    hire_date = db.Column(Date, nullable=True)
    is_active = db.Column(Boolean, default=True)
    user_id = db.Column(Integer, ForeignKey('user.id'), unique=True, nullable=True)
    payslips = db.relationship('PaySlip', backref='employee', lazy='dynamic', cascade="all, delete-orphan")
    dui = db.Column(String(20), unique=True, index=True)
    nit = db.Column(String(20), unique=True, index=True)
    isss_number = db.Column(String(20), unique=True)
    afp_number = db.Column(String(20), unique=True)

class PaySlip(db.Model):
    """Planillas de pago"""
    __tablename__ = 'payslip'
    id = db.Column(Integer, primary_key=True)
    employee_id = db.Column(Integer, ForeignKey('employee.id'), nullable=False, index=True)
    period_start = db.Column(Date)
    period_end = db.Column(Date)
    payment_date = db.Column(Date)
    base_salary = db.Column(Float, nullable=False)
    isss_employee = db.Column(Float, nullable=False)
    afp_employee = db.Column(Float, nullable=False)
    renta = db.Column(Float, nullable=False)
    net_salary = db.Column(Float, nullable=False)
    fecha_calculo = db.Column(DateTime, default=func.current_timestamp())
    gross_salary = db.Column(Float, nullable=True)
    total_deductions = db.Column(Float, nullable=True)
    is_paid = db.Column(Boolean, default=False)
    paid_at = db.Column(DateTime)

# --- MODELOS DE FIRMA ELECTRÓNICA Y CONTRATOS ---

class Cliente(db.Model):
    """Perfil de Cliente para Firma Electrónica"""
    __tablename__ = 'cliente'
    id = db.Column(Integer, primary_key=True)
    nombre_completo = db.Column(String(200), nullable=False)
    dui = db.Column(String(12), unique=True, nullable=False)
    email = db.Column(String(120), unique=True, nullable=False)
    telefono = db.Column(String(20), nullable=False)
    direccion = db.Column(String(255), nullable=False)
    estado = db.Column(String(20), default='PENDIENTE', nullable=False)
    contrato_integracion_id = db.Column(String(50), ForeignKey('contrato_integracion.contrato_id'))
    firma_electronica_id = db.Column(String(50), ForeignKey('firma_electronica.firma_id'))
    contrato_integracion = relationship("ContratoIntegracion", back_populates="clientes", foreign_keys=[contrato_integracion_id])
    firma_electronica = relationship("FirmaElectronica", back_populates="clientes", foreign_keys=[firma_electronica_id])
    __table_args__ = (UniqueConstraint('dui'), UniqueConstraint('email'))

class ContratoIntegracion(db.Model):
    """Contrato de Integración para Firma"""
    __tablename__ = 'contrato_integracion'
    id = db.Column(Integer, primary_key=True)
    contrato_id = db.Column(String(50), unique=True, nullable=False)
    cliente_dui = db.Column(String(12), nullable=False)
    cliente_nombre = db.Column(String(200), nullable=False)
    contrato_html = db.Column(Text, nullable=False)
    estado = db.Column(String(50), default="PENDIENTE_FIRMA")
    fecha_creacion = db.Column(DateTime, default=datetime.utcnow)
    fecha_firma = db.Column(DateTime)
    tipo_firma = db.Column(String(20))
    documento_firmado_url = db.Column(String(255))
    clientes = relationship("Cliente", back_populates="contrato_integracion")
    __table_args__ = (UniqueConstraint('contrato_id'),)

class FirmaElectronica(db.Model):
    """Registro de Firma Electrónica"""
    __tablename__ = 'firma_electronica'
    id = db.Column(Integer, primary_key=True)
    firma_id = db.Column(String(50), unique=True, nullable=False)
    documento_id = db.Column(String(50), nullable=False)
    cliente_dui = db.Column(String(12), nullable=False)
    hash_documento = db.Column(String(64), nullable=False)
    fecha_firma = db.Column(DateTime, nullable=False)
    hash_biometrico = db.Column(String(64))
    score_confianza = db.Column(Float)
    metodo_validacion = db.Column(String(50))
    clientes = relationship("Cliente", back_populates="firma_electronica")
    __table_args__ = (UniqueConstraint('firma_id'),)

class CertificadoValidacion(db.Model):
    """Certificado de Validación de Firma"""
    __tablename__ = 'certificado_validacion'
    id = db.Column(Integer, primary_key=True)
    certificado_id = db.Column(String(50), unique=True, nullable=False)
    firma_id = db.Column(String(50), nullable=False)
    documento_id = db.Column(String(50), nullable=False)
    cliente_dui = db.Column(String(12), nullable=False)
    pdf_certificado = db.Column(Text)
    fecha_generacion = db.Column(DateTime, default=datetime.utcnow)
    valido_hasta = db.Column(DateTime)

# --- MODELOS DE MÓDULOS DE NEGOCIO ---

class ContractTemplate(db.Model):
    __tablename__ = 'contract_template'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(100), nullable=False, index=True)
    content = db.Column(Text, nullable=False)
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    created_by_id = db.Column(Integer, ForeignKey('user.id'))
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='created_contract_templates')
    __table_args__ = (UniqueConstraint('name', 'tenant_id', name='_contract_template_tenant_uc'),)

class GeneratedContract(db.Model):
    __tablename__ = 'generated_contract'
    id = db.Column(Integer, primary_key=True)
    template_id = db.Column(Integer, ForeignKey('contract_template.id'), nullable=False)
    content_final = db.Column(Text, nullable=False)
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False)
    generated_by_id = db.Column(Integer, ForeignKey('user.id'))
    template = db.relationship('ContractTemplate', backref='generated_contracts')
    generated_by = db.relationship('User', foreign_keys=[generated_by_id], backref='generated_contracts')

class Contact(db.Model):
    __tablename__ = 'crm_contact'
    id = db.Column(Integer, primary_key=True)
    full_name = db.Column(String(120), nullable=False, index=True)
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    assigned_to_id = db.Column(Integer, ForeignKey('user.id'))
    interactions = db.relationship('Interaction', backref='contact', lazy='dynamic', cascade="all, delete-orphan")
    opportunities = db.relationship('Opportunity', backref='contact', lazy='dynamic', cascade="all, delete-orphan")
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id], backref='assigned_crm_contacts')

class Interaction(db.Model):
    __tablename__ = 'crm_interaction'
    id = db.Column(Integer, primary_key=True)
    contact_id = db.Column(Integer, ForeignKey('crm_contact.id'), nullable=False, index=True)
    user_id = db.Column(Integer, ForeignKey('user.id'))
    user = db.relationship('User', foreign_keys=[user_id], backref='created_interactions')

class Opportunity(db.Model):
    __tablename__ = 'crm_opportunity'
    id = db.Column(Integer, primary_key=True)
    contact_id = db.Column(Integer, ForeignKey('crm_contact.id'), nullable=False, index=True)
    loan_product_id = db.Column(Integer, ForeignKey('loan_product.id'), nullable=True)
    assigned_to_id = db.Column(Integer, ForeignKey('user.id'))
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id], backref='assigned_opportunities')

class Product(db.Model):
    __tablename__ = 'inventory_product'
    id = db.Column(Integer, primary_key=True)
    sku = db.Column(String(100), nullable=False, index=True)
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    movements = db.relationship('StockMovement', backref='product', lazy='dynamic', cascade="all, delete-orphan")
    __table_args__ = (UniqueConstraint('sku', 'tenant_id', name='_product_sku_tenant_uc'),)

class StockMovement(db.Model):
    __tablename__ = 'inventory_stock_movement'
    id = db.Column(Integer, primary_key=True)
    product_id = db.Column(Integer, ForeignKey('inventory_product.id'), nullable=False, index=True)
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    user_id = db.Column(Integer, ForeignKey('user.id'))
    user = db.relationship('User', foreign_keys=[user_id], backref='stock_movements')

class Quote(db.Model):
    __tablename__ = 'sales_quote'
    id = db.Column(Integer, primary_key=True)
    contact_id = db.Column(Integer, ForeignKey('crm_contact.id'), nullable=False, index=True)
    opportunity_id = db.Column(Integer, ForeignKey('crm_opportunity.id'), nullable=True, index=True)
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    created_by_id = db.Column(Integer, ForeignKey('user.id'))
    items = db.relationship('SalesOrderItem', backref='quote', lazy='dynamic', cascade="all, delete-orphan")
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='created_quotes')

class SalesOrder(db.Model):
    __tablename__ = 'sales_order'
    id = db.Column(Integer, primary_key=True)
    contact_id = db.Column(Integer, ForeignKey('crm_contact.id'), nullable=False, index=True)
    quote_id = db.Column(Integer, ForeignKey('sales_quote.id'), nullable=True, index=True)
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    created_by_id = db.Column(Integer, ForeignKey('user.id'))
    items = db.relationship('SalesOrderItem', backref='sales_order', lazy='dynamic', cascade="all, delete-orphan")
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='created_sales_orders')

class SalesOrderItem(db.Model):
    __tablename__ = 'sales_order_item'
    id = db.Column(Integer, primary_key=True)
    sales_order_id = db.Column(Integer, ForeignKey('sales_order.id'), nullable=True, index=True)
    quote_id = db.Column(Integer, ForeignKey('sales_quote.id'), nullable=True, index=True)
    product_id = db.Column(Integer, ForeignKey('inventory_product.id'), nullable=False, index=True)
    product = db.relationship('Product')
    __table_args__ = (CheckConstraint('(sales_order_id IS NOT NULL AND quote_id IS NULL) OR (sales_order_id IS NULL AND quote_id IS NOT NULL)', name='_sales_item_one_parent_check'),)

class Supplier(db.Model): __tablename__ = 'purchasing_supplier'; id = db.Column(Integer, primary_key=True)
class PurchaseOrder(db.Model): __tablename__ = 'purchasing_order'; id = db.Column(Integer, primary_key=True)
class PurchaseOrderItem(db.Model): __tablename__ = 'purchasing_order_item'; id = db.Column(Integer, primary_key=True)
class EmailLog(db.Model): __tablename__ = 'email_log'; id = db.Column(Integer, primary_key=True)
class Document(db.Model): __tablename__ = 'document'; id = db.Column(Integer, primary_key=True)
class DocumentVersion(db.Model): __tablename__ = 'document_version'; id = db.Column(Integer, primary_key=True)
class Channel(db.Model): __tablename__ = 'messaging_channel'; id = db.Column(Integer, primary_key=True)
class Message(db.Model): __tablename__ = 'messaging_message'; id = db.Column(Integer, primary_key=True)
class SignableTemplate(db.Model): __tablename__ = 'sign_template'; id = db.Column(Integer, primary_key=True)
class SignatureRequest(db.Model): __tablename__ = 'sign_request'; id = db.Column(Integer, primary_key=True)
class Form(db.Model): __tablename__ = 'form'; id = db.Column(Integer, primary_key=True)
class FormSubmission(db.Model): __tablename__ = 'form_submission'; id = db.Column(Integer, primary_key=True)
class Project(db.Model): __tablename__ = 'project'; id = db.Column(Integer, primary_key=True)
class Task(db.Model): __tablename__ = 'project_task'; id = db.Column(Integer, primary_key=True)
class Ticket(db.Model): __tablename__ = 'support_ticket'; id = db.Column(Integer, primary_key=True)
class TicketUpdate(db.Model): __tablename__ = 'support_ticket_update'; id = db.Column(Integer, primary_key=True)
class FixedAsset(db.Model): __tablename__ = 'fixed_asset'; id = db.Column(Integer, primary_key=True)
class DepreciationEntry(db.Model): __tablename__ = 'asset_depreciation_entry'; id = db.Column(Integer, primary_key=True)
class BankAccount(db.Model): __tablename__ = 'bank_account'; id = db.Column(Integer, primary_key=True)
class BankTransaction(db.Model): __tablename__ = 'bank_transaction'; id = db.Column(Integer, primary_key=True)
class CashBox(db.Model): __tablename__ = 'cash_box'; id = db.Column(Integer, primary_key=True)
class CashTransaction(db.Model): __tablename__ = 'cash_transaction'; id = db.Column(Integer, primary_key=True)
class MailingList(db.Model): __tablename__ = 'mailing_list'; id = db.Column(Integer, primary_key=True)
class AuditLog(db.Model): __tablename__ = 'audit_log'; id = db.Column(Integer, primary_key=True)
class NotificationTemplate(db.Model): __tablename__ = 'notification_template'; id = db.Column(Integer, primary_key=True)
class TaxType(db.Model): __tablename__ = 'tax_type'; id = db.Column(Integer, primary_key=True)
class TaxDeclaration(db.Model): __tablename__ = 'tax_declaration'; id = db.Column(Integer, primary_key=True)

