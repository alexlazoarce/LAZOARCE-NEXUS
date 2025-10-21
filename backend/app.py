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
from sqlalchemy import func, Boolean, Date, DateTime, Float, Integer, String, Text, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship, backref
# Se asume PostgreSQL por JSONB, si no, se debe cambiar.
from sqlalchemy.dialects.postgresql import JSONB

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

class Role(db.Model):
    """Roles de usuario con soporte multi-tenant"""
    __tablename__ = 'role'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(80), nullable=False, index=True)
    description = db.Column(String(255))
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=True, index=True)
    is_active = db.Column(Boolean, default=True)
    users = db.relationship('User', secondary=user_roles, back_populates='roles_m2m')
    __table_args__ = (UniqueConstraint('name', 'tenant_id', name='_role_name_tenant_uc'),)

class User(db.Model):
    """Usuarios con autenticación y perfil completo"""
    __tablename__ = 'user'
    id = db.Column(Integer, primary_key=True)
    email = db.Column(String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(String(256), nullable=False)
    full_name = db.Column(String(120), nullable=True)
    is_active = db.Column(Boolean, default=True)
    last_login = db.Column(DateTime)
    created_at = db.Column(DateTime, default=func.current_timestamp())
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=True, index=True)
    role_id = db.Column(Integer, ForeignKey('role.id'), nullable=True)
    roles_m2m = db.relationship('Role', secondary=user_roles, back_populates='users')
    profile = db.relationship('ClientProfile', backref='user', uselist=False, cascade="all, delete-orphan")
    employee = db.relationship('Employee', backref='user', uselist=False, cascade="all, delete-orphan")
    applications = db.relationship('LoanApplication', backref='applicant', lazy='dynamic', cascade="all, delete-orphan")
    audit_logs = db.relationship('AuditLog', backref='user', lazy='dynamic', cascade="all, delete-orphan")
    def set_password(self, password): self.password_hash = generate_password_hash(password)
    def check_password(self, password): return check_password_hash(self.password_hash, password)
    @property
    def role(self):
        if self.role_id: return db.session.get(Role, self.role_id)
        return None

class ClientProfile(db.Model):
    """Perfil detallado de cliente"""
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
class ProductoCredito(LoanProduct): __mapper_args__ = {'polymorphic_identity': 'producto_credito'}
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
    applicant = db.relationship('User')

# --- Modelos Contables ---
class Account(db.Model): __tablename__ = 'account'; id = db.Column(Integer, primary_key=True)
class JournalEntry(db.Model): __tablename__ = 'journal_entry'; id = db.Column(Integer, primary_key=True)
class Transaction(db.Model): __tablename__ = 'transaction'; id = db.Column(Integer, primary_key=True)

# --- Modelos de RRHH ---
class Employee(db.Model): __tablename__ = 'employee'; id = db.Column(Integer, primary_key=True); salario_base=db.Column(Float)
class Empleado(Employee): __mapper_args__ = {'polymorphic_identity': 'empleado'}
class PaySlip(db.Model):
    __tablename__ = 'payslip'
    id = db.Column(Integer, primary_key=True)
    isss=db.Column(Float)
    afp=db.Column(Float)
    renta=db.Column(Float)
    salario_neto=db.Column(Float)
    salario_base=db.Column(Float)
    employee_id = db.Column(Integer, ForeignKey('employee.id'))
class Planilla(PaySlip): __mapper_args__ = {'polymorphic_identity': 'planilla'}

# --- Modelos de Firma y Contratos (Integración) ---
class Cliente(db.Model):
    __tablename__ = 'cliente'
    id = db.Column(Integer, primary_key=True)
    contrato_integracion_id = db.Column(String(50), ForeignKey('contrato_integracion.contrato_id'))
    contrato_integracion = relationship("ContratoIntegracion", back_populates="clientes", foreign_keys=[contrato_integracion_id])
