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
from random import randint, choice # Incluido del 2.0 para la ruta de prueba

# --- DEFINICIÓN GLOBAL DE EXTENSIONES ---
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
    class MockService:
        def log_action(*args, **kwargs): pass
    audit_service = MockService()

except ImportError as e:
    print(f"⚠️ Error importando servicios: {e}. Usando Mocks.")
    def mock_func(*args, **kwargs): pass
    calcular_prestamo_completo = create_journal_entry = validacion_identidad_estricta = capturar_datos_biometricos = generar_contrato_integracion = firma_electronica_avanzada = calcular_planilla = mock_func

# -----------------------------------------------------------


def create_app(config_object=None, testing_config=None):
    app = Flask(__name__)
    CORS(app)
    load_dotenv()

    # === CONFIGURACIÓN ===
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-secret-key-change-me'),
        JWT_SECRET_KEY=os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-me'),
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'lazoarce.db')}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        JWT_ACCESS_TOKEN_EXPIRES=timedelta(hours=8),
        UPLOAD_FOLDER='uploads'
    )
    if config_object:
         app.config.from_object(config_object)
    if testing_config:
        app.config.from_object(testing_config)

    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', app.config.get('SQLALCHEMY_DATABASE_URI'))
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # --- INICIALIZACIÓN DE EXTENSIONES ---
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    # --- CARGA DINÁMICA DE MODELOS Y SERVICIOS ---
    with app.app_context():
        try:
            from .models import (
                Role, User, LoanProduct, LoanApplication, Account, Transaction,
                JournalEntry, Cliente, ContratoIntegracion, ProductoCredito,
                Empleado, Planilla, ClientProfile, Tenant, AuditLog, Payment,
                NotificationTemplate, Employee,
                Student, Course, Enrollment, Grade, TuitionPayment, # Modelos LAN-SCH6
                DegreeProgram, Scholarship, StudentScholarship, LibraryResource, Alumnus # Modelos LAN-UNV8
            )
            from . import audit_service
            from . import school_management_service
            from . import university_management_service
            app.services = {
                'audit_service': audit_service,
                'school_management_service': school_management_service,
                'university_management_service': university_management_service
            }

        except ImportError as e:
            app.logger.error(f"❌ Error al importar modelos/servicios: {e}.")
            class MockModel:
                query = type('Query', (), {'filter_by': lambda **kwargs: type('Filter', (), {'first': lambda: None})()})()
            Role = User = LoanProduct = LoanApplication = Account = Transaction = JournalEntry = Cliente = ContratoIntegracion = ProductoCredito = Empleado = Planilla = ClientProfile = Tenant = AuditLog = Payment = NotificationTemplate = Employee = Student = Course = Enrollment = Grade = TuitionPayment = DegreeProgram = Scholarship = StudentScholarship = LibraryResource = Alumnus = MockModel
            app.services = {'audit_service': lambda: None, 'school_management_service': lambda: None, 'university_management_service': lambda: None}

        app.models = {
            'Role': Role, 'User': User, 'LoanProduct': LoanProduct, 'LoanApplication': LoanApplication,
            'Account': Account, 'Transaction': Transaction, 'JournalEntry': JournalEntry, 'Cliente': Cliente,
            'ContratoIntegracion': ContratoIntegracion, 'ProductoCredito': ProductoCredito, 'Empleado': Empleado,
            'Planilla': Planilla, 'Employee': Employee, 'AuditLog': AuditLog,
            'Student': Student, 'Course': Course, 'Enrollment': Enrollment, 'Grade': Grade, 'TuitionPayment': TuitionPayment,
            'DegreeProgram': DegreeProgram, 'Scholarship': Scholarship, 'StudentScholarship': StudentScholarship, 'LibraryResource': LibraryResource, 'Alumnus': Alumnus
        }

    # --- DECORADORES DE AUTORIZACIÓN ---
    def role_required(required_roles):
        if not isinstance(required_roles, list):
            required_roles = [required_roles]
        def decorator(fn):
            @wraps(fn)
            @jwt_required()
            def wrapper(*args, **kwargs):
                User = app.models.get('User')
                claims = get_jwt()
                user_roles = claims.get('roles', [])
                g.current_user = User.query.filter_by(email=get_jwt_identity()).first()
                if not g.current_user:
                    return jsonify({"msg": "Usuario no encontrado"}), 404
                if not any(role in user_roles for role in required_roles):
                    return jsonify({"msg": "Acceso no autorizado para este rol"}), 403
                return fn(*args, **kwargs)
            return wrapper
        return decorator
    app.jinja_env.globals['role_required'] = role_required

    # --- RUTAS ---
    @app.route('/')
    def index():
        return jsonify({"message": "Servidor del Sistema de Gestión Financiera en funcionamiento.", "version": "2.1 (Fusion)"})

    @app.route('/api/login', methods=['POST'])
    def login():
        User = app.models.get('User')
        data = request.get_json()
        user = User.query.filter_by(email=data.get('email')).first()
        if user and user.check_password(data.get('password')):
            user_roles = [role.name for role in user.roles]
            access_token = create_access_token(identity=user.email, additional_claims={'roles': user_roles, 'tenant_id': user.tenant_id})
            return jsonify(access_token=access_token)
        return jsonify({"msg": "Credenciales inválidas"}), 401

    # Registrar Blueprints
    from .routes.school_management_routes import school_management_bp
    app.register_blueprint(school_management_bp, url_prefix='/api/school')

    from .routes.university_management_routes import university_management_bp
    app.register_blueprint(university_management_bp, url_prefix='/api/university')


    # --- COMANDOS CLI ---
    @app.cli.command("init-db")
    def init_db_command():
        db.create_all()
        # Aquí iría la lógica de seeding si es necesaria
        click.echo("Base de datos inicializada.")

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5001, debug=True)
