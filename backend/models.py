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
    role_id = db.Column(Integer, ForeignKey('role.id'), nullable=False) # Assuming single role direct link is still desired alongside M2M
    roles_m2m = db.relationship('Role', secondary=user_roles, back_populates='users')
    profile = db.relationship('ClientProfile', backref='user', uselist=False, cascade="all, delete-orphan")
    employee = db.relationship('Employee', backref='user', uselist=False, cascade="all, delete-orphan")
    applications = db.relationship('LoanApplication', backref='applicant', lazy='dynamic', cascade="all, delete-orphan")
    audit_logs = db.relationship('AuditLog', backref='user', lazy='dynamic', cascade="all, delete-orphan") # Link to AuditLog defined later
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    @property
    def role(self): # Property to easily access the direct role_id link
        return db.session.get(Role, self.role_id) if self.role_id else None
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
    type = db.Column(String(10), nullable=False) # 'debit' or 'credit'
    amount = db.Column(Float, nullable=False, default=0.0)

# --- MODELOS DE RECURSOS HUMANOS / PAYROLL ---
class Employee(db.Model):
    """Empleados y personal"""
    __tablename__ = 'employee'
    id = db.Column(Integer, primary_key=True)
    full_name = db.Column(String(120), nullable=False, index=True)
    position = db.Column(String(100), nullable=True)
    salary = db.Column(Float, default=0.0)
    employee_type = db.Column(String(20), default='interno') # E.g., interno, externo, contratista
    hire_date = db.Column(Date, nullable=True)
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
    period_start = db.Column(Date, nullable=False)
    period_end = db.Column(Date, nullable=False)
    payment_date = db.Column(Date) # Date the payment was actually made
    base_salary = db.Column(Float, nullable=False) # Salary for the period before deductions
    gross_salary = db.Column(Float, nullable=True) # Base + Bonuses/Overtime etc.
    # Deductions (example for El Salvador)
    isss_employee = db.Column(Float, nullable=False, default=0.0) # Employee contribution ISSS
    afp_employee = db.Column(Float, nullable=False, default=0.0) # Employee contribution AFP
    renta = db.Column(Float, nullable=False, default=0.0) # Income Tax withheld
    total_deductions = db.Column(Float, nullable=True) # Sum of all deductions
    net_salary = db.Column(Float, nullable=False) # Gross - Deductions
    fecha_calculo = db.Column(DateTime, default=func.current_timestamp()) # When this record was calculated
    is_paid = db.Column(Boolean, default=False)
    paid_at = db.Column(DateTime)

# --- MODELOS DE FIRMA ELECTRÓNICA Y CONTRATOS ---
# These seem specific to an integration, keeping structure
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
    tipo_firma = db.Column(String(20)) # E.g., 'simple', 'avanzada'
    documento_firmado_url = db.Column(String(255))
    clientes = relationship("Cliente", back_populates="contrato_integracion")
    __table_args__ = (UniqueConstraint('contrato_id'),)

class FirmaElectronica(db.Model):
    """Registro de Firma Electrónica"""
    __tablename__ = 'firma_electronica'
    id = db.Column(Integer, primary_key=True)
    firma_id = db.Column(String(50), unique=True, nullable=False)
    documento_id = db.Column(String(50), nullable=False) # Could link to ContratoIntegracion.contrato_id
    cliente_dui = db.Column(String(12), nullable=False)
    hash_documento = db.Column(String(64), nullable=False) # SHA256 hash of the doc *before* signing
    fecha_firma = db.Column(DateTime, nullable=False)
    # Optional fields for advanced signature / biometrics
    hash_biometrico = db.Column(String(64))
    score_confianza = db.Column(Float)
    metodo_validacion = db.Column(String(50)) # e.g., 'OTP', 'Biometric'
    clientes = relationship("Cliente", back_populates="firma_electronica")
    __table_args__ = (UniqueConstraint('firma_id'),)

class CertificadoValidacion(db.Model):
    """Certificado de Validación de Firma"""
    __tablename__ = 'certificado_validacion'
    id = db.Column(Integer, primary_key=True)
    certificado_id = db.Column(String(50), unique=True, nullable=False)
    firma_id = db.Column(String(50), ForeignKey('firma_electronica.firma_id'), nullable=False) # Link to the signature record
    documento_id = db.Column(String(50), nullable=False)
    cliente_dui = db.Column(String(12), nullable=False)
    pdf_certificado = db.Column(Text) # Or maybe path to a stored PDF?
    fecha_generacion = db.Column(DateTime, default=datetime.utcnow)
    valido_hasta = db.Column(DateTime) # Expiry if applicable
    firma = relationship("FirmaElectronica") # Relationship to FirmaElectronica


# --- MODELOS PARA FORMULACIÓN DE CONTRATOS (LAN-F2C) ---
class ContractTemplate(db.Model):
    """Plantillas de Contratos"""
    __tablename__ = 'contract_template'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(100), nullable=False, index=True)
    description = db.Column(Text)
    content = db.Column(Text, nullable=False)  # Content with placeholders like {{variable}}
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    created_by_id = db.Column(Integer, ForeignKey('user.id'))
    created_at = db.Column(DateTime, default=func.current_timestamp())
    updated_at = db.Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='created_contract_templates')
    __table_args__ = (UniqueConstraint('name', 'tenant_id', name='_contract_template_tenant_uc'),)
    def __repr__(self):
        return f'<ContractTemplate {self.name}>'

class GeneratedContract(db.Model):
    """Contratos Generados a partir de plantillas"""
    __tablename__ = 'generated_contract'
    id = db.Column(Integer, primary_key=True)
    template_id = db.Column(Integer, ForeignKey('contract_template.id'), nullable=False, index=True)
    related_entity = db.Column(String(50), index=True)  # E.g., 'LoanApplication', 'SalesOrder'
    related_entity_id = db.Column(Integer, index=True) # ID of the related entity
    content_final = db.Column(Text, nullable=False)  # Content with placeholders replaced
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    generated_by_id = db.Column(Integer, ForeignKey('user.id'))
    status = db.Column(String(50), default='Generado', nullable=False)  # Generado, EnviadoParaFirma, Firmado, Archivado
    created_at = db.Column(DateTime, default=func.current_timestamp())
    template = db.relationship('ContractTemplate', backref='generated_contracts')
    generated_by = db.relationship('User', foreign_keys=[generated_by_id], backref='generated_contracts')
    # Maybe add link to SignatureRequest if applicable
    # signature_request_id = db.Column(Integer, ForeignKey('sign_request.id'))
    # signature_request = relationship('SignatureRequest')
    def __repr__(self):
        return f'<GeneratedContract {self.id} for {self.related_entity}:{self.related_entity_id}>'

# --- MODELOS PARA CRM (LAN-CRM3) ---
class Contact(db.Model):
    """Contactos del CRM (Prospectos y Clientes)"""
    __tablename__ = 'crm_contact'
    id = db.Column(Integer, primary_key=True)
    full_name = db.Column(String(120), nullable=False, index=True)
    email = db.Column(String(120), index=True, nullable=True) # Make nullable? Unique?
    phone = db.Column(String(50))
    user_id = db.Column(Integer, ForeignKey('user.id'), nullable=True) # Link if contact is also a system user
    contact_type = db.Column(String(50), default='Prospecto', index=True) # Prospecto, Cliente, Lead, Partner etc.
    status = db.Column(String(50), default='Nuevo', index=True) # Nuevo, Contactado, Calificado, Perdido etc.
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    assigned_to_id = db.Column(Integer, ForeignKey('user.id'), nullable=True) # Sales rep assigned
    created_at = db.Column(DateTime, default=func.current_timestamp())
    updated_at = db.Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())
    interactions = db.relationship('Interaction', backref='contact', lazy='dynamic', cascade="all, delete-orphan")
    opportunities = db.relationship('Opportunity', backref='contact', lazy='dynamic', cascade="all, delete-orphan")
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id], backref='assigned_crm_contacts')
    # Optional: Link back to User profile if applicable
    # user = relationship('User', foreign_keys=[user_id])
    def __repr__(self):
        return f'<Contact {self.full_name}>'

