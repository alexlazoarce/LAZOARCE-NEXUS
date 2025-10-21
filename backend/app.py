import os
import click
from functools import wraps
from flask import Flask, jsonify, request, g, Blueprint, send_from_directory
# CORRECCIÓN: Importación de SQLAlchemy faltante
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta
from sqlalchemy import func, Boolean, Date, DateTime, Float, Integer, String, Text, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship, backref
# Se asume PostgreSQL por JSONB, si no, se debe cambiar. Usaré Text como fallback para JSON/JSONB si no se importa.
from sqlalchemy.dialects.postgresql import JSONB, JSON

# Inicializar SQLAlchemy
db = SQLAlchemy()

# === TABLAS INTERMEDIAS (Many-to-Many) ===

user_roles = db.Table('user_roles',
    db.Column('user_id', Integer, ForeignKey('user.id'), primary_key=True, comment='Foreign key al usuario'),
    db.Column('role_id', Integer, ForeignKey('role.id'), primary_key=True, comment='Foreign key al rol'),
    schema='public'
)

mailing_list_members = db.Table('mailing_list_members',
    db.Column('mailing_list_id', Integer, ForeignKey('mailing_list.id'), primary_key=True, comment='Foreign key a la lista de correo'),
    db.Column('user_id', Integer, ForeignKey('user.id'), primary_key=True, comment='Foreign key al usuario'),
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
    config = db.Column(Text, default='{}') # Usando Text como fallback para JSONB

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
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=True, index=True)
    is_active = db.Column(Boolean, default=True)

    # CORRECCIÓN: Renombrado de back_populates para evitar conflicto con User.role
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

    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=True, index=True)
    role_id = db.Column(Integer, ForeignKey('role.id'), nullable=True)

    # CORRECCIÓN: Renombrado de la relación M2M para evitar conflicto con .role
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
        if self.role_id:
            return db.session.get(Role, self.role_id)
        return None

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

    min_amount = db.Column(Float, default=0.0)
    max_amount = db.Column(Float, default=0.0)

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

    def __repr__(self):
        return f'<LoanProduct {self.name}>'

# Modelo ProductoCredito referenciado en el try/except del app factory, se mapea a LoanProduct
class ProductoCredito(LoanProduct):
    __tablename__ = 'producto_credito_alias'
    __mapper_args__ = {
        'polymorphic_identity': 'producto_credito',
    }
    # No se necesitan columnas propias si es solo un alias para la importación

class Payment(db.Model):
    """Pagos para LoanApplication (Definición completa)"""
    __tablename__ = 'payment'
    id = db.Column(Integer, primary_key=True)
    amount = db.Column(Float, nullable=False)
    date = db.Column(DateTime, default=func.current_timestamp())
    loan_application_id = db.Column(Integer, ForeignKey('loan_application.id'), nullable=False)

    def __repr__(self):
        return f'<Payment {self.id} - {self.amount}>'

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

    # Relación contable
    disbursement_entry_id = db.Column(Integer, ForeignKey('journal_entry.id'), nullable=True)
    disbursement_entry = db.relationship('JournalEntry', foreign_keys=[disbursement_entry_id], backref='disbursed_application', uselist=False)

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

    transactions = db.relationship('Transaction', backref='account', lazy='dynamic', cascade="all, delete-orphan")
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
    payslips = db.relationship('PaySlip', backref='employee', lazy='dynamic', cascade="all, delete-orphan")

    # Datos legales
    dui = db.Column(String(20), unique=True, index=True)
    nit = db.Column(String(20), unique=True, index=True)
    isss_number = db.Column(String(20), unique=True)
    afp_number = db.Column(String(20), unique=True)

    def __repr__(self):
        return f'<Employee {self.full_name}>'

# Alias Empleado referenciado en el app factory, se mapea a Employee
class Empleado(Employee):
     __tablename__ = 'empleado_alias'
     __mapper_args__ = {
        'polymorphic_identity': 'empleado',
    }

class PaySlip(db.Model):
    """Planillas de pago (Fusión de PaySlip y Planilla)"""
    __tablename__ = 'payslip'

    id = db.Column(Integer, primary_key=True)
    employee_id = db.Column(Integer, ForeignKey('employee.id'), nullable=False, index=True)

    period_start = db.Column(Date, nullable=True)
    period_end = db.Column(Date, nullable=True)
    payment_date = db.Column(Date, nullable=True)

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

# Alias Planilla referenciado en el app factory, se mapea a PaySlip
class Planilla(PaySlip):
     __tablename__ = 'planilla_alias'
     __mapper_args__ = {
        'polymorphic_identity': 'planilla',
    }


# --- MODELOS DE FIRMA ELECTRÓNICA Y CONTRATOS (Integración) ---

class Cliente(db.Model):
    """Perfil específico de Cliente (Del HEAD - Usado en módulos FEA)"""
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

    # Se añade la relación para que back_populates funcione.
    contrato_integracion = relationship("ContratoIntegracion", back_populates="clientes", foreign_keys=[contrato_integracion_id])
    firma_electronica = relationship("FirmaElectronica", back_populates="clientes", foreign_keys=[firma_electronica_id])

    __table_args__ = (UniqueConstraint('dui'), UniqueConstraint('email'))

class ContratoIntegracion(db.Model):
    """Contrato de Integración y Documentos (Del HEAD)"""
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

    clientes = relationship("Cliente", back_populates="contrato_integracion", foreign_keys=[Cliente.contrato_integracion_id])

class FirmaElectronica(db.Model):
    """Registro de Firma Electrónica (Del HEAD)"""
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

    clientes = relationship("Cliente", back_populates="firma_electronica", foreign_keys=[Cliente.firma_electronica_id])

class CertificadoValidacion(db.Model):
    """Certificado de Validación de Firma (Del HEAD)"""
    __tablename__ = 'certificado_validacion'

    id = db.Column(Integer, primary_key=True)
    certificado_id = db.Column(String(50), unique=True, nullable=False)
    firma_id = db.Column(String(50), nullable=False)
    documento_id = db.Column(String(50), nullable=False)
    cliente_dui = db.Column(String(12), nullable=False)
    pdf_certificado = db.Column(Text)
    fecha_generacion = db.Column(DateTime, default=datetime.utcnow)
    valido_hasta = db.Column(DateTime)


# --- MODELOS PARA FORMULACIÓN DE CONTRATOS (LAN-F2C) ---

class ContractTemplate(db.Model):
    """Plantillas de Contratos"""
    __tablename__ = 'contract_template'

    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(100), nullable=False, index=True)
    description = db.Column(Text)
    content = db.Column(Text, nullable=False)

    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    created_by_id = db.Column(Integer, ForeignKey('user.id'))

    created_at = db.Column(DateTime, default=func.current_timestamp())
    updated_at = db.Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())

    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='created_templates')

    __table_args__ = (UniqueConstraint('name', 'tenant_id', name='_contract_template_tenant_uc'),)

    def __repr__(self):
        return f'<ContractTemplate {self.name}>'

