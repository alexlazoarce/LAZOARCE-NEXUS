import os
import click
from functools import wraps
from flask import Flask, jsonify, request, g, Blueprint, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
from sqlalchemy import func, Boolean, Date, DateTime, Float, Integer, String, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from flask_cors import CORS

# --- DEFINICIÓN GLOBAL DE EXTENSIONES ---
db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()

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

# === MODELOS DE LA APLICACIÓN ===
# --- Modelos de Seguridad y Tenants ---
class Tenant(db.Model):
    __tablename__ = 'tenant'
    id = db.Column(Integer, primary_key=True)
    company_name = db.Column(String(100), unique=True, nullable=False, index=True)
    company_code = db.Column(String(20), unique=True, nullable=False)
    domain = db.Column(String(100), unique=True)
    is_active = db.Column(Boolean, default=True)
    created_at = db.Column(DateTime, default=func.current_timestamp())
    config = db.Column(JSONB, default=dict)
    users = relationship('User', backref='tenant', lazy='dynamic', cascade="all, delete-orphan")
    roles = relationship('Role', backref='tenant', lazy='dynamic', cascade="all, delete-orphan")
    loan_products = relationship('LoanProduct', backref='tenant', lazy='dynamic', cascade="all, delete-orphan")

class Role(db.Model):
    __tablename__ = 'role'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(80), nullable=False, index=True)
    description = db.Column(String(255))
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=True, index=True)
    is_active = db.Column(Boolean, default=True)
    users = relationship('User', secondary=user_roles, back_populates='roles_m2m')
    __table_args__ = (UniqueConstraint('name', 'tenant_id', name='_role_name_tenant_uc'),)

class User(db.Model):
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
    roles_m2m = relationship('Role', secondary=user_roles, back_populates='users')
    profile = relationship('ClientProfile', backref='user', uselist=False, cascade="all, delete-orphan")
    employee = relationship('Employee', backref='user', uselist=False, cascade="all, delete-orphan")
    applications = relationship('LoanApplication', backref='applicant', lazy='dynamic', cascade="all, delete-orphan")
    audit_logs = relationship('AuditLog', backref='user', lazy='dynamic', cascade="all, delete-orphan")
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def role(self):
        if self.role_id:
            return db.session.get(Role, self.role_id)
        return None

class ClientProfile(db.Model):
    __tablename__ = 'client_profile'
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(Integer, ForeignKey('user.id'), unique=True, nullable=False)
    full_name = db.Column(String(120))
    phone_number = db.Column(String(20))
    address = db.Column(Text)
    birth_date = db.Column(Date)

# --- Modelos de Préstamos ---
class LoanProduct(db.Model):
    __tablename__ = 'loan_product'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(100), nullable=False)
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False)

class ProductoCredito(LoanProduct):
    __mapper_args__ = {'polymorphic_identity': 'producto_credito'}

class Payment(db.Model):
    __tablename__ = 'payment'
    id = db.Column(Integer, primary_key=True)
    loan_application_id = db.Column(Integer, ForeignKey('loan_application.id'), nullable=False)
    amount = db.Column(Float, nullable=False)
    date = db.Column(DateTime, default=func.current_timestamp())

class LoanApplication(db.Model):
    __tablename__ = 'loan_application'
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(Integer, ForeignKey('user.id'), nullable=False)
    product_id = db.Column(Integer, ForeignKey('loan_product.id'), nullable=False)
    status = db.Column(String(50), default='Pendiente')
    applicant = relationship('User')

# --- Modelos Contables ---
class Account(db.Model):
    __tablename__ = 'account'
    id = db.Column(Integer, primary_key=True)

class JournalEntry(db.Model):
    __tablename__ = 'journal_entry'
    id = db.Column(Integer, primary_key=True)

class Transaction(db.Model):
    __tablename__ = 'transaction'
    id = db.Column(Integer, primary_key=True)

# --- Modelos de RRHH ---
class Employee(db.Model):
    __tablename__ = 'employee'
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(Integer, ForeignKey('user.id'), unique=True, nullable=False)
    salario_base = db.Column(Float)

class Empleado(Employee):
    __mapper_args__ = {'polymorphic_identity': 'empleado'}

class PaySlip(db.Model):
    __tablename__ = 'payslip'
    id = db.Column(Integer, primary_key=True)
    isss = db.Column(Float)
    afp = db.Column(Float)
    renta = db.Column(Float)
    salario_neto = db.Column(Float)
    salario_base = db.Column(Float)
    employee_id = db.Column(Integer, ForeignKey('employee.id'))

class Planilla(PaySlip):
    __mapper_args__ = {'polymorphic_identity': 'planilla'}

# --- Modelos de Firma y Contratos (Integración) ---
class Cliente(db.Model):
    __tablename__ = 'cliente'
    id = db.Column(Integer, primary_key=True)
    contrato_integracion_id = db.Column(String(50), ForeignKey('contrato_integracion.contrato_id'))
    firma_electronica_id = db.Column(String(50), ForeignKey('firma_electronica.firma_id'))
    contrato_integracion = relationship("ContratoIntegracion", back_populates="clientes", foreign_keys=[contrato_integracion_id])
    firma_electronica = relationship("FirmaElectronica", back_populates="clientes", foreign_keys=[firma_electronica_id])

class ContratoIntegracion(db.Model):
    __tablename__ = 'contrato_integracion'
    id = db.Column(Integer, primary_key=True)
    contrato_id = db.Column(String(50), unique=True)
    clientes = relationship("Cliente", back_populates="contrato_integracion")

class FirmaElectronica(db.Model):
    __tablename__ = 'firma_electronica'
    id = db.Column(Integer, primary_key=True)
    firma_id = db.Column(String(50), unique=True)
    clientes = relationship("Cliente", back_populates="firma_electronica")

class CertificadoValidacion(db.Model):
    __tablename__ = 'certificado_validacion'
    id = db.Column(Integer, primary_key=True)

# --- Modelos de Módulos ---
class ContractTemplate(db.Model):
    __tablename__ = 'contract_template'
    id = db.Column(Integer, primary_key=True)

class GeneratedContract(db.Model):
    __tablename__ = 'generated_contract'
    id = db.Column(Integer, primary_key=True)

class Contact(db.Model):
    __tablename__ = 'crm_contact'
    id = db.Column(Integer, primary_key=True)

