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

# Inicializar extensiones globales
db = None
jwt = None
migrate = None

def create_app(testing=False, testing_config=None):
    """Application factory function - patrón moderno Flask."""
    
    # Crear app
    app = Flask(__name__)
    CORS(app)
    
    # === CONFIGURACIÓN ===
    if testing_config:
        app.config.from_object(testing_config)
    else:
        app.config.from_object('config.DevelopmentConfig')
    
    # Variables de entorno críticas (con fallback)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', app.config.get('SECRET_KEY', 'dev-secret-key-change-me'))
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', app.config.get('JWT_SECRET_KEY', 'jwt-secret-key-change-me'))
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', app.config.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///lazoarce.db'))
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # JWT configuración
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=8)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
    
    # Inicializar extensiones
    global db, jwt, migrate
    db = SQLAlchemy()
    jwt = JWTManager()
    migrate = Migrate()
    
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    
    # IMPORTAR MODELOS DESPUÉS DE db.init_app()
    with app.app_context():
        from .models import (
            User, Role, ClientProfile, LoanProduct, Account,
            NotificationTemplate, Tenant, LoanApplication, Payment,
            AuditLog, Employee, CommunicationLog, Ticket, TicketComment
        )
        
        # Registrar modelos globalmente
        app.models = {
            'User': User, 'Role': Role, 'ClientProfile': ClientProfile,
            'LoanProduct': LoanProduct, 'Account': Account,
            'NotificationTemplate': NotificationTemplate, 'Tenant': Tenant,
            'LoanApplication': LoanApplication, 'Payment': Payment,
            'AuditLog': AuditLog, 'Employee': Employee,
            'CommunicationLog': CommunicationLog, 'Ticket': Ticket,
            'TicketComment': TicketComment
        }
    
    # === REGISTRO DE BLUEPRINTS ===
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
        # Blueprints opcionales, continuar sin ellos
    
    # === DECORADORES DE SEGURIDAD ===
    
    def require_roles(*required_roles):
        """Decorator para requerir roles específicos."""
        def decorator(fn):
            @wraps(fn)
            @jwt_required()
            def wrapper(*args, **kwargs):
                try:
                    claims = get_jwt()
                    user_id = get_jwt_identity()
                    user_roles = claims.get('roles', [])
                    
                    if not any(role in user_roles for role in required_roles):
                        return jsonify({
                            "message": "Acceso no autorizado",
                            "required_roles": required_roles,
                            "user_roles": user_roles
                        }), 403
                    
                    # Agregar usuario actual al contexto
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
        if hasattr(g, 'audit_action') and hasattr(g, 'current_user'):
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
        try:
            db_connected = db.engine.has_table("user")
        except:
            db_connected = False
            
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "2.0",
            "environment": app.config.get('ENVIRONMENT', 'development'),
            "database": db_connected,
            "blueprints": list(app.blueprints.keys())
        })
    
    @app.route('/api/metrics')
    @jwt_required()
    @require_roles('Administrador General', 'Super Administrador')
    def metrics():
        """Métricas básicas del sistema."""
        try:
            from sqlalchemy import func
            
            stats = {
                "users_total": User.query.count(),
                "applications_pending": LoanApplication.query.filter(
                    LoanApplication.status == 'Pendiente'
                ).count(),
                "active_employees": Employee.query.filter(
                    Employee.is_active == True
                ).count(),
                "accounts_total": Account.query.count()
            }
            
            # Contar pagos de hoy si Payment existe
            try:
                stats["payments_today"] = Payment.query.filter(
                    Payment.payment_date == date.today()
                ).count()
            except:
                stats["payments_today"] = 0
                
            return jsonify(stats)
        except Exception as e:
            app.logger.error(f"Error en métricas: {str(e)}")
            return jsonify({"error": "Error al obtener métricas"}), 500
    
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
    
    # === RUTAS LEGACY (Compatibilidad) ===
    
    @app.route('/api/auth/register', methods=['POST'])
    def legacy_register():
        """Registro legacy para compatibilidad."""
        try:
            data = request.get_json()
            if not data or not data.get('email') or not data.get('password'):
                return jsonify({"message": "Email y contraseña requeridos"}), 400
            
            # Verificar si ya existe
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user:
                return jsonify({"message": "El correo ya está registrado"}), 409
            
            # Obtener rol de cliente por defecto
            client_role = Role.query.filter_by(name='Cliente').first()
            if not client_role:
                # Crear rol cliente si no existe
                client_role = Role(name='Cliente')
                db.session.add(client_role)
                db.session.commit()
            
            # Crear usuario
            user = User(
                email=data['email'],
                password_hash='',  # Se establece después
                role_id=client_role.id
            )
            user.set_password(data['password'])
            
            # Crear perfil automáticamente
            profile = ClientProfile(
                user_id=user.id,
                full_name=data.get('full_name', data['email'])
            )
            
            db.session.add_all([user, profile])
            db.session.commit()
            
            # Log de auditoría
            audit_log = AuditLog(
                action='USER_REGISTER',
                details=f"Nuevo cliente registrado: {user.email}"
            )
            db.session.add(audit_log)
            db.session.commit()
            
            return jsonify({
                "message": "Usuario creado exitosamente",
                "user_id": user.id,
                "email": user.email
            }), 201
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error en registro: {str(e)}")
            return jsonify({"message": "Error al crear usuario"}), 500
    
    @app.route('/api/loans/calculate', methods=['POST'])
    @jwt_required()
    @require_roles('Cliente', 'Ejecutivo de Crédito', 'Administrador General')
    def calculate_loan():
        """Cálculo de préstamos mejorado."""
        try:
            data = request.get_json()
            
            # Validación de entrada
            required_fields = ['monto', 'producto_id', 'plazo_meses']
            for field in required_fields:
                if not data.get(field):
                    return jsonify({"error": f"El campo {field} es requerido"}), 400
            
            monto = float(data['monto'])
            producto_id = int(data['producto_id'])
            plazo = int(data['plazo_meses'])
            
            if monto <= 0 or plazo <= 0:
                return jsonify({"error": "Monto y plazo deben ser mayores a 0"}), 400
            
            # Obtener producto
            product = LoanProduct.query.get_or_404(producto_id)
            
            # Cálculo simple si no hay servicio externo
            monthly_rate = product.interest_rate / 100 / 12
            n = plazo
            
            if monthly_rate == 0:
                monthly_payment = monto / n
            else:
                monthly_payment = monto * (monthly_rate * (1 + monthly_rate)**n) / ((1 + monthly_rate)**n - 1)
            
            total_payment = monthly_payment * n
            
            return jsonify({
                "success": True,
                "calculation": {
                    "monthly_payment": round(monthly_payment, 2),
                    "total_payment": round(total_payment, 2),
                    "total_interest": round(total_payment - monto, 2),
                    "product_name": product.name
                }
            })
            
        except ValueError as e:
            return jsonify({"error": "Datos inválidos en la solicitud"}), 400
        except Exception as e:
            app.logger.error(f"Error en cálculo de préstamo: {str(e)}")
            return jsonify({"error": "Error interno en el cálculo"}), 500
    
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
    """Inicializa base de datos con datos base esenciales."""
    
    with app.app_context():
        try:
            # Crear tablas si no existen
            db.create_all()
            
            # === TENANT POR DEFECTO ===
            if not Tenant.query.first():
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
            if not User.query.filter_by(email=admin_email).first():
                superadmin_role = Role.query.filter_by(name='Super Administrador').first()
                if superadmin_role:
                    admin = User(
                        email=admin_email,
                        password_hash='',  # Se establece después
                        role_id=superadmin_role.id
                    )
                    admin.set_password('admin123')
                    
                    profile = ClientProfile(
                        user_id=admin.id,
                        full_name='Super Administrador LAZO ARCE'
                    )
                    
                    db.session.add_all([admin, profile])
                    db.session.commit()
                    
                    print("🔐 Usuario admin creado:")
                    print(f"   Email: {admin_email}")
                    print(f"   Password: admin123")
                    print("⚠️  ¡CAMBIAR CONTRASEÑA EN PRODUCCIÓN INMEDIATAMENTE!")
            
            # === PRODUCTO POR DEFECTO ===
            if not LoanProduct.query.filter_by(name='Préstamo Personal Clásico').first():
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
            if not Account.query.first():
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
            if not Employee.query.first():
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
            print(f"📊 Total usuarios: {User.query.count()}")
            print(f"💰 Productos activos: {LoanProduct.query.filter_by(is_active=True).count()}")
            print(f"🏦 Cuentas contables: {Account.query.count()}")
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error en setup_database: {str(e)}")
            print(f"❌ Error en inicialización: {str(e)}")

def initialize_database(app):
    """Alias para compatibilidad con código legacy."""
    setup_database(app)

# Crear app global para desarrollo
app = None

if __name__ == '__main__':
    app = create_app()
    
    # Inicializar base de datos (solo desarrollo/testing)
    if os.environ.get('FLASK_ENV', 'development') in ['development', 'testing']:
        setup_database(app)
    
    # Configuración de servidor
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '127.0.0.1')
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    app.run(host=host, port=port, debug=debug)