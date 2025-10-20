import os

from flask import Flask, jsonify, request, make_response

from flask_cors import CORS

from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt

from flask_migrate import Migrate

from dotenv import load_dotenv

# Importar extensiones y modelos

from backend.extensions import db, jwt

from backend.models import (

    Role, User, LoanProduct, LoanApplication, Account, Employee, 

    PayrollLog, PaySlip, Lead, CommunicationLog, Payment, 

    NotificationTemplate, AuditLog, Ticket, TicketComment, TaxType,

    ClientCompany, TemporaryAssignment, Invoice, InvoiceItem,

    SubscriptionPlan, Subscription, JournalEntry, Transaction

)

import backend.models  # Para que SQLAlchemy descubra todos los modelos

# Importar blueprints y servicios

from backend.routes.auth import auth_bp

from backend.routes.loan_management import loan_management_bp

from backend.hr.routes import hr_bp

from backend.routes.ett_routes import ett_bp

from backend.routes.accounting_routes import accounting_bp

from backend.routes.invoicing_routes import invoicing_bp

from backend.routes.billing_routes import billing_bp

# Servicios

import backend.services.accounting_service as accounting_service

import backend.services.payroll_service as payroll_service

import backend.services.collections_service as collections_service

import backend.services.notification_service as notification_service

import backend.services.audit_service as audit_service

# Calculadoras y generadores

from backend.loan_calculator import calcular_prestamo_completo as calculate_loan_details

from backend.pdf_generator import generate_contract_pdf

from datetime import datetime, date, timedelta

from dateutil.relativedelta import relativedelta