class ContratoIntegracion(db.Model):
    __tablename__ = 'contrato_integracion'
    id = db.Column(Integer, primary_key=True)
    contrato_id = db.Column(String(50), unique=True)
    clientes = relationship("Cliente", back_populates="contrato_integracion")
class FirmaElectronica(db.Model): __tablename__ = 'firma_electronica'; id = db.Column(Integer, primary_key=True)
class CertificadoValidacion(db.Model): __tablename__='certificado_validacion'; id=db.Column(Integer, primary_key=True)

# --- Modelos de Módulos ---
class ContractTemplate(db.Model): __tablename__='contract_template'; id=db.Column(Integer, primary_key=True)
class GeneratedContract(db.Model): __tablename__='generated_contract'; id=db.Column(Integer, primary_key=True)
class Contact(db.Model): __tablename__='crm_contact'; id=db.Column(Integer, primary_key=True)
class Interaction(db.Model): __tablename__='crm_interaction'; id=db.Column(Integer, primary_key=True)
class Opportunity(db.Model): __tablename__='crm_opportunity'; id=db.Column(Integer, primary_key=True)
class Product(db.Model): __tablename__='inventory_product'; id=db.Column(Integer, primary_key=True)
class StockMovement(db.Model): __tablename__='inventory_stock_movement'; id=db.Column(Integer, primary_key=True)
class Quote(db.Model): __tablename__='sales_quote'; id=db.Column(Integer, primary_key=True)
class SalesOrder(db.Model): __tablename__='sales_order'; id=db.Column(Integer, primary_key=True)
class SalesOrderItem(db.Model): __tablename__='sales_order_item'; id=db.Column(Integer, primary_key=True)
class Supplier(db.Model): __tablename__='purchasing_supplier'; id=db.Column(Integer, primary_key=True)
class PurchaseOrder(db.Model): __tablename__='purchasing_order'; id=db.Column(Integer, primary_key=True)
class PurchaseOrderItem(db.Model): __tablename__='purchasing_order_item'; id=db.Column(Integer, primary_key=True)
class EmailLog(db.Model): __tablename__='email_log'; id=db.Column(Integer, primary_key=True)
class Document(db.Model): __tablename__='document'; id=db.Column(Integer, primary_key=True)
class DocumentVersion(db.Model): __tablename__='document_version'; id=db.Column(Integer, primary_key=True)
class Channel(db.Model): __tablename__='messaging_channel'; id=db.Column(Integer, primary_key=True)
class Message(db.Model): __tablename__='messaging_message'; id=db.Column(Integer, primary_key=True)
class SignableTemplate(db.Model): __tablename__='sign_template'; id=db.Column(Integer, primary_key=True)
class SignatureRequest(db.Model): __tablename__='sign_request'; id=db.Column(Integer, primary_key=True)
class Form(db.Model): __tablename__='form'; id=db.Column(Integer, primary_key=True)
class FormSubmission(db.Model): __tablename__='form_submission'; id=db.Column(Integer, primary_key=True)
class Project(db.Model): __tablename__ = 'project'; id = db.Column(Integer, primary_key=True)
class Task(db.Model): __tablename__ = 'task'; id = db.Column(Integer, primary_key=True)
class Ticket(db.Model): __tablename__ = 'ticket'; id = db.Column(Integer, primary_key=True); updates = db.relationship('TicketUpdate')
class TicketUpdate(db.Model): __tablename__ = 'ticket_update'; id = db.Column(Integer, primary_key=True); author = db.relationship('User')
class FixedAsset(db.Model): __tablename__ = 'fixed_asset'; id = db.Column(Integer, primary_key=True); name=db.Column(String); purchase_cost=db.Column(Float); status=db.Column(String); depreciation_entries=db.relationship('DepreciationEntry')
class DepreciationEntry(db.Model): __tablename__ = 'depreciation_entry'; id = db.Column(Integer, primary_key=True); entry_date=db.Column(Date); amount=db.Column(Float)
class MailingList(db.Model): __tablename__='mailing_list'; id=db.Column(Integer, primary_key=True)
class AuditLog(db.Model): __tablename__='audit_log'; id=db.Column(Integer, primary_key=True)
class NotificationTemplate(db.Model): __tablename__='notification_template'; id=db.Column(Integer, primary_key=True)
# Nuevos modelos para Caja y Bancos
class BankAccount(db.Model): __tablename__='bank_account'; id=db.Column(Integer, primary_key=True)
class BankTransaction(db.Model): __tablename__='bank_transaction'; id=db.Column(Integer, primary_key=True)
class CashBox(db.Model): __tablename__='cash_box'; id=db.Column(Integer, primary_key=True)
class CashTransaction(db.Model): __tablename__='cash_transaction'; id=db.Column(Integer, primary_key=True)

