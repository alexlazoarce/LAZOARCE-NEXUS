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
    def __repr__(self): return f'<LoanProduct {self.name}>'

class Payment(db.Model):
    """Modelo de Pago"""
    __tablename__ = 'payment'
    id = db.Column(Integer, primary_key=True)
    loan_application_id = db.Column(Integer, ForeignKey('loan_application.id'), nullable=False)
    amount = db.Column(Float, nullable=False)
    payment_date = db.Column(DateTime, default=func.current_timestamp())
    def __repr__(self): return f'<Payment {self.id} for App {self.loan_application_id}>'

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
    def __repr__(self): return f'<LoanApplication {self.id} - {self.status}>'

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
    def __repr__(self): return f'<Account {self.account_code} - {self.name}>'

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
    account = db.relationship('Account')
    def __repr__(self): return f'<Transaction {self.id} - {self.type} {self.amount}>'

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
    def __repr__(self): return f'<Employee {self.full_name}>'

class PaySlip(db.Model):
    """Planillas de pago"""
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

# --- MODELOS DE FIRMA ELECTRÓNICA Y CONTRATOS ---

class ContratoIntegracion(db.Model):
    """Contrato de Integración y Documentos"""
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
    __table_args__ = (UniqueConstraint('firma_id'),)

class Cliente(db.Model):
    """Perfil específico de Cliente (para Firma)"""
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
    contrato = db.relationship('ContratoIntegracion', backref='clientes', foreign_keys=[contrato_integracion_id])
    firma = db.relationship('FirmaElectronica', backref='clientes', foreign_keys=[firma_electronica_id])
    __table_args__ = (UniqueConstraint('dui'), UniqueConstraint('email'))

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
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='created_contract_templates')
    __table_args__ = (UniqueConstraint('name', 'tenant_id', name='_contract_template_tenant_uc'),)
    def __repr__(self): return f'<ContractTemplate {self.name}>'

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
    generated_by = db.relationship('User', foreign_keys=[generated_by_id], backref='generated_contracts_as_generator')
    def __repr__(self): return f'<GeneratedContract {self.id} for {self.related_entity}:{self.related_entity_id}>'

# --- MODELOS PARA CRM (LAN-CRM3) ---

class Contact(db.Model):
    """Contactos del CRM"""
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
    def __repr__(self): return f'<Contact {self.full_name}>'

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
    def __repr__(self): return f'<Interaction {self.interaction_type} with Contact {self.contact_id}>'

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
    def __repr__(self): return f'<Opportunity {self.name}>'

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
    def __repr__(self): return f'<Product {self.name}>'

class StockMovement(db.Model):
    """Movimientos de Stock"""
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
    def __repr__(self): return f'<StockMovement {self.movement_type} of {self.quantity} for Product {self.product_id}>'

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
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='created_quotes')
    def __repr__(self): return f'<Quote {self.id}>'

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
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='created_sales_orders')
    def __repr__(self): return f'<SalesOrder {self.id}>'

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
    __table_args__ = (CheckConstraint('(sales_order_id IS NOT NULL AND quote_id IS NULL) OR (sales_order_id IS NULL AND quote_id IS NOT NULL)', name='_sales_item_one_parent_check'),)
    def __repr__(self): return f'<SalesOrderItem {self.quantity} x Product {self.product_id}>'

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
    def __repr__(self): return f'<Supplier {self.name}>'

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
    def __repr__(self): return f'<PurchaseOrder {self.id}>'

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
    def __repr__(self): return f'<PurchaseOrderItem {self.quantity} x Product {self.product_id}>'

# --- MODELOS PARA CORREO (LAN-MAIL1) ---

class EmailLog(db.Model):
    """Registro de correos electrónicos enviados"""
    __tablename__ = 'email_log'
    id = db.Column(Integer, primary_key=True)
    recipient = db.Column(String(120), nullable=False, index=True)
    subject = db.Column(String(255), nullable=False)
    body = db.Column(Text)
    status = db.Column(String(50), default='Enviado', index=True)
    error_message = db.Column(Text)
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    sent_by_id = db.Column(Integer, ForeignKey('user.id'))
    sent_at = db.Column(DateTime, default=func.current_timestamp())
    sent_by = db.relationship('User', foreign_keys=[sent_by_id], backref='sent_emails')
    def __repr__(self): return f'<EmailLog {self.id} to {self.recipient}>'

# --- MODELOS PARA GESTOR DE DOCUMENTOS (LAN-GD2) ---

class Document(db.Model):
    """Documento lógico con múltiples versiones."""
    __tablename__ = 'document'
    id = db.Column(Integer, primary_key=True)
    filename = db.Column(String(255), nullable=False)
    description = db.Column(Text)
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    created_by_id = db.Column(Integer, ForeignKey('user.id'), nullable=False)
    latest_version_id = db.Column(Integer, nullable=True)
    created_at = db.Column(DateTime, default=func.current_timestamp())
    updated_at = db.Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())
    versions = db.relationship('DocumentVersion', backref='document', lazy='dynamic', cascade="all, delete-orphan")
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='created_documents')
    def __repr__(self): return f'<Document {self.id}: {self.filename}>'