class Interaction(db.Model):
    """Interacciones con los contactos (Llamadas, Emails, Reuniones)"""
    __tablename__ = 'crm_interaction'
    id = db.Column(Integer, primary_key=True)
    contact_id = db.Column(Integer, ForeignKey('crm_contact.id'), nullable=False, index=True)
    interaction_type = db.Column(String(50), nullable=False) # Llamada, Correo, Reunión, Nota
    notes = db.Column(Text)
    interaction_date = db.Column(DateTime, default=func.current_timestamp())
    user_id = db.Column(Integer, ForeignKey('user.id')) # User who logged the interaction
    user = db.relationship('User', foreign_keys=[user_id], backref='created_interactions')
    # Optional: Link to Opportunity if relevant
    # opportunity_id = db.Column(Integer, ForeignKey('crm_opportunity.id'))
    def __repr__(self):
        return f'<Interaction {self.interaction_type} with Contact {self.contact_id}>'

class Opportunity(db.Model):
    """Oportunidades de Venta"""
    __tablename__ = 'crm_opportunity'
    id = db.Column(Integer, primary_key=True)
    contact_id = db.Column(Integer, ForeignKey('crm_contact.id'), nullable=False, index=True)
    name = db.Column(String(200), nullable=False) # E.g., "Loan for John Doe", "Project X with ACME"
    stage = db.Column(String(50), default='Calificación', index=True) # Calificación, Propuesta, Negociación, Cerrada Ganada, Cerrada Perdida
    amount = db.Column(Float, nullable=True) # Estimated value
    probability = db.Column(Float, nullable=True) # % chance of closing
    # Optional link to a specific product being sold/offered
    loan_product_id = db.Column(Integer, ForeignKey('loan_product.id'), nullable=True)
    # inventory_product_id = db.Column(Integer, ForeignKey('inventory_product.id'), nullable=True)
    assigned_to_id = db.Column(Integer, ForeignKey('user.id')) # Sales rep responsible
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    close_date = db.Column(Date, nullable=True) # Expected close date
    created_at = db.Column(DateTime, default=func.current_timestamp())
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id], backref='assigned_opportunities')
    def __repr__(self):
        return f'<Opportunity {self.name}>'

# --- MODELOS PARA INVENTARIO (LAN-INV9) ---
class Product(db.Model):
    """Productos del Inventario"""
    __tablename__ = 'inventory_product'
    id = db.Column(Integer, primary_key=True)
    sku = db.Column(String(100), unique=True, nullable=False, index=True) # Stock Keeping Unit
    name = db.Column(String(200), nullable=False, index=True)
    description = db.Column(Text)
    price = db.Column(Float, nullable=False) # Standard selling price
    cost = db.Column(Float, nullable=True) # Purchase cost or production cost
    stock = db.Column(Integer, default=0) # Current quantity on hand
    min_stock_level = db.Column(Integer, default=0) # Reorder point
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    is_active = db.Column(Boolean, default=True) # Can be sold/purchased
    movements = db.relationship('StockMovement', backref='product', lazy='dynamic', cascade="all, delete-orphan")
    __table_args__ = (UniqueConstraint('sku', 'tenant_id', name='_product_sku_tenant_uc'),)
    def __repr__(self):
        return f'<Product {self.name}>'

class StockMovement(db.Model):
    """Movimientos de Stock (Entradas y Salidas)"""
    __tablename__ = 'inventory_stock_movement'
    id = db.Column(Integer, primary_key=True)
    product_id = db.Column(Integer, ForeignKey('inventory_product.id'), nullable=False, index=True)
    movement_type = db.Column(String(50), nullable=False, index=True) # Entrada (Compra/Producción), Salida (Venta/Consumo), Ajuste
    quantity = db.Column(Integer, nullable=False) # Positive for entry, negative for exit/adjustment down
    notes = db.Column(Text)
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    user_id = db.Column(Integer, ForeignKey('user.id')) # User who recorded the movement
    user = db.relationship('User', foreign_keys=[user_id], backref='stock_movements')
    created_at = db.Column(DateTime, default=func.current_timestamp())
    # Optional: Link to source document (SalesOrder, PurchaseOrder, AdjustmentForm)
    # related_entity = db.Column(String(50))
    # related_entity_id = db.Column(Integer)
    def __repr__(self):
        return f'<StockMovement {self.movement_type} of {self.quantity} for Product {self.product_id}>'

# --- MODELOS PARA VENTAS (LAN-SLS2) ---
class Quote(db.Model):
    """Cotizaciones de Venta"""
    __tablename__ = 'sales_quote'
    id = db.Column(Integer, primary_key=True)
    contact_id = db.Column(Integer, ForeignKey('crm_contact.id'), nullable=False, index=True)
    opportunity_id = db.Column(Integer, ForeignKey('crm_opportunity.id'), nullable=True, index=True)
    status = db.Column(String(50), default='Borrador', index=True) # Borrador, Enviada, Aceptada, Rechazada, Expirada
    total_amount = db.Column(Float) # Calculated sum of items
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    created_by_id = db.Column(Integer, ForeignKey('user.id'))
    valid_until = db.Column(Date)
    created_at = db.Column(DateTime, default=func.current_timestamp())
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='created_quotes')
    # Relationship to Quote Items (similar to SalesOrderItems)
    # items = db.relationship('QuoteItem', backref='quote', lazy='dynamic', cascade="all, delete-orphan")
    contact = relationship('Contact')
    opportunity = relationship('Opportunity')
    def __repr__(self):
        return f'<Quote {self.id}>'

class SalesOrder(db.Model):
    """Órdenes de Venta"""
    __tablename__ = 'sales_order'
    id = db.Column(Integer, primary_key=True)
    contact_id = db.Column(Integer, ForeignKey('crm_contact.id'), nullable=False, index=True)
    quote_id = db.Column(Integer, ForeignKey('sales_quote.id'), nullable=True, index=True) # Link to original quote if exists
    status = db.Column(String(50), default='Pendiente', index=True) # Pendiente, Confirmada, Enviada, Facturada, Completada, Cancelada
    total_amount = db.Column(Float) # Calculated sum of items
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    created_by_id = db.Column(Integer, ForeignKey('user.id'))
    order_date = db.Column(Date, default=date.today)
    items = db.relationship('SalesOrderItem', backref='sales_order', lazy='dynamic', cascade="all, delete-orphan")
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='created_sales_orders')
    contact = relationship('Contact')
    quote = relationship('Quote')
    def __repr__(self):
        return f'<SalesOrder {self.id}>'

class SalesOrderItem(db.Model):
    """Líneas de una Orden de Venta"""
    __tablename__ = 'sales_order_item'
    id = db.Column(Integer, primary_key=True)
    sales_order_id = db.Column(Integer, ForeignKey('sales_order.id'), nullable=True, index=True)
    quote_id = db.Column(Integer, ForeignKey('sales_quote.id'), nullable=True, index=True) # Allow linking directly to quote items too?
    product_id = db.Column(Integer, ForeignKey('inventory_product.id'), nullable=False, index=True)
    quantity = db.Column(Integer, nullable=False)
    price_per_unit = db.Column(Float, nullable=False) # Price at the time of order
    total_price = db.Column(Float, nullable=False) # quantity * price_per_unit
    product = db.relationship('Product')
    # Ensure item belongs to either a quote OR an order, not both/neither
    __table_args__ = (CheckConstraint('(sales_order_id IS NOT NULL AND quote_id IS NULL) OR (sales_order_id IS NULL AND quote_id IS NOT NULL)', name='_sales_item_one_parent_check'),)
    def __repr__(self):
        parent_id = self.sales_order_id or self.quote_id
        parent_type = "Order" if self.sales_order_id else "Quote"
        return f'<SalesOrderItem {self.quantity} x Prod {self.product_id} for {parent_type} {parent_id}>'

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
    purchase_orders = relationship('PurchaseOrder', backref='supplier', lazy='dynamic')
    def __repr__(self):
        return f'<Supplier {self.name}>'

