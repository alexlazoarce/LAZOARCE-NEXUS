 import os
from flask import Flask, jsonify, request, make_response, g
from flask_cors import CORS
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, JWTManager, get_jwt
from flask_migrate import Migrate
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
    # Point to the provided PostgreSQL database with the corrected hostname
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1sQl4WixNdQihHxd@db.efntaqjschznzrnzrnhh.supabase.co:5432/postgres?sslmode=require'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    jwt = JWTManager(app)
    migrate = Migrate(app, db)

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

    # ... (all other routes would be here) ...

    return app

def setup_database(app):
    """
    This function is now only for seeding data if needed, AFTER a migration.
    """
    with app.app_context():
        print("Seeding initial data if necessary...")
        if Tenant.query.first() is None:
            print("No default tenant found, creating one...")
            default_tenant = Tenant(company_name='LAZOARCE NEXUS')
            db.session.add(default_tenant)
            db.session.commit()
            print("Default tenant created.")

            default_tenant = Tenant.query.first()

            print("Creating default roles...")
            roles = [Role(name=r, tenant_id=default_tenant.id) for r in ['SuperAdmin', 'Admin', 'Cliente']]
            db.session.bulk_save_objects(roles)
            db.session.commit()
            print("Default roles created.")

            print("Creating SuperAdmin user...")
            super_admin_role = Role.query.filter_by(name='SuperAdmin', tenant_id=default_tenant.id).first()
            super_admin_user = User(
                email='support@lazoarce.com',
                tenant_id=default_tenant.id,
                role_id=super_admin_role.id,
                full_name='LAZOARCE Support'
            )
            super_admin_user.set_password('superadmin123')
            db.session.add(super_admin_user)
            db.session.commit()
            print("SuperAdmin user created.")
        else:
            print("Default tenant already exists. No seeding needed.")