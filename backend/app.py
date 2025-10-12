import os
from flask import Flask, jsonify, request, make_response, g
from flask_cors import CORS
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, JWTManager, get_jwt
from functools import wraps

from .models import (
    db, Tenant, Role, User, LoanProduct, LoanApplication, Account, JournalEntry, Transaction,
    Employee, Lead, CommunicationLog, Payment, NotificationTemplate, AuditLog,
    Opportunity, Project, Task
)
from .loan_calculator import calculate_loan_details
from .pdf_generator import generate_contract_pdf
from . import accounting_service
from . import payroll_service
from . import collections_service
from . import notification_service
from . import audit_service
from . import event_service
from datetime import datetime, date, timedelta

def create_app():
    app = Flask(__name__)
    CORS(app)
    app.config['SECRET_KEY'] = 'dev'
    app.config['JWT_SECRET_KEY'] = 'dev'
    instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(instance_path, 'lazoarce.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    jwt = JWTManager(app)

    def tenant_required(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            g.tenant_id = claims.get('tenant_id')
            if not g.tenant_id: return jsonify({"message": "Token JWT no contiene tenant_id"}), 400
            g.user = User.query.filter_by(email=get_jwt_identity(), tenant_id=g.tenant_id).first_or_404()
            g.user_roles = [role.name for role in g.user.roles]
            return fn(*args, **kwargs)
        return wrapper

    @app.route('/api/auth/login', methods=['POST'])
    def login():
        data = request.get_json()
        tenant_name = data.get('tenant_name')
        email = data.get('email')
        password = data.get('password')

        if not tenant_name or not email or not password:
            return jsonify({"message": "Faltan el nombre del inquilino, el email o la contraseña."}), 400

        if email == 'support@lazoarce.com':
            tenant = Tenant.query.filter_by(company_name='LAZOARCE NEXUS').first()
        else:
            tenant = Tenant.query.filter_by(company_name=tenant_name).first()

        if not tenant:
            return jsonify({"message": "Inquilino no encontrado."}), 404

        user = User.query.filter_by(email=email, tenant_id=tenant.id).first()

        if user and user.check_password(password):
            roles = [role.name for role in user.roles]
            additional_claims = {'roles': roles, 'tenant_id': user.tenant_id}
            access_token = create_access_token(identity=user.email, additional_claims=additional_claims)

            try:
                audit_user_id = user.id
                audit_tenant_id = user.tenant_id
                audit_service.log_action('USER_LOGIN', user_id=audit_user_id, tenant_id=audit_tenant_id, details=f"User {email} logged in to tenant {tenant.company_name}.")
            except Exception as e:
                print(f"Error during audit logging: {e}")

            return jsonify(access_token=access_token)

        return jsonify({"message": "Credenciales incorrectas para el inquilino especificado."}), 401

    @app.route('/api/profile', methods=['GET', 'PUT'])
    @tenant_required
    def user_profile():
        if request.method == 'GET':
            return jsonify({"full_name": g.user.full_name, "dui": g.user.dui, "nit": g.user.nit, "email": g.user.email, "roles": g.user_roles})
        data = request.get_json()
        g.user.full_name = data.get('full_name', g.user.full_name)
        g.user.dui = data.get('dui', g.user.dui)
        g.user.nit = data.get('nit', g.user.nit)
        db.session.commit()
        return jsonify({"message": "Perfil actualizado."})

    @app.route('/api/products', methods=['GET'])
    @tenant_required
    def get_products():
        products = LoanProduct.query.filter_by(tenant_id=g.tenant_id, is_active=True).all()
        return jsonify([p.to_dict() for p in products])

    @app.route('/api/applications', methods=['POST'])
    @tenant_required
    def create_application():
        if not g.user.full_name or not g.user.dui or not g.user.nit:
            return jsonify({"message": "Por favor, complete su perfil (Nombre, DUI y NIT) antes de solicitar un préstamo."}), 400
        data = request.get_json()
        product = LoanProduct.query.filter_by(id=data['product_id'], tenant_id=g.tenant_id).first_or_404()
        new_application = LoanApplication(tenant_id=g.tenant_id, user_id=g.user.id, product_id=product.id, amount_requested=data['amount_requested'], term_months=data['term_months'])
        db.session.add(new_application)
        db.session.commit()
        return jsonify(new_application.to_dict()), 201

    @app.route('/api/applications', methods=['GET'])
    @tenant_required
    def get_applications():
        if 'Admin' in g.user_roles:
            apps = LoanApplication.query.filter_by(tenant_id=g.tenant_id).all()
        else:
            apps = LoanApplication.query.filter_by(tenant_id=g.tenant_id, user_id=g.user.id).all()
        return jsonify([app.to_dict() for app in apps])

    @app.route('/api/tenants', methods=['GET', 'POST'])
    @tenant_required
    def handle_tenants():
        if 'SuperAdmin' not in g.user_roles:
            return jsonify({"message": "Acceso de Super Administrador requerido."}), 403

        if request.method == 'GET':
            tenants = Tenant.query.filter(Tenant.company_name != 'LAZOARCE NEXUS').all()
            return jsonify([t.to_dict() for t in tenants])

        if request.method == 'POST':
            data = request.get_json()
            name = data.get('name')
            admin_email = data.get('admin_email')
            admin_password = data.get('admin_password')

            if not name or not admin_email or not admin_password:
                return jsonify({'msg': 'Faltan datos para crear el inquilino.'}), 400

            if Tenant.query.filter_by(company_name=name).first():
                return jsonify({'msg': f"El inquilino '{name}' ya existe."}), 409

            new_tenant = Tenant(company_name=name)
            db.session.add(new_tenant)
            db.session.flush()

            role_names = ['Admin', 'Cliente', 'Contador', 'Ejecutivo de Crédito', 'Cobrador', 'Soporte']
            roles = [Role(name=r, tenant_id=new_tenant.id) for r in role_names]
            db.session.bulk_save_objects(roles)
            db.session.flush()

            admin_role = Role.query.filter_by(name='Admin', tenant_id=new_tenant.id).first()
            if User.query.filter_by(email=admin_email, tenant_id=new_tenant.id).first():
                 db.session.rollback()
                 return jsonify({'msg': f"El email '{admin_email}' ya está en uso en este inquilino."}), 409

            admin_user = User(
                email=admin_email,
                tenant_id=new_tenant.id,
                full_name=f"Admin de {name}"
            )
            admin_user.set_password(admin_password)
            admin_user.roles.append(admin_role)
            db.session.add(admin_user)

            db.session.commit()
            return jsonify({'msg': f"Inquilino '{name}' creado con éxito.", 'tenant': new_tenant.to_dict()}), 201

    return app

def setup_database(app):
    with app.app_context():
        db.create_all()
        if not Tenant.query.first():
            default_tenant = Tenant(company_name='LAZOARCE NEXUS')
            db.session.add(default_tenant)
            db.session.commit()

        default_tenant = Tenant.query.first()

        if not Role.query.filter_by(tenant_id=default_tenant.id).first():
            roles = [Role(name=r, tenant_id=default_tenant.id) for r in ['SuperAdmin', 'Admin', 'Cliente', 'Contador', 'Ejecutivo de Crédito', 'Cobrador', 'Soporte']]
            db.session.bulk_save_objects(roles)
            db.session.commit()

        if not User.query.filter_by(email='support@lazoarce.com', tenant_id=default_tenant.id).first():
            super_admin_role = Role.query.filter_by(name='SuperAdmin', tenant_id=default_tenant.id).first()
            super_admin_user = User(email='support@lazoarce.com', tenant_id=default_tenant.id, role_id=super_admin_role.id, full_name='LAZOARCE Support')
            super_admin_user.set_password('superadmin123')
            db.session.add(super_admin_user)
            db.session.commit()