class PurchaseOrder(db.Model):
    """Órdenes de Compra"""
    __tablename__ = 'purchasing_order'
    id = db.Column(Integer, primary_key=True)
    supplier_id = db.Column(Integer, ForeignKey('purchasing_supplier.id'), nullable=False, index=True)
    order_date = db.Column(Date, default=date.today)
    expected_delivery_date = db.Column(Date)
    status = db.Column(String(50), default='Borrador', index=True) # Borrador, Enviada, Parcialmente Recibida, Recibida, Cancelada
    total_amount = db.Column(Float) # Calculated sum of items
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    created_by_id = db.Column(Integer, ForeignKey('user.id'))
    items = db.relationship('PurchaseOrderItem', backref='purchase_order', lazy='dynamic', cascade="all, delete-orphan")
    # supplier defined via backref from Supplier model
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
    price_per_unit = db.Column(Float, nullable=False) # Cost at time of order
    total_price = db.Column(Float, nullable=False) # quantity * price_per_unit
    product = db.relationship('Product')
    # purchase_order defined via backref
    def __repr__(self):
        return f'<PurchaseOrderItem {self.quantity} x Prod {self.product_id} for PO {self.purchase_order_id}>'

# --- MODELOS PARA CORREO (LAN-MAIL1) ---
class EmailLog(db.Model):
    """Registro de correos electrónicos enviados"""
    __tablename__ = 'email_log'
    id = db.Column(Integer, primary_key=True)
    recipient = db.Column(String(120), nullable=False, index=True)
    subject = db.Column(String(255), nullable=False)
    body = db.Column(Text)
    status = db.Column(String(50), default='Enviado', index=True) # Enviado, Fallido, En Cola
    error_message = db.Column(Text, nullable=True)
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    sent_by_id = db.Column(Integer, ForeignKey('user.id'), nullable=True) # Nullable if sent by system
    sent_at = db.Column(DateTime, default=func.current_timestamp())
    sent_by = relationship('User', foreign_keys=[sent_by_id]) # Relationship added
    def __repr__(self):
        return f'<EmailLog {self.id} to {self.recipient}>'

# --- MODELOS DE MÓDULOS EXTENDIDOS ---
class MailingList(db.Model):
    """Listas de correo"""
    __tablename__ = 'mailing_list'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(150), nullable=False)
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    members = db.relationship('User', secondary=mailing_list_members, backref='mailing_lists', lazy='dynamic')
    __table_args__ = (UniqueConstraint('name', 'tenant_id', name='_mailing_list_name_tenant_uc'),)
    def __repr__(self):
        return f'<MailingList {self.name}>'

# --- MODELOS PARA GESTOR DE DOCUMENTOS (LAN-GD2) ---
class Document(db.Model):
    """Representa un documento lógico que puede tener múltiples versiones."""
    __tablename__ = 'document'
    id = db.Column(Integer, primary_key=True)
    filename = db.Column(String(255), nullable=False) # Original filename at creation
    description = db.Column(Text)
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    created_by_id = db.Column(Integer, ForeignKey('user.id'), nullable=False)
    latest_version_id = db.Column(Integer, nullable=True) # FK to DocumentVersion, set manually or via trigger
    created_at = db.Column(DateTime, default=func.current_timestamp())
    updated_at = db.Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())
    versions = db.relationship('DocumentVersion', backref='document', lazy='dynamic', cascade="all, delete-orphan", order_by='DocumentVersion.version_number')
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='created_documents')
    # Consider adding latest_version relationship for easier access
    # latest_version = relationship('DocumentVersion', foreign_keys=[latest_version_id], post_update=True)
    def __repr__(self):
        return f'<Document {self.id}: {self.filename}>'

class DocumentVersion(db.Model):
    """Representa una versión específica de un archivo de un documento."""
    __tablename__ = 'document_version'
    id = db.Column(Integer, primary_key=True)
    document_id = db.Column(Integer, ForeignKey('document.id'), nullable=False, index=True)
    version_number = db.Column(Integer, nullable=False)
    filepath = db.Column(String(500), nullable=False) # Path in storage (local or cloud URL)
    file_hash = db.Column(String(128)) # SHA-512 or similar hash for integrity check
    uploaded_by_id = db.Column(Integer, ForeignKey('user.id'), nullable=False)
    created_at = db.Column(DateTime, default=func.current_timestamp())
    uploaded_by = db.relationship('User', foreign_keys=[uploaded_by_id], backref='uploaded_document_versions')
    # document defined by backref from Document
    __table_args__ = (UniqueConstraint('document_id', 'version_number', name='_doc_version_uc'),)
    def __repr__(self):
        return f'<DocumentVersion {self.id} (v{self.version_number}) for Document {self.document_id}>'

# --- MODELOS PARA MENSAJERÍA CORPORATIVA (LAN-C8T) ---
class Channel(db.Model):
    """Canales de comunicación para la mensajería interna"""
    __tablename__ = 'messaging_channel'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(150), nullable=False)
    description = db.Column(Text)
    channel_type = db.Column(String(50), default='public', index=True) # public, private, direct
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    created_by_id = db.Column(Integer, ForeignKey('user.id'), nullable=False)
    created_at = db.Column(DateTime, default=func.current_timestamp())
    messages = db.relationship('Message', backref='channel', lazy='dynamic', cascade="all, delete-orphan", order_by='Message.created_at')
    members = db.relationship('User', secondary=channel_members, backref='messaging_channels', lazy='dynamic')
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='created_channels')
    __table_args__ = (UniqueConstraint('name', 'tenant_id', name='_channel_name_tenant_uc'),)
    def __repr__(self):
        return f'<Channel {self.name}>'

class Message(db.Model):
    """Mensajes individuales dentro de un canal"""
    __tablename__ = 'messaging_message'
    id = db.Column(Integer, primary_key=True)
    channel_id = db.Column(Integer, ForeignKey('messaging_channel.id'), nullable=False, index=True)
    user_id = db.Column(Integer, ForeignKey('user.id'), nullable=False, index=True) # Author
    content = db.Column(Text, nullable=False)
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    created_at = db.Column(DateTime, default=func.current_timestamp(), index=True)
    author = db.relationship('User', foreign_keys=[user_id], backref='messages')
    # channel defined by backref
    def __repr__(self):
        return f'<Message {self.id} in Channel {self.channel_id}>'

