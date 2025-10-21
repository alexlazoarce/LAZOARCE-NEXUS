import os
import click
from functools import wraps
from flask import Flask, jsonify, request, g, Blueprint, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta
from sqlalchemy import func, Boolean, Date, DateTime, Float, Integer, String, Text, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship, backref
# Se asume PostgreSQL por JSONB, si no, se debe cambiar. Usaré Text como fallback.
from sqlalchemy.dialects.postgresql import JSONB

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
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=True, index=True)
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

    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=True, index=True)
    role_id = db.Column(Integer, ForeignKey('role.id'), nullable=True)

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
    """Perfil detallado de cliente"""
    __tablename__ = 'client_profile'
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(Integer, ForeignKey('user.id'), unique=True, nullable=False)
    full_name = db.Column(String(120))
    phone_number = db.Column(String(20))
    address = db.Column(Text)
    birth_date = db.Column(Date)
    occupation = db.Column(String(100))
    monthly_income = db.Column(Float)

class LoanProduct(db.Model):
    """Productos de préstamo configurables"""
    __tablename__ = 'loan_product'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(100), nullable=False, index=True)
    tenant_id = db.Column(Integer, ForeignKey('tenant.id'), nullable=False, index=True)
    # ... (el resto de las columnas y relaciones de LoanProduct)

class ProductoCredito(LoanProduct):
    __mapper_args__ = {'polymorphic_identity': 'producto_credito'}

class LoanApplication(db.Model):
    """Solicitudes de préstamo"""
    __tablename__ = 'loan_application'
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(Integer, ForeignKey('user.id'), nullable=False, index=True)
    product_id = db.Column(Integer, ForeignKey('loan_product.id'), nullable=False, index=True)
    # ... (el resto de las columnas y relaciones de LoanApplication)

class Account(db.Model):
    """Plan de cuentas contable"""
    __tablename__ = 'account'
    id = db.Column(Integer, primary_key=True)
    # ... (el resto de las columnas y relaciones de Account)

class JournalEntry(db.Model):
    """Asiento contable (Encabezado)"""
    __tablename__ = 'journal_entry'
    id = db.Column(Integer, primary_key=True)
    # ... (el resto de las columnas y relaciones de JournalEntry)

class Transaction(db.Model):
    """Movimiento contable individual (Detalle)"""
    __tablename__ = 'transaction'
    id = db.Column(Integer, primary_key=True)
    # ... (el resto de las columnas y relaciones de Transaction)

class Employee(db.Model):
    """Empleados y personal"""
    __tablename__ = 'employee'
    id = db.Column(Integer, primary_key=True)
    salary = db.Column(Float)
    # ... (el resto de las columnas y relaciones de Employee)

class Empleado(Employee):
    __mapper_args__ = {'polymorphic_identity': 'empleado'}

class PaySlip(db.Model):
    """Planillas de pago"""
    __tablename__ = 'payslip'
    id = db.Column(Integer, primary_key=True)
    # ... (el resto de las columnas y relaciones de PaySlip)

class Planilla(PaySlip):
    __mapper_args__ = {'polymorphic_identity': 'planilla'}

class Payment(db.Model):
    """Pagos de un préstamo"""
    __tablename__ = 'payment'
    id = db.Column(Integer, primary_key=True)
    loan_application_id = db.Column(Integer, ForeignKey('loan_application.id'))
    # ... (el resto de las columnas y relaciones de Payment)


class Cliente(db.Model):
    """Perfil de Cliente para Firma Electrónica"""
    __tablename__ = 'cliente'
    id = db.Column(Integer, primary_key=True)
    contrato_integracion_id = db.Column(String(50), ForeignKey('contrato_integracion.contrato_id'))
    firma_electronica_id = db.Column(String(50), ForeignKey('firma_electronica.firma_id'))
    contrato_integracion = relationship("ContratoIntegracion", back_populates="clientes", foreign_keys=[contrato_integracion_id])
    firma_electronica = relationship("FirmaElectronica", back_populates="clientes", foreign_keys=[firma_electronica_id])
    # ... (el resto de las columnas y relaciones de Cliente)