class GeneratedContract(db.Model):
    """Contratos Generados a partir de plantillas"""
    __tablename__ = 'generated_contract'

    id = db.Column(Integer, primary_key=True)
    template_id = db.Column(Integer, ForeignKey('contract_template.id'), nullable=False, index=True)

    related_entity = db.Column(String(50), index=True)
    related_entity_id = db.Column(Integer, index=True)

    content_final = db.Column(Text, nullable=False)

    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    generated_by_id = db.Column(Integer, ForeignKey('user.id'))

    status = db.Column(String(50), default='Generado', nullable=False)

    created_at = db.Column(DateTime, default=func.current_timestamp())

    template = db.relationship('ContractTemplate')
    generated_by = db.relationship('User', foreign_keys=[generated_by_id], backref='generated_contracts')

    def __repr__(self):
        return f'<GeneratedContract {self.id} for {self.related_entity}:{self.related_entity_id}>'

# --- MODELOS PARA CRM (LAN-CRM3) ---

class Contact(db.Model):
    """Contactos del CRM (Prospectos y Clientes)"""
    __tablename__ = 'crm_contact'

    id = db.Column(Integer, primary_key=True)
    full_name = db.Column(String(120), nullable=False, index=True)
    email = db.Column(String(120), index=True)
    phone = db.Column(String(50))

    user_id = db.Column(Integer, ForeignKey('user.id'), nullable=True)

    contact_type = db.Column(String(50), default='Prospecto', index=True)
    status = db.Column(String(50), default='Nuevo', index=True)

    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    assigned_to_id = db.Column(Integer, ForeignKey('user.id'))

    created_at = db.Column(DateTime, default=func.current_timestamp())
    updated_at = db.Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())

    interactions = db.relationship('Interaction', backref='contact', lazy='dynamic', cascade="all, delete-orphan")
    opportunities = db.relationship('Opportunity', backref='contact', lazy='dynamic', cascade="all, delete-orphan")
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id], backref='assigned_crm_contacts')

    def __repr__(self):
        return f'<Contact {self.full_name}>'

class Interaction(db.Model):
    """Interacciones con los contactos"""
    __tablename__ = 'crm_interaction'

    id = db.Column(Integer, primary_key=True)
    contact_id = db.Column(Integer, ForeignKey('crm_contact.id'), nullable=False, index=True)

    interaction_type = db.Column(String(50), nullable=False)
    notes = db.Column(Text)

    interaction_date = db.Column(DateTime, default=func.current_timestamp())

    user_id = db.Column(Integer, ForeignKey('user.id'))
    user = db.relationship('User', foreign_keys=[user_id], backref='created_interactions')

    def __repr__(self):
        return f'<Interaction {self.interaction_type} with Contact {self.contact_id}>'

class Opportunity(db.Model):
    """Oportunidades de Venta"""
    __tablename__ = 'crm_opportunity'

    id = db.Column(Integer, primary_key=True)
    contact_id = db.Column(Integer, ForeignKey('crm_contact.id'), nullable=False, index=True)

    name = db.Column(String(200), nullable=False)
    stage = db.Column(String(50), default='Calificación', index=True)
    amount = db.Column(Float)

    loan_product_id = db.Column(Integer, ForeignKey('loan_product.id'), nullable=True)

    assigned_to_id = db.Column(Integer, ForeignKey('user.id'))
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)

    close_date = db.Column(Date)
    created_at = db.Column(DateTime, default=func.current_timestamp())

    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id], backref='assigned_opportunities')

    def __repr__(self):
        return f'<Opportunity {self.name}>'


# --- MODELOS PARA INVENTARIO (LAN-INV9) ---

class Product(db.Model):
    """Productos del Inventario"""
    __tablename__ = 'inventory_product'

    id = db.Column(Integer, primary_key=True)
    sku = db.Column(String(100), nullable=False, index=True)
    name = db.Column(String(200), nullable=False, index=True)
    description = db.Column(Text)

    price = db.Column(Float, nullable=False)
    stock = db.Column(Integer, default=0)

    min_stock_level = db.Column(Integer, default=0)

    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    is_active = db.Column(Boolean, default=True)

    movements = db.relationship('StockMovement', backref='product', lazy='dynamic', cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint('sku', 'tenant_id', name='_product_sku_tenant_uc'),)

    def __repr__(self):
        return f'<Product {self.name}>'

class StockMovement(db.Model):
    """Movimientos de Stock (Entradas y Salidas)"""
    __tablename__ = 'inventory_stock_movement'

    id = db.Column(Integer, primary_key=True)
    product_id = db.Column(Integer, ForeignKey('inventory_product.id'), nullable=False, index=True)

    movement_type = db.Column(String(50), nullable=False, index=True)
    quantity = db.Column(Integer, nullable=False)

    notes = db.Column(Text)

    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    user_id = db.Column(Integer, ForeignKey('user.id'))

    created_at = db.Column(DateTime, default=func.current_timestamp())
    user = db.relationship('User', foreign_keys=[user_id], backref='stock_movements')

    def __repr__(self):
        return f'<StockMovement {self.movement_type} of {self.quantity} for Product {self.product_id}>'


# --- MODELOS PARA VENTAS (LAN-SLS2) ---

class Quote(db.Model):
    """Cotizaciones de Venta"""
    __tablename__ = 'sales_quote'

    id = db.Column(Integer, primary_key=True)
    contact_id = db.Column(Integer, ForeignKey('crm_contact.id'), nullable=False, index=True)
    opportunity_id = db.Column(Integer, ForeignKey('crm_opportunity.id'), nullable=True, index=True)

    status = db.Column(String(50), default='Borrador', index=True)
    total_amount = db.Column(Float)

    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    created_by_id = db.Column(Integer, ForeignKey('user.id'))

    valid_until = db.Column(Date)
    created_at = db.Column(DateTime, default=func.current_timestamp())

    items = db.relationship('SalesOrderItem', backref='quote', lazy='dynamic', cascade="all, delete-orphan")
    contact = db.relationship('Contact', backref='quotes')
    opportunity = db.relationship('Opportunity', backref='quotes')
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='created_quotes')

    def __repr__(self):
        return f'<Quote {self.id}>'