# --- MODELOS PARA FIRMAR (LAN-SGN3) ---
class SignableTemplate(db.Model):
    """Plantillas de documentos comerciales para firma (propuestas, etc.)."""
    __tablename__ = 'sign_template'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(150), nullable=False, index=True)
    description = db.Column(Text)
    content = db.Column(Text, nullable=False) # HTML/Markdown content with placeholders {{variable}}
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
    template_id = db.Column(Integer, ForeignKey('sign_template.id'), nullable=True) # Optional: if generated from template
    signer_name = db.Column(String(150), nullable=False)
    signer_email = db.Column(String(120), nullable=False, index=True)
    status = db.Column(String(50), default='draft', nullable=False, index=True) # draft, sent, viewed, signed, declined, expired
    unique_token = db.Column(String(128), unique=True, nullable=False, index=True) # For the public signing URL
    final_document_content = db.Column(Text) # The document content after filling placeholders
    signature_data = db.Column(Text) # Can be Base64 data URL of the signature image/vector
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    created_by_id = db.Column(Integer, ForeignKey('user.id'))
    created_at = db.Column(DateTime, default=func.current_timestamp())
    sent_at = db.Column(DateTime, nullable=True)
    signed_at = db.Column(DateTime, nullable=True)
    template = db.relationship('SignableTemplate', backref='signature_requests')
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='created_signature_requests')
    def __repr__(self):
        return f'<SignatureRequest {self.id} for {self.signer_email}>'

# --- MODELOS PARA FORMULARIOS (LAN-FRM5) ---
class Form(db.Model):
    """Define la estructura de un formulario web."""
    __tablename__ = 'form'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(150), nullable=False)
    description = db.Column(Text)
    # JSONB storing field definitions: [{"name": "email", "label": "Email", "type": "email", "required": true}, ...]
    fields = db.Column(JSONB, nullable=False, default=list)
    public_token = db.Column(String(128), unique=True, nullable=False, index=True) # Unique token for public access URL
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    created_by_id = db.Column(Integer, ForeignKey('user.id'))
    created_at = db.Column(DateTime, default=func.current_timestamp())
    submissions = db.relationship('FormSubmission', backref='form', lazy='dynamic', cascade="all, delete-orphan")
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='created_forms')
    __table_args__ = (UniqueConstraint('name', 'tenant_id', name='_form_name_tenant_uc'),)
    def __repr__(self):
        return f'<Form {self.name}>'

class FormSubmission(db.Model):
    """Almacena un envío de datos de un formulario."""
    __tablename__ = 'form_submission'
    id = db.Column(Integer, primary_key=True)
    form_id = db.Column(Integer, ForeignKey('form.id'), nullable=False, index=True)
    # JSONB storing submitted data: {"email": "test@example.com", "name": "John"}
    data = db.Column(JSONB, nullable=False)
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    submitted_at = db.Column(DateTime, default=func.current_timestamp(), index=True)
    # form defined by backref
    def __repr__(self):
        return f'<FormSubmission {self.id} for Form {self.form_id}>'

# --- MODELOS PARA GESTIÓN DE PROYECTOS (LAN-PR0) ---
class Project(db.Model):
    """Define un proyecto con presupuesto y cronograma."""
    __tablename__ = 'project'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(200), nullable=False, index=True)
    description = db.Column(Text)
    budget = db.Column(Float, default=0.0)
    start_date = db.Column(Date)
    end_date = db.Column(Date) # Target end date
    status = db.Column(String(50), default='Planificado', index=True) # Planificado, En Progreso, Completado, En Espera, Cancelado
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    manager_id = db.Column(Integer, ForeignKey('user.id'), nullable=True) # Project Manager
    created_at = db.Column(DateTime, default=func.current_timestamp())
    tasks = db.relationship('Task', backref='project', lazy='dynamic', cascade="all, delete-orphan")
    manager = db.relationship('User', foreign_keys=[manager_id], backref='managed_projects')
    __table_args__ = (UniqueConstraint('name', 'tenant_id', name='_project_name_tenant_uc'),)
    def __repr__(self):
        return f'<Project {self.name}>'

class Task(db.Model):
    """Tareas individuales dentro de un proyecto."""
    __tablename__ = 'project_task' # Changed table name for clarity
    id = db.Column(Integer, primary_key=True)
    project_id = db.Column(Integer, ForeignKey('project.id'), nullable=False, index=True)
    title = db.Column(String(200), nullable=False)
    description = db.Column(Text)
    status = db.Column(String(50), default='Pendiente', index=True) # Pendiente, En Progreso, Completada, Bloqueada
    due_date = db.Column(Date)
    assigned_to_id = db.Column(Integer, ForeignKey('user.id'), nullable=True)
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    created_at = db.Column(DateTime, default=func.current_timestamp())
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id], backref='assigned_tasks')
    # project defined by backref
    def __repr__(self):
        return f'<Task {self.title}>'

# --- MODELOS PARA SOPORTE TÉCNICO (LAN-SOP1) ---
class Ticket(db.Model):
    """Tickets de soporte técnico."""
    __tablename__ = 'support_ticket' # Changed table name for clarity
    id = db.Column(Integer, primary_key=True)
    subject = db.Column(String(255), nullable=False)
    description = db.Column(Text, nullable=False)
    status = db.Column(String(50), default='Abierto', index=True) # Abierto, En Progreso, Esperando Respuesta, Cerrado
    priority = db.Column(String(50), default='Media', index=True) # Baja, Media, Alta, Urgente
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    created_by_id = db.Column(Integer, ForeignKey('user.id'), nullable=False) # User who created the ticket
    assigned_to_id = db.Column(Integer, ForeignKey('user.id'), nullable=True) # Support agent assigned
    created_at = db.Column(DateTime, default=func.current_timestamp())
    updated_at = db.Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='created_tickets')
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id], backref='assigned_tickets')
    updates = db.relationship('TicketUpdate', backref='ticket', lazy='dynamic', cascade="all, delete-orphan", order_by='TicketUpdate.created_at')
    def __repr__(self):
        return f'<Ticket {self.id}: {self.subject}>'

class TicketUpdate(db.Model):
    """Actualizaciones o comentarios en un ticket."""
    __tablename__ = 'support_ticket_update' # Changed table name
    id = db.Column(Integer, primary_key=True)
    ticket_id = db.Column(Integer, ForeignKey('support_ticket.id'), nullable=False, index=True)
    user_id = db.Column(Integer, ForeignKey('user.id'), nullable=False) # Author of the update
    comment = db.Column(Text, nullable=False)
    created_at = db.Column(DateTime, default=func.current_timestamp())
    author = db.relationship('User', foreign_keys=[user_id], backref='ticket_updates')
    # ticket defined by backref
    def __repr__(self):
        return f'<TicketUpdate {self.id} for Ticket {self.ticket_id}>'

# --- MODELOS PARA ACTIVOS FIJOS (LAN-AFX4) ---
class FixedAsset(db.Model):
    """Activos fijos de la empresa."""
    __tablename__ = 'fixed_asset'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(200), nullable=False)
    description = db.Column(Text)
    purchase_date = db.Column(Date, nullable=False)
    purchase_cost = db.Column(Float, nullable=False)
    useful_life = db.Column(Integer, nullable=False) # In months
    salvage_value = db.Column(Float, default=0.0) # Residual value
    depreciation_method = db.Column(String(50), default='linea_recta', nullable=False) # e.g., linea_recta, doble_saldo_decreciente
    status = db.Column(String(50), default='Activo', index=True) # Activo, Vendido, Dado de Baja
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    created_at = db.Column(DateTime, default=func.current_timestamp())
    depreciation_entries = db.relationship('DepreciationEntry', backref='asset', lazy='dynamic', cascade="all, delete-orphan", order_by='DepreciationEntry.entry_date')
    def __repr__(self):
        return f'<FixedAsset {self.name}>'

class DepreciationEntry(db.Model):
    """Entradas de depreciación mensual para un activo."""
    __tablename__ = 'asset_depreciation_entry' # Changed table name
    id = db.Column(Integer, primary_key=True)
    asset_id = db.Column(Integer, ForeignKey('fixed_asset.id'), nullable=False, index=True)
    entry_date = db.Column(Date, nullable=False, index=True) # Date the depreciation applies to (e.g., end of month)
    amount = db.Column(Float, nullable=False) # Calculated depreciation amount
    journal_entry_id = db.Column(Integer, ForeignKey('journal_entry.id'), nullable=True) # Link to accounting entry
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    # asset defined by backref
    def __repr__(self):
        return f'<DepreciationEntry {self.id} for Asset {self.asset_id} on {self.entry_date}>'