class DocumentVersion(db.Model):
    """Versión específica de un archivo de un documento."""
    __tablename__ = 'document_version'
    id = db.Column(Integer, primary_key=True)
    document_id = db.Column(Integer, ForeignKey('document.id'), nullable=False, index=True)
    version_number = db.Column(Integer, nullable=False)
    filepath = db.Column(String(500), nullable=False)
    file_hash = db.Column(String(128))
    uploaded_by_id = db.Column(Integer, ForeignKey('user.id'), nullable=False)
    created_at = db.Column(DateTime, default=func.current_timestamp())
    uploaded_by = db.relationship('User', foreign_keys=[uploaded_by_id], backref='uploaded_document_versions')
    def __repr__(self): return f'<DocumentVersion {self.id} (v{self.version_number}) for Document {self.document_id}>'

# --- MODELOS PARA MENSAJERÍA CORPORATIVA (LAN-C8T) ---

class Channel(db.Model):
    """Canales de comunicación para la mensajería interna"""
    __tablename__ = 'messaging_channel'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(150), nullable=False)
    description = db.Column(Text)
    channel_type = db.Column(String(50), default='public', index=True)
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    created_by_id = db.Column(Integer, ForeignKey('user.id'), nullable=False)
    created_at = db.Column(DateTime, default=func.current_timestamp())
    messages = db.relationship('Message', backref='channel', lazy='dynamic', cascade="all, delete-orphan")
    members = db.relationship('User', secondary=channel_members, backref='messaging_channels', lazy='dynamic')
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='created_channels')
    __table_args__ = (UniqueConstraint('name', 'tenant_id', name='_channel_name_tenant_uc'),)
    def __repr__(self): return f'<Channel {self.name}>'

class Message(db.Model):
    """Mensajes individuales dentro de un canal"""
    __tablename__ = 'messaging_message'
    id = db.Column(Integer, primary_key=True)
    channel_id = db.Column(Integer, ForeignKey('messaging_channel.id'), nullable=False, index=True)
    user_id = db.Column(Integer, ForeignKey('user.id'), nullable=False, index=True)
    content = db.Column(Text, nullable=False)
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    created_at = db.Column(DateTime, default=func.current_timestamp(), index=True)
    author = db.relationship('User', foreign_keys=[user_id], backref='sent_messages')
    def __repr__(self): return f'<Message {self.id} in Channel {self.channel_id}>'

# --- MODELOS DE MÓDULOS EXTENDIDOS (MailingList, Firma, Formularios, Proyectos, Soporte) ---

class MailingList(db.Model):
    """Lista de correos para campañas de marketing"""
    __tablename__ = 'mailing_list'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(100), nullable=False)
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=True)
    members = db.relationship('User', secondary=mailing_list_members, backref='mailing_lists')
    def __repr__(self): return f'<MailingList {self.name}>'

class SignableTemplate(db.Model):
    """Plantillas de documentos para firma."""
    __tablename__ = 'sign_template'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(150), nullable=False, index=True)
    description = db.Column(Text)
    content = db.Column(Text, nullable=False)
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    created_by_id = db.Column(Integer, ForeignKey('user.id'))
    created_at = db.Column(DateTime, default=func.current_timestamp())
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='created_signable_templates')
    __table_args__ = (UniqueConstraint('name', 'tenant_id', name='_sign_template_tenant_uc'),)
    def __repr__(self): return f'<SignableTemplate {self.name}>'

class SignatureRequest(db.Model):
    """Solicitudes de firma para documentos."""
    __tablename__ = 'sign_request'
    id = db.Column(Integer, primary_key=True)
    template_id = db.Column(Integer, ForeignKey('sign_template.id'), nullable=True)
    signer_name = db.Column(String(150), nullable=False)
    signer_email = db.Column(String(120), nullable=False, index=True)
    status = db.Column(String(50), default='draft', nullable=False, index=True)
    unique_token = db.Column(String(128), unique=True, nullable=False, index=True)
    final_document_content = db.Column(Text)
    signature_data = db.Column(Text)
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    created_by_id = db.Column(Integer, ForeignKey('user.id'))
    created_at = db.Column(DateTime, default=func.current_timestamp())
    sent_at = db.Column(DateTime)
    signed_at = db.Column(DateTime)
    template = db.relationship('SignableTemplate')
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='created_signature_requests')
    def __repr__(self): return f'<SignatureRequest {self.id} for {self.signer_email}>'

