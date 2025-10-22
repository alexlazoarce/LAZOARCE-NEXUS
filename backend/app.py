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

# Importaciones de blueprints
try:
    from backend.routes.health_routes import health_bp
    # Using education_bp instead of school/university specific ones
    from backend.routes.education_routes import education_bp
    from backend.routes.logistics_routes import logistics_bp
    from backend.routes.cash_and_banks_routes import cash_and_banks_bp
    from backend.routes.tax_routes import tax_bp
    from backend.routes.material_routes import material_bp
    from backend.routes.construction_routes import construction_bp
    from backend.routes.restaurant_routes import restaurant_bp
    from backend.routes.commercial_kitchen_routes import commercial_kitchen_bp
    from backend.routes.field_routes import field_bp
    # Adding technical service blueprint from feature branch
    from backend.routes.technical_service_routes import technical_service_bp
except ImportError:
    # Fallback blueprints if imports fail
    health_bp = Blueprint('health', __name__, url_prefix='/api/health')
    education_bp = Blueprint('education', __name__, url_prefix='/api/education')
    logistics_bp = Blueprint('logistics', __name__, url_prefix='/api/logistics')
    cash_and_banks_bp = Blueprint('cash_and_banks', __name__, url_prefix='/api/cash_and_banks')
    tax_bp = Blueprint('tax', __name__, url_prefix='/api/tax')
    material_bp = Blueprint('material', __name__, url_prefix='/api/material')
    construction_bp = Blueprint('construction', __name__, url_prefix='/api/construction')
    restaurant_bp = Blueprint('restaurant', __name__, url_prefix='/api/restaurant')
    commercial_kitchen_bp = Blueprint('commercial_kitchen', __name__, url_prefix='/api/commercial_kitchen')
    field_bp = Blueprint('field', __name__, url_prefix='/api/field')
    technical_service_bp = Blueprint('technical_service', __name__, url_prefix='/api/technical')  # Added fallback

# Definición global de extensiones
db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()

# Importaciones de servicios (Asunciones del HEAD)
try:
    from .loan_calculator import calcular_prestamo_completo
    from .pdf_generator import create_contract_pdf, convert_html_to_pdf
    from .accounting_service import create_journal_entry
    from .firma_service import (
        validacion_identidad_estricta,
        capturar_datos_biometricos,
        generar_contrato_integracion,
        firma_electronica_avanzada
    )
    from .payroll_service import calcular_planilla
    class MockService:
        def log_action(*args, **kwargs): pass
    audit_service = MockService()
except ImportError as e:
    print(f"⚠️ Error importando servicios: {e}. Usando Mocks.")
    def mock_func(*args, **kwargs): pass
    calcular_prestamo_completo = create_journal_entry = validacion_identidad_estricta = capturar_datos_biometricos = generar_contrato_integracion = firma_electronica_avanzada = calcular_planilla = mock_func

# Tablas intermedias (Many-to-Many)
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

# Mock Models & Services
class MockModel:
    def __init__(self, **kwargs): pass
    @classmethod
    def query(cls): return cls()
    def filter_by(self, **kwargs): return self
    def first(self): return None
    def all(self): return []
    def get(self, id): return None
    def get_or_404(self, id): return None

Role = User = LoanProduct = LoanApplication = Account = Transaction = JournalEntry = Cliente = ContratoIntegracion = FirmaElectronica = CertificadoValidacion = ProductoCredito = Empleado = Planilla = ClientProfile = Tenant = AuditLog = Payment = NotificationTemplate = Employee = ContractTemplate = GeneratedContract = Contact = Interaction = Opportunity = Product = StockMovement = Quote = SalesOrder = SalesOrderItem = Supplier = PurchaseOrder = PurchaseOrderItem = EmailLog = MailingList = Document = DocumentVersion = Channel = Message = SignableTemplate = SignatureRequest = Form = FormSubmission = Project = Task = Ticket = TicketUpdate = FixedAsset = DepreciationEntry = BankAccount = BankTransaction = CashBox = CashTransaction = TaxType = TaxDeclaration = Material = MaterialRequest = ConstructionProject = BudgetItem = ProgressReport = Certification = RFI = Milestone = PatientRecord = MedicalAppointment = Prescription = LabOrder = Student = Course = Enrollment = Grade = Vehicle = Driver = Route = Delivery = MenuItem = Table = RestaurantOrder = RestaurantOrderItem = KitchenSpace = KitchenBooking = HACCPLog = FieldTask = TaskReport = ServiceJob = JobQuote = JobInvoice = MockModel

