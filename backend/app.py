import os

from flask import Flask, jsonify, request, make_response

from flask_cors import CORS

from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt

from flask_migrate import Migrate

from dotenv import load_dotenv

# Importar extensiones y modelos

from backend.extensions import db, jwt

from backend.models import (

    Role, User, ClientProfile, LoanProduct, LoanApplication, Account, Employee,

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