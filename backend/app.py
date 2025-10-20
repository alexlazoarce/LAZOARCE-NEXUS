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

# Importar modelos (importados aquí para evitar circular imports)

from .models import (

    User, Role, ClientProfile, LoanProduct, Account, 

    NotificationTemplate, Tenant, LoanApplication, Payment,

    AuditLog, Employee, CommunicationLog

)

def create_app(testing=False, testing_config=None):

    """Application factory function - patrón moderno Flask."""

    

    app = Flask(__name__)

    CORS(app)

    

    # === CONFIGURACIÓN ===

    if testing_config:

        app.config.from_object(testing_config)

    else:

        app.config.from_object('config.DevelopmentConfig')

    

    # Variables de entorno críticas (con fallback)

    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', app.config['SECRET_KEY'])

    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', app.config['JWT_SECRET_KEY'])

    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', app.config['SQLALCHEMY_DATABASE_URI'])

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    

    # JWT configuración

    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=8)

    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)

    

    # Inicializar extensiones

    global db, jwt, migrate

    db = db or SQLAlchemy()

    jwt = jwt or JWTManager()

    migrate = migrate or Migrate()

    

    db.init_app(app)

    jwt.init_app(app)

    migrate.init_app(app, db)

    

    # === REGISTRO DE BLUEPRINTS ===

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

    

    # === DECORADORES DE SEGURIDAD ===

    

    def require_roles(*required_roles):

        """Decorator para requerir roles específicos."""

        def decorator(fn):

            @wraps(fn)

            @jwt_required()

            def wrapper(*args, **kwargs):

                claims = get_jwt()

                user_roles = claims.get('roles', [])

                

                if not any(role in user_roles for role in required_roles):

                    return jsonify({

                        "message": "Acceso no autorizado",

                        "required_roles": required_roles

                    }), 403

                

                # Agregar usuario actual al contexto

                g.current_user = User.query.get(get_jwt_identity())

                return fn(*args, **kwargs)

            return wrapper

        return decorator

    

    def role_required(*roles):

        """Alias para require_roles."""

        return require_roles(*roles)

    

    # Registrar en Jinja y app context

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

                    details=f"Status: {response.status_code}",

                    ip_address=request.remote_addr

                )

                db.session.add(audit_log)

                db.session.commit()

            except:

                db.session.rollback()

        

        return response

    

    # === RUTAS PRINCIPALES ===

    

    @app.route('/api/health')

    def health_check():

        """Health check endpoint."""

        return jsonify({

            "status": "healthy", 

            "timestamp": datetime.utcnow().isoformat(),

            "version": "2.0",

            "environment": app.config.get('ENVIRONMENT', 'development'),

            "database": db.engine.has_table("user")

        })

    

    @app.route('/api/metrics')

    @jwt_required()

    def metrics():

        """Métricas básicas del sistema."""

        from sqlalchemy import func

        

        stats = {

            "users_total": db.session.query(func.count(User.id)).scalar(),

            "applications_pending": db.session.query(func.count(LoanApplication.id)).filter(

                LoanApplication.status == 'Pendiente'

            ).scalar(),

            "payments_today": db.session.query(func.count(Payment.id)).filter(

                Payment.payment_date == date.today()

            ).scalar(),

            "active_employees": db.session.query(func.count(Employee.id)).filter(

                Employee.is_active == True

            ).scalar()

        }

        

        return jsonify(stats)

    

    @app.route('/')

    def index():

        """Landing page con documentación."""

        return jsonify({

            "message": "Sistema de Gestión Financiera LAZO ARCE",

            "version": "2.0",

            "endpoints": [

                "/api/health",

                "/api/auth/register",

                "/api/auth/login", 

                "/api/loans/applications",

                "/api/loans/products",

                "/api/hr/employees",

                "/api/accounting/accounts"

            ],

            "docs": "/api/docs/swagger",  # Future Swagger

            "blueprints": [bp.name for bp in app.blueprints.values()]

        })

    

    # === RUTAS LEGACY (Compatibilidad) ===

    

    @app.route('/api/auth/register', methods=['POST'])

    def legacy_register():

        """Registro legacy para compatibilidad."""

        data = request.get_json()

        if not data or not data.get('email') or not data.get('password'):

            return jsonify({"message": "Email y contraseña requeridos"}), 400

        

        # Verificar si ya existe

        existing_user = User.query.filter_by(email=data['email']).first()

        if existing_user:

            return jsonify({"message": "El correo ya está registrado"}), 409

        

        try:

            # Obtener rol de cliente por defecto

            client_role = Role.query.filter_by(name='Cliente').first()

            if not client_role:

                return jsonify({"message": "Rol de cliente no encontrado"}), 500

            

            # Crear usuario

            user = User(

                email=data['email'],

                full_name=data.get('full_name', data['email']),

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

                user_id=user.id,

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

            return jsonify({"message": f"Error al crear usuario"}), 500

    

    @app.route('/api/loans/calculate', methods=['POST'])

    @jwt_required()

    @role_required('Cliente', 'Ejecutivo de Crédito', 'Administrador General')

    def calculate_loan():

        """Cálculo de préstamos mejorado."""

        from .services.loan_service import LoanCalculator

        

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

            

            # Calcular préstamo

            calculator = LoanCalculator(product)

            result = calculator.calculate(monto, plazo, data.get('opciones', {}))

            

            if 'error' in result:

                return jsonify(result), 400

            

            return jsonify({

                "success": True,

                "calculation": result

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

        # Crear tablas si no existen

        db.create_all()

        

        # === TENANT POR DEFECTO ===

        if not Tenant.query.first():

            default_tenant = Tenant(company_name='LAZOARCE NEXUS', is_active=True)

            db.session.add(default_tenant)

            db.session.commit()

        else:

            default_tenant = Tenant.query.first()

        

        # === ROLES ===

        required_roles = [

            'Super Administrador', 'Administrador General', 

            'Ejecutivo de Crédito', 'Cobrador', 'Contador', 'Cliente'

        ]

        

        existing_roles = {role.name for role in Role.query.all()}

        missing_roles = [role for role in required_roles if role not in existing_roles]

        

        if missing_roles:

            roles_to_create = [

                Role(name=role_name, tenant_id=default_tenant.id) 

                for role_name in missing_roles

            ]

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

                    full_name='Super Administrador LAZO ARCE',

                    role_id=superadmin_role.id

                )

                admin.set_password('admin123')  # CAMBIAR EN PRODUCCIÓN

                

                profile = ClientProfile(

                    user_id=admin.id,

                    full_name='Super Administrador LAZO ARCE'

                )

                

                db.session.add_all([admin, profile])

                db.session.commit()

                

                print("🔐 Usuario admin creado:")

                print(f"   Email: {admin_email}")

                print(f"   Password: admin123")

                print("⚠️   ¡CAMBIAR CONTRASEÑA EN PRODUCCIÓN INMEDIATAMENTE!")

        

        # === PRODUCTO POR DEFECTO ===

        if not LoanProduct.query.filter_by(name='Préstamo Personal Clásico').first():

            default_product = LoanProduct(

                name="Préstamo Personal Clásico",

                min_amount=1000.0,

                max_amount=50000.0,

                interest_rate=12.0,

                commission_rate=2.0,

                term_months=12,

                comision_apertura=0.02,

                comision_administracion=10.0,

                seguro=5.0,

                comisiones_se_descuentan_capital=True,

                is_active=True

            )

            db.session.add(default_product)

            db.session.commit()

            print("✅ Producto de préstamo por defecto creado")

        

        # === CUENTAS CONTABLES BÁSICAS ===

        if not Account.query.first():

            basic_accounts = [

                # Activos

                {'name': 'Caja', 'category': 'Asset', 'normal_balance': 'Debit', 'account_code': '1101'},

                {'name': 'Bancos', 'category': 'Asset', 'normal_balance': 'Debit', 'account_code': '1102'},

                {'name': 'Cuentas por Cobrar Clientes', 'category': 'Asset', 'normal_balance': 'Debit', 'account_code': '1201'},

                

                # Pasivos

                {'name': 'Retenciones por Pagar', 'category': 'Liability', 'normal_balance': 'Credit', 'account_code': '2101'},

                {'name': 'Sueldos por Pagar', 'category': 'Liability', 'normal_balance': 'Credit', 'account_code': '2102'},

                

                # Patrimonio

                {'name': 'Capital Social', 'category': 'Equity', 'normal_balance': 'Credit', 'account_code': '3101'},

                

                # Ingresos

                {'name': 'Ingresos por Intereses', 'category': 'Revenue', 'normal_balance': 'Credit', 'account_code': '4101'},

                {'name': 'Ingresos por Comisiones', 'category': 'Revenue', 'normal_balance': 'Credit', 'account_code': '4102'},

                

                # Gastos

                {'name': 'Sueldos y Salarios', 'category': 'Expense', 'normal_balance': 'Debit', 'account_code': '5101'},

            ]

            

            accounts = [Account(**data) for data in basic_accounts]

            db.session.bulk_save_objects(accounts)

            db.session.commit()

            print(f"✅ {len(accounts)} cuentas contables básicas creadas")

        

        # === PLANTILLAS DE NOTIFICACIÓN ===

        if not NotificationTemplate.query.first():

            templates = [

                NotificationTemplate(

                    slug='loan-application-received',

                    subject='✅ Recibimos tu solicitud de préstamo',

                    body='Hola {customer_name},\n\nHemos recibido tu solicitud por ${amount}. Te contactaremos pronto.',

                    type='Email'

                ),

                NotificationTemplate(

                    slug='loan-approved',

                    subject='🎉 ¡Tu préstamo fue APROBADO!',

                    body='¡Felicidades {customer_name}! Tu préstamo por ${amount} ha sido aprobado.\n\nPróximos pasos:',

                    type='Email'

                ),

                NotificationTemplate(

                    slug='payment-reminder',

                    subject='⏰ Recordatorio de pago',

                    body='Hola {customer_name},\n\nTe recordamos que vence tu cuota de ${amount} el {due_date}.',

                    type='SMS'

                )

            ]

            db.session.bulk_save_objects(templates)

            db.session.commit()

            print("✅ Plantillas de notificación creadas")

        

        # === EMPLEADO DE PRUEBA ===

        if not Employee.query.first():

            test_employee = Employee(

                full_name='Ana García López',

                position='Ejecutivo de Crédito',

                salary=1200.00,

                hire_date=date(2024, 1, 15),

                dui='12345678-9',

                nit='1234-567890-123-4',

                is_active=True

            )

            db.session.add(test_employee)

            db.session.commit()

            print("✅ Empleado de prueba creado")

        

        print("✅ 🎉 Base de datos inicializada correctamente")

        print(f"📊 Total usuarios: {User.query.count()}")

        print(f"💰 Productos activos: {LoanProduct.query.filter_by(is_active=True).count()}")

        print(f"🏦 Cuentas contables: {Account.query.count()}")

def initialize_database(app):

    """Alias para compatibilidad con código legacy."""

    setup_database(app)

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