class Interaction(db.Model):
    __tablename__ = 'crm_interaction'
    id = db.Column(Integer, primary_key=True)

class Opportunity(db.Model):
    __tablename__ = 'crm_opportunity'
    id = db.Column(Integer, primary_key=True)

class Product(db.Model):
    __tablename__ = 'inventory_product'
    id = db.Column(Integer, primary_key=True)

class StockMovement(db.Model):
    __tablename__ = 'inventory_stock_movement'
    id = db.Column(Integer, primary_key=True)

class Quote(db.Model):
    __tablename__ = 'sales_quote'
    id = db.Column(Integer, primary_key=True)

class SalesOrder(db.Model):
    __tablename__ = 'sales_order'
    id = db.Column(Integer, primary_key=True)

class SalesOrderItem(db.Model):
    __tablename__ = 'sales_order_item'
    id = db.Column(Integer, primary_key=True)

class Supplier(db.Model):
    __tablename__ = 'purchasing_supplier'
    id = db.Column(Integer, primary_key=True)

class PurchaseOrder(db.Model):
    __tablename__ = 'purchasing_order'
    id = db.Column(Integer, primary_key=True)

class PurchaseOrderItem(db.Model):
    __tablename__ = 'purchasing_order_item'
    id = db.Column(Integer, primary_key=True)

class EmailLog(db.Model):
    __tablename__ = 'email_log'
    id = db.Column(Integer, primary_key=True)

class Document(db.Model):
    __tablename__ = 'document'
    id = db.Column(Integer, primary_key=True)
    filename = db.Column(String)
    description = db.Column(String)
    latest_version_id = db.Column(Integer)
    created_at = db.Column(DateTime, default=func.current_timestamp())
    updated_at = db.Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())

class DocumentVersion(db.Model):
    __tablename__ = 'document_version'
    id = db.Column(Integer, primary_key=True)
    filepath = db.Column(String)

class Channel(db.Model):
    __tablename__ = 'messaging_channel'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String)
    description = db.Column(String)
    channel_type = db.Column(String)

class Message(db.Model):
    __tablename__ = 'messaging_message'
    id = db.Column(Integer, primary_key=True)
    content = db.Column(Text)
    user_id = db.Column(Integer, ForeignKey('user.id'))
    created_at = db.Column(DateTime, default=func.current_timestamp())
    author = relationship('User')

class SignableTemplate(db.Model):
    __tablename__ = 'sign_template'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String)
    description = db.Column(String)
    content = db.Column(Text)

class SignatureRequest(db.Model):
    __tablename__ = 'sign_request'
    id = db.Column(Integer, primary_key=True)
    signer_name = db.Column(String)
    signer_email = db.Column(String)
    status = db.Column(String)
    created_at = db.Column(DateTime, default=func.current_timestamp())
    final_document_content = db.Column(Text)

class Form(db.Model):
    __tablename__ = 'form'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String)
    description = db.Column(String)
    fields = db.Column(JSONB)
    public_token = db.Column(String, unique=True)

class FormSubmission(db.Model):
    __tablename__ = 'form_submission'
    id = db.Column(Integer, primary_key=True)
    data = db.Column(JSONB)
    submitted_at = db.Column(DateTime, default=func.current_timestamp())

class Project(db.Model):
    __tablename__ = 'project'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String)
    description = db.Column(String)
    status = db.Column(String)
    budget = db.Column(Float)
    end_date = db.Column(Date)

class Task(db.Model):
    __tablename__ = 'task'
    id = db.Column(Integer, primary_key=True)
    title = db.Column(String)
    status = db.Column(String)
    due_date = db.Column(Date)

class Ticket(db.Model):
    __tablename__ = 'ticket'
    id = db.Column(Integer, primary_key=True)
    subject = db.Column(String)
    description = db.Column(Text)
    status = db.Column(String)
    priority = db.Column(String)
    updated_at = db.Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())
    updates = relationship('TicketUpdate')

class TicketUpdate(db.Model):
    __tablename__ = 'ticket_update'
    id = db.Column(Integer, primary_key=True)
    comment = db.Column(Text)
    author = relationship('User')

class FixedAsset(db.Model):
    __tablename__ = 'fixed_asset'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String)
    description = db.Column(String)
    purchase_cost = db.Column(Float)
    status = db.Column(String)
    purchase_date = db.Column(Date)
    useful_life = db.Column(Integer)
    salvage_value = db.Column(Float)
    depreciation_entries = relationship('DepreciationEntry')

class DepreciationEntry(db.Model):
    __tablename__ = 'depreciation_entry'
    id = db.Column(Integer, primary_key=True)
    entry_date = db.Column(Date)
    amount = db.Column(Float)

class MailingList(db.Model):
    __tablename__ = 'mailing_list'
    id = db.Column(Integer, primary_key=True)

class AuditLog(db.Model):
    __tablename__ = 'audit_log'
    id = db.Column(Integer, primary_key=True)

class NotificationTemplate(db.Model):
    __tablename__ = 'notification_template'
    id = db.Column(Integer, primary_key=True)

class BankAccount(db.Model):
    __tablename__ = 'bank_account'
    id = db.Column(Integer, primary_key=True)

class BankTransaction(db.Model):
    __tablename__ = 'bank_transaction'
    id = db.Column(Integer, primary_key=True)

class CashBox(db.Model):
    __tablename__ = 'cash_box'
    id = db.Column(Integer, primary_key=True)

class CashTransaction(db.Model):
    __tablename__ = 'cash_transaction'
    id = db.Column(Integer, primary_key=True)

class TaxType(db.Model):
    __tablename__ = 'tax_type'
    id = db.Column(Integer, primary_key=True)

class TaxDeclaration(db.Model):
    __tablename__ = 'tax_declaration'
    id = db.Column(Integer, primary_key=True)

class Material(db.Model):
    __tablename__ = 'material'
    id = db.Column(Integer, primary_key=True)

class MaterialRequest(db.Model):
    __tablename__ = 'material_request'
    id = db.Column(Integer, primary_key=True)

class ConstructionProject(db.Model):
    __tablename__ = 'construction_project'
    id = db.Column(Integer, primary_key=True)

class BudgetItem(db.Model):
    __tablename__ = 'budget_item'
    id = db.Column(Integer, primary_key=True)

class ProgressReport(db.Model):
    __tablename__ = 'progress_report'
    id = db.Column(Integer, primary_key=True)