def create_app():

    """Application factory function - UNIFICADA Y MEJORADA."""

    load_dotenv()

    app = Flask(__name__)

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Configuración de Flask

    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-super-segura')

    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'dev-jwt-super-segura')

    

    # Configuración de base de datos

    if os.environ.get('DATABASE_URL'):

        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL'].replace('postgres://', 'postgresql://')

    else:

        # SQLite local para desarrollo

        instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')

        os.makedirs(instance_path, exist_ok=True)

        db_path = os.path.join(instance_path, 'lazoarce.db')

        app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"

    

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=8)

    # Inicializar extensiones

    db.init_app(app)

    Migrate(app, db)

    JWTManager(app)

    # Registrar Blueprints

    app.register_blueprint(auth_bp, url_prefix='/api')

    app.register_blueprint(loan_management_bp, url_prefix='/api')

    app.register_blueprint(hr_bp, url_prefix='/api')

    app.register_blueprint(ett_bp, url_prefix='/api')

    app.register_blueprint(accounting_bp, url_prefix='/api')

    app.register_blueprint(invoicing_bp, url_prefix='/api')

    app.register_blueprint(billing_bp, url_prefix='/api')

    # --- RUTAS PRINCIPALES (AUTH, LOANS, EMPLOYEES, CRM) ---

    # AUTH ROUTES (mejoradas)

    @app.route('/api/auth/register', methods=['POST'])

    def register():

        data = request.get_json()

        if not data or not data.get('email') or not data.get('password'):

            return jsonify({"message": "Email y contraseña requeridos"}), 400

        

        if User.query.filter_by(email=data['email']).first():

            return jsonify({"message": "El correo ya está registrado"}), 409

        try:

            client_role = Role.query.filter_by(name='Cliente').first()

            if not client_role:

                return jsonify({"message": "Rol de cliente no encontrado"}), 500

            user = User(

                email=data['email'],

                role_id=client_role.id

            )

            user.set_password(data['password'])

            

            # Crear perfil automáticamente

            profile = ClientProfile(

                user_id=user.id,

                full_name=data.get('full_name', data['email'])

            )

            db.session.add(profile)

            db.session.add(user)

            db.session.commit()

            

            return jsonify({

                "message": "Usuario creado exitosamente",

                "user_id": user.id

            }), 201

            

        except Exception as e:

            db.session.rollback()

            return jsonify({"message": f"Error al crear usuario: {str(e)}"}), 500

    @app.route('/api/auth/login', methods=['POST'])

    def login():

        data = request.get_json()

        if not data or not data.get('email') or not data.get('password'):

            return jsonify({"message": "Email y contraseña requeridos"}), 400

        user = User.query.filter_by(email=data['email']).first()

        if user and user.check_password(data['password']):

            access_token = create_access_token(

                identity=user.id,  # Usar ID en lugar de email

                additional_claims={

                    'email': user.email,

                    'roles': [user.role.name],

                    'full_name': user.profile.full_name if user.profile else ''

                }

            )

            

            # Log de auditoría

            audit_service.log_action(

                action='USER_LOGIN',

                user_id=user.id,

                details=f"Login exitoso para {user.email}"

            )

            db.session.commit()

            

            return jsonify({

                "access_token": access_token,

                "user": {

                    "id": user.id,

                    "email": user.email,

                    "full_name": user.profile.full_name if user.profile else '',

                    "roles": [user.role.name]

                }

            })

        

        return jsonify({"message": "Credenciales incorrectas"}), 401

    # USER PROFILE

    @app.route('/api/profile', methods=['GET', 'PUT'])

    @jwt_required()

    def user_profile():

        current_user_id = get_jwt_identity()

        user = User.query.get_or_404(current_user_id)

        

        if request.method == 'GET':

            return jsonify(user.to_dict())

        

        data = request.get_json()

        if not data:

            return jsonify({"message": "Datos requeridos"}), 400

        

        # Actualizar perfil

        profile = user.profile

        if profile:

            profile.full_name = data.get('full_name', profile.full_name)

            profile.phone_number = data.get('phone_number', profile.phone_number)

            profile.address = data.get('address', profile.address)

            profile.dui = data.get('dui', profile.dui)

            profile.nit = data.get('nit', profile.nit)

        else:

            profile = ClientProfile(

                user_id=user.id,

                full_name=data.get('full_name', ''),

                phone_number=data.get('phone_number'),

                address=data.get('address'),

                dui=data.get('dui'),

                nit=data.get('nit')

            )

            db.session.add(profile)

        

        db.session.commit()

        return jsonify({"message": "Perfil actualizado exitosamente"})

    # LOAN PRODUCTS

    @app.route('/api/products', methods=['GET', 'POST'])

    @jwt_required()

    def handle_products():

        claims = get_jwt()

        user_roles = claims.get('roles', [])

        

        if request.method == 'POST':

            if 'Admin' not in user_roles and 'Administrador General' not in user_roles:

                return jsonify({"message": "Acceso no autorizado"}), 403

            

            data = request.get_json()

            if not all(k in data for k in ['name', 'min_amount', 'max_amount', 'interest_rate', 'term_months']):

                return jsonify({"message": "Datos incompletos"}), 400

            

            product = LoanProduct(

                name=data['name'],

                min_amount=float(data['min_amount']),

                max_amount=float(data['max_amount']),

                interest_rate=float(data['interest_rate']),

                commission_rate=float(data.get('commission_rate', 0)),

                term_months=int(data['term_months']),

                comision_apertura=float(data.get('comision_apertura', 0)),

                comision_administracion=float(data.get('comision_administracion', 0)),

                seguro=float(data.get('seguro', 0)),

                comisiones_se_descuentan_capital=data.get('comisiones_se_descuentan_capital', True)

            )

            

            db.session.add(product)

            db.session.commit()

            return jsonify(product.to_dict()), 201

        

        # GET - Productos activos

        products = LoanProduct.query.filter_by(is_active=True).order_by(LoanProduct.name).all()

        return jsonify([p.to_dict() for p in products])

    # LOAN APPLICATIONS

    @app.route('/api/applications', methods=['GET', 'POST'])

    @jwt_required()

    def handle_applications():

        current_user_id = get_jwt_identity()

        user = User.query.get_or_404(current_user_id)

        claims = get_jwt()

        user_roles = claims.get('roles', [])

        

        if request.method == 'POST':

            # Validar perfil completo

            if not (user.profile and user.profile.full_name and user.profile.dui and user.profile.nit):

                return jsonify({

                    "message": "Complete su perfil (Nombre, DUI, NIT) antes de solicitar préstamo",

                    "missing_fields": []

                }), 400

            

            data = request.get_json()

            product = LoanProduct.query.get_or_404(data['product_id'])

            

            # Validar monto

            if not (product.min_amount <= data['amount_requested'] <= product.max_amount):

                return jsonify({"message": f"Monto fuera de rango: {product.min_amount} - {product.max_amount}"}), 400

            

            # Calcular préstamo

            calculation = calcular_prestamo_completo(

                monto_solicitado=data['amount_requested'],

                producto=product,

                plazo_meses=data['term_months']

            )

            

            if not calculation.get('success'):

                return jsonify({"message": calculation.get('error', 'Error en cálculo')}), 400

            

            application = LoanApplication(

                user_id=user.id,

                product_id=product.id,

                amount_requested=float(data['amount_requested']),

                term_months=int(data['term_months']),

                commission_calculation_method=data['commission_calculation_method'],

                monthly_payment=calculation['cuota_detalle']['cuota_mensual_total_aprox'],

                total_payment=calculation['resumen_costos']['costo_total_credito'],

                status='Pendiente'

            )

            

            db.session.add(application)

            db.session.commit()

            

            # Notificación

            notification_service.send_notification(

                user_id=user.id,

                template_slug='loan-application-received',

                data={'amount': data['amount_requested']}

            )

            

            return jsonify(application.to_dict()), 201

        

        # GET applications

        if 'Admin' in user_roles or 'Administrador General' in user_roles:

            applications = LoanApplication.query.order_by(LoanApplication.application_date.desc()).all()

        else:

            applications = LoanApplication.query.filter_by(user_id=user.id).all()

        

        return jsonify([app.to_dict() for app in applications])

    @app.route('/api/applications/<int:app_id>/status', methods=['PUT'])

    @jwt_required()

    def update_application_status(app_id):

        claims = get_jwt()

        if 'Admin' not in claims.get('roles', []) and 'Administrador General' not in claims.get('roles', []):

            return jsonify({"message": "Acceso no autorizado"}), 403

        application = LoanApplication.query.get_or_404(app_id)

        data = request.get_json()

        new_status = data.get('status')

        

        if new_status not in ['Aprobada', 'Rechazada', 'Desembolsada']:

            return jsonify({"message": "Estado inválido"}), 400

        

        old_status = application.status

        

        if new_status == 'Desembolsada' and old_status != 'Desembolsada':

            # Crear entrada contable para desembolso

            disbursement_source = data.get('disbursement_source', 'Bancos')

            transactions_data = [

                {

                    'account_name': 'Cuentas por Cobrar Clientes',

                    'type': 'Debit',

                    'amount': application.amount_requested

                },

                {

                    'account_name': disbursement_source,

                    'type': 'Credit',

                    'amount': application.amount_requested

                }

            ]

            

            journal_entry = accounting_service.create_journal_entry(

                date=datetime.utcnow(),

                description=f"Desembolso préstamo {application.id} - {application.applicant.profile.full_name}",

                transactions_data=transactions_data

            )

            application.disbursement_entry = journal_entry

        

        # Actualizar estado

        application.status = new_status

        application.decision_date = datetime.utcnow()

        

        # Notificaciones

        if new_status == 'Aprobada':

            notification_service.send_notification(

                user_id=application.user_id,

                template_slug='loan-approved',

                data={'amount': application.amount_requested}

            )

        elif new_status == 'Rechazada':

            notification_service.send_notification(

                user_id=application.user_id,

                template_slug='loan-rejected'

            )

        

        # Auditoría

        current_user_id = get_jwt_identity()

        audit_service.log_action(

            action='LOAN_STATUS_CHANGE',

            user_id=current_user_id,

            details=f"Préstamo {app_id}: {old_status} → {new_status}"

        )

        

        db.session.commit()

        return jsonify(application.to_dict())

    # EMPLOYEES (CRUD básico)

    @app.route('/api/employees', methods=['GET', 'POST'])

    @jwt_required()

    def handle_employees():

        claims = get_jwt()

        if 'Admin' not in claims.get('roles', []):

            return jsonify({"message": "Acceso no autorizado"}), 403

        

        if request.method == 'POST':

            data = request.get_json()

            employee = Employee(

                full_name=data['full_name'],

                employee_type=data.get('employee_type', 'interno'),

                position=data.get('position'),

                salary=float(data.get('salary', 0)),

                hire_date=date.fromisoformat(data['hire_date']) if data.get('hire_date') else None,

                dui=data.get('dui'),

                nit=data.get('nit'),

                isss_number=data.get('isss_number'),

                afp_number=data.get('afp_number')

            )

            db.session.add(employee)

            db.session.commit()

            return jsonify(employee.to_dict()), 201

        

        employees = Employee.query.filter_by(is_active=True).order_by(Employee.full_name).all()

        return jsonify([e.to_dict() for e in employees])

    # LEADS (CRUD básico)

    @app.route('/api/leads', methods=['GET', 'POST'])

    @jwt_required()

    def handle_leads():

        claims = get_jwt()

        user_roles = claims.get('roles', [])

        if 'Admin' not in user_roles and 'Ejecutivo de Crédito' not in user_roles:

            return jsonify({"message": "Acceso no autorizado"}), 403

        

        if request.method == 'POST':

            data = request.get_json()

            lead = Lead(

                full_name=data['full_name'],

                email=data.get('email'),

                phone=data.get('phone'),

                status=data.get('status', 'Nuevo'),

                source=data.get('source'),

                notes=data.get('notes')

            )

            db.session.add(lead)

            db.session.commit()

            return jsonify(lead.to_dict()), 201

        

        leads = Lead.query.order_by(Lead.created_at.desc()).all()

        return jsonify([lead.to_dict() for lead in leads])

    # HEALTH CHECK

    @app.route('/api/health')

    def health_check():

        return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()})

    # ROOT

    @app.route('/')

    def index():

        return jsonify({

            "message": "Sistema de Gestión Financiera LAZO ARCE",

            "version": "2.0",

            "endpoints": "/api/health, /api/auth/*, /api/applications/*, etc.",

            "docs": "/api/docs"  # Swagger docs si se implementa

        })

    # Error handlers

    @app.errorhandler(404)

    def not_found(error):

        return jsonify({"message": "Endpoint no encontrado"}), 404

    @app.errorhandler(500)

    def internal_error(error):

        db.session.rollback()

        return jsonify({"message": "Error interno del servidor"}), 500

    return app