# --- MODELOS PARA CAJA Y BANCOS (LAN-CB2) ---
class BankAccount(db.Model):
    """Cuentas bancarias de la empresa."""
    __tablename__ = 'bank_account'
    id = db.Column(Integer, primary_key=True)
    account_name = db.Column(String(150), nullable=False)
    account_number = db.Column(String(100), nullable=False)
    bank_name = db.Column(String(100))
    initial_balance = db.Column(Float, default=0.0)
    gl_account_id = db.Column(Integer, ForeignKey('account.id'), nullable=True) # Link to GL account
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    is_active = db.Column(Boolean, default=True)
    transactions = relationship('BankTransaction', backref='bank_account', lazy='dynamic', order_by='BankTransaction.transaction_date')
    __table_args__ = (UniqueConstraint('account_number', 'tenant_id', name='_bank_account_tenant_uc'),)
    def __repr__(self):
        return f'<BankAccount {self.account_name}>'

class BankTransaction(db.Model):
    """Transacciones en una cuenta bancaria."""
    __tablename__ = 'bank_transaction'
    id = db.Column(Integer, primary_key=True)
    bank_account_id = db.Column(Integer, ForeignKey('bank_account.id'), nullable=False, index=True)
    transaction_date = db.Column(Date, nullable=False)
    description = db.Column(String(255), nullable=False)
    amount = db.Column(Float, nullable=False) # Positive for deposit/inflow, negative for withdrawal/outflow
    transaction_type = db.Column(String(50), nullable=True) # Depósito, Retiro, Transferencia, Cheque, Comisión
    reference = db.Column(String(100)) # Check number, transfer ID etc.
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    # bank_account defined by backref
    # Optional: Link to JournalEntry if reconciled
    # journal_entry_id = db.Column(Integer, ForeignKey('journal_entry.id'))
    def __repr__(self):
        return f'<BankTransaction {self.id} of {self.amount}>'

class CashBox(db.Model):
    """Cajas chicas de la empresa."""
    __tablename__ = 'cash_box'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(100), nullable=False)
    initial_balance = db.Column(Float, default=0.0)
    responsible_id = db.Column(Integer, ForeignKey('user.id')) # User responsible for the cash box
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    responsible = db.relationship('User', foreign_keys=[responsible_id], backref='cash_boxes')
    transactions = relationship('CashTransaction', backref='cash_box', lazy='dynamic', order_by='CashTransaction.transaction_date')
    __table_args__ = (UniqueConstraint('name', 'tenant_id', name='_cash_box_name_tenant_uc'),)
    def __repr__(self):
        return f'<CashBox {self.name}>'

class CashTransaction(db.Model):
    """Transacciones en una caja chica."""
    __tablename__ = 'cash_transaction'
    id = db.Column(Integer, primary_key=True)
    cash_box_id = db.Column(Integer, ForeignKey('cash_box.id'), nullable=False, index=True)
    transaction_date = db.Column(Date, nullable=False)
    description = db.Column(String(255), nullable=False)
    amount = db.Column(Float, nullable=False) # Positive for inflow, negative for outflow
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    # cash_box defined by backref
    # Optional: Link to JournalEntry if reconciled
    # journal_entry_id = db.Column(Integer, ForeignKey('journal_entry.id'))
    def __repr__(self):
        return f'<CashTransaction {self.id} of {self.amount}>'

# --- MODELOS PARA IMPUESTOS (LAN-TAX1) ---
class TaxType(db.Model):
    """Tipos de Impuestos (IVA, Retenciones, etc.)"""
    __tablename__ = 'tax_type'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(100), nullable=False, index=True)
    rate = db.Column(Float, nullable=False)  # Rate as percentage, e.g., 13.0 for 13%
    country_code = db.Column(String(3), index=True) # SV, GT, HN, etc.
    tax_category = db.Column(String(50), index=True) # IVA, RetencionFuente, ImpuestoEspecifico etc.
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    is_active = db.Column(Boolean, default=True)
    __table_args__ = (UniqueConstraint('name', 'tenant_id', 'country_code', name='_tax_type_tenant_country_uc'),)
    def to_dict(self): # Keep existing to_dict methods
        return {
            'id': self.id, 'name': self.name, 'rate': self.rate,
            'country_code': self.country_code, 'tax_category': self.tax_category,
            'is_active': self.is_active
        }
    def __repr__(self):
        return f'<TaxType {self.name} ({self.rate}%)>'

class TaxDeclaration(db.Model):
    """Declaraciones de Impuestos Generadas"""
    __tablename__ = 'tax_declaration'
    id = db.Column(Integer, primary_key=True)
    declaration_type = db.Column(String(50), nullable=False) # IVAMensual, RentaAnual, PagoACuenta
    period_start = db.Column(Date, nullable=False)
    period_end = db.Column(Date, nullable=False)
    # JSONB storing calculated data: {"total_debitos": 1300, "total_creditos": 800, "impuesto_a_pagar": 500}
    calculated_data = db.Column(JSONB)
    status = db.Column(String(50), default='Borrador') # Borrador, Generada, Presentada, Pagada
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    generated_by_id = db.Column(Integer, ForeignKey('user.id'))
    generated_at = db.Column(DateTime, default=func.current_timestamp())
    generated_by = db.relationship('User', foreign_keys=[generated_by_id], backref='generated_tax_declarations')
    def to_dict(self): # Keep existing to_dict methods
        return {
            'id': self.id, 'declaration_type': self.declaration_type,
            'period_start': self.period_start.isoformat(), 'period_end': self.period_end.isoformat(),
            'calculated_data': self.calculated_data, 'status': self.status,
            'generated_at': self.generated_at.isoformat()
        }
    def __repr__(self):
        return f'<TaxDeclaration {self.id} - {self.declaration_type}>'

# --- MODELOS PARA RECURSOS MATERIALES (LAN-RM1) ---
class Material(db.Model):
    """Materiales de oficina (stock no valorado)."""
    __tablename__ = 'material'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(150), nullable=False, index=True)
    description = db.Column(Text)
    stock = db.Column(Integer, default=0) # Current quantity
    unit = db.Column(String(50)) # E.g., 'unidades', 'cajas', 'resmas'
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    is_active = db.Column(Boolean, default=True)
    requests = relationship('MaterialRequest', backref='material', lazy='dynamic') # Added backref relationship
    __table_args__ = (UniqueConstraint('name', 'tenant_id', name='_material_name_tenant_uc'),)
    def to_dict(self): # Keep existing to_dict methods
        return {
            'id': self.id, 'name': self.name, 'description': self.description,
            'stock': self.stock, 'unit': self.unit, 'is_active': self.is_active
        }
    def __repr__(self):
        return f'<Material {self.name}>'