# === MOCK DE SERVICIOS Y UTILIDADES ===
class MockService:
    def __init__(self, name): self.name = name
    def __call__(self, *args, **kwargs): return self
    def send_email(self, *args, **kwargs): return True, "OK"
    def log_action(self, *args, **kwargs): pass
    def get_asset_details(self, *args, **kwargs): class A: id=1; name='A1'; description='D'; purchase_cost=1000; depreciation_entries=[]; return A()
    def get_asset_book_value(self, *args, **kwargs): return 900
    def get_assets_for_tenant(self, *args, **kwargs): class A: id=1; name='A1'; purchase_cost=1000; status='Active'; return [A()]
    def create_asset(self, *args, **kwargs): class A: id=2; return A()
    def calculate_monthly_depreciation(self, *args, **kwargs): class E: id=3; amount=100; return E()
    def get_projects_for_tenant(self, *args, **kwargs): class P: id=1; name='P1'; status='In Progress'; end_date=datetime.now().date(); return [P()]
    def create_project(self, *args, **kwargs): class P: id=2; return P()
    def get_project_details(self, *args, **kwargs): class P: id=1; name='P1'; description='D'; status='In Progress'; budget=100; return P()
    def get_tasks_for_project(self, *args, **kwargs): class T: id=1; title='T1'; status='To Do'; due_date=datetime.now().date(); return [T()]
    def create_task(self, *args, **kwargs): class T: id=2; return T()
    def update_task_status(self, *args, **kwargs): class T: id=1; status='Done'; return T()
    def get_tickets_for_tenant(self, *args, **kwargs): class T: id=1; subject='S1'; status='Open'; priority='High'; updated_at=datetime.utcnow(); return [T()]
    def create_ticket(self, *args, **kwargs): class T: id=2; return T()
    def get_ticket_details(self, *args, **kwargs): class T: id=1; subject='S1'; description='D'; status='Open'; priority='High'; updates=[]; return T()
    def add_ticket_update(self, *args, **kwargs): class U: id=3; return U()
    def assign_ticket(self, *args, **kwargs): class T: id=1; return T()
    def change_ticket_status(self, *args, **kwargs): class T: id=1; status='Closed'; return T()

