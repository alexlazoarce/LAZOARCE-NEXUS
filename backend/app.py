import os

from flask import Flask, jsonify, request, make_response, g

from flask_cors import CORS

from flask_jwt_extended import (

    create_access_token, jwt_required, get_jwt_identity, 

    JWTManager, get_jwt

)

from flask_migrate import Migrate

from functools import wraps

from datetime import datetime, date, timedelta

# Inicializar extensiones globales

db = None

jwt = None

migrate = None

def create_app(testing=False, testing_config=None):

    """Application factory function."""

    app = Flask(__name__)

    CORS(app)

    

    # === CONFIGURACIÓN ===

    if testing_config:

        app.config.from_object(testing_config)

    else:

        app.config.from_object('config.DevelopmentConfig')

    

    # Variables de entorno críticas

    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', app.config['SECRET_KEY'])

    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', app.config['JWT_SECRET_KEY'])

    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', app.config['SQLALCHEMY_DATABASE_URI'])

    

    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=8)

    

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

        accounting_bp, invoicing_bp, billing_bp

    )

    

    app.register_blueprint(auth_bp, url_prefix='/api')

    app.register_blueprint(loan_management_bp, url_prefix='/api')

    app.register_blueprint(hr_bp, url_prefix='/api')

    app.register_blueprint(ett_bp, url_prefix='/api')

    app.register_blueprint(accounting_bp, url_prefix='/api')

    app.register_blueprint(invoicing_bp, url_prefix='/api')

    app.register_blueprint(billing_bp, url_prefix='/api')

    

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

                    return jsonify({"message": "Acceso no autorizado"}), 403

                return fn(*args, **kwargs)

            return wrapper

        return decorator

    

    app.jinja_env.globals['require_roles'] = require_roles

    

    # === RUTAS PRINCIPALES (Fallbacks) ===

    

    # Health check

    @app.route('/api/health')

    def health_check():

        return jsonify({

            "status": "healthy", 

            "timestamp": datetime.utcnow().isoformat(),

            "version": "2.0",

            "environment": app.config.get('ENVIRONMENT', 'development')

        })

    

    # Root endpoint

    @app.route('/')

    def index():

        return jsonify({

            "message": "Sistema de Gestión Financiera LAZO ARCE",

            "version": "2.0",

            "endpoints": [

                "/api/health",

                "/api/auth/register",

                "/api/auth/login", 

                "/api/applications",

                "/api/products"

            ],

            "docs": "/api/docs"  # Swagger docs

        })

    

    # Error handlers

    @app.errorhandler(404)

    def not_found(error):

        return jsonify({"message": "Endpoint no encontrado"}), 404

    

    @app.errorhandler(500)

    def internal_error(error):

        db.session.rollback()

        return jsonify({"message": "Error interno del servidor"}), 500

    

    @app.errorhandler(400)

    def bad_request(error):

        return jsonify({"message": "Solicitud inválida"}), 400

    

    @app.errorhandler(401)

    def unauthorized(error):

        return jsonify({"message": "No autorizado"}), 401

    

    @app.errorhandler(403)

    def forbidden(error):

        return jsonify({"message": "Acceso prohibido"}), 403

    

    # === RUTAS LEGACY (para compatibilidad) ===

    

    # AUTH - Register (simplificado)

    @app.route('/api/auth/register', methods=['POST'])

    def register():

        """Registro básico de cliente (legacy)"""

        from .models import User, Role, ClientProfile

        

        data = request.get_json()

        if not data or not data.get('email') or not data.get('password'):

            return jsonify({"message": "Email y contraseña requeridos"}), 400

        

        # Verificar si ya existe

        if User.query.filter_by(email=data['email']).first():

            return jsonify({"message": "El correo ya está registrado"}), 409

        

        try:

            # Obtener rol de cliente

            client_role = Role.query.filter_by(name='Cliente').first()

            if not client_role:

                return jsonify({"message": "Rol de cliente no encontrado"}), 500

            

            # Crear usuario

            user = User(

                email=data['email'],

                role_id=client_role.id,

                full_name=data.get('full_name', data['email'])

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

            from .services import audit_service

            audit_service.log_action(

                action='USER_REGISTER',

                user_id=user.id,

                details=f"Nuevo cliente registrado: {user.email}"

            )

            

            return jsonify({

                "message": "Usuario creado exitosamente",

                "user_id": user.id,

                "email": user.email

            }), 201

            

        except Exception as e:

            db.session.rollback()

            return jsonify({"message": f"Error al crear usuario: {str(e)}"}), 500

    

    # AUTH - Login (multi-tenant compatible)

    @app.route('/api/auth/login', methods=['POST'])

    def login():

        """Login con soporte multi-tenant"""

        from .models import User, Tenant

        

        data = request.get_json()

        if not data or not data.get('email') or not data.get('password'):

            return jsonify({"message": "Email y contraseña requeridos"}), 400

        

        email = data['email']

        password = data['password']

        tenant_name = data.get('tenant_name')

        

        try:

            # Determinar tenant

            if email == 'support@lazoarce.com' or not tenant_name:

                # Super admin o tenant por defecto

                tenant = Tenant.query.filter_by(company_name='LAZOARCE NEXUS').first()

            else:

                tenant = Tenant.query.filter_by(company_name=tenant_name).first()

            

            if not tenant:

                return jsonify({"message": "Inquilino no encontrado"}), 404

            

            # Buscar usuario en el tenant

            user = User.query.filter_by(

                email=email, 

                tenant_id=tenant.id

            ).first()

            

            if not user or not user.check_password(password):

                return jsonify({"message": "Credenciales incorrectas"}), 401

            

            # Generar token JWT

            roles = [role.name for role in user.roles]

            additional_claims = {

                'roles': roles,

                'tenant_id': tenant.id,

                'tenant_name': tenant.company_name

            }

            

            access_token = create_access_token(

                identity=user.id,  # Usar ID como identidad principal

                additional_claims=additional_claims

            )

            

            # Log de auditoría

            from .services import audit_service

            try:

                audit_service.log_action(

                    action='USER_LOGIN',

                    user_id=user.id,

                    tenant_id=tenant.id,

                    details=f"Login exitoso: {user.email} en tenant {tenant.company_name}"

                )

            except:

                pass  # No fallar login por error de auditoría

            

            return jsonify({

                "access_token": access_token,

                "user": {

                    "id": user.id,

                    "email": user.email,

                    "full_name": user.full_name,

                    "roles": roles,

                    "tenant": {

                        "id": tenant.id,

                        "name": tenant.company_name

                    }

                }

            })

            

        except Exception as e:

            return jsonify({"message": "Error en autenticación"}), 500

    

    # Profile (mejorado)

    @app.route('/api/profile', methods=['GET', 'PUT'])

    @jwt_required()

    def user_profile():

        """Gestión de perfil de usuario"""

        from .models import User, ClientProfile

        

        current_user_id = get_jwt_identity()

        user = User.query.get_or_404(current_user_id)

        

        if request.method == 'GET':

            profile_data = {

                "id": user.id,

                "email": user.email,

                "full_name": user.full_name,

                "roles": [r.name for r in user.roles],

                "tenant_id": user.tenant_id if hasattr(user, 'tenant_id') else None

            }

            

            # Incluir perfil si existe

            if hasattr(user, 'profile') and user.profile:

                profile_data.update({

                    "profile": user.profile.to_dict()

                })

            

            return jsonify(profile_data)

        

        # PUT - Actualizar perfil

        data = request.get_json()

        if not data:

            return jsonify({"message": "Datos requeridos"}), 400

        

        try:

            # Actualizar perfil

            profile = getattr(user, 'profile', None)

            if profile:

                profile.full_name = data.get('full_name', profile.full_name)

                profile.phone_number = data.get('phone_number', profile.phone_number)

                profile.address = data.get('address', profile.address)

                profile.dui = data.get('dui', profile.dui)

                profile.nit = data.get('nit', profile.nit)

            else:

                profile = ClientProfile(

                    user_id=user.id,

                    full_name=data.get('full_name', user.full_name or ''),

                    phone_number=data.get('phone_number'),

                    address=data.get('address'),

                    dui=data.get('dui'),

                    nit=data.get('nit')

                )

                db.session.add(profile)

                setattr(user, 'profile', profile)

            

            db.session.commit()

            return jsonify({"message": "Perfil actualizado exitosamente"})

            

        except Exception as e:

            db.session.rollback()

            return jsonify({"message": f"Error actualizando perfil: {str(e)}"}), 500

    

    return app

def setup_database(app):

    """Inicializa base de datos con datos base."""

    from .models import (

        Tenant, Role, User, ClientProfile, LoanProduct, Account, 

        NotificationTemplate

    )

    

    with app.app_context():

        # Crear tablas

        db.create_all()

        

        # === TENANTS ===

        if not Tenant.query.first():

            default_tenant = Tenant(company_name='LAZOARCE NEXUS')

            db.session.add(default_tenant)

            db.session.commit()

        else:

            default_tenant = Tenant.query.first()

        

        # === ROLES ===

        if not Role.query.first():

            roles_data = [

                ('Super Administrador', default_tenant.id),

                ('Administrador General', default_tenant.id),

                ('Ejecutivo de Crédito', default_tenant.id),

                ('Cobrador', default_tenant.id),

                ('Contador', default_tenant.id),

                ('Cliente', default_tenant.id)

            ]

            

            roles = [Role(name=name, tenant_id=tenant_id) for name, tenant_id in roles_data]

            db.session.bulk_save_objects(roles)

            db.session.commit()

        

        # === USUARIO ADMIN ===

        if not User.query.filter_by(email='admin@lazoarce.com').first():

            superadmin_role = Role.query.filter_by(name='Super Administrador').first()

            if superadmin_role:

                admin = User(

                    email='admin@lazoarce.com',

                    tenant_id=default_tenant.id,

                    role_id=superadmin_role.id,

                    full_name='Super Administrador'

                )

                admin.set_password('admin123')

                

                profile = ClientProfile(

                    user_id=admin.id,

                    full_name='Super Administrador'

                )

                

                db.session.add_all([admin, profile])

                db.session.commit()

        

        # === PRODUCTO POR DEFECTO ===

        if not LoanProduct.query.first():

            default_product = LoanProduct(

                name="Préstamo Personal Clásico",

                min_amount=1000.0,

                max_amount=50000.0,

                interest_rate=12.0,  # 12% anual

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

        

        # === CUENTAS CONTABLES ===

        if not Account.query.first():

            accounts = [

                # Activos

                Account(name='Caja', category='Asset', normal_balance='Debit'),

                Account(name='Bancos', category='Asset', normal_balance='Debit'),

                Account(name='Cuentas por Cobrar Clientes', category='Asset', normal_balance='Debit'),

                # Pasivos

                Account(name='Retenciones por Pagar', category='Liability', normal_balance='Credit'),

                Account(name='Sueldos por Pagar', category='Liability', normal_balance='Credit'),

                # Patrimonio

                Account(name='Capital Social', category='Equity', normal_balance='Credit'),

                # Ingresos

                Account(name='Ingresos por Intereses', category='Revenue', normal_balance='Credit'),

                Account(name='Ingresos por Comisiones', category='Revenue', normal_balance='Credit'),

                # Gastos

                Account(name='Sueldos y Salarios', category='Expense', normal_balance='Debit')

            ]

            db.session.bulk_save_objects(accounts)

            db.session.commit()

        

        # === PLANTILLAS DE NOTIFICACIÓN ===

        if not NotificationTemplate.query.first():

            templates = [

                NotificationTemplate(

                    slug='loan-application-received',

                    subject='Recibimos tu solicitud de préstamo',

                    body='Hola {customer_name},\n\nHemos recibido tu solicitud por ${amount}. Te contactaremos pronto.'

                ),

                NotificationTemplate(

                    slug='loan-approved',

                    subject='¡Tu préstamo fue APROBADO! 🎉',

                    body='¡Felicidades {customer_name}! Tu préstamo por ${amount} ha sido aprobado.'

                ),

                NotificationTemplate(

                    slug='loan-rejected',

                    subject='Actualización de tu solicitud',

                    body='Hola {customer_name},\n\nLamentamos informarte que tu solicitud no pudo ser aprobada.'

                )

            ]

            db.session.bulk_save_objects(templates)

            db.session.commit()

        

        print("✅ Base de datos inicializada correctamente")

def initialize_database(app):

    """Alias para compatibilidad."""

    setup_database(app)

if __name__ == '__main__':

    app = create_app()

    

    # Inicializar base de datos (solo en desarrollo)

    if os.environ.get('FLASK_ENV', 'development') != 'production':

        setup_database(app)

    

    # Configuración de servidor

    port = int(os.environ.get('PORT', 5000))

    host = os.environ.get('HOST', '127.0.0.1')

    debug = os.environ.get('FLASK_ENV') == 'development'

    

    app.run(host=host, port=port, debug=debug)