class Form(db.Model):
    """Define la estructura de un formulario web."""
    __tablename__ = 'form'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(150), nullable=False)
    description = db.Column(Text)
    fields = db.Column(JSONB, nullable=False, default=list)
    public_token = db.Column(String(128), unique=True, nullable=False, index=True)
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    created_by_id = db.Column(Integer, ForeignKey('user.id'))
    created_at = db.Column(DateTime, default=func.current_timestamp())
    submissions = db.relationship('FormSubmission', backref='form', lazy='dynamic', cascade="all, delete-orphan")
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='created_forms')
    __table_args__ = (UniqueConstraint('name', 'tenant_id', name='_form_name_tenant_uc'),)
    def __repr__(self): return f'<Form {self.name}>'

class FormSubmission(db.Model):
    """Almacena un envío de datos de un formulario."""
    __tablename__ = 'form_submission'
    id = db.Column(Integer, primary_key=True)
    form_id = db.Column(Integer, ForeignKey('form.id'), nullable=False, index=True)
    data = db.Column(JSONB, nullable=False)
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    submitted_at = db.Column(DateTime, default=func.current_timestamp(), index=True)
    def __repr__(self): return f'<FormSubmission {self.id} for Form {self.form_id}>'

class Project(db.Model):
    """Proyectos de la empresa."""
    __tablename__ = 'project'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(200), nullable=False, index=True)
    description = db.Column(Text)
    budget = db.Column(Float, default=0.0)
    start_date = db.Column(Date)
    end_date = db.Column(Date)
    status = db.Column(String(50), default='Planificado', index=True)
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    manager_id = db.Column(Integer, ForeignKey('user.id'))
    created_at = db.Column(DateTime, default=func.current_timestamp())
    tasks = db.relationship('Task', backref='project', lazy='dynamic', cascade="all, delete-orphan")
    manager = db.relationship('User', foreign_keys=[manager_id], backref='managed_projects')
    __table_args__ = (UniqueConstraint('name', 'tenant_id', name='_project_name_tenant_uc'),)
    def __repr__(self): return f'<Project {self.name}>'

class Task(db.Model):
    """Tareas individuales dentro de un proyecto."""
    __tablename__ = 'project_task'
    id = db.Column(Integer, primary_key=True)
    project_id = db.Column(Integer, ForeignKey('project.id'), nullable=False, index=True)
    title = db.Column(String(200), nullable=False)
    description = db.Column(Text)
    status = db.Column(String(50), default='Pendiente', index=True)
    due_date = db.Column(Date)
    priority = db.Column(String(50), default='Medium')
    assigned_to_id = db.Column(Integer, ForeignKey('user.id'), nullable=True)
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    created_at = db.Column(DateTime, default=func.current_timestamp())
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id], backref='assigned_tasks')
    def __repr__(self): return f'<Task {self.title}>'

class Ticket(db.Model):
    """Tickets de soporte técnico."""
    __tablename__ = 'support_ticket'
    id = db.Column(Integer, primary_key=True)
    subject = db.Column(String(255), nullable=False)
    description = db.Column(Text, nullable=False)
    status = db.Column(String(50), default='Abierto', index=True)
    priority = db.Column(String(50), default='Media', index=True)
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    created_by_id = db.Column(Integer, ForeignKey('user.id'), nullable=False)
    assigned_to_id = db.Column(Integer, ForeignKey('user.id'), nullable=True)
    created_at = db.Column(DateTime, default=func.current_timestamp())
    updated_at = db.Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='created_tickets')
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id], backref='assigned_tickets')
    updates = db.relationship('TicketUpdate', backref='ticket', lazy='dynamic', cascade="all, delete-orphan")
    def __repr__(self): return f'<Ticket {self.id}: {self.subject}>'

class TicketUpdate(db.Model):
    """Actualizaciones o comentarios en un ticket."""
    __tablename__ = 'support_ticket_update'
    id = db.Column(Integer, primary_key=True)
    ticket_id = db.Column(Integer, ForeignKey('support_ticket.id'), nullable=False, index=True)
    user_id = db.Column(Integer, ForeignKey('user.id'), nullable=False)
    comment = db.Column(Text, nullable=False)
    created_at = db.Column(DateTime, default=func.current_timestamp())
    author = db.relationship('User', foreign_keys=[user_id], backref='ticket_updates')
    def __repr__(self): return f'<TicketUpdate {self.id} for Ticket {self.ticket_id}>'

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
    def __repr__(self): return f'<AuditLog {self.action} by {self.user_id}>'

class NotificationTemplate(db.Model):
    """Plantillas de notificación"""
    __tablename__ = 'notification_template'
    id = db.Column(Integer, primary_key=True)
    slug = db.Column(String(50), nullable=False, index=True)
    name = db.Column(String(100), nullable=False)
    subject = db.Column(String(255), nullable=False)
    body = db.Column(Text, nullable=False)
    type = db.Column(String(20), default='Email')
    variables = db.Column(JSONB, default=list)
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    is_active = db.Column(Boolean, default=True)
    __table_args__ = (UniqueConstraint('slug', 'tenant_id', name='_notification_template_tenant_uc'),)
    def __repr__(self): return f'<NotificationTemplate {self.slug}>'