class Certification(db.Model):
    __tablename__ = 'certification'
    id = db.Column(Integer, primary_key=True)

# === MOCK DE SERVICIOS Y UTILIDADES ===
class MockService:
    def __init__(self, name):
        self.name = name
    
    def __call__(self, *args, **kwargs):
        return self
    
    def send_email(self, *args, **kwargs):
        return True, "OK"
    
    def log_action(self, *args, **kwargs):
        pass
    
    def get_asset_details(self, *args, **kwargs):
        class A:
            id = 1
            name = 'A1'
            description = 'D'
            purchase_cost = 1000
            purchase_date = date.today()
            useful_life = 5
            salvage_value = 0
            depreciation_entries = []
        return A()
    
    def get_asset_book_value(self, *args, **kwargs):
        return 900
    
    def get_assets_for_tenant(self, *args, **kwargs):
        class A:
            id = 1
            name = 'A1'
            purchase_cost = 1000
            status = 'Active'
        return [A()]
    
    def create_asset(self, *args, **kwargs):
        class A:
            id = 2
        return A()
    
    def calculate_monthly_depreciation(self, *args, **kwargs):
        class E:
            id = 3
            amount = 100
        return E()
    
    def get_projects_for_tenant(self, *args, **kwargs):
        class P:
            id = 1
            name = 'P1'
            status = 'In Progress'
            end_date = datetime.now().date()
        return [P()]
    
    def create_project(self, *args, **kwargs):
        class P:
            id = 2
        return P()
    
    def get_project_details(self, *args, **kwargs):
        class P:
            id = 1
            name = 'P1'
            description = 'D'
            status = 'In Progress'
            budget = 100
        return P()
    
    def get_tasks_for_project(self, *args, **kwargs):
        class T:
            id = 1
            title = 'T1'
            status = 'To Do'
            due_date = datetime.now().date()
        return [T()]
    
    def create_task(self, *args, **kwargs):
        class T:
            id = 2
        return T()
    
    def update_task_status(self, *args, **kwargs):
        class T:
            id = 1
            status = 'Done'
        return T()
    
    def get_tickets_for_tenant(self, *args, **kwargs):
        class T:
            id = 1
            subject = 'S1'
            status = 'Open'
            priority = 'High'
            updated_at = datetime.utcnow()
        return [T()]
    
    def create_ticket(self, *args, **kwargs):
        class T:
            id = 2
        return T()
    
    def get_ticket_details(self, *args, **kwargs):
        class T:
            id = 1
            subject = 'S1'
            description = 'D'
            status = 'Open'
            priority = 'High'
            updates = []
        return T()
    
    def add_ticket_update(self, *args, **kwargs):
        class U:
            id = 3
        return U()
    
    def assign_ticket(self, *args, **kwargs):
        class T:
            id = 1
        return T()
    
    def change_ticket_status(self, *args, **kwargs):
        class T:
            id = 1
            status = 'Closed'
        return T()
    
    def get_documents_for_tenant(self, *args, **kwargs):
        class D:
            id = 1
            filename = 'doc1.pdf'
            description = 'Test Document'
            latest_version_id = 1
            created_at = datetime.utcnow()
            updated_at = datetime.utcnow()
        return [D()]
    
    def create_document(self, *args, **kwargs):
        class D:
            id = 1
        return D()
    
    def add_new_version(self, *args, **kwargs):
        class V:
            id = 2
        return V()
    
    def get_document_version(self, *args, **kwargs):
        class V:
            id = 1
            filepath = '/path/to/file'
        return V()
    
    def get_user_channels(self, *args, **kwargs):
        class C:
            id = 1
            name = 'Channel1'
            description = 'Test Channel'
            channel_type = 'public'
        return [C()]
    
    def create_channel(self, *args, **kwargs):
        class C:
            id = 1
        return C()
    
    def get_messages_for_channel(self, *args, **kwargs):
        class M:
            id = 1
            content = 'Test Message'
            user_id = 1
            created_at = datetime.utcnow()
            author = type('User', (), {'full_name': 'Test User'})()
        return [M()]
    
    def post_message(self, *args, **kwargs):
        class M:
            id = 1
        return M()
    
    def get_templates_for_tenant(self, *args, **kwargs):
        class T:
            id = 1
            name = 'Template1'
            description = 'Test Template'
        return [T()]
    
    def create_template(self, *args, **kwargs):
        class T:
            id = 1
        return T()
    
    def get_signature_requests(self, *args, **kwargs):
        class R:
            id = 1
            signer_name = 'Test Signer'
            signer_email = 'test@example.com'
            status = 'sent'
            created_at = datetime.utcnow()
        return [R()]
    
    def create_signature_request(self, *args, **kwargs):
        class R:
            id = 1
        return R()
    
    def get_request_by_token(self, *args, **kwargs):
        class R:
            id = 1
            signer_name = 'Test Signer'
            final_document_content = 'Document Content'
            status = 'sent'
        return R()
    
    def send_signature_request(self, *args, **kwargs):
        pass
    
    def sign_document(self, *args, **kwargs):
        pass
    
    def get_forms_for_tenant(self, *args, **kwargs):
        class F:
            id = 1
            name = 'Form1'
            public_token = 'token123'
        return [F()]
    
    def create_form(self, *args, **kwargs):
        class F:
            id = 1
            public_token = 'token123'
        return F()
    
    def get_submissions_for_form(self, *args, **kwargs):
        class S:
            id = 1
            data = {}
            submitted_at = datetime.utcnow()
        return [S()]
    
    def get_form_by_token(self, *args, **kwargs):
        class F:
            id = 1
            name = 'Form1'
            description = 'Test Form'
            fields = []
        return F()
    
    def submit_form(self, *args, **kwargs):
        pass
    
    def get_balance_sheet(self, *args, **kwargs):
        return {}
    
    def get_income_statement(self, *args, **kwargs):
        return {}

def validacion_identidad_estricta(data):
    return True

def capturar_datos_biometricos():
    return {"biometric_data": "hash"}

def generar_contrato_integracion(data):
    return "CONTRATO-123"

def firma_electronica_avanzada(contrato_id, data, datos_biometricos):
    return {"valida": True, "firma_id": "FIRMA-456"}

def calcular_planilla(salario_base):
    return {'success': True, 'salario_base': salario_base, 'isss': 100, 'afp': 100, 'renta': 50, 'salario_neto': salario_base - 250}