class MockService:
    def __init__(self, name):
        self.name = name
    def __call__(self, *args, **kwargs):
        return self
    def send_email(self, *args, **kwargs): return True, "OK"
    def log_action(self, *args, **kwargs): pass
    def get_asset_details(self, *args, **kwargs): return MockModel()
    def get_asset_book_value(self, *args, **kwargs): return 900
    def get_assets_for_tenant(self, *args, **kwargs): return [MockModel()]
    def create_asset(self, *args, **kwargs): return MockModel()
    def calculate_monthly_depreciation(self, *args, **kwargs): return MockModel()

# Function definitions
def validacion_identidad_estricta(data): return True
def capturar_datos_biometricos(): return {"biometric_data": "hash"}
def generar_contrato_integracion(data): return "CONTRATO-123"
def firma_electronica_avanzada(contrato_id, data, datos_biometricos): return {"valida": True, "firma_id": "FIRMA-456"}
def calcular_planilla(salario_base): return {'success': True, 'salario_base': salario_base, 'isss': 100, 'afp': 100, 'renta': 50, 'salario_neto': salario_base - 250}

# App factory
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
        JWT_ACCESS_TOKEN_EXPIRES=timedelta(hours=8),
        UPLOAD_FOLDER=os.path.join(app.instance_path, 'Uploads')
    )
    if config_object:
        app.config.from_object(config_object)
    if testing_config:
        app.config.from_mapping(testing_config)
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Inicialización de extensiones
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        # Intenta cargar modelos y servicios reales
        try:
            from .models import (
                Tenant, Role, User, ClientProfile, LoanProduct, LoanApplication, Payment,
                Account, JournalEntry, Transaction, Employee, PaySlip,
                Cliente, ContratoIntegracion, FirmaElectronica, CertificadoValidacion,
                ContractTemplate, GeneratedContract, Contact, Interaction, Opportunity,
                Product, StockMovement, Quote, SalesOrder, SalesOrderItem, Supplier,
                PurchaseOrder, PurchaseOrderItem, EmailLog, MailingList, Document, DocumentVersion,
                Channel, Message, SignableTemplate, SignatureRequest, Form, FormSubmission,
                Project, Task, Ticket, TicketUpdate, FixedAsset, DepreciationEntry,
                BankAccount, BankTransaction, CashBox, CashTransaction, TaxType, TaxDeclaration,
                Material, MaterialRequest, ConstructionProject, BudgetItem, ProgressReport, Certification, RFI, Milestone,
                PatientRecord, MedicalAppointment, Prescription, LabOrder,
                Student, Course, Enrollment, Grade,
                Vehicle, Driver, Route, Delivery,
                MenuItem, Table, RestaurantOrder, RestaurantOrderItem,
                KitchenSpace, KitchenBooking, HACCPLog,
                FieldTask, TaskReport,
                ServiceJob, JobQuote, JobInvoice,
                AuditLog, NotificationTemplate
            )
            from . import (
                audit_service, contract_service, crm_service, inventory_service,
                sales_service, purchasing_service, email_service, document_service,
                messaging_service, sign_service, form_service, project_service,
                support_service, asset_service, tax_service, material_service,
                construction_service, health_service, education_service, logistics_service,
                restaurant_service, commercial_kitchen_service, field_service, technical_service,
                accounting_service
            )
            app.services = {
                'audit_service': audit_service,
                'contract_service': contract_service,
                'crm_service': crm_service,
                'inventory_service': inventory_service,
                'sales_service': sales_service,
                'purchasing_service': purchasing_service,
                'email_service': email_service,
                'document_service': document_service,
                'messaging_service': messaging_service,
                'sign_service': sign_service,
                'form_service': form_service,
                'project_service': project_service,
                'support_service': support_service,
                'asset_service': asset_service,
                'tax_service': tax_service,
                'material_service': material_service,
                'construction_service': construction_service,
                'health_service': health_service,
                'education_service': education_service,
                'logistics_service': logistics_service,
                'restaurant_service': restaurant_service,
                'commercial_kitchen_service': commercial_kitchen_service,
                'field_service': field_service,
                'technical_service': technical_service,
                'accounting_service': accounting_service
            }
            app.models = {
                'Tenant': Tenant, 'Role': Role, 'User': User, 'ClientProfile': ClientProfile,
                'LoanProduct': LoanProduct, 'LoanApplication': LoanApplication, 'Payment': Payment,
                'Account': Account, 'JournalEntry': JournalEntry, 'Transaction': Transaction,
                'Employee': Employee, 'PaySlip': PaySlip, 'Cliente': Cliente,
                'ContratoIntegracion': ContratoIntegracion, 'FirmaElectronica': FirmaElectronica, 'CertificadoValidacion': CertificadoValidacion,
                'ContractTemplate': ContractTemplate, 'GeneratedContract': GeneratedContract,
                'Contact': Contact, 'Interaction': Interaction, 'Opportunity': Opportunity,
                'Product': Product, 'StockMovement': StockMovement,
                'Quote': Quote, 'SalesOrder': SalesOrder, 'SalesOrderItem': SalesOrderItem,
                'Supplier': Supplier, 'PurchaseOrder': PurchaseOrder, 'PurchaseOrderItem': PurchaseOrderItem,
                'EmailLog': EmailLog, 'MailingList': MailingList, 'Document': Document, 'DocumentVersion': DocumentVersion,
                'Channel': Channel, 'Message': Message,
                'SignableTemplate': SignableTemplate, 'SignatureRequest': SignatureRequest,
                'Form': Form, 'FormSubmission': FormSubmission,
                'Project': Project, 'Task': Task,
                'Ticket': Ticket, 'TicketUpdate': TicketUpdate,
                'FixedAsset': FixedAsset, 'DepreciationEntry': DepreciationEntry,
                'BankAccount': BankAccount, 'BankTransaction': BankTransaction, 'CashBox': CashBox, 'CashTransaction': CashTransaction,
                'TaxType': TaxType, 'TaxDeclaration': TaxDeclaration,
                'Material': Material, 'MaterialRequest': MaterialRequest,
                'ConstructionProject': ConstructionProject, 'BudgetItem': BudgetItem, 'ProgressReport': ProgressReport, 'Certification': Certification, 'RFI': RFI, 'Milestone': Milestone,
                'PatientRecord': PatientRecord, 'MedicalAppointment': MedicalAppointment, 'Prescription': Prescription, 'LabOrder': LabOrder,
                'Student': Student, 'Course': Course, 'Enrollment': Enrollment, 'Grade': Grade,
                'Vehicle': Vehicle, 'Driver': Driver, 'Route': Route, 'Delivery': Delivery,
                'MenuItem': MenuItem, 'Table': Table, 'RestaurantOrder': RestaurantOrder, 'RestaurantOrderItem': RestaurantOrderItem,
                'KitchenSpace': KitchenSpace, 'KitchenBooking': KitchenBooking, 'HACCPLog': HACCPLog,
                'FieldTask': FieldTask, 'TaskReport': TaskReport,
                'ServiceJob': ServiceJob, 'JobQuote': JobQuote, 'JobInvoice': JobInvoice,
                'AuditLog': AuditLog, 'NotificationTemplate': NotificationTemplate
            }
        except ImportError as e:
            app.logger.error(f"❌ Error al importar modelos/servicios reales: {e}. Se usarán Mocks.")
            app.services = {name: MockService(name.split('_')[0].capitalize()) for name in [
                'audit_service', 'contract_service', 'crm_service', 'inventory_service',
                'sales_service', 'purchasing_service', 'email_service', 'document_service',
                'messaging_service', 'sign_service', 'form_service', 'project_service',
                'support_service', 'asset_service', 'tax_service', 'material_service',
                'construction_service', 'health_service', 'education_service', 'logistics_service',
                'restaurant_service', 'commercial_kitchen_service', 'field_service',
                'technical_service', 'accounting_service'
            ]}
            model_keys = [
                'Tenant', 'Role', 'User', 'ClientProfile', 'LoanProduct', 'LoanApplication', 'Payment',
                'Account', 'JournalEntry', 'Transaction', 'Employee', 'PaySlip', 'Cliente',
                'ContratoIntegracion', 'FirmaElectronica', 'CertificadoValidacion',
                'ContractTemplate', 'GeneratedContract', 'Contact', 'Interaction', 'Opportunity',
                'Product', 'StockMovement', 'Quote', 'SalesOrder', 'SalesOrderItem', 'Supplier',
                'PurchaseOrder', 'PurchaseOrderItem', 'EmailLog', 'MailingList', 'Document', 'DocumentVersion',
                'Channel', 'Message', 'SignableTemplate', 'SignatureRequest', 'Form', 'FormSubmission',
                'Project', 'Task', 'Ticket', 'TicketUpdate', 'FixedAsset', 'DepreciationEntry',
                'BankAccount', 'BankTransaction', 'CashBox', 'CashTransaction', 'TaxType', 'TaxDeclaration',
                'Material', 'MaterialRequest', 'ConstructionProject', 'BudgetItem', 'ProgressReport', 'Certification', 'RFI', 'Milestone',
                'PatientRecord', 'MedicalAppointment', 'Prescription', 'LabOrder',
                'Student', 'Course', 'Enrollment', 'Grade', 'Vehicle', 'Driver', 'Route', 'Delivery',
                'MenuItem', 'Table', 'RestaurantOrder', 'RestaurantOrderItem', 'KitchenSpace', 'KitchenBooking', 'HACCPLog',
                'FieldTask', 'TaskReport', 'ServiceJob', 'JobQuote', 'JobInvoice',
                'AuditLog', 'NotificationTemplate'
            ]
            app.models = {key: MockModel for key in model_keys}

    # Decorador de autorización
    def role_required(required_roles):
        if not isinstance(required_roles, list):
            required_roles = [required_roles]
        def decorator(fn):
            @wraps(fn)
            @jwt_required()
            def wrapper(*args, **kwargs):
                claims = get_jwt()
                user_roles_from_claims = set(claims.get('roles', []))
                user_identity = get_jwt_identity()
                User_model = app.models.get('User', MockModel)
                g.current_user = User_model.query.filter_by(email=user_identity).first()
                if not g.current_user or g.current_user == MockModel:
                    if User_model == MockModel:
                        app.logger.warning("Using MockModel for User in role_required")
                        return jsonify({"msg": "Error interno: Modelo de Usuario no cargado"}), 500
                    return jsonify({"msg": "Usuario no encontrado"}), 404
                user_roles_combined = user_roles_from_claims
                if hasattr(g.current_user, 'role') and g.current_user.role:
                    user_roles_combined.add(g.current_user.role.name)
                if hasattr(g.current_user, 'roles_m2m'):
                    for role in g.current_user.roles_m2m:
                        user_roles_combined.add(role.name)
                if not any(role in user_roles_combined for role in required_roles):
                    return jsonify({"msg": "Acceso no autorizado para este rol"}), 403
                return fn(*args, **kwargs)
            return wrapper
        return decorator

    app.jinja_env.globals['role_required'] = role_required

    # Rutas base
    @app.route('/')
    def index():
        return jsonify({"message": "Servidor del Sistema de Gestión Financiera en funcionamiento.", "version": "2.1 (Fusion)"})

    @app.route('/api/health')
    def health_check():
        return jsonify({"status": "healthy"})

    @app.route('/api/login', methods=['POST'])
    def login():
        data = request.get_json()
        User_model = app.models.get('User', MockModel)
        if User_model == MockModel:
            return jsonify({"msg": "Error interno: Modelo de Usuario no cargado"}), 500
        user = User_model.query.filter_by(email=data.get('email')).first()
        if user and user.check_password(data.get('password')):
            user_roles = set()
            if hasattr(user, 'role') and user.role:
                user_roles.add(user.role.name)
            if hasattr(user, 'roles_m2m'):
                for role in user.roles_m2m:
                    user_roles.add(role.name)
            if not user_roles:
                user_roles.add('Cliente')
            access_token = create_access_token(
                identity=user.email,
                additional_claims={
                    'roles': list(user_roles),
                    'user_id': user.id,
                    'tenant_id': user.tenant_id
                }
            )
            user.last_login = datetime.utcnow()
            db.session.commit()
            return jsonify(access_token=access_token)
        return jsonify({"msg": "Credenciales inválidas"}), 401

    # Rutas para préstamos
    @app.route('/api/loan-applications/submit', methods=['POST'])
    @jwt_required()
    def submit_loan_application():
        return jsonify({"message": "Ruta de solicitud de préstamo implementada."}), 201

    @app.route('/api/applications/<int:app_id>/send-reminder', methods=['POST'])
    @jwt_required()
    @role_required(['Administrador General'])
    def send_payment_reminder(app_id):
        LoanApplication = app.models.get('LoanApplication', MockModel)
        if LoanApplication == MockModel:
            return jsonify({"error": "Modelo LoanApplication no cargado"}), 500
        application = LoanApplication.query.get_or_404(app_id)
        if not hasattr(application, 'applicant') or not application.applicant:
            return jsonify({"error": "Solicitud no tiene aplicante asociado."}), 404
        recipient = application.applicant.email
        subject = f"Recordatorio de Pago para su Préstamo #{application.id}"
        body = f"Hola {application.applicant.full_name},\n\nEste es un recordatorio de que su próximo pago para el préstamo #{application.id} está por vencer."
        email_service = app.services.get('email_service')
        if not email_service:
            return jsonify({"error": "Servicio de correo no configurado."}), 503
        success, message = email_service.send_email(recipient, subject, body, g.current_user.tenant_id)
        if success:
            audit_service = app.services.get('audit_service')
            if audit_service:
                audit_service.log_action(g.current_user.id, 'send_reminder', 'LoanApplication', app_id, g.current_user.tenant_id)
            return jsonify({"message": f"Recordatorio de pago enviado para la solicitud {app_id}."}), 200
        else:
            return jsonify({"error": f"Error al enviar recordatorio: {message}"}), 500

    @app.route('/api/applications/<int:app_id>/status', methods=['PUT'])
    @jwt_required()
    @role_required(['Ejecutivo de Crédito', 'Administrador General'])
    def update_application_status(app_id):
        LoanApplication = app.models.get('LoanApplication', MockModel)
        if LoanApplication == MockModel:
            return jsonify({"error": "Modelo LoanApplication no cargado"}), 500
        application = LoanApplication.query.get_or_404(app_id)
        data = request.get_json()
        new_status = data.get('status')
        if not new_status:
            return jsonify({"error": "El campo 'status' es requerido."}), 400
        old_status = application.status
        application.status = new_status
        if old_status != 'Aprobado' and new_status == 'Aprobado':
            contract_service = app.services.get('contract_service')
            if contract_service:
                try:
                    pass  # Placeholder
                except Exception as e:
                    app.logger.error(f"Error generando contrato para {app_id}: {e}")
        db.session.commit()
        audit_service = app.services.get('audit_service')
        if audit_service:
            audit_service.log_action(g.current_user.id, 'update_status', 'LoanApplication', app_id, g.current_user.tenant_id, details=f"Status changed to {new_status}")
        return jsonify({"message": f"Estado de la solicitud {app_id} actualizado a '{new_status}'."})

    # Rutas para reportes contables
    @app.route('/api/reports/balance-sheet', methods=['GET'])
    @jwt_required()
    @role_required(['Contador', 'Administrador General'])
    def get_balance_sheet_report():
        tenant_id = g.current_user.tenant_id
        accounting_service = app.services.get('accounting_service')
        if not accounting_service:
            return jsonify({"error": "Servicio contable no disponible"}), 503
        report_data = accounting_service.get_balance_sheet(tenant_id)
        return jsonify(report_data), 200

    @app.route('/api/reports/income-statement', methods=['GET'])
    @jwt_required()
    @role_required(['Contador', 'Administrador General'])
    def get_income_statement_report():
        tenant_id = g.current_user.tenant_id
        accounting_service = app.services.get('accounting_service')
        if not accounting_service:
            return jsonify({"error": "Servicio contable no disponible"}), 503
        report_data = accounting_service.get_income_statement(tenant_id)
        return jsonify(report_data), 200

    # Rutas para correo
    @app.route('/api/email/test', methods=['POST'])
    @jwt_required()
    @role_required(['Administrador General'])
    def test_email_sending():
        data = request.get_json()
        recipient = data.get('recipient')
        if not recipient:
            return jsonify({"error": "El destinatario es requerido."}), 400
        subject = data.get('subject', 'Correo de Prueba')
        body = data.get('body', 'Este es un correo de prueba desde el sistema LAZOARCE UBMS.')
        email_service = app.services.get('email_service')
        if not email_service:
            return jsonify({"error": "Servicio de correo no disponible"}), 503
        success, message = email_service.send_email(recipient, subject, body, g.current_user.tenant_id)
        return jsonify({"message": message} if success else {"error": message}), 200 if success else 500

    # Rutas para gestor de documentos
    documents_bp = Blueprint('documents', __name__, url_prefix='/api/documents')
    app.register_blueprint(documents_bp)

    # Rutas para mensajería corporativa
    messaging_bp = Blueprint('messaging', __name__, url_prefix='/api/messaging')
    app.register_blueprint(messaging_bp)

    # Rutas para firmar
    sign_bp = Blueprint('signer', __name__, url_prefix='/api/signer')
    app.register_blueprint(sign_bp)

    # Rutas para formularios
    forms_bp = Blueprint('forms', __name__, url_prefix='/api/forms')
    app.register_blueprint(forms_bp)

    # Rutas para gestión de proyectos
    projects_bp = Blueprint('projects', __name__, url_prefix='/api/projects')
    app.register_blueprint(projects_bp)

    # Rutas para soporte técnico
    support_bp = Blueprint('support', __name__, url_prefix='/api/support')
    app.register_blueprint(support_bp)

    # Rutas para activos fijos
    assets_bp = Blueprint('assets', __name__, url_prefix='/api/assets')
    app.register_blueprint(assets_bp)

    # Registro de blueprints adicionales
    app.register_blueprint(cash_and_banks_bp)
    app.register_blueprint(tax_bp)
    app.register_blueprint(material_bp)
    app.register_blueprint(construction_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(education_bp)
    app.register_blueprint(logistics_bp)
    app.register_blueprint(restaurant_bp)
    app.register_blueprint(commercial_kitchen_bp)
    app.register_blueprint(field_bp)
    app.register_blueprint(technical_service_bp)

    # Registro de comandos CLI
    @app.cli.command("init-db")
    def init_db_command():
        """Inicializa la base de datos y crea los datos por defecto."""
        with app.app_context():
            Role = app.models.get('Role')
            User = app.models.get('User')
            if not Role or not User or Role == MockModel or User == MockModel:
                click.echo("Error: No se pudieron cargar los modelos reales. Abortando init-db.")
                return
            try:
                db.create_all()
                click.echo("Tablas creadas (si no existían).")
                if Role.query.first() is None:
                    roles = ['Super Administrador', 'Administrador General', 'Ejecutivo de Crédito', 'Cobrador', 'Contador', 'Cliente', 'Soporte']
                    for role_name in roles:
                        db.session.add(Role(name=role_name))
                    db.session.commit()
                    click.echo("Roles por defecto creados.")
                else:
                    click.echo("Roles ya existen.")
                if not User.query.filter_by(email='admin@lazoarce.com').first():
                    admin_role = Role.query.filter_by(name='Administrador General').first()
                    if admin_role:
                        admin_user = User(email='admin@lazoarce.com', role_id=admin_role.id, full_name='Administrador Principal')
                        admin_user.set_password('admin')
                        db.session.add(admin_user)
                        db.session.commit()
                        click.echo("Usuario administrador por defecto creado (admin@lazoarce.com / admin).")
                    else:
                        click.echo("Error: No se encontró el rol 'Administrador General'.")
                else:
                    click.echo("Usuario administrador ya existe.")
                click.echo("✅ Base de datos inicializada correctamente.")
            except Exception as e:
                db.session.rollback()
                click.echo(f"❌ Error durante init-db: {e}")

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"message": "Endpoint no encontrado"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Internal Server Error: {error}", exc_info=True)
        try:
            db.session.rollback()
        except Exception as e:
            app.logger.error(f"Error during rollback: {e}")
        return jsonify({"message": "Error interno del servidor"}), 500

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5001, debug=True)