class MaterialRequest(db.Model):
    """Solicitudes de materiales por parte de empleados."""
    __tablename__ = 'material_request'
    id = db.Column(Integer, primary_key=True)
    material_id = db.Column(Integer, ForeignKey('material.id'), nullable=False, index=True)
    requester_id = db.Column(Integer, ForeignKey('user.id'), nullable=False, index=True)
    quantity = db.Column(Integer, nullable=False)
    status = db.Column(String(50), default='Pendiente', index=True) # Pendiente, Aprobada, Rechazada, Entregada
    notes = db.Column(Text) # Notes from requester
    approver_id = db.Column(Integer, ForeignKey('user.id'), nullable=True) # User who approved/rejected
    approval_notes = db.Column(Text) # Notes from approver
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    created_at = db.Column(DateTime, default=func.current_timestamp())
    updated_at = db.Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp()) # Track status changes
    # material defined by backref
    requester = db.relationship('User', foreign_keys=[requester_id], backref='material_requests')
    approver = db.relationship('User', foreign_keys=[approver_id], backref='approved_material_requests')
    def to_dict(self): # Keep existing to_dict methods
        return {
            'id': self.id, 'material_id': self.material_id,
            'material_name': self.material.name if self.material else None, # Handle if material deleted
            'requester_id': self.requester_id,
            'requester_name': self.requester.full_name if self.requester else None, # Handle if user deleted
            'quantity': self.quantity, 'status': self.status, 'notes': self.notes,
            'created_at': self.created_at.isoformat()
        }
    def __repr__(self):
        return f'<MaterialRequest {self.id} for {self.quantity} of Material {self.material_id}>'

# --- MODELOS PARA OBRAS Y CONSTRUCCIÓN (LAN-OBR5) ---
class ConstructionProject(db.Model):
    """Proyectos de construcción."""
    __tablename__ = 'construction_project'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(200), nullable=False, index=True)
    location = db.Column(String(255))
    start_date = db.Column(Date)
    end_date = db.Column(Date) # Target end date
    budget = db.Column(Float, default=0.0)
    status = db.Column(String(50), default='Planificado', index=True) # Planificado, En Progreso, Completado, Cancelado
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    manager_id = db.Column(Integer, ForeignKey('user.id'), nullable=True)
    budget_items = db.relationship('BudgetItem', backref='project', lazy='dynamic', cascade="all, delete-orphan")
    progress_reports = db.relationship('ProgressReport', backref='project', lazy='dynamic', cascade="all, delete-orphan")
    certifications = relationship('Certification', backref='project', lazy='dynamic', cascade="all, delete-orphan") # Added relationship
    rfis = relationship('RFI', backref='project', lazy='dynamic', cascade="all, delete-orphan") # Added relationship
    milestones = relationship('Milestone', backref='project', lazy='dynamic', cascade="all, delete-orphan") # Added relationship
    manager = db.relationship('User', foreign_keys=[manager_id], backref='managed_construction_projects')
    def to_dict(self): # Keep existing to_dict methods
        return {
            'id': self.id, 'name': self.name, 'location': self.location,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'budget': self.budget, 'status': self.status
        }
    def __repr__(self):
        return f'<ConstructionProject {self.name}>'

class BudgetItem(db.Model):
    """Partidas del presupuesto de una obra."""
    __tablename__ = 'construction_budget_item' # Renamed table for consistency
    id = db.Column(Integer, primary_key=True)
    project_id = db.Column(Integer, ForeignKey('construction_project.id'), nullable=False, index=True)
    name = db.Column(String(200), nullable=False)
    description = db.Column(Text)
    code = db.Column(String(50)) # Item code
    amount = db.Column(Float, nullable=False)
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    # project defined by backref
    def to_dict(self): # Keep existing to_dict methods
        return {
            'id': self.id, 'project_id': self.project_id, 'name': self.name,
            'code': self.code, 'amount': self.amount
        }
    def __repr__(self):
        return f'<BudgetItem {self.name}>'

class ProgressReport(db.Model):
    """Reportes de avance físico de la obra."""
    __tablename__ = 'construction_progress_report' # Renamed table for consistency
    id = db.Column(Integer, primary_key=True)
    project_id = db.Column(Integer, ForeignKey('construction_project.id'), nullable=False, index=True)
    report_date = db.Column(Date, nullable=False)
    percentage_complete = db.Column(Float, nullable=False) # Physical progress %
    notes = db.Column(Text)
    reported_by_id = db.Column(Integer, ForeignKey('user.id'))
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    reported_by = db.relationship('User', foreign_keys=[reported_by_id], backref='progress_reports')
    # project defined by backref
    def to_dict(self): # Keep existing to_dict methods
        return {
            'id': self.id, 'report_date': self.report_date.isoformat(),
            'percentage_complete': self.percentage_complete, 'notes': self.notes
        }
    def __repr__(self):
        return f'<ProgressReport {self.id} for Project {self.project_id}>'

class Certification(db.Model):
    """Certificaciones de pago a contratistas."""
    __tablename__ = 'construction_certification' # Renamed table for consistency
    id = db.Column(Integer, primary_key=True)
    project_id = db.Column(Integer, ForeignKey('construction_project.id'), nullable=False, index=True)
    certification_date = db.Column(Date, nullable=False)
    amount = db.Column(Float, nullable=False)
    description = db.Column(Text)
    status = db.Column(String(50), default='Pendiente', index=True) # Pendiente, Aprobada, Rechazada, Pagada
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    approved_by_id = db.Column(Integer, ForeignKey('user.id'), nullable=True)
    approved_by = db.relationship('User', foreign_keys=[approved_by_id], backref='approved_certifications')
    # project defined by backref
    def to_dict(self): # Keep existing to_dict methods
        return {
            'id': self.id, 'certification_date': self.certification_date.isoformat(),
            'amount': self.amount, 'description': self.description, 'status': self.status
        }
    def __repr__(self):
        return f'<Certification {self.id} for Project {self.project_id}>'

class RFI(db.Model):
    """Request for Information (RFI) para un proyecto de construcción."""
    __tablename__ = 'construction_rfi'
    id = db.Column(Integer, primary_key=True)
    project_id = db.Column(Integer, ForeignKey('construction_project.id'), nullable=False, index=True)
    subject = db.Column(String(255), nullable=False)
    question = db.Column(Text, nullable=False)
    answer = db.Column(Text)
    status = db.Column(String(50), default='Abierto', index=True) # Abierto, Respondido, Cerrado
    created_by_id = db.Column(Integer, ForeignKey('user.id'))
    answered_by_id = db.Column(Integer, ForeignKey('user.id'), nullable=True)
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    # project defined by backref
    created_by = relationship('User', foreign_keys=[created_by_id])
    answered_by = relationship('User', foreign_keys=[answered_by_id])

class Milestone(db.Model):
    """Hitos de facturación para un proyecto de construcción."""
    __tablename__ = 'construction_milestone'
    id = db.Column(Integer, primary_key=True)
    project_id = db.Column(Integer, ForeignKey('construction_project.id'), nullable=False, index=True)
    name = db.Column(String(200), nullable=False)
    due_date = db.Column(Date)
    amount = db.Column(Float, nullable=False)
    status = db.Column(String(50), default='Pendiente', index=True) # Pendiente, Facturado, Pagado
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    # project defined by backref

# --- MODELOS PARA SALUD (LAN-H7S) ---
class PatientRecord(db.Model):
    """Ficha de paciente o historial clínico."""
    __tablename__ = 'health_patient_record'
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(Integer, ForeignKey('user.id'), nullable=True, index=True) # Link if patient is a system user
    contact_id = db.Column(Integer, ForeignKey('crm_contact.id'), nullable=True, index=True) # Link if patient is in CRM
    full_name = db.Column(String(200), nullable=False) # Copied in case not linked, or for specific medical name
    birth_date = db.Column(Date)
    gender = db.Column(String(20)) # Optional
    medical_history_summary = db.Column(Text) # Allergies, chronic conditions etc.
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    created_at = db.Column(DateTime, default=func.current_timestamp())
    appointments = db.relationship('MedicalAppointment', backref='patient', lazy='dynamic', cascade="all, delete-orphan")
    user = relationship('User') # Relationship for user_id link
    contact = relationship('Contact') # Relationship for contact_id link
    def to_dict(self): # Keep existing to_dict methods
        return {
            'id': self.id, 'user_id': self.user_id, 'contact_id': self.contact_id,
            'full_name': self.full_name,
            'birth_date': self.birth_date.isoformat() if self.birth_date else None,
            'medical_history_summary': self.medical_history_summary
        }