class SalesOrder(db.Model):
    """Órdenes de Venta"""
    __tablename__ = 'sales_order'

    id = db.Column(Integer, primary_key=True)
    contact_id = db.Column(Integer, ForeignKey('crm_contact.id'), nullable=False, index=True)
    quote_id = db.Column(Integer, ForeignKey('sales_quote.id'), nullable=True, index=True)

    status = db.Column(String(50), default='Pendiente', index=True)
    total_amount = db.Column(Float)

    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    created_by_id = db.Column(Integer, ForeignKey('user.id'))

    order_date = db.Column(Date, default=date.today)

    items = db.relationship('SalesOrderItem', backref='sales_order', lazy='dynamic', cascade="all, delete-orphan")
    contact = db.relationship('Contact', backref='sales_orders')
    quote = db.relationship('Quote', foreign_keys=[quote_id], backref=backref('sales_order_link', uselist=False))
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='created_sales_orders')


    def __repr__(self):
        return f'<SalesOrder {self.id}>'

class SalesOrderItem(db.Model):
    """Líneas de una Orden de Venta"""
    __tablename__ = 'sales_order_item'

    id = db.Column(Integer, primary_key=True)

    sales_order_id = db.Column(Integer, ForeignKey('sales_order.id'), nullable=True, index=True)
    quote_id = db.Column(Integer, ForeignKey('sales_quote.id'), nullable=True, index=True)

    product_id = db.Column(Integer, ForeignKey('inventory_product.id'), nullable=False, index=True)

    quantity = db.Column(Integer, nullable=False)
    price_per_unit = db.Column(Float, nullable=False)

    total_price = db.Column(Float, nullable=False)

    product = db.relationship('Product')

    __table_args__ = (
        CheckConstraint('(sales_order_id IS NOT NULL AND quote_id IS NULL) OR (sales_order_id IS NULL AND quote_id IS NOT NULL)',
                        name='_sales_item_one_parent_check'),
    )

    def __repr__(self):
        return f'<SalesOrderItem {self.quantity} x Product {self.product_id}>'


# --- MODELOS PARA COMPRAS (LAN-CO1M) ---

class Supplier(db.Model):
    """Proveedores de la empresa"""
    __tablename__ = 'purchasing_supplier'

    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(150), nullable=False, index=True)
    contact_person = db.Column(String(150))
    email = db.Column(String(120), index=True)
    phone = db.Column(String(50))
    address = db.Column(Text)

    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    is_active = db.Column(Boolean, default=True)

    purchase_orders = db.relationship('PurchaseOrder', backref='supplier_obj', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Supplier {self.name}>'

class PurchaseOrder(db.Model):
    """Órdenes de Compra"""
    __tablename__ = 'purchasing_order'

    id = db.Column(Integer, primary_key=True)
    supplier_id = db.Column(Integer, ForeignKey('purchasing_supplier.id'), nullable=False, index=True)

    order_date = db.Column(Date, default=date.today)
    expected_delivery_date = db.Column(Date)

    status = db.Column(String(50), default='Borrador', index=True)
    total_amount = db.Column(Float)

    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    created_by_id = db.Column(Integer, ForeignKey('user.id'))

    items = db.relationship('PurchaseOrderItem', backref='purchase_order', lazy='dynamic', cascade="all, delete-orphan")
    supplier = db.relationship('Supplier')
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='created_purchase_orders')


    def __repr__(self):
        return f'<PurchaseOrder {self.id}>'

class PurchaseOrderItem(db.Model):
    """Líneas de una Orden de Compra"""
    __tablename__ = 'purchasing_order_item'

    id = db.Column(Integer, primary_key=True)
    purchase_order_id = db.Column(Integer, ForeignKey('purchasing_order.id'), nullable=False, index=True)
    product_id = db.Column(Integer, ForeignKey('inventory_product.id'), nullable=False, index=True)

    quantity = db.Column(Integer, nullable=False)
    price_per_unit = db.Column(Float, nullable=False)

    total_price = db.Column(Float, nullable=False)

    product = db.relationship('Product')

    def __repr__(self):
        return f'<PurchaseOrderItem {self.quantity} x Product {self.product_id}>'


# --- MODELOS DE MENSAJERÍA (LAN-C8T) ---

class Channel(db.Model):
    """Canales de mensajería (general o privado)"""
    __tablename__ = 'channel'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(100), nullable=False)
    description = db.Column(Text)
    channel_type = db.Column(String(20), default='public') # public, private, direct
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False)
    creator_id = db.Column(Integer, ForeignKey('user.id'), nullable=False)

    messages = db.relationship('Message', backref='channel', lazy='dynamic', cascade="all, delete-orphan")
    creator = db.relationship('User', foreign_keys=[creator_id], backref='created_channels')

    def __repr__(self):
        return f'<Channel {self.name} ({self.channel_type})>'

class Message(db.Model):
    """Mensajes dentro de un canal"""
    __tablename__ = 'message'
    id = db.Column(Integer, primary_key=True)
    channel_id = db.Column(Integer, ForeignKey('channel.id'), nullable=False)
    user_id = db.Column(Integer, ForeignKey('user.id'), nullable=False)
    content = db.Column(Text, nullable=False)
    created_at = db.Column(DateTime, default=func.current_timestamp())

    author = db.relationship('User', foreign_keys=[user_id], backref='sent_messages')

    def __repr__(self):
        return f'<Message {self.id} in Channel {self.channel_id}>'


# --- MODELOS DE MÓDULOS EXTENDIDOS ---

class MailingList(db.Model):
    """Lista de correos para campañas de marketing"""
    __tablename__ = 'mailing_list'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(100), nullable=False)
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=True)
    members = db.relationship('User', secondary=mailing_list_members, backref='mailing_lists')

    def __repr__(self):
        return f'<MailingList {self.name}>'

class AuditLog(db.Model):
    """Registro de auditoría"""
    __tablename__ = 'audit_log'
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(Integer, ForeignKey('user.id'), nullable=False, index=True)
    action = db.Column(String(100), nullable=False, index=True)
    details = db.Column(Text)
    ip_address = db.Column(String(45))
    user_agent = db.Column(String(500))
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=True, index=True)
    timestamp = db.Column(DateTime, default=func.current_timestamp(), index=True)

    def __repr__(self):
        return f'<AuditLog {self.action} by {self.user_id}>'

class NotificationTemplate(db.Model):
    """Plantillas de notificación"""
    __tablename__ = 'notification_template'
    id = db.Column(Integer, primary_key=True)
    slug = db.Column(String(50), nullable=False, index=True)
    name = db.Column(String(100), nullable=False)
    subject = db.Column(String(255), nullable=False)
    body = db.Column(Text, nullable=False)
    type = db.Column(String(20), default='Email')
    variables = db.Column(Text, default='[]') # Usando Text como fallback para JSONB
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    is_active = db.Column(Boolean, default=True)
    __table_args__ = (UniqueConstraint('slug', 'tenant_id', name='_notification_template_tenant_uc'),)

    def __repr__(self):
        return f'<NotificationTemplate {self.slug}>'

