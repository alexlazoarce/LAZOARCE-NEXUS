import os
import click
from flask import Flask, jsonify, request, make_response, g
from flask_cors import CORS
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity,
    JWTManager, get_jwt, verify_jwt_in_request
)
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from functools import wraps
from datetime import datetime, date, timedelta
from io import BytesIO
from random import randint, choice

# --- DEFINICIÓN GLOBAL DE EXTENSIONES ---
# Se necesita definir SQLAlchemy globalmente antes de create_app si se usa en modelos importados
try:
    from .database import db as global_db
    db = global_db
except ImportError:
    db = SQLAlchemy()

jwt = JWTManager()
migrate = Migrate()

# --- IMPORTACIONES DE SERVICIOS (Asunciones del HEAD) ---
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
    # Se incluyen los nuevos servicios CRM y Contract (asumidos del HEAD)
    from . import audit_service, contract_service, crm_service 
    
except ImportError as e:
    print(f"⚠️ Error importando servicios: {e}. Usando Mocks.")
    def mock_func(*args, **kwargs): return {} # Retorna dict vacío para FEA/Payroll
    class MockService:
        def log_action(*args, **kwargs): pass
        def create_contact(*args, **kwargs): return {'id': 1}
        def get_contacts(*args, **kwargs): return []
        def create_interaction(*args, **kwargs): return {'id': 1}
        def create_opportunity(*args, **kwargs): return {'id': 1}
        
    calcular_prestamo_completo = create_journal_entry = validacion_identidad_estricta = capturar_datos_biometricos = mock_func
    generar_contrato_integracion = lambda data: 'CONTRATO-MOCK-123'
    firma_electronica_avanzada = lambda c, d, b: {'valida': True, 'firma_id': 'FIRM-1', 'certificado_id': 'CERT-1', 'error': None}
    calcular_planilla = lambda s: {"success": True, "salario_base": s, "isss": 0, "afp": 0, "renta": 0, "salario_neto": s}
    audit_service = contract_service = crm_service = MockService()
# -----------------------------------------------------------


