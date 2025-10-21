import os
from flask import Flask, jsonify, request, make_response, g
from flask_cors import CORS
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity,
    JWTManager, get_jwt
)
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

# Inicializar extensiones globales (se inicializarán realmente en create_app)
db = SQLAlchemy() # Inicialización para evitar problemas de importación circular
jwt = JWTManager()
migrate = Migrate()

# Se importa la configuración aquí o se espera que exista un archivo config.py
# from config import DevelopmentConfig, TestingConfig, ProductionConfig 

def create_app(testing=False, testing_config=None):
    """Application factory function - patrón moderno Flask."""
    
    # Crear app
    app = Flask(__name__)
    CORS(app)
    
    # === CONFIGURACIÓN ===
    if testing_config:
        app.config.from_object(testing_config)
    else:
        # Asume que tienes un archivo config.py o una clase DevelopmentConfig
        # Si no tienes config.py, puedes usar un diccionario
        app.config.from_mapping(
            SECRET_KEY='dev-secret-key-change-me',
            JWT_SECRET_KEY='jwt-secret-key-change-me',
            SQLALCHEMY_DATABASE_URI='sqlite:///lazoarce.db', # Fallback local
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            JWT_ACCESS_TOKEN_EXPIRES=timedelta(hours=8),
            JWT_REFRESH_TOKEN_EXPIRES=timedelta(days=30),
            ENVIRONMENT='development',
            DEBUG=True,
            # Otros ajustes
        )

    # Variables de entorno críticas (con fallback)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', app.config.get('SECRET_KEY'))
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', app.config.get('JWT_SECRET_KEY'))
    # El URI de la base de datos de Supabase del código de la izquierda se puede incluir aquí si es necesario.
    # Usando el de la versión 2.0 que prioriza variables de entorno o la configuración interna:
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', app.config.get('SQLALCHEMY_DATABASE_URI'))
    
    # Inicializar extensiones
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    
    # IMPORTAR MODELOS DESPUÉS DE db.init_app()
    with app.app_context():
        # Importar modelos dentro del contexto para evitar importaciones circulares en proyectos grandes
        try:
            from .models import (
                User, Role, ClientProfile, LoanProduct, Account,
                NotificationTemplate, Tenant, LoanApplication, Payment,
                AuditLog, Employee, CommunicationLog, Ticket, TicketComment,
                JournalEntry, Transaction # Agregados de la versión anterior
            )
            
            # Registrar modelos en el objeto app
            app.models = {
                'User': User, 'Role': Role, 'ClientProfile': ClientProfile,
                'LoanProduct': LoanProduct, 'Account': Account,
                'NotificationTemplate': NotificationTemplate, 'Tenant': Tenant,
                'LoanApplication': LoanApplication, 'Payment': Payment,
                'AuditLog': AuditLog, 'Employee': Employee,
                'CommunicationLog': CommunicationLog, 'Ticket': Ticket,
                'TicketComment': TicketComment,
                'JournalEntry': JournalEntry, 'Transaction': Transaction
            }
        except ImportError as e:
            app.logger.error(f"❌ Error al importar modelos: {e}. Asegúrate de que .models esté definido.")
    
    # === REGISTRO DE BLUEPRINTS ===
    # El código asume que tienes un paquete llamado 'blueprints' con tus rutas.
    try:
        from .blueprints import (
            auth_bp, loan_management_bp, hr_bp, ett_bp,
            accounting_bp, invoicing_bp, billing_bp, crm_bp,
            helpdesk_bp, marketing_bp
        )
        
        # Registrar blueprints con prefijo /api
        blueprints = [
            (auth_bp, ''),
            (loan_management_bp, '/loans'),
            (hr_bp, '/hr'),
            (ett_bp, '/ett'),
            (accounting_bp, '/accounting'),
            (invoicing_bp, '/invoicing'),
            (crm_bp, '/crm'),
            (helpdesk_bp, '/helpdesk'),
            (marketing_bp, '/marketing')
        ]
        
        for blueprint, prefix in blueprints:
            app.register_blueprint(blueprint, url_prefix=f'/api{prefix}')
            app.logger.info(f"✅ Blueprint registrado: {blueprint.name}{prefix}")
            
    except ImportError as e:
        app.logger.warning(f"⚠️ Algunos blueprints no se pudieron importar: {e}")
        # Continuar sin blueprints si no son críticos
    
    # === DECORADORES DE SEGURIDAD ===
    
    def require_roles(*required_roles):
        """Decorator para requerir roles específicos."""
        def decorator(fn):
            @wraps(fn)
            @jwt_required()
            def wrapper(*args, **kwargs):
                try:
                    claims = get_jwt()
                    # El JWT ID en esta versión se asume que es el user.id, no el email
                    user_id = claims.get('user_id') # Usar user_id en lugar de email
                    user_roles = claims.get('roles', [])
                    
                    if not any(role in user_roles for role in required_roles):
                        return jsonify({
                            "message": "Acceso no autorizado",
                            "required_roles": required_roles,
                            "user_roles": user_roles
                        }), 403
                    
                    # Agregar usuario actual al contexto
                    User = app.models.get('User')
                    g.current_user = User.query.get(user_id)
                    if not g.current_user:
                        return jsonify({"message": "Usuario no encontrado"}), 404
                    
                    return fn(*args, **kwargs)
                except Exception as e:
                    app.logger.error(f"Error en require_roles: {str(e)}")
                    return jsonify({"message": "Error de autorización"}), 403
            return wrapper
        return decorator
    
    def role_required(*roles):
        """Alias para require_roles."""
        return require_roles(*roles)
    
    # Registrar en app context
    app.jinja_env.globals['require_roles'] = require_roles
    app.jinja_env.globals['role_required'] = role_required
    
    # === MIDDLEWARE DE AUDITORÍA ===
    
    @app.before_request
    def audit_request():
        """Registra requests importantes para auditoría."""
        if request.path.startswith('/api/') and request.method in ['POST', 'PUT', 'DELETE']:
            g.audit_action = f"{request.method} {request.path}"
    
    @app.after_request
    def audit_response(response):
        """Log de auditoría automático."""
        AuditLog = app.models.get('AuditLog')
        
        if hasattr(g, 'audit_action') and hasattr(g, 'current_user') and AuditLog:
            try:
                audit_log = AuditLog(
                    user_id=g.current_user.id,
                    action=g.audit_action,
                    details=f"Status: {response.status_code}, IP: {request.remote_addr}"
                )
                db.session.add(audit_log)
                db.session.commit()
            except Exception as e:
                app.logger.error(f"Error en auditoría: {str(e)}")
                db.session.rollback()
        
        return response
    
    # === RUTAS PRINCIPALES ===
    
    @app.route('/api/health')
    def health_check():
        """Health check endpoint."""
        db_connected = False
        try:
            # Una verificación simple a la base de datos
            db.session.execute(db.select(1)).one()
            db_connected = True
        except Exception as e:
            app.logger.error(f"Error de conexión DB en health check: {str(e)}")
            db_connected = False
            
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "2.0",
            "environment": app.config.get('ENVIRONMENT', 'development'),
            "database": db_connected,
            "blueprints": list(app.blueprints.keys())
        })
    
    # La ruta /api/metrics y otras se asume que se manejan en los Blueprints
    
    @app.route('/')
    def index():
        """Landing page con documentación."""
        return jsonify({
            "message": "Sistema de Gestión Financiera LAZO ARCE",
            "version": "2.0",
            "endpoints": [
                "/api/health",
                "/api/auth/register",
                "/api/auth/login"
            ],
            "docs": "/api/docs/swagger",
            "blueprints": list(app.blueprints.keys())
        })
    
    # === ERROR HANDLERS ===
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"message": "Endpoint no encontrado"}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.error(f"Error 500: {str(error)}")
        return jsonify({"message": "Error interno del servidor"}), 500
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"message": "Solicitud inválida"}), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({"message": "No autorizado - Token inválido"}), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({"message": "Acceso prohibido - Permisos insuficientes"}), 403
    
    @app.errorhandler(409)
    def conflict(error):
        return jsonify({"message": "Conflicto - Recurso ya existe"}), 409
    
    # === CONTEXT PROCESSOR ===
    
    @app.context_processor
    def inject_config():
        """Inyecta configuración segura en templates."""
        return dict(
            ENVIRONMENT=app.config.get('ENVIRONMENT', 'development'),
            DEBUG=app.config.get('DEBUG', False),
            VERSION='2.0'
        )
    
    return app