class ContratoIntegracion(db.Model):
    """Contrato de Integración para Firma"""
    __tablename__ = 'contrato_integracion'
    id = db.Column(Integer, primary_key=True)
    contrato_id = db.Column(String(50), unique=True, nullable=False)
    clientes = relationship("Cliente", back_populates="contrato_integracion")
    # ... (el resto de las columnas y relaciones de ContratoIntegracion)

class FirmaElectronica(db.Model):
    """Registro de Firma Electrónica"""
    __tablename__ = 'firma_electronica'
    id = db.Column(Integer, primary_key=True)
    firma_id = db.Column(String(50), unique=True, nullable=False)
    clientes = relationship("Cliente", back_populates="firma_electronica")
    # ... (el resto de las columnas y relaciones de FirmaElectronica)

class CertificadoValidacion(db.Model):
    """Certificado de Validación de Firma"""
    __tablename__ = 'certificado_validacion'
    id = db.Column(Integer, primary_key=True)
    # ... (el resto de las columnas y relaciones de CertificadoValidacion)


class ContractTemplate(db.Model): __tablename__='contract_template'; id=db.Column(Integer, primary_key=True) #...
class GeneratedContract(db.Model): __tablename__='generated_contract'; id=db.Column(Integer, primary_key=True) #...
class Contact(db.Model): __tablename__='crm_contact'; id=db.Column(Integer, primary_key=True) #...
class Interaction(db.Model): __tablename__='crm_interaction'; id=db.Column(Integer, primary_key=True) #...
class Opportunity(db.Model): __tablename__='crm_opportunity'; id=db.Column(Integer, primary_key=True) #...
class Product(db.Model): __tablename__='inventory_product'; id=db.Column(Integer, primary_key=True) #...
class StockMovement(db.Model): __tablename__='inventory_stock_movement'; id=db.Column(Integer, primary_key=True) #...
class Quote(db.Model): __tablename__='sales_quote'; id=db.Column(Integer, primary_key=True) #...
class SalesOrder(db.Model): __tablename__='sales_order'; id=db.Column(Integer, primary_key=True) #...
class SalesOrderItem(db.Model): __tablename__='sales_order_item'; id=db.Column(Integer, primary_key=True) #...
class Supplier(db.Model): __tablename__='purchasing_supplier'; id=db.Column(Integer, primary_key=True) #...
class PurchaseOrder(db.Model): __tablename__='purchasing_order'; id=db.Column(Integer, primary_key=True) #...
class PurchaseOrderItem(db.Model): __tablename__='purchasing_order_item'; id=db.Column(Integer, primary_key=True) #...
class EmailLog(db.Model): __tablename__='email_log'; id=db.Column(Integer, primary_key=True) #...
class Document(db.Model): __tablename__='document'; id=db.Column(Integer, primary_key=True) #...
class DocumentVersion(db.Model): __tablename__='document_version'; id=db.Column(Integer, primary_key=True) #...
class Channel(db.Model): __tablename__='channel'; id=db.Column(Integer, primary_key=True) #...
class Message(db.Model): __tablename__='message'; id=db.Column(Integer, primary_key=True) #...
class SignableTemplate(db.Model): __tablename__='sign_template'; id=db.Column(Integer, primary_key=True) #...
class SignatureRequest(db.Model): __tablename__='sign_request'; id=db.Column(Integer, primary_key=True) #...
class Form(db.Model): __tablename__='form'; id=db.Column(Integer, primary_key=True); fields = db.Column(JSONB, nullable=False, default=list) #...
class FormSubmission(db.Model): __tablename__='form_submission'; id=db.Column(Integer, primary_key=True); data = db.Column(JSONB, nullable=False) #...
class Project(db.Model): __tablename__ = 'project'; id = db.Column(Integer, primary_key=True); name = db.Column(String(150), nullable=False, index=True); #...
class Task(db.Model): __tablename__ = 'task'; id = db.Column(Integer, primary_key=True); title = db.Column(String(200), nullable=False); #...
class Ticket(db.Model): __tablename__ = 'ticket'; id = db.Column(Integer, primary_key=True); subject = db.Column(String(200), nullable=False); #...
class TicketUpdate(db.Model): __tablename__ = 'ticket_update'; id = db.Column(Integer, primary_key=True); #...
class MailingList(db.Model): __tablename__='mailing_list'; id=db.Column(Integer, primary_key=True) #...
class AuditLog(db.Model): __tablename__='audit_log'; id=db.Column(Integer, primary_key=True) #...
class NotificationTemplate(db.Model): __tablename__='notification_template'; id=db.Column(Integer, primary_key=True) #...