class EmailLog(db.Model):
    """Registro de correos enviados (Definición completa)"""
    __tablename__ = 'email_log'
    id = db.Column(Integer, primary_key=True)
    recipient = db.Column(String(120), nullable=False)
    subject = db.Column(String(255), nullable=False)
    sent_at = db.Column(DateTime, default=func.current_timestamp())
    # Campos adicionales asumidos por la lógica de la app
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=True)
    sent_by_id = db.Column(Integer, ForeignKey('user.id'), nullable=True)
    sent_by = db.relationship('User', foreign_keys=[sent_by_id], backref='sent_email_logs') # Added relationship

    def __repr__(self):
        return f'<EmailLog {self.id} - {self.recipient}>'

# --- MODELOS PARA FIRMAR (LAN-SGN3) ---
# Added from feature-LAN-F2C branch
class SignableTemplate(db.Model):
    """Plantillas de documentos comerciales para firma (propuestas, etc.)."""
    __tablename__ = 'sign_template'

    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(150), nullable=False, index=True)
    description = db.Column(Text)
    content = db.Column(Text, nullable=False)  # Contenido con placeholders como {{variable}}

    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    created_by_id = db.Column(Integer, ForeignKey('user.id'))

    created_at = db.Column(DateTime, default=func.current_timestamp())
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='created_signable_templates')

    __table_args__ = (UniqueConstraint('name', 'tenant_id', name='_sign_template_tenant_uc'),)

    def __repr__(self):
        return f'<SignableTemplate {self.name}>'

class SignatureRequest(db.Model):
    """Solicitudes de firma para documentos específicos."""
    __tablename__ = 'sign_request'

    id = db.Column(Integer, primary_key=True)
    template_id = db.Column(Integer, ForeignKey('sign_template.id'), nullable=True)

    signer_name = db.Column(String(150), nullable=False)
    signer_email = db.Column(String(120), nullable=False, index=True)

    status = db.Column(String(50), default='draft', nullable=False, index=True) # draft, sent, viewed, signed, declined

    unique_token = db.Column(String(128), unique=True, nullable=False, index=True) # Para la URL pública

    final_document_content = db.Column(Text) # El documento con los datos rellenados
    signature_data = db.Column(Text) # Puede ser un data URL de la imagen de la firma

    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    created_by_id = db.Column(Integer, ForeignKey('user.id'))

    created_at = db.Column(DateTime, default=func.current_timestamp())
    sent_at = db.Column(DateTime)
    signed_at = db.Column(DateTime)

    template = db.relationship('SignableTemplate', backref='signature_requests')
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='created_signature_requests')

    def __repr__(self):
        return f'<SignatureRequest {self.id} for {self.signer_email}>'
    
# --- MODELOS PARA GESTIÓN DE PROYECTOS (LAN-PR0) ---
# Added from feature-LAN-F2C branch
class Project(db.Model):
    """Proyectos de la empresa."""
    __tablename__ = 'project'

    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(150), nullable=False, index=True)
    description = db.Column(Text)
    status = db.Column(String(50), default='Not Started', nullable=False, index=True) # Not Started, In Progress, Completed, On Hold

    start_date = db.Column(Date)
    end_date = db.Column(Date)
    budget = db.Column(Float)

    manager_id = db.Column(Integer, ForeignKey('user.id'))
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)

    created_at = db.Column(DateTime, default=func.current_timestamp())

    manager = db.relationship('User', foreign_keys=[manager_id], backref='managed_projects')
    tasks = db.relationship('Task', backref='project', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Project {self.name}>'

class Task(db.Model):
    """Tareas dentro de un proyecto."""
    __tablename__ = 'task'

    id = db.Column(Integer, primary_key=True)
    project_id = db.Column(Integer, ForeignKey('project.id'), nullable=False, index=True)
    title = db.Column(String(200), nullable=False)
    description = db.Column(Text)
    status = db.Column(String(50), default='To Do', nullable=False, index=True) # To Do, In Progress, Done

    due_date = db.Column(Date)
    priority = db.Column(String(50), default='Medium') # Low, Medium, High

    assigned_to_id = db.Column(Integer, ForeignKey('user.id'))
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)

    created_at = db.Column(DateTime, default=func.current_timestamp())

    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id], backref='assigned_tasks')

    def __repr__(self):
        return f'<Task {self.title}>'

# --- FIN DE MODELOS ---

# === MOCK DE SERVICIOS Y UTILIDADES (Necesario para que el app factory funcione) ===