def setup_database(app):
    """Inicializa base de datos con datos base esenciales (seeding)."""
    
    with app.app_context():
        try:
            # Obtener modelos del contexto
            Tenant = app.models.get('Tenant')
            Role = app.models.get('Role')
            User = app.models.get('User')
            ClientProfile = app.models.get('ClientProfile')
            LoanProduct = app.models.get('LoanProduct')
            Account = app.models.get('Account')
            Employee = app.models.get('Employee')
            
            # Crear tablas si no existen
            db.create_all()
            
            # === TENANT POR DEFECTO ===
            if Tenant.query.first() is None:
                default_tenant = Tenant(company_name='LAZOARCE NEXUS', is_active=True)
                db.session.add(default_tenant)
                db.session.commit()
                print("✅ Tenant por defecto creado")
            
            # === ROLES ===
            required_roles = [
                'Super Administrador', 'Administrador General',
                'Ejecutivo de Crédito', 'Cobrador', 'Contador', 'Cliente'
            ]
            
            existing_roles = {role.name for role in Role.query.all()}
            missing_roles = [role for role in required_roles if role not in existing_roles]
            
            if missing_roles:
                roles_to_create = [Role(name=role_name) for role_name in missing_roles]
                db.session.bulk_save_objects(roles_to_create)
                db.session.commit()
                print(f"✅ Creados {len(missing_roles)} roles: {missing_roles}")
            
            # === USUARIO SUPERADMIN ===
            admin_email = 'admin@lazoarce.com'
            if User.query.filter_by(email=admin_email).first() is None:
                superadmin_role = Role.query.filter_by(name='Super Administrador').first()
                if superadmin_role:
                    admin = User(
                        email=admin_email,
                        role_id=superadmin_role.id
                    )
                    # La clase User debe tener un método set_password
                    # Usando check_password_hash de werkzeug
                    admin.password_hash = generate_password_hash('admin123') 
                    
                    profile = ClientProfile(
                        user_id=None, # El ID se asigna después del commit de User
                        full_name='Super Administrador LAZO ARCE'
                    )
                    
                    db.session.add(admin)
                    db.session.commit() # Commit para obtener el ID de usuario
                    
                    profile.user_id = admin.id
                    db.session.add(profile)
                    db.session.commit()
                    
                    print("🔐 Usuario admin creado:")
                    print(f"    Email: {admin_email}")
                    print(f"    Password: admin123")
                    print("⚠️  ¡CAMBIAR CONTRASEÑA EN PRODUCCIÓN INMEDIATAMENTE!")
            
            # === PRODUCTO POR DEFECTO ===
            if LoanProduct.query.filter_by(name='Préstamo Personal Clásico').first() is None:
                default_product = LoanProduct(
                    name="Préstamo Personal Clásico",
                    min_amount=1000.0,
                    max_amount=50000.0,
                    interest_rate=12.0,
                    term_months=12,
                    is_active=True
                )
                db.session.add(default_product)
                db.session.commit()
                print("✅ Producto de préstamo por defecto creado")
            
            # === CUENTAS CONTABLES BÁSICAS ===
            if Account.query.first() is None:
                basic_accounts = [
                    # Activos
                    Account(name='Caja', category='Asset', normal_balance='Debit'),
                    Account(name='Bancos', category='Asset', normal_balance='Debit'),
                    Account(name='Cuentas por Cobrar Clientes', category='Asset', normal_balance='Debit'),
                    
                    # Pasivos
                    Account(name='Retenciones por Pagar', category='Liability', normal_balance='Credit'),
                    Account(name='Sueldos por Pagar', category='Liability', normal_balance='Credit'),
                    
                    # Ingresos
                    Account(name='Ingresos por Intereses', category='Revenue', normal_balance='Credit'),
                    Account(name='Ingresos por Comisiones', category='Revenue', normal_balance='Credit'),
                    
                    # Gastos
                    Account(name='Sueldos y Salarios', category='Expense', normal_balance='Debit'),
                ]
                
                db.session.bulk_save_objects(basic_accounts)
                db.session.commit()
                print(f"✅ {len(basic_accounts)} cuentas contables básicas creadas")
            
            # === EMPLEADO DE PRUEBA ===
            if Employee.query.first() is None:
                test_employee = Employee(
                    full_name='Ana García López',
                    position='Ejecutivo de Crédito',
                    salary=1200.00,
                    is_active=True
                )
                db.session.add(test_employee)
                db.session.commit()
                print("✅ Empleado de prueba creado")
            
            print("✅ 🎉 Base de datos inicializada correctamente")
            # Se asume que los modelos existen para estas consultas
            if User and LoanProduct and Account:
                print(f"📊 Total usuarios: {User.query.count()}")
                print(f"💰 Productos activos: {LoanProduct.query.filter_by(is_active=True).count()}")
                print(f"🏦 Cuentas contables: {Account.query.count()}")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error en inicialización de base de datos: {str(e)}")
            app.logger.error(f"Error en setup_database: {str(e)}")


def initialize_database(app):
    """Alias para compatibilidad con código legacy."""
    setup_database(app)

# Crear app global para desarrollo (solo si el módulo se ejecuta directamente)
app = None

if __name__ == '__main__':
    # Usar un patrón más seguro para la configuración de desarrollo
    class DevelopmentConfig:
        DEBUG = True
        TESTING = False
        SECRET_KEY = 'dev-secret-key-change-me'
        JWT_SECRET_KEY = 'jwt-secret-key-change-me'
        SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///lazoarce.db')
        SQLALCHEMY_TRACK_MODIFICATIONS = False
        # ... otras configuraciones

    app = create_app(testing_config=DevelopmentConfig)
    
    # Inicializar base de datos (solo desarrollo/testing)
    if app.config.get('ENVIRONMENT') in ['development', 'testing'] or app.config.get('DEBUG'):
        setup_database(app)
    
    # Configuración de servidor
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '127.0.0.1')
    debug = app.config.get('DEBUG', False)
    
    # app.run requiere que el objeto 'app' no sea None
    app.run(host=host, port=port, debug=debug)