# === MOCK DE SERVICIOS Y UTILIDADES ===
class MockService:
    def __init__(self, name): self.name = name
    def __call__(self, *args, **kwargs): return self
    def send_email(self, recipient, subject, body, tenant): print(f"[{self.name}] Enviando email a {recipient}"); return True, "OK"
    # ... (resto de métodos mock abreviados) ...
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

jwt = JWTManager()
migrate = Migrate()

# --- APP FACTORY ---
def create_app(config_object=None, testing_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        JWT_SECRET_KEY='jwt-dev',
        SQLALCHEMY_DATABASE_URI='sqlite:///' + os.path.join(app.instance_path, 'app.sqlite'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        UPLOAD_FOLDER=os.path.join(app.instance_path, 'uploads')
    )
    if testing_config: app.config.from_mapping(testing_config)
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        app.models = {model.__name__: model for model in db.Model._decl_class_registry.values() if isinstance(model, type) and issubclass(model, db.Model) and hasattr(model, '__tablename__')}
        app.services = {
            'audit_service': MockService('Audit'), 'contract_service': MockService('Contract'),
            'crm_service': MockService('CRM'), 'inventory_service': MockService('Inventory'),
            'sales_service': MockService('Sales'), 'purchasing_service': MockService('Purchasing'),
            'email_service': MockService('Email'), 'document_service': MockService('Document'),
            'accounting_service': MockService('Accounting'), 'messaging_service': MockService('Messaging'),
            'sign_service': MockService('Sign'), 'form_service': MockService('Form'),
            'project_service': MockService('Project'), 'support_service': MockService('Support')
        }

    def role_required(required_roles):
        if not isinstance(required_roles, list): required_roles = [required_roles]
        def decorator(fn):
            @wraps(fn)
            @jwt_required()
            def wrapper(*args, **kwargs):
                claims = get_jwt()
                user_roles = set(claims.get('roles', []))
                if not any(role in user_roles for role in required_roles):
                    return jsonify({"msg": "Acceso no autorizado para este rol"}), 403
                g.current_user = app.models['User'].query.filter_by(email=get_jwt_identity()).first()
                return fn(*args, **kwargs)
            return wrapper
        return decorator

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
    
    projects_bp = Blueprint('projects', __name__, url_prefix='/api/projects')
    @projects_bp.route('/', methods=['GET'])
    @jwt_required()
    def get_projects():
        projects = app.services['project_service'].get_projects_for_tenant(g.current_user.tenant_id)
        return jsonify([{'id': p.id, 'name': p.name, 'status': p.status, 'end_date': p.end_date.isoformat() if p.end_date else None} for p in projects])
    # ... (resto de las rutas de projects_bp)
    app.register_blueprint(projects_bp)

    support_bp = Blueprint('support', __name__, url_prefix='/api/support')
    @support_bp.route('/tickets', methods=['GET'])
    @jwt_required()
    def get_tickets():
        user_role = g.current_user.role.name if g.current_user.role else 'Cliente'
        tickets = app.services['support_service'].get_tickets_for_tenant(g.current_user.tenant_id, user_role, g.current_user.id)
        return jsonify([{'id': t.id, 'subject': t.subject, 'status': t.status, 'priority': t.priority, 'updated_at': t.updated_at.isoformat()} for t in tickets])
    # ... (resto de las rutas de support_bp)
    app.register_blueprint(support_bp)

    @app.cli.command("init-db")
    def init_db_command():
        db.create_all()
        print("Base de datos inicializada.")

    @app.errorhandler(404)
    def not_found(error): return jsonify({"message": "Endpoint no encontrado"}), 404
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({"message": "Error interno del servidor"}), 500

    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get("PORT", 5001))
    app.run(host='0.0.0.0', port=port, debug=True)