class MockService:
    def __init__(self, name):
        self.name = name
    def __call__(self, *args, **kwargs):
        return self
    def send_email(self, recipient, subject, body, tenant):
        print(f"[{self.name}] Enviando correo a {recipient}. Asunto: {subject}")
        return True, f"Correo enviado a {recipient}"
    def get_documents_for_tenant(self, tenant_id):
        # Devuelve un mock para la ruta GET /api/documents
        class MockDoc:
            id = 1
            filename = 'test.pdf'
            description = 'Mock'
            latest_version_id = 1
            created_at = datetime.utcnow()
            updated_at = datetime.utcnow()
        return [MockDoc()]
    def create_document(self, tenant_id, user_id, file, description):
        class MockDoc: id = 2
        return MockDoc()
    def add_new_version(self, doc_id, user_id, file):
        class MockVersion: id = 3
        return MockVersion()
    def get_document_version(self, version_id):
        class MockVersionFile:
            filepath = os.path.join(os.getcwd(), 'test_file.txt')
        # Crear archivo mock si no existe para evitar FileNotFoundError
        if not os.path.exists(MockVersionFile.filepath):
             with open(MockVersionFile.filepath, 'w') as f: f.write('Mock content.')
        return MockVersionFile()
    def get_balance_sheet(self, tenant_id):
        return {"report_name": "Balance Sheet", "assets": 100000.0}
    def get_income_statement(self, tenant_id):
        return {"report_name": "Income Statement", "revenue": 20000.0}
    def get_user_channels(self, user_id, tenant_id):
        class MockChannel:
            id = 1
            name = 'General'
            description = 'Canal general'
            channel_type = 'public'
        return [MockChannel()]
    def create_channel(self, name, description, channel_type, tenant_id, creator_id):
        class MockChannel: id = 2
        return MockChannel()
    def get_messages_for_channel(self, channel_id):
        class MockMessage:
            id = 101
            content = "Hola!"
            user_id = 1
            author = self.get_mock_user()
            created_at = datetime.utcnow()
        return [MockMessage()]
    def post_message(self, channel_id, user_id, content):
        class MockMessage: id = 102
        return MockMessage()
    def get_mock_user(self):
         class MockUser: full_name = "Mock User"
         return MockUser()
    def log_action(self, *args, **kwargs):
        pass # No implementado en mock
    def create_template(self, *args, **kwargs):
         class MockTemplate: id = 5
         return MockTemplate() # Needed for sign_bp
    # --- Mocks para servicios añadidos ---
    def create_contact(self, *args, **kwargs): pass
    def get_contacts(self, *args, **kwargs): return []
    def get_contact_details(self, *args, **kwargs): return {}
    def create_interaction(self, *args, **kwargs): pass
    def create_opportunity(self, *args, **kwargs): pass
    def update_opportunity_stage(self, *args, **kwargs): pass
    def create_product(self, *args, **kwargs): pass
    def get_products(self, *args, **kwargs): return []
    def record_stock_movement(self, *args, **kwargs): pass
    def create_quote(self, *args, **kwargs): pass
    def get_sales_orders(self, *args, **kwargs): return []
    def convert_quote_to_sales_order(self, *args, **kwargs): pass
    def confirm_sales_order(self, *args, **kwargs): pass
    def create_supplier(self, *args, **kwargs): pass
    def create_purchase_order(self, *args, **kwargs): pass
    def receive_purchase_order(self, *args, **kwargs): pass
    # --- Mocks for sign_service ---
    def get_templates_for_tenant(self, *args, **kwargs):
        class MockSignTemplate:
             id=1; name='Test Sign Template'; description='Desc'
        return [MockSignTemplate()]
    def get_signature_requests(self, *args, **kwargs):
        class MockSignReq:
             id=1; signer_name='John Doe'; signer_email='j@d.com'; status='sent'; created_at=datetime.utcnow()
        return [MockSignReq()]
    def create_signature_request(self, *args, **kwargs):
        class MockSignReq: id=2
        return MockSignReq()
    def send_signature_request(self, *args, **kwargs): pass
    def get_request_by_token(self, token):
        class MockSignReq:
             status = 'sent'; signer_name='Jane Doe'; final_document_content='<p>Sign Here</p>'
        if token == 'valid_token': return MockSignReq()
        raise ValueError("Invalid Token")
    def sign_document(self, token, data):
        if token != 'valid_token': raise ValueError("Invalid Token")
        print(f"Signing document for token {token} with data: {data}")
    # --- Mocks for form_service (Placeholder as models are missing) ---
    def get_forms_for_tenant(self, *args, **kwargs): return []
    def create_form(self, *args, **kwargs): class MockForm: id=1; public_token='abc'; return MockForm()
    def get_submissions_for_form(self, *args, **kwargs): return []
    def get_form_by_token(self, token): raise ValueError("Invalid Token") # Placeholder
    def submit_form(self, token, data): raise ValueError("Invalid Token") # Placeholder
    # --- Mocks for project_service ---
    def get_projects_for_tenant(self, *args, **kwargs):
        class MockProject:
            id=1; name='Test Project'; status='In Progress'; end_date=datetime.utcnow().date()
        return [MockProject()]
    def create_project(self, *args, **kwargs):
        class MockProject: id=2
        return MockProject()
    def get_project_details(self, *args, **kwargs):
        class MockProject:
            id=1; name='Test Project'; description='Desc'; status='In Progress'; budget=5000.0
        return MockProject()
    def get_tasks_for_project(self, *args, **kwargs):
        class MockTask:
            id=101; title='Develop feature'; status='To Do'; due_date=datetime.utcnow().date()
        return [MockTask()]
    def create_task(self, *args, **kwargs):
        class MockTask: id=102
        return MockTask()
    def update_task_status(self, *args, **kwargs):
        class MockTask: id=101; status='In Progress'
        return MockTask()


def validacion_identidad_estricta(data): return True
def capturar_datos_biometricos(): return {"biometric_data": "hash_biometrico"}
def generar_contrato_integracion(data): return "CONTRATO-UUID-123"
def firma_electronica_avanzada(contrato_id, data, datos_biometricos):
    return {"valida": True, "firma_id": "FIRMA-UUID-456"}
def calcular_planilla(salario_base):
    return {
        'success': True,
        'salario_base': salario_base,
        'isss': 100,
        'afp': 100,
        'renta': 50,
        'salario_neto': salario_base - 250
    }

# Inicializar extensiones fuera del factory, pero sin app
jwt = JWTManager()
migrate = Migrate()

# --- APP FACTORY ---