def create_app(config_object=None, testing_config=None):
    """
    Application Factory para crear y configurar la aplicación Flask.
    """
    app = Flask(__name__)
    CORS(app)

    # Cargar variables de entorno (del HEAD)
    load_dotenv()

    # === CONFIGURACIÓN (Fusionado del 2.0 + HEAD) ===
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-secret-key-change-me'),
        JWT_SECRET_KEY=os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-me'),
        SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL', 'sqlite:///lazoarce.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        JWT_ACCESS_TOKEN_EXPIRES=timedelta(hours=8),
        JWT_REFRESH_TOKEN_EXPIRES=timedelta(days=30),
        ENVIRONMENT='development',
        DEBUG=True,
        UPLOAD_FOLDER='uploads'
    )
    
    # Sobrescribir con config_object o testing_config
    if config_object:
         app.config.from_object(config_object)
    if testing_config:
        app.config.from_object(testing_config)
    
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', app.config.get('SECRET_KEY'))
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', app.config.get('JWT_SECRET_KEY'))
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', app.config.get('SQLALCHEMY_DATABASE_URI'))

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # --- INICIALIZACIÓN DE EXTENSIONES ---
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db) 

    # --- CARGA DINÁMICA DE MODELOS Y SERVICIOS ---
    with app.app_context():
        # Intenta cargar modelos
        try:
            from .models import (
                Role, User, LoanProduct, LoanApplication, Account, Transaction,
                JournalEntry, Cliente, ContratoIntegracion, ProductoCredito,
                Empleado, Planilla, ClientProfile, Tenant, AuditLog, Payment,
                NotificationTemplate, Employee, ContractTemplate, GeneratedContract,
                Contact, Interaction, Opportunity # Nuevos modelos CRM/Contract
            )
            app.services = {
                'audit_service': audit_service,
                'contract_service': contract_service,
                'crm_service': crm_service
            }
            
        except ImportError as e:
            app.logger.error(f"❌ Error al importar modelos: {e}. Se usarán Mocks.")
            # Definición de MockModel si falla la importación
            class MockModel:
                def __init__(self, **kwargs): pass
                def query(self): return self
                def filter_by(self, **kwargs): return self
                def first(self): return None
                def all(self): return []
                def get(self, id): return None
                def get_or_404(self, id): return None
            
            Role = User = LoanProduct = LoanApplication = Account = Transaction = JournalEntry = Cliente = ContratoIntegracion = ProductoCredito = Empleado = Planilla = ClientProfile = Tenant = AuditLog = Payment = NotificationTemplate = Employee = ContractTemplate = GeneratedContract = Contact = Interaction = Opportunity = MockModel
            app.services = {'audit_service': lambda: None, 'contract_service': lambda: None, 'crm_service': lambda: None}
            
        # Asignar modelos al contexto de la app
        app.models = {
            'Role': Role, 'User': User, 'LoanProduct': LoanProduct, 'LoanApplication': LoanApplication, 
            'Account': Account, 'Transaction': Transaction, 'JournalEntry': JournalEntry, 'Cliente': Cliente,
            'ContratoIntegracion': ContratoIntegracion, 'ProductoCredito': ProductoCredito, 'Empleado': Empleado,
            'Planilla': Planilla, 'Employee': Employee, 'AuditLog': AuditLog,
            'ContractTemplate': ContractTemplate, 'GeneratedContract': GeneratedContract,
            'Contact': Contact, 'Interaction': Interaction, 'Opportunity': Opportunity
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
                user_roles = claims.get('roles', [])
                user_identity = get_jwt_identity()
                g.current_user = User.query.filter_by(email=user_identity).first()
                
                if not g.current_user:
                    return jsonify({"msg": "Usuario no encontrado en la base de datos"}), 404

                user_has_required_role = any(role in user_roles for role in required_roles)
                if g.current_user.role and g.current_user.role.name in required_roles:
                    user_has_required_role = True

                if not user_has_required_role:
                    return jsonify({"msg": "Acceso no autorizado para este rol"}), 403
                return fn(*args, **kwargs)
            return wrapper
        return decorator
    
    app.jinja_env.globals['role_required'] = role_required
    app.jinja_env.globals['require_roles'] = role_required

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
                audit_log = AuditLog(
                    user_id=g.current_user.id,
                    action=g.audit_action,
                    details=f"Status: {response.status_code}",
                    ip_address=request.remote_addr
                )
                db.session.add(audit_log)
                db.session.commit()
            except Exception as e:
                app.logger.error(f"Error en auditoría: {str(e)}")
                db.session.rollback()
        
        return response

    # -------------------------------------------------------------------
    # === RUTAS MONOLÍTICAS (Fusión de todas las funcionalidades) ===
    # -------------------------------------------------------------------

    ## RUTAS BASE
    @app.route('/')
    def index():
        return jsonify({"message": "Servidor del Sistema de Gestión Financiera en funcionamiento.", "version": "2.1 (Fusion)"})

    @app.route('/api/health')
    def health_check():
        db_connected = False
        try:
            db.session.execute(db.select(1)).one()
            db_connected = True
        except Exception:
            db_connected = False
            
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": db_connected,
        })
    
    ## RUTAS DE AUTENTICACIÓN/PERFIL
    @app.route('/api/register', methods=['POST'])
    def register():
        User = app.models.get('User')
        Role = app.models.get('Role')
        if not User or not Role: return jsonify({"msg": "Error de sistema (Modelos no cargados)"}), 500
        data = request.get_json()
        email, password, role_name = data.get('email'), data.get('password'), data.get('role', 'Cliente')
        if not email or not password: return jsonify({"msg": "Email y contraseña son requeridos"}), 400
        if User.query.filter_by(email=email).first(): return jsonify({"msg": "El email ya está registrado"}), 400
        role = Role.query.filter_by(name=role_name).first()
        if not role: return jsonify({"msg": f"El rol '{role_name}' no es válido"}), 400
        new_user = User(email=email, role_id=role.id)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"msg": "Usuario creado exitosamente"}), 201

    @app.route('/api/login', methods=['POST'])
    def login():
        User = app.models.get('User')
        if not User: return jsonify({"msg": "Error de sistema (Modelo User)"}), 500
        data = request.get_json()
        email, password = data.get('email'), data.get('password')
        if not email or not password: return jsonify({"msg": "Email y contraseña son requeridos"}), 400
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            user_roles = [user.role.name] if user.role else ['Cliente']
            access_token = create_access_token(identity=user.email, additional_claims={'roles': user_roles, 'email': user.email, 'user_id': user.id})
            return jsonify(access_token=access_token)
        return jsonify({"msg": "Credenciales inválidas"}), 401

    @app.route('/api/profile', methods=['GET'])
    @jwt_required()
    def get_profile():
        user = g.current_user
        if not user: return jsonify({"msg": "Usuario no encontrado"}), 404
        return jsonify({ "email": user.email, "full_name": user.full_name, "dui": user.dui, "nit": user.nit, "role": user.role.name if user.role else 'N/A'})

    ## RUTAS DE CLIENTES Y FIRMA ELECTRÓNICA
    @app.route('/api/clientes/nuevo', methods=['POST'])
    @jwt_required()
    @role_required(['Administrador General', 'Ejecutivo de Crédito'])
    def crear_nuevo_cliente():
        Cliente, ContratoIntegracion = app.models.get('Cliente'), app.models.get('ContratoIntegracion')
        if not Cliente or not ContratoIntegracion: return jsonify({"error": "Error de sistema (Modelos no cargados)"}), 500
        try:
            data = request.get_json()
            if not validacion_identidad_estricta(data): return jsonify({'error': 'Validación de identidad falló.'}), 400
            datos_biometricos = capturar_datos_biometricos()
            if not datos_biometricos: return jsonify({'error': 'Error en la captura de datos biométricos.'}), 500
            contrato_id = generar_contrato_integracion(data)
            if not contrato_id: return jsonify({'error': 'No se pudo generar el contrato de integración.'}), 500
            resultado_firma = firma_electronica_avanzada(contrato_id, data, datos_biometricos)
            if not resultado_firma.get('valida'):
                contrato = ContratoIntegracion.query.filter_by(contrato_id=contrato_id).first()
                if contrato: db.session.delete(contrato); db.session.commit()
                return jsonify({'error': 'El proceso de firma electrónica falló.', 'detalle': resultado_firma.get('error')}), 400
            cliente = Cliente(nombre_completo=data['nombre_completo'], dui=data['dui'], email=data['email'], telefono=data['telefono'], direccion=data['direccion'], contrato_integracion_id=contrato_id, estado='ACTIVO')
            db.session.add(cliente)
            db.session.commit()
            return jsonify({'success': True, 'cliente_id': cliente.id, 'contrato_id': contrato_id, 'mensaje': 'Cliente creado y contrato firmado exitosamente.'}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Ocurrió un error inesperado en el servidor.', 'detalle': str(e)}), 500

    ## RUTAS DE PRÉSTAMOS
    @app.route('/api/applications/<int:app_id>/status', methods=['PUT'])
    @jwt_required()
    @role_required(['Ejecutivo de Crédito', 'Administrador General'])
    def update_application_status(app_id):
        LoanApplication = app.models.get('LoanApplication')
        application = LoanApplication.query.get_or_404(app_id)
        new_status = request.get_json().get('status')
        if not new_status: return jsonify({"error": "El campo 'status' es requerido."}), 400
        application.status = new_status
        # Si el estado es "Aprobado", se podría generar el contrato aquí
        if new_status == 'Aprobado':
            # Llamada simulada al servicio de contratos
            pass 
        db.session.commit()
        return jsonify({"message": f"Estado de la solicitud {app_id} actualizado a '{new_status}'."})

    ## RUTAS DE GESTIÓN DE CONTRATOS (LAN-F2C)
    @app.route('/api/contracts/templates', methods=['POST'])
    @jwt_required()
    @role_required(['Administrador General'])
    def create_contract_template_route():
        data = request.get_json()
        app.services['contract_service'].create_template(data, g.current_user.id)
        return jsonify({"message": "Ruta para crear plantilla de contrato implementada."}), 201

    ## RUTAS DE CRM (LAN-CRM3)
    @app.route('/api/crm/contacts', methods=['POST'])
    @jwt_required()
    @role_required(['Ejecutivo de Crédito', 'Administrador General'])
    def create_crm_contact():
        data = request.get_json()
        app.services['crm_service'].create_contact(data, g.current_user.id)
        return jsonify({"message": "Ruta para crear contacto de CRM implementada."}), 201

    @app.route('/api/crm/opportunities/<int:opp_id>/stage', methods=['PUT'])
    @jwt_required()
    @role_required(['Ejecutivo de Crédito', 'Administrador General'])
    def update_crm_opportunity_stage(opp_id):
        data = request.get_json()
        app.services['crm_service'].update_opportunity_stage(opp_id, data.get('stage'), g.current_user.id)
        return jsonify({"message": f"Ruta para actualizar etapa de la oportunidad {opp_id}."}), 200

    ## RUTAS DE PAYROLL
    @app.route('/api/payroll/calculate', methods=['POST'])
    @role_required(['Contador', 'Administrador General'])
    def calculate_payroll_for_employee():
        Empleado, Planilla = app.models.get('Empleado'), app.models.get('Planilla')
        if not Empleado or not Planilla: return jsonify({'error': 'Error de sistema (Modelos no cargados)'}), 500
        empleado_id = request.get_json().get('empleado_id')
        empleado = Empleado.query.get_or_404(empleado_id)
        resultado_calculo = calcular_planilla(empleado.salario_base)
        if not resultado_calculo.get('success'): return jsonify({'error': 'Error al calcular la planilla.', 'detalle': resultado_calculo.get('error')}), 500
        try:
            nueva_planilla = Planilla(empleado_id=empleado.id, salario_base=resultado_calculo['salario_base'], isss=resultado_calculo['isss'], afp=resultado_calculo['afp'], renta=resultado_calculo['renta'], salario_neto=resultado_calculo['salario_neto'])
            db.session.add(nueva_planilla)
            db.session.commit()
            return jsonify({"success": True, "planilla_id": nueva_planilla.id, "calculo": resultado_calculo})
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Error al guardar el registro de la planilla.', 'detalle': str(e)}), 500
    
    # --- REGISTRO DE COMANDOS CLI (Se mantiene el del HEAD) ---
    @app.cli.command("init-db")
    def init_db_command():
        with app.app_context():
            Role, User = app.models.get('Role'), app.models.get('User')
            db.create_all()
            if Role and Role.query.first() is None:
                roles = ['Super Administrador', 'Administrador General', 'Ejecutivo de Crédito', 'Cobrador', 'Contador', 'Cliente']
                for role_name in roles: db.session.add(Role(name=role_name))
                db.session.commit()
            if User and Role and not User.query.filter_by(email='admin@lazoarce.com').first():
                 admin_role = Role.query.filter_by(name='Administrador General').first()
                 if admin_role:
                    admin_user = User(email='admin@lazoarce.com', role_id=admin_role.id, full_name='Administrador Principal')
                    admin_user.set_password('admin')
                    db.session.add(admin_user)
                    db.session.commit()
            click.echo("Base de datos inicializada y poblada con datos por defecto.")

    # --- ERROR HANDLERS (Del 2.0) ---
    @app.errorhandler(404)
    def not_found(error): return jsonify({"message": "Endpoint no encontrado"}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({"message": "Error interno del servidor"}), 500
    
    return app

if __name__ == '__main__':
    class DevelopmentConfig:
        DEBUG = True
        TESTING = False
        SECRET_KEY = 'dev-secret-key-change-me'
        JWT_SECRET_KEY = 'jwt-secret-key-change-me'
        SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///lazoarce.db')
        SQLALCHEMY_TRACK_MODIFICATIONS = False

    app = create_app(config_object=DevelopmentConfig)
    
    instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
    os.makedirs(instance_path, exist_ok=True)
    
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '127.0.0.1')
    debug = app.config.get('DEBUG', False)
    
    app.run(host=host, port=port, debug=debug)