def setup_database(app):

    """Inicializa base de datos con datos base."""

    with app.app_context():

        db.create_all()

        

        # Roles

        if not Role.query.first():

            roles = [

                'Super Administrador', 'Administrador General', 'Ejecutivo de Crédito',

                'Cobrador', 'Contador', 'Cliente'

            ]

            for role_name in roles:

                db.session.add(Role(name=role_name))

            db.session.commit()

        

        # Admin por defecto

        if not User.query.filter_by(email='admin@lazoarce.com').first():

            admin_role = Role.query.filter_by(name='Super Administrador').first()

            admin = User(email='admin@lazoarce.com', role_id=admin_role.id)

            admin.set_password('admin123')

            profile = ClientProfile(user_id=admin.id, full_name='Super Administrador')

            db.session.add_all([admin, profile])

            db.session.commit()

        

        # Producto por defecto

        if not LoanProduct.query.first():

            product = LoanProduct(

                name="Préstamo Personal Clásico",

                min_amount=1000.0,

                max_amount=50000.0,

                interest_rate=12.0,  # 12% anual

                commission_rate=2.0,  # 2% apertura

                term_months=12,

                comision_apertura=0.02,  # 2%

                comision_administracion=10.0,  # $10 mensual

                seguro=5.0,  # $5 mensual

                comisiones_se_descuentan_capital=True

            )

            db.session.add(product)

            db.session.commit()

        

        # Cuentas contables básicas

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

        

        # Plantillas de notificación

        if not NotificationTemplate.query.first():

            templates = [

                NotificationTemplate(

                    slug='loan-application-received',

                    subject='Recibimos tu solicitud de préstamo',

                    body='Hola {customer_name},\n\nHemos recibido tu solicitud por ${amount}. Te contactaremos pronto.\n\nSaludos,\nLAZO ARCE'

                ),

                NotificationTemplate(

                    slug='loan-approved',

                    subject='¡Tu préstamo fue APROBADO! 🎉',

                    body='¡Felicidades {customer_name}! Tu préstamo por ${amount} ha sido aprobado.\n\nDescarga tu contrato en el portal.\n\n¡Gracias por confiar en nosotros!'

                ),

                NotificationTemplate(

                    slug='loan-rejected',

                    subject='Actualización de tu solicitud',

                    body='Hola {customer_name},\n\nLamentamos informarte que tu solicitud no pudo ser aprobada en esta ocasión.\n\nTe invitamos a mejorar tu perfil y volver a solicitar.\n\nSaludos,\nLAZO ARCE'

                )

            ]

            db.session.bulk_save_objects(templates)

            db.session.commit()

        

        print("✅ Base de datos inicializada correctamente")

def initialize_database(app):

    """Alias para compatibilidad con código anterior."""

    setup_database(app)

if __name__ == '__main__':

    app = create_app()

    

    # Inicializar base de datos

    if os.environ.get('FLASK_ENV') != 'production':

        setup_database(app)

    

    # Configuración de puerto

    port = int(os.environ.get('PORT', 5000))

    host = os.environ.get('HOST', '0.0.0.0') if os.environ.get('FLASK_ENV') == 'production' else '127.0.0.1'

    

    debug = os.environ.get('FLASK_ENV') == 'development'

    app.run(host=host, port=port, debug=debug)