def create_app(config_object=None, testing_config=None):
    # Flask app instance
    app = Flask(__name__, instance_relative_config=True)

    # Configuración de base (Debería estar en un archivo config.py)
    app.config.from_mapping(
        SECRET_KEY='default-secret-key',
        JWT_SECRET_KEY='default-jwt-secret-key',
        SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        UPLOAD_FOLDER=os.path.join(app.instance_path, 'uploads')
    )

    # Sobrescribir con config_object o testing_config
    if config_object:
         app.config.from_object(config_object)
    if testing_config:
        app.config.from_object(testing_config)

    # Variables de entorno críticas (con fallback)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', app.config.get('SECRET_KEY'))
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', app.config.get('JWT_SECRET_KEY'))
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', app.config.get('SQLALCHEMY_DATABASE_URI'))

    # Crear carpeta de uploads
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # --- INICIALIZACIÓN DE EXTENSIONES ---
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    # --- CARGA DINÁMICA DE MODELOS Y SERVICIOS ---
    with app.app_context():
        # RESOLUCIÓN DE CONFLICTO: Se usa la lógica de Mocks pero se incluyen TODOS los modelos definidos.

        # Mapear modelos al contexto de la app, incluyendo alias para compatibilidad
        app.models = {
            'Role': Role, 'User': User, 'LoanProduct': LoanProduct, 'LoanApplication': LoanApplication,
            'Account': Account, 'Transaction': Transaction, 'JournalEntry': JournalEntry, 'Cliente': Cliente,
            'ContratoIntegracion': ContratoIntegracion, 'ProductoCredito': ProductoCredito,
            'Empleado': Empleado, 'Planilla': Planilla, 'Employee': Employee, 'AuditLog': AuditLog,
            'ClientProfile': ClientProfile, 'Tenant': Tenant, 'Payment': Payment,
            'NotificationTemplate': NotificationTemplate, 'ContractTemplate': ContractTemplate,
            'GeneratedContract': GeneratedContract, 'Contact': Contact, 'Interaction': Interaction,
            'Opportunity': Opportunity, 'Product': Product, 'StockMovement': StockMovement,
            'Quote': Quote, 'SalesOrder': SalesOrder, 'SalesOrderItem': SalesOrderItem,
            'Supplier': Supplier, 'PurchaseOrder': PurchaseOrder, 'PurchaseOrderItem': PurchaseOrderItem,
            'EmailLog': EmailLog, 'Channel': Channel, 'Message': Message,
            'SignableTemplate': SignableTemplate, 'SignatureRequest': SignatureRequest,
            'Form': Form, 'FormSubmission': FormSubmission, 'Project': Project, 'Task': Task
        }

        # Asignar servicios mock (simulación) - Actualizado con todos los servicios
        app.services = {
            'audit_service': MockService('Audit'),
            'contract_service': MockService('Contract'),
            'crm_service': MockService('CRM'),
            'inventory_service': MockService('Inventory'),
            'sales_service': MockService('Sales'),
            'purchasing_service': MockService('Purchasing'),
            'email_service': MockService('Email'),
            'document_service': MockService('Document'),
            'accounting_service': MockService('Accounting'),
            'messaging_service': MockService('Messaging'),
            'sign_service': MockService('Sign'), # Added mock for sign service
            'form_service': MockService('Form'),  # Added mock for form service
            'project_service': MockService('Project') # Added mock for project service
        }

    # --- DECORADORES DE AUTORIZACIÓN (Unificado) ---
    def role_required(required_roles):
        if not isinstance(required_roles, list):
            required_roles = [required_roles]

        def decorator(fn):
            @wraps(fn)
            @jwt_required()
            def wrapper(*args, **kwargs):
                User = app.models.get('User')
                if not User: return jsonify({"msg": "Error interno de sistema (Modelo User)"}), 500

                claims = get_jwt()
                user_identity = get_jwt_identity()

                g.current_user = User.query.filter_by(email=user_identity).first()
                if not g.current_user:
                    return jsonify({"msg": "Usuario no encontrado en la base de datos"}), 404

                # Obtener roles: del token (claims) y el rol principal (ForeignKey)
                user_roles = set(claims.get('roles', []))
                if g.current_user.role:
                     user_roles.add(g.current_user.role.name)

                user_has_required_role = any(role in user_roles for role in required_roles)

                if not user_has_required_role:
                    return jsonify({"msg": "Acceso no autorizado para este rol"}), 403
                return fn(*args, **kwargs)
            return wrapper
        return decorator

    app.jinja_env.globals['role_required'] = role_required
    app.jinja_env.globals['require_roles'] = role_required # Alias

    # --- MIDDLEWARE DE AUDITORÍA (Del 2.0) ---

    @app.before_request
    def audit_request():
        if request.path.startswith('/api/') and request.method in ['POST', 'PUT', 'DELETE']:
            g.audit_action = f"{request.method} {request.path}"

    @app.after_request
    def audit_response(response):
        AuditLog = app.models.get('AuditLog')

        if hasattr(g, 'audit_action') and hasattr(g, 'current_user') and AuditLog and g.current_user and hasattr(g.current_user, 'id'):
            try:
                # El modelo AuditLog tiene 'tenant_id' como nullable, se puede omitir si no existe.
                audit_log = AuditLog(
                    user_id=g.current_user.id,
                    action=g.audit_action,
                    details=f"Status: {response.status_code}",
                    ip_address=request.remote_addr,
                    tenant_id=getattr(g.current_user, 'tenant_id', None) # Safely get tenant_id
                )
                db.session.add(audit_log)
                db.session.commit()
            except Exception as e:
                app.logger.error(f"Error en auditoría: {str(e)}")
                db.session.rollback()

        return response

    # -------------------------------------------------------------------
    # === RUTAS MONOLÍTICAS ===
    # -------------------------------------------------------------------

    # --- RUTAS BASE ---
    @app.route('/')
    def index():
        return jsonify({"message": "Servidor del Sistema de Gestión Financiera en funcionamiento.", "version": "2.1 (Fusion)"})

    @app.route('/api/health')
    def health_check():
        db_connected = False
        try:
            # Use text() for database-agnostic check
            from sqlalchemy import text
            db.session.execute(text("SELECT 1")).scalar()
            db_connected = True
        except Exception as e:
            app.logger.error(f"Health check DB connection failed: {e}")
            db_connected = False

        return jsonify({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database_connected": db_connected,
        })

    # --- RUTAS DE AUTENTICACIÓN ---
    @app.route('/api/register', methods=['POST'])
    def register():
        User = app.models.get('User')
        Role = app.models.get('Role')
        if not User or not Role: return jsonify({"msg": "Error de sistema (Modelos no cargados)"}), 500

        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        role_name = data.get('role', 'Cliente') # Default role if not provided

        if not email or not password:
            return jsonify({"msg": "Email y contraseña son requeridos"}), 400
        if User.query.filter_by(email=email).first():
            return jsonify({"msg": "El email ya está registrado"}), 400

        # Find role - assuming roles might be tenant-specific or global (tenant_id=None)
        # This logic might need refinement based on actual multi-tenant role strategy
        role = Role.query.filter_by(name=role_name, tenant_id=None).first() # Example: Check for global role first
        # if not role and tenant_id: # If tenant context exists, check tenant-specific role
        #     role = Role.query.filter_by(name=role_name, tenant_id=tenant_id).first()

        if not role:
             # Fallback: Create a default 'Cliente' role if it doesn't exist? Or return error.
             if role_name == 'Cliente':
                 role = Role(name='Cliente', description='Rol de cliente por defecto', tenant_id=None)
                 db.session.add(role)
                 db.session.flush() # Get the ID before commit
                 app.logger.info(f"Created default role: {role_name}")
             else:
                return jsonify({"msg": f"El rol '{role_name}' no es válido o no está configurado"}), 400

        # Associate user with the role's tenant (or global if role is global)
        new_user = User(email=email, role_id=role.id, tenant_id=role.tenant_id)
        new_user.set_password(password)
        db.session.add(new_user)
        try:
            db.session.commit()
            return jsonify({"msg": "Usuario creado exitosamente"}), 201
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error registering user: {e}")
            return jsonify({"msg": "Error al crear el usuario"}), 500


    @app.route('/api/login', methods=['POST'])
    def login():
        User = app.models.get('User')
        if not User: return jsonify({"msg": "Error de sistema (Modelo User)"}), 500

        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({"msg": "Email y contraseña son requeridos"}), 400

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            # Fetch roles for claims (both primary via role_id and secondary via roles_m2m)
            user_roles_names = set()
            if user.role:
                user_roles_names.add(user.role.name)
            for role_obj in user.roles_m2m:
                user_roles_names.add(role_obj.name)

            # Ensure there's at least a default role if none assigned
            if not user_roles_names:
                user_roles_names.add('Cliente') # Default fallback role

            access_token = create_access_token(
                identity=user.email,
                additional_claims={
                    'roles': list(user_roles_names),
                    'email': user.email,
                    'user_id': user.id,
                    'tenant_id': user.tenant_id
                }
            )
            
            return jsonify(access_token=access_token)

        return jsonify({"msg": "Credenciales inválidas"}), 401


    @app.route('/api/admin/test')
    @role_required('Administrador General') # Example role name
    def admin_test_route():
        # g.current_user is set by the role_required decorator
        return jsonify(logged_in_as=g.current_user.email, role=g.current_user.role.name if g.current_user.role else 'N/A'), 200

    @app.route('/api/profile', methods=['GET'])
    @jwt_required()
    def get_profile():
        current_identity = get_jwt_identity()
        User = app.models.get('User')
        user = User.query.filter_by(email=current_identity).first()

        if not user: return jsonify({"msg": "Usuario no encontrado"}), 404

        return jsonify({
            "email": user.email,
            "full_name": user.full_name,
            "dui": user.dui,
            "nit": user.nit,
            "role": user.role.name if user.role else 'N/A' # Primary role
        })

    # --- RUTA DE CREACIÓN DE CLIENTE CON FEA ---
    @app.route('/api/clientes/nuevo', methods=['POST'])
    @jwt_required()
    @role_required(['Administrador General', 'Ejecutivo de Crédito']) # Example roles
    def crear_nuevo_cliente():
        Cliente = app.models.get('Cliente')
        ContratoIntegracion = app.models.get('ContratoIntegracion')
        if not Cliente or not ContratoIntegracion: return jsonify({"error": "Error de sistema (Modelos no cargados)"}), 500

        try:
            data = request.get_json()
            datos_requeridos = ['nombre_completo', 'dui', 'email', 'telefono', 'direccion']
            for campo in datos_requeridos:
                if campo not in data:
                    return jsonify({'error': f'Campo requerido: {campo}'}), 400
            
            if not validacion_identidad_estricta(data):
                return jsonify({'error': 'Validación de identidad falló.'}), 400

            datos_biometricos = capturar_datos_biometricos()
            if not datos_biometricos:
                return jsonify({'error': 'Error en la captura de datos biométricos.'}), 500

            contrato_id = generar_contrato_integracion(data)
            if not contrato_id:
                return jsonify({'error': 'No se pudo generar el contrato de integración.'}), 500

            resultado_firma = firma_electronica_avanzada(contrato_id, data, datos_biometricos)
            
            if not resultado_firma.get('valida'):
                contrato = ContratoIntegracion.query.filter_by(contrato_id=contrato_id).first()
                if contrato:
                    db.session.delete(contrato)
                    db.session.commit()
                return jsonify({'error': 'El proceso de firma electrónica falló.', 'detalle': resultado_firma.get('error')}), 400

            cliente = Cliente(
                nombre_completo=data['nombre_completo'],
                dui=data['dui'],
                email=data['email'],
                telefono=data['telefono'],
                direccion=data['direccion'],
                contrato_integracion_id=contrato_id,
                firma_electronica_id=resultado_firma.get('firma_id'),
                estado='ACTIVO'
            )
            db.session.add(cliente)
            db.session.commit()

            return jsonify({
                'success': True,
                'cliente_id': cliente.id,
                'contrato_id': contrato_id,
                'mensaje': 'Cliente creado y contrato firmado exitosamente.'
            }), 201

        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error creating client: {e}")
            return jsonify({'error': 'Ocurrió un error inesperado.', 'detalle': str(e)}), 500


    # --- RUTA DE CALCULO DE PLANILLA ---
    @app.route('/api/payroll/calculate', methods=['POST'])
    @role_required(['Contador', 'Administrador General']) # Example roles
    def calculate_payroll_for_employee():
        Empleado = app.models.get('Empleado') # Uses alias
        Planilla = app.models.get('Planilla') # Uses alias
        if not Empleado or not Planilla: return jsonify({'error': 'Error de sistema (Modelos de Payroll no cargados)'}), 500

        data = request.get_json()
        empleado_id = data.get('empleado_id')
        if not empleado_id:
            return jsonify({'error': 'El campo empleado_id es requerido.'}), 400

        empleado = Empleado.query.get(empleado_id)
        if not empleado:
            return jsonify({'error': 'Empleado no encontrado.'}), 404
        
        resultado_calculo = calcular_planilla(empleado.salary)

        if not resultado_calculo.get('success'):
            return jsonify({'error': 'Error al calcular la planilla.', 'detalle': resultado_calculo.get('error')}), 500

        try:
            nueva_planilla = Planilla(
                employee_id=empleado.id,
                base_salary=resultado_calculo['salario_base'],
                isss_employee=resultado_calculo['isss'],
                afp_employee=resultado_calculo['afp'],
                renta=resultado_calculo['renta'],
                net_salary=resultado_calculo['salario_neto']
            )
            db.session.add(nueva_planilla)
            db.session.commit()
            return jsonify({"success": True, "planilla_id": nueva_planilla.id, "calculo": resultado_calculo})
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error saving payslip: {e}")
            return jsonify({'error': 'Error al guardar el registro de la planilla.', 'detalle': str(e)}), 500

    # ... (Otras rutas de la aplicación omitidas por brevedad) ...

    # --- INICIO DE RUTAS FUSIONADAS (de la rama feature-LAN-F2C...) ---

    @app.route('/api/applications/submit', methods=['POST'])
    @jwt_required()
    def submit_loan_application():
        # TODO: Implement actual loan application submission logic
        return jsonify({"message": "Ruta de solicitud de préstamo pendiente de implementación."}), 501


    @app.route('/api/applications/<int:app_id>/send-reminder', methods=['POST'])
    @jwt_required()
    @role_required(['Administrador General'])
    def send_payment_reminder(app_id):
        LoanApplication = app.models.get('LoanApplication')
        application = LoanApplication.query.get_or_404(app_id)
        
        recipient = application.applicant.email
        subject = f"Recordatorio de Pago para su Préstamo #{application.id}"
        body = f"Hola {application.applicant.full_name or 'cliente'},\n\nEste es un recordatorio de que su próximo pago para el préstamo #{application.id} está por vencer."

        email_service = app.services.get('email_service')
        if not email_service:
             return jsonify({"error": "Servicio de Email no configurado."}), 500

        success, message = email_service.send_email(recipient, subject, body, g.current_user.tenant)

        if success:
             return jsonify({"message": f"Recordatorio de pago enviado para la solicitud {app_id}."}), 200
        else:
             return jsonify({"error": f"Error al enviar recordatorio: {message}"}), 500


    @app.route('/api/applications/<int:app_id>/status', methods=['PUT'])
    @jwt_required()
    @role_required(['Ejecutivo de Crédito', 'Administrador General'])
    def update_application_status(app_id):
        LoanApplication = app.models.get('LoanApplication')
        application = LoanApplication.query.get_or_404(app_id)

        data = request.get_json()
        new_status = data.get('status')

        allowed_statuses = ['Solicitud Recibida', 'En Revisión', 'Aprobado', 'Rechazado', 'Desembolsado']
        if not new_status or new_status not in allowed_statuses:
            return jsonify({"error": f"Estado inválido. Valores permitidos: {', '.join(allowed_statuses)}"}), 400

        old_status = application.status
        application.status = new_status

        if new_status == 'Aprobado' and old_status != 'Aprobado':
            # TODO: Lógica para generar contrato
            pass
        
        try:
            db.session.commit()
            return jsonify({"message": f"Estado de la solicitud {app_id} actualizado a '{new_status}'."})
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error updating application status {app_id}: {e}")
            return jsonify({"error": "Error al actualizar estado."}), 500


    # --- RUTAS PARA GESTIÓN DE CONTRATOS (LAN-F2C) ---

    @app.route('/api/contracts/templates', methods=['POST'])
    @jwt_required()
    @role_required(['Administrador General'])
    def create_contract_template_route():
        data = request.get_json()
        contract_service = app.services.get('contract_service')
        try:
            template = contract_service.create_template(data) # Using mock
            return jsonify({"message": "Plantilla creada.", "template_id": getattr(template,'id',None)}), 201
        except ValueError as e:
             return jsonify({"error": str(e)}), 400
        except Exception as e:
            app.logger.error(f"Error creating contract template: {e}")
            return jsonify({"error": "Error interno al crear plantilla."}), 500


    @app.route('/api/contracts/generate', methods=['POST'])
    @jwt_required()
    @role_required(['Ejecutivo de Crédito', 'Administrador General'])
    def generate_contract_route():
        data = request.get_json()
        return jsonify({"message": "Ruta para generar un contrato (pendiente)."}), 201

    # --- RUTAS PARA CRM (LAN-CRM3) ---

    @app.route('/api/crm/contacts', methods=['POST'])
    @jwt_required()
    @role_required(['Ejecutivo de Crédito', 'Administrador General'])
    def create_crm_contact():
        data = request.get_json()
        app.services['crm_service'].create_contact(data) # Using mock
        return jsonify({"message": "Ruta para crear contacto de CRM implementada."}), 201

    @app.route('/api/crm/contacts', methods=['GET'])
    @jwt_required()
    def get_crm_contacts():
        contacts = app.services['crm_service'].get_contacts(g.current_user.tenant_id) # Using mock
        return jsonify(contacts), 200

    # --- RUTAS PARA GESTIÓN DE PROYECTOS (LAN-PR0) ---
    projects_bp = Blueprint('projects', __name__, url_prefix='/api/projects')

    @projects_bp.route('/', methods=['GET'])
    @jwt_required()
    def get_projects():
        projects = app.services['project_service'].get_projects_for_tenant(g.current_user.tenant_id)
        return jsonify([{'id': p.id, 'name': p.name, 'status': p.status, 'end_date': p.end_date.isoformat() if p.end_date else None} for p in projects])

    @projects_bp.route('/', methods=['POST'])
    @jwt_required()
    def create_project_route():
        data = request.get_json()
        try:
            project = app.services['project_service'].create_project(
                name=data.get('name'),
                description=data.get('description'),
                budget=data.get('budget'),
                start_date=data.get('start_date'),
                end_date=data.get('end_date'),
                manager_id=g.current_user.id,
                tenant_id=g.current_user.tenant_id
            )
            return jsonify({'message': 'Proyecto creado exitosamente', 'project_id': project.id}), 201
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

    @projects_bp.route('/<int:project_id>', methods=['GET'])
    @jwt_required()
    def get_project_details_route(project_id):
        project = app.services['project_service'].get_project_details(project_id, g.current_user.tenant_id)
        tasks = app.services['project_service'].get_tasks_for_project(project_id, g.current_user.tenant_id)
        return jsonify({
            'id': project.id,
            'name': project.name,
            'description': project.description,
            'status': project.status,
            'budget': project.budget,
            'tasks': [{'id': t.id, 'title': t.title, 'status': t.status, 'due_date': t.due_date.isoformat() if t.due_date else None} for t in tasks]
        })

    @projects_bp.route('/<int:project_id>/tasks', methods=['POST'])
    @jwt_required()
    def create_task_route(project_id):
        data = request.get_json()
        try:
            task = app.services['project_service'].create_task(
                project_id=project_id,
                title=data.get('title'),
                description=data.get('description'),
                due_date=data.get('due_date'),
                assigned_to_id=data.get('assigned_to_id'),
                tenant_id=g.current_user.tenant_id
            )
            return jsonify({'message': 'Tarea creada exitosamente', 'task_id': task.id}), 201
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

    @projects_bp.route('/tasks/<int:task_id>/status', methods=['PUT'])
    @jwt_required()
    def update_task_status_route(task_id):
        data = request.get_json()
        try:
            task = app.services['project_service'].update_task_status(task_id, data.get('status'), g.current_user.tenant_id)
            return jsonify({'message': 'Estado de la tarea actualizado', 'task_id': task.id, 'new_status': task.status})
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

    app.register_blueprint(projects_bp)
    
    # --- FIN DE RUTAS FUSIONADAS ---

    # --- REGISTRO DE COMANDOS CLI (Del HEAD) ---
    @app.cli.command("init-db")
    def init_db_command():
        """Inicializa la base de datos y crea los datos por defecto."""
        try:
            print("Inicializando la base de datos...")
            db.create_all()
            print("Tablas creadas (si no existían).")
            Role = app.models.get('Role')
            if Role and not Role.query.first():
                 print("Creando roles por defecto...")
                 default_roles = [
                      Role(name='Administrador General', description='Acceso completo al sistema', tenant_id=None),
                      Role(name='Ejecutivo de Crédito', description='Gestiona solicitudes de préstamo', tenant_id=None),
                      Role(name='Contador', description='Gestiona contabilidad', tenant_id=None),
                      Role(name='Cliente', description='Usuario final solicitante', tenant_id=None)
                 ]
                 db.session.add_all(default_roles)
                 db.session.commit()
                 print("Roles por defecto creados.")
            else:
                 print("Roles ya existen o modelo Role no disponible.")
            print("Base de datos inicializada.")
        except Exception as e:
            db.session.rollback()
            print(f"Error durante init-db: {e}")


    # --- ERROR HANDLERS (Del 2.0) ---
    @app.errorhandler(404)
    def not_found(error): return jsonify({"message": "Endpoint no encontrado"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.error(f"Internal Server Error: {error}", exc_info=True)
        return jsonify({"message": "Error interno del servidor"}), 500

    return app

# --- LÓGICA DE EJECUCIÓN ---
if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get("PORT", 5001))
    app.run(host='0.0.0.0', port=port, debug=True)