# --- APP FACTORY ---
def create_app(config_object=None, testing_config=None):
    app = Flask(__name__)
    CORS(app)
    load_dotenv()
    
    # Configuración
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-secret-key-change-me'),
        JWT_SECRET_KEY=os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-me'),
        SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL', f"sqlite:///{os.path.join(app.instance_path, 'app.db')}"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        UPLOAD_FOLDER=os.path.join(app.instance_path, 'Uploads')
    )
    
    if testing_config:
        app.config.from_mapping(testing_config)
    
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Inicialización de extensiones
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    
    with app.app_context():
        # Asignar modelos al contexto de la app
        app.models = {
            'Role': Role, 'User': User, 'LoanProduct': LoanProduct, 'LoanApplication': LoanApplication,
            'Account': Account, 'Transaction': Transaction, 'JournalEntry': JournalEntry, 'Cliente': Cliente,
            'ContratoIntegracion': ContratoIntegracion, 'ProductoCredito': ProductoCredito, 'Empleado': Empleado,
            'Planilla': Planilla, 'Employee': Employee, 'AuditLog': AuditLog, 'ClientProfile': ClientProfile,
            'Tenant': Tenant, 'Payment': Payment, 'NotificationTemplate': NotificationTemplate,
            'ContractTemplate': ContractTemplate, 'GeneratedContract': GeneratedContract, 'Contact': Contact,
            'Interaction': Interaction, 'Opportunity': Opportunity, 'Product': Product, 'StockMovement': StockMovement,
            'Quote': Quote, 'SalesOrder': SalesOrder, 'SalesOrderItem': SalesOrderItem, 'Supplier': Supplier,
            'PurchaseOrder': PurchaseOrder, 'PurchaseOrderItem': PurchaseOrderItem, 'EmailLog': EmailLog,
            'Channel': Channel, 'Message': Message, 'SignableTemplate': SignableTemplate, 'SignatureRequest': SignatureRequest,
            'Form': Form, 'FormSubmission': FormSubmission, 'Project': Project, 'Task': Task,
            'Ticket': Ticket, 'TicketUpdate': TicketUpdate, 'FixedAsset': FixedAsset, 'DepreciationEntry': DepreciationEntry,
            'BankAccount': BankAccount, 'BankTransaction': BankTransaction, 'CashBox': CashBox, 'CashTransaction': CashTransaction,
            'TaxType': TaxType, 'TaxDeclaration': TaxDeclaration, 'Material': Material, 'MaterialRequest': MaterialRequest,
            'ConstructionProject': ConstructionProject, 'BudgetItem': BudgetItem, 'ProgressReport': ProgressReport,
            'Certification': Certification
        }
        
        # Asignar servicios mock
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
            'sign_service': MockService('Sign'),
            'form_service': MockService('Form'),
            'project_service': MockService('Project'),
            'support_service': MockService('Support'),
            'asset_service': MockService('Asset'),
            'tax_service': MockService('Tax'),
            'material_service': MockService('Material'),
            'construction_service': MockService('Construction')
        }
    
    # Decorador de autorización
    def role_required(required_roles):
        if not isinstance(required_roles, list):
            required_roles = [required_roles]
        
        def decorator(fn):
            @wraps(fn)
            @jwt_required()
            def wrapper(*args, **kwargs):
                claims = get_jwt()
                user_roles = set(claims.get('roles', []))
                user_identity = get_jwt_identity()
                g.current_user = app.models['User'].query.filter_by(email=user_identity).first()
                if not g.current_user:
                    return jsonify({"msg": "Usuario no encontrado"}), 404
                if g.current_user.role:
                    user_roles.add(g.current_user.role.name)
                if not any(role in user_roles for role in required_roles):
                    return jsonify({"msg": "Acceso no autorizado para este rol"}), 403
                return fn(*args, **kwargs)
            return wrapper
        return decorator
    
    # Rutas base
    @app.route('/api/health')
    def health_check():
        return jsonify({"status": "healthy"})
    
    @app.route('/api/login', methods=['POST'])
    def login():
        data = request.get_json()
        user = app.models['User'].query.filter_by(email=data.get('email')).first()
        if user and user.check_password(data.get('password')):
            user_roles = [r.name for r in user.roles_m2m] + ([user.role.name] if user.role else [])
            if not user_roles:
                user_roles = ['Cliente']
            access_token = create_access_token(identity=user.email, additional_claims={'roles': list(set(user_roles)), 'user_id': user.id, 'tenant_id': user.tenant_id})
            return jsonify(access_token=access_token)
        return jsonify({"msg": "Credenciales inválidas"}), 401
    
    # --- RUTAS PARA PRÉSTAMOS ---
    @app.route('/api/applications/<int:app_id>/send-reminder', methods=['POST'])
    @jwt_required()
    @role_required(['Administrador General'])
    def send_payment_reminder(app_id):
        LoanApplication = app.models.get('LoanApplication')
        application = LoanApplication.query.get_or_404(app_id)
        recipient = application.applicant.email
        subject = f"Recordatorio de Pago para su Préstamo #{application.id}"
        body = f"Hola {application.applicant.full_name},\n\nEste es un recordatorio de que su próximo pago para el préstamo #{application.id} está por vencer."
        success, message = app.services['email_service'].send_email(
            recipient,
            subject,
            body,
            g.current_user.tenant
        )
        return jsonify({"message": f"Recordatorio de pago enviado para la solicitud {app_id}."}), 200
    
    @app.route('/api/applications/<int:app_id>/status', methods=['PUT'])
    @jwt_required()
    @role_required(['Ejecutivo de Crédito', 'Administrador General'])
    def update_application_status(app_id):
        LoanApplication = app.models.get('LoanApplication')
        application = LoanApplication.query.get_or_404(app_id)
        data = request.get_json()
        new_status = data.get('status')
        if not new_status:
            return jsonify({"error": "El campo 'status' es requerido."}), 400
        application.status = new_status
        db.session.commit()
        return jsonify({"message": f"Estado de la solicitud {app_id} actualizado a '{new_status}'."})
    
    # --- RUTAS PARA GESTIÓN DE CONTRATOS (LAN-F2C) ---
    @app.route('/api/contracts/templates', methods=['POST'])
    @jwt_required()
    @role_required(['Administrador General'])
    def create_contract_template_route():
        data = request.get_json()
        return jsonify({"message": "Ruta para crear plantilla de contrato implementada."}), 201
    
    @app.route('/api/contracts/templates/<int:template_id>', methods=['GET'])
    @jwt_required()
    def get_contract_template_route(template_id):
        return jsonify({"message": f"Ruta para obtener plantilla {template_id}."}), 200
    
    @app.route('/api/contracts/templates/<int:template_id>', methods=['PUT'])
    @jwt_required()
    @role_required(['Administrador General'])
    def update_contract_template_route(template_id):
        data = request.get_json()
        return jsonify({"message": f"Ruta para actualizar plantilla {template_id}."}), 200
    
    @app.route('/api/contracts/templates/<int:template_id>', methods=['DELETE'])
    @jwt_required()
    @role_required(['Administrador General'])
    def delete_contract_template_route(template_id):
        return jsonify({"message": f"Ruta para eliminar plantilla {template_id}."}), 200
    
    @app.route('/api/contracts/generate', methods=['POST'])
    @jwt_required()
    @role_required(['Ejecutivo de Crédito', 'Administrador General'])
    def generate_contract_route():
        data = request.get_json()
        return jsonify({"message": "Ruta para generar un contrato implementada."}), 201
    
    # --- RUTAS PARA CRM (LAN-CRM3) ---
    @app.route('/api/crm/contacts', methods=['POST'])
    @jwt_required()
    @role_required(['Ejecutivo de Crédito', 'Administrador General'])
    def create_crm_contact():
        data = request.get_json()
        return jsonify({"message": "Ruta para crear contacto de CRM implementada."}), 201
    
    @app.route('/api/crm/contacts', methods=['GET'])
    @jwt_required()
    def get_crm_contacts():
        return jsonify([]), 200
    
    @app.route('/api/crm/contacts/<int:contact_id>', methods=['GET'])
    @jwt_required()
    def get_crm_contact_details(contact_id):
        return jsonify({"message": f"Ruta para obtener detalles del contacto {contact_id}."}), 200
    
    @app.route('/api/crm/contacts/<int:contact_id>/interactions', methods=['POST'])
    @jwt_required()
    def add_crm_interaction(contact_id):
        data = request.get_json()
        return jsonify({"message": f"Ruta para añadir interacción al contacto {contact_id}."}), 201
    
    @app.route('/api/crm/opportunities', methods=['POST'])
    @jwt_required()
    @role_required(['Ejecutivo de Crédito', 'Administrador General'])
    def create_crm_opportunity():
        data = request.get_json()
        return jsonify({"message": "Ruta para crear oportunidad de CRM implementada."}), 201
    
    @app.route('/api/crm/opportunities/<int:opp_id>/stage', methods=['PUT'])
    @jwt_required()
    @role_required(['Ejecutivo de Crédito', 'Administrador General'])
    def update_crm_opportunity_stage(opp_id):
        data = request.get_json()
        return jsonify({"message": f"Ruta para actualizar etapa de la oportunidad {opp_id}."}), 200
    
    # --- RUTAS PARA INVENTARIO (LAN-INV9) ---
    @app.route('/api/inventory/products', methods=['POST'])
    @jwt_required()
    @role_required(['Administrador General'])
    def create_inventory_product():
        data = request.get_json()
        return jsonify({"message": "Ruta para crear producto de inventario implementada."}), 201
    
    @app.route('/api/inventory/products', methods=['GET'])
    @jwt_required()
    def get_inventory_products():
        return jsonify([]), 200
    
    @app.route('/api/inventory/products/<int:product_id>/movements', methods=['POST'])
    @jwt_required()
    @role_required(['Administrador General'])
    def record_inventory_movement(product_id):
        data = request.get_json()
        return jsonify({"message": f"Ruta para registrar movimiento de stock para el producto {product_id}."}), 201
    
    # --- RUTAS PARA VENTAS (LAN-SLS2) ---
    @app.route('/api/sales/quotes', methods=['POST'])
    @jwt_required()
    @role_required(['Ejecutivo de Crédito', 'Administrador General'])
    def create_sales_quote():
        data = request.get_json()
        return jsonify({"message": "Ruta para crear cotización de venta implementada."}), 201
    
    @app.route('/api/sales/orders', methods=['GET'])
    @jwt_required()
    def get_sales_orders():
        return jsonify([]), 200
    
    @app.route('/api/sales/quotes/<int:quote_id>/convert', methods=['POST'])
    @jwt_required()
    @role_required(['Ejecutivo de Crédito', 'Administrador General'])
    def convert_quote_to_order(quote_id):
        return jsonify({"message": f"Ruta para convertir cotización {quote_id} a orden de venta."}), 201
    
    @app.route('/api/sales/orders/<int:order_id>/confirm', methods=['POST'])
    @jwt_required()
    @role_required(['Administrador General'])
    def confirm_sales_order(order_id):
        return jsonify({"message": f"Ruta para confirmar la orden de venta {order_id} y ajustar stock."}), 200
    
    # --- RUTAS PARA COMPRAS (LAN-CO1M) ---
    @app.route('/api/purchasing/suppliers', methods=['POST'])
    @jwt_required()
    @role_required(['Administrador General'])
    def create_supplier():
        data = request.get_json()
        return jsonify({"message": "Ruta para crear proveedor implementada."}), 201
    
    @app.route('/api/purchasing/orders', methods=['POST'])
    @jwt_required()
    @role_required(['Administrador General'])
    def create_purchase_order():
        data = request.get_json()
        return jsonify({"message": "Ruta para crear orden de compra implementada."}), 201
    
    @app.route('/api/purchasing/orders/<int:order_id>/receive', methods=['POST'])
    @jwt_required()
    @role_required(['Administrador General'])
    def receive_purchase_order(order_id):
        return jsonify({"message": f"Ruta para registrar la recepción de la orden {order_id}."}), 200
    
    # --- RUTAS PARA REPORTES CONTABLES (LAN-BKS1) ---
    @app.route('/api/reports/balance-sheet', methods=['GET'])
    @jwt_required()
    @role_required(['Contador', 'Administrador General'])
    def get_balance_sheet_report():
        tenant_id = g.current_user.tenant_id
        report_data = app.services['accounting_service'].get_balance_sheet(tenant_id)
        return jsonify(report_data), 200
    
    @app.route('/api/reports/income-statement', methods=['GET'])
    @jwt_required()
    @role_required(['Contador', 'Administrador General'])
    def get_income_statement_report():
        tenant_id = g.current_user.tenant_id
        report_data = app.services['accounting_service'].get_income_statement(tenant_id)
        return jsonify(report_data), 200
    
    # --- RUTAS PARA CORREO (LAN-MAIL1) ---
    @app.route('/api/email/test', methods=['POST'])
    @jwt_required()
    @role_required(['Administrador General'])
    def test_email_sending():
        data = request.get_json()
        recipient = data.get('recipient')
        subject = data.get('subject', 'Correo de Prueba')
        body = data.get('body', 'Este es un correo de prueba desde el sistema LAZOARCE NEXUS.')
        if not recipient:
            return jsonify({"error": "El destinatario es requerido."}), 400
        success, message = app.services['email_service'].send_email(
            recipient,
            subject,
            body,
            g.current_user.tenant
        )
        if success:
            return jsonify({"message": message}), 200
        else:
            return jsonify({"error": message}), 500
    
    # --- RUTAS PARA GESTOR DE DOCUMENTOS (LAN-GD2) ---
    documents_bp = Blueprint('documents', __name__, url_prefix='/api/documents')
    
    @documents_bp.route('/', methods=['GET'])
    @jwt_required()
    def list_documents():
        tenant_id = g.current_user.tenant_id
        documents = app.services['document_service'].get_documents_for_tenant(tenant_id)
        return jsonify([{
            'id': doc.id,
            'filename': doc.filename,
            'description': doc.description,
            'latest_version_id': doc.latest_version_id,
            'created_at': doc.created_at.isoformat(),
            'updated_at': doc.updated_at.isoformat()
        } for doc in documents])
    
    @documents_bp.route('/', methods=['POST'])
    @jwt_required()
    def upload_document():
        if 'file' not in request.files:
            return jsonify({"error": "No se encontró el archivo"}), 400
        file = request.files['file']
        description = request.form.get('description', '')
        tenant_id = g.current_user.tenant_id
        user_id = g.current_user.id
        try:
            document = app.services['document_service'].create_document(tenant_id, user_id, file, description)
            return jsonify({"message": "Documento creado exitosamente", "document_id": document.id}), 201
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            app.logger.error(f"Error al crear documento: {e}")
            return jsonify({"error": "Error interno al guardar el documento"}), 500
    
    @documents_bp.route('/<int:doc_id>/versions', methods=['POST'])
    @jwt_required()
    def upload_new_version(doc_id):
        if 'file' not in request.files:
            return jsonify({"error": "No se encontró el archivo"}), 400
        file = request.files['file']
        user_id = g.current_user.id
        try:
            version = app.services['document_service'].add_new_version(doc_id, user_id, file)
            return jsonify({"message": "Nueva versión añadida exitosamente", "version_id": version.id}), 201
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            app.logger.error(f"Error al añadir nueva versión: {e}")
            return jsonify({"error": "Error interno al guardar la nueva versión"}), 500
    
    @documents_bp.route('/versions/<int:version_id>/download', methods=['GET'])
    @jwt_required()
    def download_version(version_id):
        version = app.services['document_service'].get_document_version(version_id)
        try:
            directory = os.path.dirname(version.filepath)
            filename = os.path.basename(version.filepath)
            return send_from_directory(directory, filename, as_attachment=True)
        except FileNotFoundError:
            return jsonify({"error": "Archivo no encontrado en el servidor."}), 404
    
    app.register_blueprint(documents_bp)
    
    # --- RUTAS PARA MENSAJERÍA CORPORATIVA (LAN-C8T) ---
    messaging_bp = Blueprint('messaging', __name__, url_prefix='/api/messaging')
    
    @messaging_bp.route('/channels', methods=['GET'])
    @jwt_required()
    def get_channels():
        user_id = g.current_user.id
        tenant_id = g.current_user.tenant_id
        channels = app.services['messaging_service'].get_user_channels(user_id, tenant_id)
        return jsonify([{'id': c.id, 'name': c.name, 'description': c.description, 'type': c.channel_type} for c in channels])
    
    @messaging_bp.route('/channels', methods=['POST'])
    @jwt_required()
    def create_messaging_channel():
        data = request.get_json()
        name = data.get('name')
        description = data.get('description', '')
        channel_type = data.get('type', 'public')
        tenant_id = g.current_user.tenant_id
        creator_id = g.current_user.id
        try:
            channel = app.services['messaging_service'].create_channel(name, description, channel_type, tenant_id, creator_id)
            return jsonify({'message': 'Canal creado exitosamente', 'channel_id': channel.id}), 201
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
    
    @messaging_bp.route('/channels/<int:channel_id>/messages', methods=['GET'])
    @jwt_required()
    def get_channel_messages(channel_id):
        messages = app.services['messaging_service'].get_messages_for_channel(channel_id)
        messages.reverse()
        return jsonify([{
            'id': m.id,
            'content': m.content,
            'author': m.author.full_name if m.author else 'Usuario Desconocido',
            'user_id': m.user_id,
            'created_at': m.created_at.isoformat()
        } for m in messages])
    
    @messaging_bp.route('/channels/<int:channel_id>/messages', methods=['POST'])
    @jwt_required()
    def post_channel_message(channel_id):
        data = request.get_json()
        content = data.get('content')
        user_id = g.current_user.id
        try:
            message = app.services['messaging_service'].post_message(channel_id, user_id, content)
            return jsonify({'message': 'Mensaje enviado exitosamente', 'message_id': message.id}), 201
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
    
    app.register_blueprint(messaging_bp)
    
    # --- RUTAS PARA FIRMAR (LAN-SGN3) ---
    sign_bp = Blueprint('signer', __name__, url_prefix='/api/signer')
    
    @sign_bp.route('/templates', methods=['GET'])
    @jwt_required()
    def get_sign_templates():
        templates = app.services['sign_service'].get_templates_for_tenant(g.current_user.tenant_id)
        return jsonify([{'id': t.id, 'name': t.name, 'description': t.description} for t in templates])
    
    @sign_bp.route('/templates', methods=['POST'])
    @jwt_required()
    def create_sign_template():
        data = request.get_json()
        try:
            template = app.services['sign_service'].create_template(
                name=data.get('name'),
                description=data.get('description'),
                content=data.get('content'),
                tenant_id=g.current_user.tenant_id,
                user_id=g.current_user.id
            )
            return jsonify({'message': 'Plantilla creada exitosamente', 'template_id': template.id}), 201
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
    
    @sign_bp.route('/requests', methods=['GET'])
    @jwt_required()
    def get_sign_requests():
        requests = app.services['sign_service'].get_signature_requests(g.current_user.tenant_id)
        return jsonify([{
            'id': r.id,
            'signer_name': r.signer_name,
            'signer_email': r.signer_email,
            'status': r.status,
            'created_at': r.created_at.isoformat()
        } for r in requests])
    
    @sign_bp.route('/requests', methods=['POST'])
    @jwt_required()
    def create_sign_request():
        data = request.get_json()
        try:
            req = app.services['sign_service'].create_signature_request(
                template_id=data.get('template_id'),
                signer_name=data.get('signer_name'),
                signer_email=data.get('signer_email'),
                data_payload=data.get('payload', {}),
                tenant_id=g.current_user.tenant_id,
                user_id=g.current_user.id
            )
            if data.get('send_now', False):
                app.services['sign_service'].send_signature_request(req.id)
            return jsonify({'message': 'Solicitud de firma creada', 'request_id': req.id}), 201
        except Exception as e:
            return jsonify({'error': f'Error al crear la solicitud: {str(e)}'}), 500
    
    @sign_bp.route('/public/request/<string:token>', methods=['GET'])
    def get_public_sign_request(token):
        try:
            req = app.services['sign_service'].get_request_by_token(token)
            if req.status not in ['sent', 'viewed']:
                return jsonify({'error': 'Esta solicitud de firma ya no es válida o ha sido completada.'}), 410
            if req.status == 'sent':
                req.status = 'viewed'
                db.session.commit()
            return jsonify({
                'signer_name': req.signer_name,
                'document_content': req.final_document_content,
                'status': req.status
            })
        except Exception:
            return jsonify({'error': 'Solicitud de firma no encontrada o inválida.'}), 404
    
    @sign_bp.route('/public/request/<string:token>/sign', methods=['POST'])
    def sign_public_document(token):
        data = request.get_json()
        signature_data = data.get('signature_data')
        if not signature_data:
            return jsonify({'error': 'No se proporcionaron datos de firma.'}), 400
        try:
            app.services['sign_service'].sign_document(token, signature_data)
            return jsonify({'message': 'Documento firmado exitosamente.'}), 200
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception:
            return jsonify({'error': 'No se pudo completar la firma.'}), 500
    
    app.register_blueprint(sign_bp)
    
    # --- RUTAS PARA FORMULARIOS (LAN-FRM5) ---
    forms_bp = Blueprint('forms', __name__, url_prefix='/api/forms')
    
    @forms_bp.route('/', methods=['GET'])
    @jwt_required()
    def get_forms():
        forms = app.services['form_service'].get_forms_for_tenant(g.current_user.tenant_id)
        return jsonify([{'id': f.id, 'name': f.name, 'public_token': f.public_token} for f in forms])
    
    @forms_bp.route('/', methods=['POST'])
    @jwt_required()
    def create_form_route():
        data = request.get_json()
        try:
            form = app.services['form_service'].create_form(
                name=data.get('name'),
                description=data.get('description'),
                fields=data.get('fields', []),
                tenant_id=g.current_user.tenant_id,
                user_id=g.current_user.id
            )
            return jsonify({'message': 'Formulario creado exitosamente', 'form_id': form.id, 'public_token': form.public_token}), 201
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
    
    @forms_bp.route('/<int:form_id>/submissions', methods=['GET'])
    @jwt_required()
    def get_form_submissions(form_id):
        submissions = app.services['form_service'].get_submissions_for_form(form_id, g.current_user.tenant_id)
        return jsonify([{'id': s.id, 'data': s.data, 'submitted_at': s.submitted_at.isoformat()} for s in submissions])
    
    @forms_bp.route('/public/<string:token>', methods=['GET'])
    def get_public_form(token):
        try:
            form = app.services['form_service'].get_form_by_token(token)
            return jsonify({
                'name': form.name,
                'description': form.description,
                'fields': form.fields
            })
        except Exception:
            return jsonify({'error': 'Formulario no encontrado.'}), 404
    
    @forms_bp.route('/public/<string:token>/submit', methods=['POST'])
    def submit_public_form(token):
        data = request.get_json()
        try:
            app.services['form_service'].submit_form(token, data)
            return jsonify({'message': 'Formulario enviado exitosamente.'}), 200
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception:
            return jsonify({'error': 'No se pudo procesar el envío.'}), 500
    
    app.register_blueprint(forms_bp)
    
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
    
    # --- RUTAS PARA SOPORTE TÉCNICO (LAN-SOP1) ---
    support_bp = Blueprint('support', __name__, url_prefix='/api/support')
    
    @support_bp.route('/tickets', methods=['GET'])
    @jwt_required()
    def get_tickets():
        user_role = g.current_user.role.name if g.current_user.role else 'Cliente'
        tickets = app.services['support_service'].get_tickets_for_tenant(g.current_user.tenant_id, user_role, g.current_user.id)
        return jsonify([{'id': t.id, 'subject': t.subject, 'status': t.status, 'priority': t.priority, 'updated_at': t.updated_at.isoformat()} for t in tickets])
    
    @support_bp.route('/tickets', methods=['POST'])
    @jwt_required()
    def create_ticket_route():
        data = request.get_json()
        try:
            ticket = app.services['support_service'].create_ticket(
                subject=data.get('subject'),
                description=data.get('description'),
                priority=data.get('priority', 'Media'),
                tenant_id=g.current_user.tenant_id,
                user_id=g.current_user.id
            )
            return jsonify({'message': 'Ticket creado exitosamente', 'ticket_id': ticket.id}), 201
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
    
    @support_bp.route('/tickets/<int:ticket_id>', methods=['GET'])
    @jwt_required()
    def get_ticket_details_route(ticket_id):
        ticket = app.services['support_service'].get_ticket_details(ticket_id, g.current_user.tenant_id)
        return jsonify({
            'id': ticket.id,
            'subject': ticket.subject,
            'description': ticket.description,
            'status': ticket.status,
            'priority': ticket.priority,
            'updates': [{'id': u.id, 'comment': u.comment, 'author': u.author.full_name, 'created_at': u.created_at.isoformat()} for u in ticket.updates]
        })
    
    @support_bp.route('/tickets/<int:ticket_id>/updates', methods=['POST'])
    @jwt_required()
    def add_ticket_update_route(ticket_id):
        data = request.get_json()
        try:
            update = app.services['support_service'].add_ticket_update(
                ticket_id=ticket_id,
                user_id=g.current_user.id,
                comment=data.get('comment')
            )
            return jsonify({'message': 'Actualización añadida al ticket', 'update_id': update.id}), 201
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
    
    @support_bp.route('/tickets/<int:ticket_id>/assign', methods=['PUT'])
    @jwt_required()
    @role_required(['Administrador General', 'Soporte'])
    def assign_ticket_route(ticket_id):
        data = request.get_json()
        assignee_id = data.get('assignee_id')
        try:
            ticket = app.services['support_service'].assign_ticket(ticket_id, assignee_id, g.current_user.tenant_id)
            return jsonify({'message': f'Ticket asignado a usuario {assignee_id}', 'ticket_id': ticket.id})
        except Exception as e:
            return jsonify({'error': str(e)}), 404
    
    @support_bp.route('/tickets/<int:ticket_id>/status', methods=['PUT'])
    @jwt_required()
    @role_required(['Administrador General', 'Soporte'])
    def change_ticket_status_route(ticket_id):
        data = request.get_json()
        try:
            ticket = app.services['support_service'].change_ticket_status(ticket_id, data.get('status'), g.current_user.tenant_id)
            return jsonify({'message': 'Estado del ticket actualizado', 'new_status': ticket.status})
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
    
    app.register_blueprint(support_bp)
    
    # --- RUTAS PARA ACTIVOS FIJOS (LAN-AFX4) ---
    assets_bp = Blueprint('assets', __name__, url_prefix='/api/assets')
    
    @assets_bp.route('/', methods=['GET'])
    @jwt_required()
    @role_required(['Contador', 'Administrador General'])
    def get_assets():
        assets = app.services['asset_service'].get_assets_for_tenant(g.current_user.tenant_id)
        return jsonify([{'id': a.id, 'name': a.name, 'purchase_cost': a.purchase_cost, 'status': a.status} for a in assets])
    
    @assets_bp.route('/', methods=['POST'])
    @jwt_required()
    @role_required(['Contador', 'Administrador General'])
    def create_asset_route():
        data = request.get_json()
        try:
            asset = app.services['asset_service'].create_asset(
                name=data.get('name'),
                description=data.get('description'),
                purchase_date=date.fromisoformat(data.get('purchase_date')),
                purchase_cost=data.get('purchase_cost'),
                useful_life=data.get('useful_life'),
                salvage_value=data.get('salvage_value', 0),
                tenant_id=g.current_user.tenant_id
            )
            return jsonify({'message': 'Activo fijo creado exitosamente', 'asset_id': asset.id}), 201
        except (ValueError, TypeError) as e:
            return jsonify({'error': str(e)}), 400
    
    @assets_bp.route('/<int:asset_id>', methods=['GET'])
    @jwt_required()
    @role_required(['Contador', 'Administrador General'])
    def get_asset_details_route(asset_id):
        asset = app.services['asset_service'].get_asset_details(asset_id, g.current_user.tenant_id)
        book_value = app.services['asset_service'].get_asset_book_value(asset_id, g.current_user.tenant_id)
        return jsonify({
            'id': asset.id,
            'name': asset.name,
            'description': asset.description,
            'purchase_cost': asset.purchase_cost,
            'book_value': book_value,
            'depreciation_entries': [{'id': e.id, 'entry_date': e.entry_date.isoformat(), 'amount': e.amount} for e in asset.depreciation_entries]
        })
    
    @assets_bp.route('/<int:asset_id>/depreciate', methods=['POST'])
    @jwt_required()
    @role_required(['Contador', 'Administrador General'])
    def depreciate_asset_route(asset_id):
        try:
            entry = app.services['asset_service'].calculate_monthly_depreciation(asset_id, g.current_user.tenant_id)
            return jsonify({'message': 'Depreciación calculada exitosamente', 'entry_id': entry.id, 'amount': entry.amount}), 201
        except (ValueError, NotImplementedError) as e:
            return jsonify({'error': str(e)}), 400
    
    app.register_blueprint(assets_bp)
    
    # --- RUTAS PARA CAJA Y BANCOS (LAN-CB2) ---
    cash_and_banks_bp = Blueprint('cash_and_banks', __name__, url_prefix='/api/cash_and_banks')
    
    @cash_and_banks_bp.route('/accounts', methods=['GET'])
    @jwt_required()
    @role_required(['Contador', 'Administrador General'])
    def get_bank_accounts():
        return jsonify([]), 200
    
    app.register_blueprint(cash_and_banks_bp)
    
    # --- RUTAS PARA IMPUESTOS (LAN-TAX1) ---
    tax_bp = Blueprint('tax', __name__, url_prefix='/api/tax')
    
    @tax_bp.route('/types', methods=['GET'])
    @jwt_required()
    @role_required(['Contador', 'Administrador General'])
    def get_tax_types():
        return jsonify([]), 200
    
    app.register_blueprint(tax_bp)
    
    # --- RUTAS PARA RECURSOS MATERIALES (LAN-RM1) ---
    material_bp = Blueprint('material', __name__, url_prefix='/api/material')
    
    @material_bp.route('/', methods=['GET'])
    @jwt_required()
    @role_required(['Administrador General'])
    def get_materials():
        return jsonify([]), 200
    
    app.register_blueprint(material_bp)
    
    # --- RUTAS PARA OBRAS Y CONSTRUCCIÓN (LAN-OBR5) ---
    construction_bp = Blueprint('construction', __name__, url_prefix='/api/construction')
    
    @construction_bp.route('/projects', methods=['GET'])
    @jwt_required()
    @role_required(['Administrador General'])
    def get_construction_projects():
        return jsonify([]), 200
    
    app.register_blueprint(construction_bp)
    
    # --- REGISTRO DE COMANDOS CLI ---
    @app.cli.command("init-db")
    def init_db_command():
        with app.app_context():
            db.create_all()
            click.echo("Base de datos inicializada.")
    
    # Error Handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"message": "Endpoint no encontrado"}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({"message": "Error interno del servidor"}), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5001)), debug=True)