def validacion_identidad_estricta(data): return True
def capturar_datos_biometricos(): return {"biometric_data": "hash"}
def generar_contrato_integracion(data): return "CONTRATO-123"
def firma_electronica_avanzada(contrato_id, data, datos_biometricos): return {"valida": True, "firma_id": "FIRMA-456"}
def calcular_planilla(salario_base): return {'success': True, 'salario_base': salario_base, 'isss': 100, 'afp': 100, 'renta': 50, 'salario_neto': salario_base-250}

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
        UPLOAD_FOLDER=os.path.join(app.instance_path, 'uploads')
    )
    if testing_config: app.config.from_mapping(testing_config)
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Inicialización de extensiones
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        # Carga de modelos y servicios
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
            'BankAccount': BankAccount, 'BankTransaction': BankTransaction, 'CashBox': CashBox, 'CashTransaction': CashTransaction
        }
        app.services = {
            'audit_service': MockService('Audit'), 'contract_service': MockService('Contract'),
            'crm_service': MockService('CRM'), 'inventory_service': MockService('Inventory'),
            'sales_service': MockService('Sales'), 'purchasing_service': MockService('Purchasing'),
            'email_service': MockService('Email'), 'document_service': MockService('Document'),
            'accounting_service': MockService('Accounting'), 'messaging_service': MockService('Messaging'),
            'sign_service': MockService('Sign'), 'form_service': MockService('Form'),
            'project_service': MockService('Project'), 'support_service': MockService('Support'),
            'asset_service': MockService('Asset')
        }

    # Decorador de autorización
    def role_required(required_roles):
        if not isinstance(required_roles, list): required_roles = [required_roles]
        def decorator(fn):
            @wraps(fn)
            @jwt_required()
            def wrapper(*args, **kwargs):
                claims = get_jwt()
                user_roles = set(claims.get('roles', []))
                user_identity = get_jwt_identity()
                g.current_user = app.models['User'].query.filter_by(email=user_identity).first()
                if not g.current_user: return jsonify({"msg": "Usuario no encontrado"}), 404
                if g.current_user.role: user_roles.add(g.current_user.role.name)
                if not any(role in user_roles for role in required_roles):
                    return jsonify({"msg": "Acceso no autorizado para este rol"}), 403
                return fn(*args, **kwargs)
            return wrapper
        return decorator

    # Rutas base
    @app.route('/api/health')
    def health_check(): return jsonify({"status": "healthy"})
    
    @app.route('/api/login', methods=['POST'])
    def login():
        data = request.get_json()
        user = app.models['User'].query.filter_by(email=data.get('email')).first()
        if user and user.check_password(data.get('password')):
            user_roles = [r.name for r in user.roles_m2m] + ([user.role.name] if user.role else [])
            if not user_roles: user_roles = ['Cliente']
            access_token = create_access_token(identity=user.email, additional_claims={'roles': list(set(user_roles)), 'user_id': user.id, 'tenant_id': user.tenant_id})
            return jsonify(access_token=access_token)
        return jsonify({"msg": "Credenciales inválidas"}), 401
    
    # --- BLUEPRINTS PARA MÓDULOS ---
    
    # --- RUTAS PARA GESTIÓN DE PROYECTOS (LAN-PR0) ---
    projects_bp = Blueprint('projects', __name__, url_prefix='/api/projects')
    @projects_bp.route('/', methods=['GET'])
    @jwt_required()
    def get_projects():
        # ... Lógica de la ruta
        return jsonify([])
    # ... (Otras rutas de projects)
    app.register_blueprint(projects_bp)

    # --- RUTAS PARA SOPORTE TÉCNICO (LAN-SOP1) ---
    support_bp = Blueprint('support', __name__, url_prefix='/api/support')
    @support_bp.route('/tickets', methods=['GET'])
    @jwt_required()
    def get_tickets():
        # ... Lógica de la ruta
        return jsonify([])
    # ... (Otras rutas de support)
    app.register_blueprint(support_bp)

    # --- RUTAS PARA ACTIVOS FIJOS (LAN-AFX4) ---
    assets_bp = Blueprint('assets', __name__, url_prefix='/api/assets')
    @assets_bp.route('/', methods=['GET'])
    @jwt_required()
    def get_assets():
        # ... Lógica de la ruta
        return jsonify([])
    # ... (Otras rutas de assets)
    app.register_blueprint(assets_bp)

    # Comando CLI
    @app.cli.command("init-db")
    def init_db_command():
        with app.app_context():
            db.create_all()
            click.echo("Base de datos inicializada.")

    # Error Handlers
    @app.errorhandler(404)
    def not_found(error): return jsonify({"message": "Endpoint no encontrado"}), 404
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({"message": "Error interno del servidor"}), 500

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5001)), debug=True)

