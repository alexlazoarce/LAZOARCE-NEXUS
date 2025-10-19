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
from . import recruitment_service
from . import subscription_service
from . import licensing_service
from . import gym_service
from . import barbershop_service
from . import automation_service
from . import make_integration_service
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

    def module_access_required(module_code):
        def decorator(fn):
            @wraps(fn)
            @tenant_required # Ensures we have g.tenant_id and g.user
            def wrapper(*args, **kwargs):
                # Super Admins have access to everything
                if 'Super Administrador' in g.user_roles:
                    return fn(*args, **kwargs)

                if not subscription_service.has_active_subscription(g.tenant_id, module_code):
                    return jsonify({"message": f"Acceso denegado. Se requiere una suscripción activa para el módulo {module_code}."}), 403
                return fn(*args, **kwargs)
            return wrapper
        return decorator

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
    @module_access_required('LAN-GP1')
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

    # --- Recruitment (LAN-REC7) ---
    @app.route('/api/recruitment/vacancies', methods=['POST'])
    @tenant_required
    def create_vacancy_route():
        # Role check for HR/Admin would be appropriate here
        data = request.get_json()
        data['created_by_id'] = g.user.id # Set the creator from the logged-in user
        try:
            vacancy = recruitment_service.create_job_vacancy(data)
            db.session.commit()
            return jsonify({
                "message": "Vacante creada exitosamente.",
                "vacancy_id": vacancy.id
            }), 201
        except (ValueError, KeyError) as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 400

    @app.route('/api/recruitment/vacancies', methods=['GET'])
    @tenant_required
    def get_all_vacancies_route():
        vacancies = recruitment_service.get_all_vacancies()
        return jsonify([
            {
                "id": v.id,
                "title": v.title,
                "description": v.description,
                "status": v.status,
                "created_by": v.created_by.full_name
            } for v in vacancies
        ])

    @app.route('/api/recruitment/vacancies/<int:vacancy_id>/apply', methods=['POST'])
    def apply_for_vacancy_route(vacancy_id):
        # This endpoint is public-facing, so no @tenant_required
        # The tenant context must be derived from the vacancy itself.
        data = request.get_json()
        try:
            # We pass the vacancy_id to the service to handle tenant scoping internally if needed
            application = recruitment_service.create_candidate_and_apply(vacancy_id, data)
            db.session.commit()
            return jsonify({
                "message": "Aplicación enviada exitosamente.",
                "application_id": application.id
            }), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 400

    @app.route('/api/recruitment/vacancies/<int:vacancy_id>/applications', methods=['GET'])
    @tenant_required
    def get_applications_for_vacancy_route(vacancy_id):
        applications = recruitment_service.get_applications_for_vacancy(vacancy_id)
        return jsonify([
            {
                "id": app.id,
                "candidate_name": app.candidate.full_name,
                "candidate_email": app.candidate.email,
                "application_date": app.application_date.isoformat(),
                "status": app.status
            } for app in applications
        ])

    @app.route('/api/recruitment/applications/<int:application_id>/status', methods=['PUT'])
    @tenant_required
    def update_application_status_route(application_id):
        # Role check for HR/Admin recommended
        data = request.get_json()
        try:
            application = recruitment_service.update_application_status(application_id, data['status'])
            db.session.commit()
            return jsonify({"message": f"Estado de la aplicación actualizado a {application.status}."})
        except (ValueError, KeyError) as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 400

    # --- Subscription Management (LAN-SUB1) ---

    @app.route('/api/subscriptions/tenant/<int:tenant_id>', methods=['GET'])
    @module_access_required('LAN-SUB1') # Only Super Admins can really get here
    def get_tenant_subscriptions_route(tenant_id):
        if 'Super Administrador' not in g.user_roles:
            return jsonify({"message": "Acceso denegado."}), 403

        subscriptions = subscription_service.get_tenant_subscriptions(tenant_id)
        return jsonify(subscriptions)

    @app.route('/api/subscriptions/grant', methods=['POST'])
    @module_access_required('LAN-SUB1')
    def grant_subscription_route():
        if 'Super Administrador' not in g.user_roles:
            return jsonify({"message": "Acceso denegado."}), 403

        data = request.get_json()
        try:
            end_date = datetime.fromisoformat(data['end_date']) if data.get('end_date') else None
            subscription_service.grant_subscription(
                tenant_id=data['tenant_id'],
                module_code=data['module_code'],
                end_date=end_date
            )
            return jsonify({"message": "Suscripción otorgada/actualizada exitosamente."}), 200
        except (ValueError, KeyError) as e:
            return jsonify({"error": str(e)}), 400

    # --- On-Premise Licensing (LAN-LIC1) ---

    with app.app_context():
        # This is a demonstration of how an on-premise instance would check its license on startup.
        # In a real on-premise deployment, this key would be stored in a config file.
        # We will simulate this by checking a dummy key or a key we generate for a test tenant.
        # NOTE: This will run every time the app starts. For a real app, this logic would be
        # more sophisticated, perhaps only running if deployment_type is 'on-premise'.
        print("\n[STARTUP] Realizando simulación de chequeo de licencia on-premise...")

        # To make this simulation work, we'd need to have a tenant with a license key.
        # We'll just use a placeholder for now. The function handles invalid keys gracefully.
        dummy_license_key = "LAN-LIC-DUMMY-KEY-FOR-STARTUP-SIMULATION"
        licensing_service.simulate_on_premise_startup_check(dummy_license_key)


    @app.route('/api/licensing/validate', methods=['POST'])
    def validate_license_route():
        data = request.get_json()
        license_key = data.get('license_key')

        if not license_key:
            return jsonify({"is_valid": False, "error": "Falta la clave de licencia."}), 400

        result = licensing_service.validate_license_key(license_key)

        status_code = 200 if result['is_valid'] else 403 # Forbidden
        return jsonify(result), status_code

    @app.route('/api/licensing/tenant/<int:tenant_id>/generate', methods=['POST'])
    @module_access_required('LAN-LIC1')
    def generate_license_route(tenant_id):
        if 'Super Administrador' not in g.user_roles:
            return jsonify({"message": "Acceso denegado."}), 403

        try:
            # First, ensure the tenant is set to on-premise.
            # This is a simplified approach. A real app might have a dedicated tenant update endpoint.
            tenant = Tenant.query.get(tenant_id)
            if not tenant:
                return jsonify({"error": "Inquilino no encontrado."}), 404
            tenant.deployment_type = 'on-premise'
            db.session.commit()

            new_key = licensing_service.generate_license_key_for_tenant(tenant_id)
            return jsonify({"license_key": new_key})
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

    # --- Gym Management (LAN-GYM1) ---

    @app.route('/api/gym/plans', methods=['POST'])
    @module_access_required('LAN-GYM1')
    def create_plan_route():
        plan = gym_service.create_membership_plan(g.tenant_id, request.get_json())
        return jsonify({'message': 'Plan creado exitosamente', 'plan_id': plan.id}), 201

    @app.route('/api/gym/plans', methods=['GET'])
    @module_access_required('LAN-GYM1')
    def get_plans_route():
        plans = gym_service.get_membership_plans(g.tenant_id)
        return jsonify([{'id': p.id, 'name': p.name, 'price': p.price, 'duration_days': p.duration_days} for p in plans])

    @app.route('/api/gym/members', methods=['POST'])
    @module_access_required('LAN-GYM1')
    def register_member_route():
        member = gym_service.register_member(g.tenant_id, request.get_json())
        return jsonify({'message': 'Miembro registrado exitosamente', 'member_id': member.id}), 201

    @app.route('/api/gym/members', methods=['GET'])
    @module_access_required('LAN-GYM1')
    def get_members_route():
        members = gym_service.get_members(g.tenant_id)
        return jsonify([{
            'id': m.id, 'full_name': m.full_name, 'email': m.email,
            'status': m.status, 'membership_end_date': m.membership_end_date.isoformat() if m.membership_end_date else None
        } for m in members])

    @app.route('/api/gym/members/<int:member_id>/assign-plan', methods=['POST'])
    @module_access_required('LAN-GYM1')
    def assign_plan_route(member_id):
        data = request.get_json()
        member = gym_service.assign_membership_to_member(g.tenant_id, member_id, data['plan_id'])
        return jsonify({'message': f'Plan asignado a {member.full_name}'})

    @app.route('/api/gym/classes', methods=['POST'])
    @module_access_required('LAN-GYM1')
    def create_class_route():
        gym_class = gym_service.create_gym_class(g.tenant_id, request.get_json())
        return jsonify({'message': 'Clase creada exitosamente', 'class_id': gym_class.id}), 201

    @app.route('/api/gym/classes', methods=['GET'])
    @module_access_required('LAN-GYM1')
    def get_classes_route():
        classes = gym_service.get_gym_classes(g.tenant_id)
        return jsonify([{'id': c.id, 'name': c.name, 'instructor': c.instructor, 'schedule': c.schedule} for c in classes])

    @app.route('/api/gym/classes/attendance', methods=['POST'])
    @module_access_required('LAN-GYM1')
    def record_attendance_route():
        data = request.get_json()
        attendance = gym_service.record_class_attendance(g.tenant_id, data['class_id'], data['member_id'])
        return jsonify({'message': 'Asistencia registrada', 'attendance_id': attendance.id}), 201

    # --- Barbershop Management (LAN-BAR1) ---

    @app.route('/api/barbershop/stylists', methods=['POST'])
    @module_access_required('LAN-BAR1')
    def add_stylist_route():
        stylist = barbershop_service.add_stylist(g.tenant_id, request.get_json())
        return jsonify({'message': 'Estilista añadido exitosamente', 'stylist_id': stylist.id}), 201

    @app.route('/api/barbershop/stylists', methods=['GET'])
    @module_access_required('LAN-BAR1')
    def get_stylists_route():
        stylists = barbershop_service.get_stylists(g.tenant_id)
        return jsonify([{'id': s.id, 'name': s.name, 'specialty': s.specialty} for s in stylists])

    @app.route('/api/barbershop/appointments', methods=['POST'])
    @module_access_required('LAN-BAR1')
    def book_appointment_route():
        try:
            appointment = barbershop_service.book_appointment(g.tenant_id, request.get_json())
            return jsonify({'message': 'Cita agendada exitosamente', 'appointment_id': appointment.id}), 201
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

    @app.route('/api/barbershop/appointments/<string:day>', methods=['GET'])
    @module_access_required('LAN-BAR1')
    def get_appointments_route(day):
        try:
            request_date = date.fromisoformat(day)
            appointments = barbershop_service.get_appointments_for_day(g.tenant_id, request_date)
            return jsonify([{
                'id': a.id,
                'stylist': a.stylist.name,
                'client': a.client_name,
                'time': a.appointment_time.isoformat(),
                'status': a.status
            } for a in appointments])
        except ValueError:
            return jsonify({'error': 'Formato de fecha inválido. Usar YYYY-MM-DD.'}), 400

    # --- Automation (LAN-AGT5 & LAN-N8N1) ---

    @app.route('/api/automations/webhook/<string:event_type>', methods=['POST'])
    def automation_webhook_route(event_type):
        # This is a public endpoint. Tenant identification happens inside the service.
        payload = request.get_json()
        result = automation_service.trigger_workflow(event_type, payload)
        return jsonify(result)

    @app.route('/api/automations/workflows', methods=['GET'])
    @module_access_required('LAN-N8N1')
    def get_workflows_route():
        workflows = automation_service.get_workflows(g.tenant_id)
        return jsonify([{'id': w.id, 'name': w.name, 'trigger_event': w.trigger_event, 'is_active': w.is_active} for w in workflows])

    @app.route('/api/automations/workflows', methods=['POST'])
    @module_access_required('LAN-N8N1')
    def save_workflow_route():
        data = request.get_json()
        try:
            workflow = automation_service.save_workflow(
                g.tenant_id, data['name'], data['trigger_event'], data['workflow_json']
            )
            return jsonify({'message': 'Flujo de trabajo guardado', 'workflow_id': workflow.id}), 201
        except (KeyError, TypeError):
            return jsonify({'error': 'Faltan datos requeridos (name, trigger_event, workflow_json).'}), 400

    # --- Make.com Integration (LAN-MKE1) ---

    @app.route('/api/make/scenarios', methods=['GET'])
    @module_access_required('LAN-MKE1')
    def get_scenarios_route():
        scenarios = make_integration_service.get_scenarios(g.tenant_id)
        return jsonify([{'id': s.id, 'name': s.name, 'is_active': s.is_active} for s in scenarios])

    @app.route('/api/make/scenarios', methods=['POST'])
    @module_access_required('LAN-MKE1')
    def save_scenario_route():
        data = request.get_json()
        try:
            scenario = make_integration_service.save_scenario(
                g.tenant_id, data['name'], data['scenario_blueprint']
            )
            return jsonify({'message': 'Escenario guardado', 'scenario_id': scenario.id}), 201
        except (KeyError, TypeError):
            return jsonify({'error': 'Faltan datos requeridos (name, scenario_blueprint).'}), 400

    return app