class MedicalAppointment(db.Model):
    """Citas médicas."""
    __tablename__ = 'health_appointment'
    id = db.Column(Integer, primary_key=True)
    patient_id = db.Column(Integer, ForeignKey('health_patient_record.id'), nullable=False, index=True)
    doctor_id = db.Column(Integer, ForeignKey('user.id'), nullable=False, index=True) # Doctor must be a system User
    appointment_time = db.Column(DateTime, nullable=False, index=True) # Date and Time
    duration_minutes = db.Column(Integer, default=30) # Optional duration
    status = db.Column(String(50), default='Programada', index=True) # Programada, Confirmada, Realizada, Cancelada, NoPresentado
    reason = db.Column(Text) # Reason for visit
    notes = db.Column(Text) # Doctor's notes from the appointment
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    doctor = db.relationship('User', foreign_keys=[doctor_id], backref='medical_appointments')
    # patient defined by backref
    prescriptions = relationship('Prescription', backref='appointment', lazy='dynamic') # Added relationship
    lab_orders = relationship('LabOrder', backref='appointment', lazy='dynamic') # Added relationship
    def to_dict(self): # Keep existing to_dict methods
        return {
            'id': self.id, 'patient_id': self.patient_id,
            'patient_name': self.patient.full_name if self.patient else None,
            'doctor_name': self.doctor.full_name if self.doctor else None,
            'appointment_time': self.appointment_time.isoformat(), 'status': self.status,
            'reason': self.reason
        }

class Prescription(db.Model):
    """Recetas médicas generadas en una cita."""
    __tablename__ = 'health_prescription'
    id = db.Column(Integer, primary_key=True)
    appointment_id = db.Column(Integer, ForeignKey('health_appointment.id'), nullable=False, index=True)
    medication_details = db.Column(Text, nullable=False) # Name, dosage, frequency, duration etc.
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    issued_at = db.Column(DateTime, default=func.current_timestamp())
    # appointment defined by backref

class LabOrder(db.Model):
    """Órdenes de laboratorio."""
    __tablename__ = 'health_lab_order'
    id = db.Column(Integer, primary_key=True)
    appointment_id = db.Column(Integer, ForeignKey('health_appointment.id'), nullable=False, index=True)
    test_details = db.Column(Text, nullable=False) # Which tests are ordered
    status = db.Column(String(50), default='Solicitado', index=True) # Solicitado, MuestraTomada, ResultadosRecibidos, Revisado
    results = db.Column(Text) # Place for results summary or link to result file
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    # appointment defined by backref

# --- MODELOS PARA EDUCACIÓN (LAN-ED3U) ---
class Student(db.Model):
    """Registro de un estudiante."""
    __tablename__ = 'education_student'
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(Integer, ForeignKey('user.id'), nullable=True, unique=True) # Link if student is a user
    full_name = db.Column(String(200), nullable=False)
    student_code = db.Column(String(50), unique=True, nullable=True) # Make nullable?
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    enrollments = db.relationship('Enrollment', backref='student', lazy='dynamic', cascade="all, delete-orphan")
    user = relationship('User') # Added relationship
    def to_dict(self): # Keep existing to_dict methods
        return {'id': self.id, 'full_name': self.full_name, 'student_code': self.student_code}

class Course(db.Model):
    """Cursos o asignaturas."""
    __tablename__ = 'education_course'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(200), nullable=False)
    course_code = db.Column(String(50), unique=True, nullable=True) # Make nullable?
    teacher_id = db.Column(Integer, ForeignKey('user.id'), nullable=True) # Teacher must be a user
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    teacher = db.relationship('User', backref='courses')
    enrollments = db.relationship('Enrollment', backref='course', lazy='dynamic', cascade="all, delete-orphan")
    def to_dict(self): # Keep existing to_dict methods
        return {
            'id': self.id, 'name': self.name, 'course_code': self.course_code,
            'teacher_name': self.teacher.full_name if self.teacher else 'N/A'
        }

class Enrollment(db.Model):
    """Inscripción de un estudiante en un curso."""
    __tablename__ = 'education_enrollment'
    id = db.Column(Integer, primary_key=True)
    student_id = db.Column(Integer, ForeignKey('education_student.id'), nullable=False)
    course_id = db.Column(Integer, ForeignKey('education_course.id'), nullable=False)
    enrollment_date = db.Column(Date, default=date.today)
    final_grade = db.Column(Float, nullable=True) # Grade for the course
    status = db.Column(String(50), default='Inscrito') # Inscrito, Retirado, Completado
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    grades = db.relationship('Grade', backref='enrollment', lazy='dynamic', cascade="all, delete-orphan") # Individual grades
    # student defined by backref
    # course defined by backref
    __table_args__ = (UniqueConstraint('student_id', 'course_id', name='_student_course_uc'),) # Ensure student enrolls only once

class Grade(db.Model):
    """Calificaciones individuales de un estudiante en una inscripción."""
    __tablename__ = 'education_grade'
    id = db.Column(Integer, primary_key=True)
    enrollment_id = db.Column(Integer, ForeignKey('education_enrollment.id'), nullable=False)
    grade_name = db.Column(String(100)) # E.g., "Examen Parcial 1", "Tarea 3"
    score = db.Column(Float, nullable=False)
    max_score = db.Column(Float, default=100.0) # Optional: Max possible score for weighting
    grade_date = db.Column(Date) # Optional: Date the grade was given
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    # enrollment defined by backref

# --- MODELOS PARA LOGÍSTICA (LAN-LOG6) ---
class Vehicle(db.Model):
    """Vehículos de la flota."""
    __tablename__ = 'logistics_vehicle'
    id = db.Column(Integer, primary_key=True)
    plate = db.Column(String(20), unique=True, nullable=False)
    brand = db.Column(String(50))
    model = db.Column(String(50))
    year = db.Column(Integer)
    status = db.Column(String(50), default='Disponible') # Disponible, En Ruta, Mantenimiento, FueraDeServicio
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    routes = relationship('Route', backref='vehicle', lazy='dynamic') # Added relationship

class Driver(db.Model):
    """Conductores."""
    __tablename__ = 'logistics_driver'
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(Integer, ForeignKey('user.id'), unique=True, nullable=False) # Driver must be a user
    license_number = db.Column(String(50), unique=True, nullable=False)
    license_expiry = db.Column(Date) # Optional expiry date
    is_available = db.Column(Boolean, default=True)
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    user = db.relationship('User', backref=backref('driver_profile', uselist=False)) # Changed backref
    routes = relationship('Route', backref='driver', lazy='dynamic') # Added relationship

class Route(db.Model):
    """Rutas de entrega."""
    __tablename__ = 'logistics_route'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(200), nullable=False) # E.g., "Ruta Centro", "Entrega Lunes AM"
    driver_id = db.Column(Integer, ForeignKey('logistics_driver.id'), nullable=True)
    vehicle_id = db.Column(Integer, ForeignKey('logistics_vehicle.id'), nullable=True)
    start_time = db.Column(DateTime, nullable=True) # Planned/Actual start
    end_time = db.Column(DateTime, nullable=True) # Planned/Actual end
    status = db.Column(String(50), default='Planificada') # Planificada, En Progreso, Completada, Cancelada
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    # driver defined by backref
    # vehicle defined by backref
    deliveries = db.relationship('Delivery', backref='route', lazy='dynamic', cascade="all, delete-orphan")

