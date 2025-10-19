import os
from flask import Flask, jsonify, request, make_response, g
from flask_cors import CORS
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, JWTManager, get_jwt
from flask_migrate import Migrate
from functools import wraps
from dotenv import load_dotenv

load_dotenv()

from .models import db, Tenant, Role, User, LoanProduct, LoanApplication, Account, JournalEntry, Transaction, Employee, Lead, CommunicationLog, Payment, NotificationTemplate, AuditLog, Opportunity, Project, Task
from .loan_calculator import calculate_loan_details
from .pdf_generator import generate_contract_pdf
from . import accounting_service
from . import payroll_service
from . import collections_service
from . import notification_service
from . import audit_service
from . import event_service
from . import bank_reconciliation_service
from . import absence_service
from . import onboarding_service
from . import attendance_service
from datetime import datetime, date, timedelta
import werkzeug

def create_app():
    app = Flask(__name__)
    CORS(app)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
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

    @app.route('/api/loan_applications', methods=['POST'])
    @tenant_required
    def create_loan_application():
        data = request.get_json()
        product = LoanProduct.query.filter_by(id=data['product_id'], tenant_id=g.tenant_id).first_or_404()

        loan_details = calculate_loan_details(
            principal=data['amount_requested'],
            annual_interest_rate=product.interest_rate,
            term_months=data['term_months'],
            commission_rate=product.commission_rate,
            commission_type='Al Inicio' # Assuming a default, this could be part of the product model
        )

        new_application = LoanApplication(
            tenant_id=g.tenant_id,
            user_id=g.user.id,
            product_id=data['product_id'],
            amount_requested=data['amount_requested'],
            term_months=data['term_months'],
            monthly_payment=loan_details['monthly_payment'],
            total_payment=loan_details['total_payment'],
            status='Pendiente'
        )
        db.session.add(new_application)
        db.session.commit()
        return jsonify({"message": "Solicitud de préstamo creada exitosamente.", "application_id": new_application.id}), 201

    @app.route('/api/loan_applications/<int:app_id>/approve', methods=['POST'])
    @tenant_required
    def approve_loan(app_id):
        application = LoanApplication.query.filter_by(id=app_id, tenant_id=g.tenant_id).first_or_404()
        if application.status != 'Pendiente':
            return jsonify({"error": "La solicitud no está en estado 'Pendiente'."}), 400
        application.status = 'Aprobada'
        application.decision_date = datetime.utcnow()
        db.session.commit()
        return jsonify({"message": "Solicitud aprobada."})

    @app.route('/api/loan_applications/<int:app_id>/reject', methods=['POST'])
    @tenant_required
    def reject_loan(app_id):
        application = LoanApplication.query.filter_by(id=app_id, tenant_id=g.tenant_id).first_or_404()
        if application.status != 'Pendiente':
            return jsonify({"error": "La solicitud no está en estado 'Pendiente'."}), 400
        application.status = 'Rechazada'
        application.decision_date = datetime.utcnow()
        db.session.commit()
        return jsonify({"message": "Solicitud rechazada."})

    @app.route('/api/loan_applications/<int:app_id>/disburse', methods=['POST'])
    @tenant_required
    def disburse_loan(app_id):
        application = LoanApplication.query.filter_by(id=app_id, tenant_id=g.tenant_id).first_or_404()

        if application.status != 'Aprobada':
            return jsonify({"error": "La solicitud no está en estado 'Aprobada'."}), 400

        data = request.get_json()
        disbursement_source = data.get('disbursement_source', 'Bancos') # Default to 'Bancos'

        application.status = 'Desembolsada'
        application.disbursement_date = datetime.utcnow()

        try:
            accounting_service.create_disbursement_journal_entry(application, disbursement_source)
            db.session.commit()
            return jsonify({"message": "Préstamo desembolsado y asiento contable creado."})
        except ValueError as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 400

    @app.route('/api/portfolio/user_status', methods=['GET'])
    @tenant_required
    def get_user_portfolio_status():
        # g.user is populated by the tenant_required decorator
        user_id = g.user.id

        # Call the new service function to get the portfolio status
        portfolio_data = collections_service.get_portfolio_status(user_id)

        if "error" in portfolio_data:
            return jsonify(portfolio_data), 404

        return jsonify(portfolio_data)

    # --- Bank Reconciliation (LAN-CB7) ---
    @app.route('/api/reconciliation/upload', methods=['POST'])
    @tenant_required
    def upload_bank_statement():
        if 'statement' not in request.files:
            return jsonify({"error": "No se encontró el archivo del extracto."}), 400

        file = request.files['statement']
        if file.filename == '':
            return jsonify({"error": "No se seleccionó ningún archivo."}), 400

        # Secure the filename and save it temporarily
        filename = werkzeug.utils.secure_filename(file.filename)
        temp_path = os.path.join('/tmp', filename)
        file.save(temp_path)

        # Extract metadata from form
        account_id = request.form.get('account_id')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        start_balance = request.form.get('start_balance')
        end_balance = request.form.get('end_balance')

        result, status_code = bank_reconciliation_service.process_bank_statement_csv(
            file_path=temp_path,
            tenant_id=g.tenant_id,
            account_id=account_id,
            start_date=start_date,
            end_date=end_date,
            start_balance=start_balance,
            end_balance=end_balance
        )

        # Clean up the temporary file
        os.remove(temp_path)

        return jsonify(result), status_code

    @app.route('/api/reconciliation/statement/<int:statement_id>', methods=['GET'])
    @tenant_required
    def get_reconciliation_status(statement_id):
        statement = bank_reconciliation_service.get_statement_details(statement_id, g.tenant_id)
        return jsonify(statement)

    @app.route('/api/reconciliation/statement/<int:statement_id>/reconcile', methods=['POST'])
    @tenant_required
    def reconcile_bank_statement(statement_id):
        result = bank_reconciliation_service.reconcile_statement(statement_id, g.tenant_id)
        return jsonify(result)

    # --- Financial Reports (LAN-BKS1) ---
    @app.route('/api/reports/balance-sheet', methods=['GET'])
    @tenant_required
    def get_balance_sheet_report():
        report_data = accounting_service.get_balance_sheet(g.tenant_id)
        return jsonify(report_data)

    @app.route('/api/reports/income-statement', methods=['GET'])
    @tenant_required
    def get_income_statement_report():
        report_data = accounting_service.get_income_statement(g.tenant_id)
        return jsonify(report_data)

    # --- Payroll (LAN-NR4) ---
    @app.route('/api/payroll/process', methods=['POST'])
    @tenant_required
    def process_payroll():
        result, status_code = payroll_service.process_payroll_for_tenant(g.tenant_id)
        if status_code == 201:
            db.session.commit()
        else:
            db.session.rollback()
        return jsonify(result), status_code

    # --- Absence Management (LAN-V1A) ---
    @app.route('/api/absences/balance', methods=['GET'])
    @tenant_required
    def get_my_vacation_balance():
        # Assuming the logged-in user is an employee
        employee = Employee.query.filter_by(email=g.user.email, tenant_id=g.tenant_id).first()
        if not employee:
            return jsonify({"error": "No se encontró el perfil de empleado para este usuario."}), 404
        balance = absence_service.get_vacation_balance(employee.id)
        return jsonify({"vacation_balance": balance})

    @app.route('/api/absences/requests', methods=['POST'])
    @tenant_required
    def create_absence_request_route():
        employee = Employee.query.filter_by(email=g.user.email, tenant_id=g.tenant_id).first()
        if not employee:
            return jsonify({"error": "No se encontró el perfil de empleado para este usuario."}), 404

        data = request.get_json()
        try:
            new_request = absence_service.create_absence_request(
                employee_id=employee.id,
                tenant_id=g.tenant_id,
                absence_type=data['absence_type'],
                start_date=date.fromisoformat(data['start_date']),
                end_date=date.fromisoformat(data['end_date']),
                comments=data.get('comments')
            )
            db.session.commit()
            return jsonify({"message": "Solicitud de ausencia creada.", "request_id": new_request.id}), 201
        except (ValueError, KeyError) as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 400

    @app.route('/api/absences/requests', methods=['GET'])
    @tenant_required
    def get_my_absence_requests():
        employee = Employee.query.filter_by(email=g.user.email, tenant_id=g.tenant_id).first()
        if not employee:
            return jsonify({"error": "No se encontró el perfil de empleado para este usuario."}), 404

        requests = absence_service.get_absence_requests_for_employee(employee.id)
        return jsonify([
            {
                "id": req.id,
                "absence_type": req.absence_type,
                "start_date": req.start_date.isoformat(),
                "end_date": req.end_date.isoformat(),
                "status": req.status,
                "comments": req.comments
            } for req in requests
        ])

    @app.route('/api/absences/requests/<int:request_id>/approve', methods=['POST'])
    @tenant_required
    def approve_absence_request_route(request_id):
        # In a real app, you'd check if g.user has manager roles
        try:
            absence_service.approve_absence_request(request_id, g.user.id)
            db.session.commit()
            return jsonify({"message": "Solicitud aprobada."})
        except ValueError as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 400

    # --- Onboarding (LAN-OBD2) ---
    @app.route('/api/onboarding/assign', methods=['POST'])
    @tenant_required
    def assign_onboarding_template():
        # HR/Admin role check would go here
        data = request.get_json()
        try:
            onboarding_service.assign_onboarding_template_to_employee(data['employee_id'], data['template_id'])
            db.session.commit()
            return jsonify({"message": "Plantilla de onboarding asignada correctamente."}), 201
        except (ValueError, KeyError) as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 400

    @app.route('/api/onboarding/my-status', methods=['GET'])
    @tenant_required
    def get_my_onboarding_status():
        employee = Employee.query.filter_by(email=g.user.email, tenant_id=g.tenant_id).first()
        if not employee:
            return jsonify({"error": "No se encontró el perfil de empleado para este usuario."}), 404

        status = onboarding_service.get_employee_onboarding_status(employee.id)
        return jsonify(status)

    @app.route('/api/onboarding/complete-step', methods=['POST'])
    @tenant_required
    def complete_onboarding_step_route():
        employee = Employee.query.filter_by(email=g.user.email, tenant_id=g.tenant_id).first()
        if not employee:
            return jsonify({"error": "No se encontró el perfil de empleado para este usuario."}), 404

        data = request.get_json()
        try:
            onboarding_service.complete_onboarding_step(employee.id, data['step_id'])
            db.session.commit()
            return jsonify({"message": "Paso de onboarding completado."})
        except (ValueError, KeyError) as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 400

    # --- Attendance (LAN-AT5) ---
    @app.route('/api/attendance/my-qr-token', methods=['GET'])
    @tenant_required
    def get_my_qr_token():
        employee = Employee.query.filter_by(email=g.user.email, tenant_id=g.tenant_id).first()
        if not employee:
            return jsonify({"error": "No se encontró el perfil de empleado para este usuario."}), 404
        token = attendance_service.generate_qr_code_token_for_employee(employee.id)
        return jsonify({"qr_code_token": token})

    @app.route('/api/attendance/record', methods=['POST'])
    def record_attendance_route():
        data = request.get_json()
        try:
            record = attendance_service.record_attendance(data['qr_code_token'], data['event_type'])
            db.session.commit()
            return jsonify({"message": f"Asistencia registrada: {record.event_type} a las {record.timestamp}"}), 201
        except (ValueError, KeyError) as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 400

    @app.route('/api/attendance/my-history', methods=['GET'])
    @tenant_required
    def get_my_attendance_history():
        employee = Employee.query.filter_by(email=g.user.email, tenant_id=g.tenant_id).first()
        if not employee:
            return jsonify({"error": "No se encontró el perfil de empleado para este usuario."}), 404

        history = attendance_service.get_attendance_history(employee.id)
        return jsonify([
            {
                "id": rec.id,
                "timestamp": rec.timestamp.isoformat(),
                "event_type": rec.event_type
            } for rec in history
        ])

    return app