class Delivery(db.Model):
    """Entregas individuales en una ruta."""
    __tablename__ = 'logistics_delivery'
    id = db.Column(Integer, primary_key=True)
    route_id = db.Column(Integer, ForeignKey('logistics_route.id'), nullable=False)
    sales_order_id = db.Column(Integer, ForeignKey('sales_order.id'), nullable=True) # Link to SalesOrder if applicable
    address = db.Column(Text, nullable=False)
    recipient_name = db.Column(String(150)) # Optional recipient name
    status = db.Column(String(50), default='Pendiente') # Pendiente, EnTransito, Entregado, Fallido, Reprogramado
    delivery_time = db.Column(DateTime, nullable=True) # Actual time of delivery/failure
    signature_data = db.Column(Text) # Base64 signature image data
    notes = db.Column(Text) # Delivery notes
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    sales_order = db.relationship('SalesOrder', backref='deliveries')
    # route defined by backref

# --- MODELOS PARA GESTIÓN DE RESTAURANTES (LAN-RST1) ---
class MenuItem(db.Model):
    """Ítems del menú (platos, bebidas)."""
    __tablename__ = 'restaurant_menu_item'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(150), nullable=False)
    description = db.Column(Text)
    price = db.Column(Float, nullable=False)
    category = db.Column(String(50)) # Entrada, Plato Fuerte, Bebida, Postre, etc.
    is_available = db.Column(Boolean, default=True) # Can be ordered?
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    order_items = relationship('RestaurantOrderItem', backref='menu_item', lazy='dynamic') # Added relationship

class Table(db.Model):
    """Mesas del restaurante."""
    __tablename__ = 'restaurant_table'
    id = db.Column(Integer, primary_key=True)
    table_number = db.Column(String(20), nullable=False)
    capacity = db.Column(Integer)
    status = db.Column(String(50), default='Libre') # Libre, Ocupada, Reservada, Limpieza
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    orders = relationship('RestaurantOrder', backref='table', lazy='dynamic') # Added relationship

class RestaurantOrder(db.Model):
    """Órdenes o comandas de una mesa."""
    __tablename__ = 'restaurant_order'
    id = db.Column(Integer, primary_key=True)
    table_id = db.Column(Integer, ForeignKey('restaurant_table.id'), nullable=False)
    waiter_id = db.Column(Integer, ForeignKey('user.id')) # Waiter must be a user
    order_time = db.Column(DateTime, default=datetime.utcnow)
    status = db.Column(String(50), default='Abierta') # Abierta, EnviadaACocina, Servida, Cerrada, Pagada, Cancelada
    total_amount = db.Column(Float, default=0.0) # Calculated sum
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    # table defined by backref
    waiter = db.relationship('User', backref='restaurant_orders')
    items = db.relationship('RestaurantOrderItem', backref='order', lazy='dynamic', cascade="all, delete-orphan")

class RestaurantOrderItem(db.Model):
    """Ítems dentro de una orden."""
    __tablename__ = 'restaurant_order_item'
    id = db.Column(Integer, primary_key=True)
    order_id = db.Column(Integer, ForeignKey('restaurant_order.id'), nullable=False)
    menu_item_id = db.Column(Integer, ForeignKey('restaurant_menu_item.id'), nullable=False)
    quantity = db.Column(Integer, default=1)
    price = db.Column(Float) # Price at the time of the order (in case menu price changes)
    notes = db.Column(Text) # E.g., "Sin cebolla", "Término medio"
    status = db.Column(String(50), default='Pendiente') # Pendiente, Enviado, Preparando, Listo, Servido
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    # menu_item defined by backref
    # order defined by backref

# --- MODELOS PARA COCINA COMERCIAL (LAN-KTC4) ---
class KitchenSpace(db.Model):
    """Espacios o estaciones de cocina para alquilar."""
    __tablename__ = 'commercial_kitchen_space'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(150), nullable=False)
    description = db.Column(Text)
    hourly_rate = db.Column(Float)
    is_available = db.Column(Boolean, default=True) # Overall availability
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    bookings = relationship('KitchenBooking', backref='space', lazy='dynamic') # Added relationship

class KitchenBooking(db.Model):
    """Reservas de espacios de cocina."""
    __tablename__ = 'commercial_kitchen_booking'
    id = db.Column(Integer, primary_key=True)
    space_id = db.Column(Integer, ForeignKey('commercial_kitchen_space.id'), nullable=False)
    user_id = db.Column(Integer, ForeignKey('user.id'), nullable=False) # User who booked
    start_time = db.Column(DateTime, nullable=False)
    end_time = db.Column(DateTime, nullable=False)
    total_cost = db.Column(Float) # Calculated based on duration and rate
    status = db.Column(String(50), default='Confirmada') # Confirmada, EnCurso, Finalizada, Cancelada
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    # space defined by backref
    user = db.relationship('User', backref='kitchen_bookings')

class HACCPLog(db.Model):
    """Registros de control HACCP (Análisis de Peligros y Puntos Críticos de Control)."""
    __tablename__ = 'commercial_kitchen_haccp_log'
    id = db.Column(Integer, primary_key=True)
    log_date = db.Column(DateTime, default=datetime.utcnow)
    control_point = db.Column(String(200), nullable=False) # E.g., "Temperatura Refrigerador Carnes", "Limpieza Campana"
    measurement = db.Column(String(100), nullable=False) # E.g., "4°C", "OK", "150 ppm Cloro"
    is_compliant = db.Column(Boolean, nullable=False) # Meets criteria?
    corrective_action = db.Column(Text) # Action taken if not compliant
    verified_by_id = db.Column(Integer, ForeignKey('user.id')) # User who performed check
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    verified_by = db.relationship('User', backref='haccp_logs')

# --- MODELOS PARA OPERACIONES DE CAMPO (LAN-FLD2) ---
# These were only in feature-LAN-F2C
class FieldTask(db.Model):
    """Tareas asignadas a técnicos en campo."""
    __tablename__ = 'field_task'
    id = db.Column(Integer, primary_key=True)
    title = db.Column(String(200), nullable=False)
    description = db.Column(Text)
    address = db.Column(Text)
    latitude = db.Column(Float)
    longitude = db.Column(Float)
    assigned_to_id = db.Column(Integer, ForeignKey('user.id'), nullable=False)
    due_date = db.Column(Date)
    status = db.Column(String(50), default='Asignada') # Asignada, En Progreso, Completada, Cancelada, Bloqueada
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    assigned_to = db.relationship('User', backref='field_tasks')
    reports = db.relationship('TaskReport', backref='task', lazy='dynamic', cascade="all, delete-orphan")

class TaskReport(db.Model):
    """Reportes de avance enviados desde el campo."""
    __tablename__ = 'field_task_report'
    id = db.Column(Integer, primary_key=True)
    task_id = db.Column(Integer, ForeignKey('field_task.id'), nullable=False)
    notes = db.Column(Text)
    photo_url = db.Column(String(255)) # URL to evidence photo (e.g., stored in S3)
    latitude = db.Column(Float) # Geolocation when report submitted
    longitude = db.Column(Float)
    created_by_id = db.Column(Integer, ForeignKey('user.id')) # Should match task.assigned_to_id
    created_at = db.Column(DateTime, default=datetime.utcnow)
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    # task defined by backref
    created_by = relationship('User', backref='task_reports')

# --- MODELOS DE AUDITORÍA Y NOTIFICACIONES ---
class NotificationTemplate(db.Model):
    """Plantillas de notificaciones (email, SMS, in-app)"""
    __tablename__ = 'notification_template'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(150), nullable=False) # Unique name for identification (e.g., 'welcome_email', 'payment_reminder')
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
    # user defined by backref from User model
    def __repr__(self):
        return f'<AuditLog {self.id} User:{self.user_id} Action:{self.action} on {self.entity}:{self.entity_id}>'