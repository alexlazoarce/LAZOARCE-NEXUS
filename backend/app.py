import os
from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, JWTManager, get_jwt

from models import db, Role, User, LoanProduct, LoanApplication, Account, Employee, PayrollLog, PaySlip, Lead, CommunicationLog, Payment, NotificationTemplate, AuditLog, Opportunity, MailingList, Campaign, Ticket, TicketComment, Tenant, SystemModule, TenantSubscription, SignatureRequest
from loan_calculator import calculate_loan_details
from pdf_generator import generate_contract_pdf
import accounting_service
import payroll_service
import collections_service
import notification_service
import audit_service
import firma_service
from datetime import datetime, date, timedelta
    """Application factory function."""
    app = Flask(__name__)
    CORS(app)

    app.config['SECRET_KEY'] = 'dev'
    app.config['JWT_SECRET_KEY'] = 'dev'
    instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
    os.makedirs(instance_path, exist_ok=True)
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(instance_path, 'lazoarce.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    jwt = JWTManager(app)

    # --- Custom Decorators ---
    def module_access_required(module_code):
        def decorator(fn):
            @wraps(fn)
            @jwt_required()
            def wrapper(*args, **kwargs):
                current_user_email = get_jwt_identity()
                user = User.query.filter_by(email=current_user_email).first()

                if not user:
                    return jsonify({"message": "Usuario no encontrado."}), 404

                # System-wide admins have access to everything
                if user.role.name == 'Admin' and user.tenant_id is None:
                    return fn(*args, **kwargs)

                if not user.tenant:
                    return jsonify({"message": "Acceso no autorizado. El usuario no pertenece a un tenant."}), 403

                # Check for an active subscription
                today = date.today()
                subscription = TenantSubscription.query.join(SystemModule).filter(
                    TenantSubscription.tenant_id == user.tenant_id,
                    SystemModule.module_code == module_code,
                    TenantSubscription.is_active == True,
                    TenantSubscription.start_date <= today,
                    (TenantSubscription.end_date == None) | (TenantSubscription.end_date >= today)
                ).first()

                if not subscription:
                    return jsonify({"message": f"Acceso no autorizado. Se requiere una suscripción activa para el módulo '{module_code}'."}), 403

                return fn(*args, **kwargs)
            return wrapper
        return decorator

    # --- AUTH & USER ROUTES ---
    @app.route('/api/auth/register', methods=['POST'])
    def register():
        data = request.get_json()
        if User.query.filter_by(email=data['email']).first(): return jsonify({"message": "El correo ya está registrado"}), 409
        # Default to 'Cliente' role
        client_role = Role.query.filter_by(name='Cliente').first()
        if not client_role:
             return jsonify({"message": "Rol de cliente no encontrado"}), 500
        user = User(email=data['email'], role_id=client_role.id, full_name=data.get('username'))
        user.set_password(data['password'])
        db.session.add(user)
        db.session.commit()
        return jsonify({"message": "Usuario creado exitosamente"}), 201

    @app.route('/api/auth/login', methods=['POST'])
    def login():
        data = request.get_json()
        user = User.query.filter_by(email=data.get('email')).first()
        if user and user.check_password(data.get('password')):
            access_token = create_access_token(identity=user.email, additional_claims={'roles': [user.role.name]})
            audit_service.log_action('USER_LOGIN', user_id=user.id, details=f"User {user.email} logged in successfully.")
            db.session.commit() # Commit the audit log
            return jsonify(access_token=access_token)
        return jsonify({"message": "Credenciales incorrectas"}), 401

    @app.route('/api/profile', methods=['GET', 'PUT'])
    @jwt_required()
    def user_profile():
        current_user_email = get_jwt_identity()
        user = User.query.filter_by(email=current_user_email).first_or_404()
        if request.method == 'GET':
            return jsonify({
                "full_name": user.full_name,
                "dui": user.dui,
                "nit": user.nit,
                "email": user.email,
                "roles": [user.role.name]
            })
        data = request.get_json()
        user.full_name = data.get('full_name', user.full_name)
        user.dui = data.get('dui', user.dui)
        user.nit = data.get('nit', user.nit)
        db.session.commit()
        return jsonify({"message": "Perfil actualizado exitosamente"})

    @app.route('/api/users', methods=['GET'])
    @jwt_required()
    def get_users():
        claims = get_jwt()
        if 'Admin' not in claims.get('roles', []):
            return jsonify({"message": "Acceso no autorizado"}), 403

        users = User.query.all()
        return jsonify([{'id': u.id, 'full_name': u.full_name, 'email': u.email} for u in users])

    # --- LOAN PRODUCT ROUTES ---
    @app.route('/api/products', methods=['GET', 'POST'])
    @jwt_required()
    def handle_products():
        claims = get_jwt()
        user_roles = claims.get('roles', [])

        if request.method == 'POST':
            if 'Admin' not in user_roles:
                return jsonify({"message": "Acceso no autorizado"}), 403
            data = request.get_json()
            new_product = LoanProduct(
                name=data['name'],
                min_amount=data['min_amount'],
                max_amount=data['max_amount'],
                interest_rate=data['interest_rate'],
                commission_rate=data['commission_rate'],
                term_months=data['term_months']
            )
            db.session.add(new_product)
            db.session.commit()
            return jsonify(new_product.to_dict()), 201

        # GET request
        products = LoanProduct.query.filter_by(is_active=True).all()
        return jsonify([p.to_dict() for p in products])

    @app.route('/api/products/<int:product_id>', methods=['GET', 'PUT', 'DELETE'])
    @jwt_required()
    def handle_product(product_id):
        # ... (Implementation for PUT and DELETE for Admins)
        return jsonify({"message": "Not implemented"}), 501


    # --- PUBLIC SIMULATOR ---
    @app.route('/api/public/simulate', methods=['POST'])
    def public_loan_simulator():
        # This is a public endpoint, no JWT required.
        data = request.get_json()
        product = LoanProduct.query.get_or_404(data['product_id'])

        calculation = calculate_loan_details(
            principal=data['amount'],
            annual_interest_rate=product.interest_rate,
            term_months=data['term'],
            commission_rate=product.commission_rate,
            commission_type=data['commission_calculation_method']
        )
        return jsonify(calculation)

    # --- LOAN SIMULATOR (Authenticated) ---
    @app.route('/api/loans/simulate', methods=['POST'])
    @jwt_required()
    def loan_simulator():
        data = request.get_json()
        product = LoanProduct.query.get_or_404(data['product_id'])

        calculation = calculate_loan_details(
            principal=data['amount'],
            annual_interest_rate=product.interest_rate,
            term_months=data['term'],
            commission_rate=product.commission_rate,
            commission_type=data['commission_calculation_method']
        )
        return jsonify(calculation)

    # --- LOAN APPLICATION ROUTES ---
    @app.route('/api/applications', methods=['POST', 'GET'])
    @jwt_required()
    def handle_applications():
        current_user_email = get_jwt_identity()
        user = User.query.filter_by(email=current_user_email).first_or_404()

        if request.method == 'POST':
            # --- Refinement: Profile Completion Validation ---
            if not user.full_name or not user.dui or not user.nit:
                return jsonify({"message": "Por favor, complete su perfil (Nombre, DUI y NIT) antes de solicitar un préstamo."}), 400

            data = request.get_json()
            product = LoanProduct.query.get_or_404(data['product_id'])

            # Basic Validation
            if not (product.min_amount <= data['amount_requested'] <= product.max_amount):
                return jsonify({"message": "Monto solicitado fuera de los límites del producto"}), 400

            # Recalculate to ensure data integrity
            calculation = calculate_loan_details(
                principal=data['amount_requested'],
                annual_interest_rate=product.interest_rate,
                term_months=data['term_months'],
                commission_rate=product.commission_rate,
                commission_type=data['commission_calculation_method']
            )

            new_application = LoanApplication(
                user_id=user.id,
                product_id=product.id,
                amount_requested=data['amount_requested'],
                term_months=data['term_months'],
                commission_calculation_method=data['commission_calculation_method'],
                monthly_payment=calculation['monthly_payment'],
                total_payment=calculation['total_payment']
            )
            db.session.add(new_application)
            db.session.commit()
            return jsonify(new_application.to_dict()), 201

        # GET request
        claims = get_jwt()
        user_roles = claims.get('roles', [])
        if 'Admin' in user_roles:
            # Admins see all applications
            apps = LoanApplication.query.all()
        else:
            # Clients see only their own applications
            apps = LoanApplication.query.filter_by(user_id=user.id).all()

        return jsonify([app.to_dict() for app in apps])

    @app.route('/api/applications/<int:app_id>/status', methods=['PUT'])
    @jwt_required()
    def update_application_status(app_id):
        claims = get_jwt()
        user_roles = claims.get('roles', [])
        # Only Admins should be able to change status
        if 'Admin' not in user_roles:
            return jsonify({"message": "Acceso no autorizado"}), 403

        current_user = User.query.filter_by(email=get_jwt_identity()).first()
        app_to_update = LoanApplication.query.get_or_404(app_id)
        data = request.get_json()
        old_status = app_to_update.status
        new_status = data.get('status')

        if new_status not in ['Aprobada', 'Rechazada', 'Desembolsada']:
            return jsonify({"message": "Estado no válido"}), 400

        # --- Accounting Integration ---
        if new_status == 'Desembolsada' and app_to_update.status != 'Desembolsada':
            try:
                # --- Refinement: Flexible Disbursement Source ---
                disbursement_source = data.get('disbursement_source', 'Bancos') # Default to 'Bancos'
                if disbursement_source not in ['Bancos', 'Caja']:
                    raise ValueError("Fuente de desembolso no válida. Debe ser 'Bancos' or 'Caja'.")

                # 1. Prepare transaction data for the journal entry
                transactions_data = [
                    {
                        'account_name': 'Cuentas por Cobrar Clientes',
                        'type': 'Debit',
                        'amount': app_to_update.amount_requested
                    },
                    {
                        'account_name': disbursement_source,
                        'type': 'Credit',
                        'amount': app_to_update.amount_requested
                    }
                ]

                # 2. Create the journal entry via the service
                description = f"Desembolso de préstamo ID {app_to_update.id} para {app_to_update.applicant.full_name}"
                journal_entry = accounting_service.create_journal_entry(
                    date=datetime.utcnow(),
                    description=description,
                    transactions_data=transactions_data
                )

                # 3. Link the entry to the loan application
                app_to_update.disbursement_entry = journal_entry

            except ValueError as e:
                db.session.rollback()
                return jsonify({"message": f"Error de contabilidad: {str(e)}"}), 500

        # --- Notification Integration ---
        if new_status == 'Aprobada':
            notification_service.send_notification(
                user_id=app_to_update.user_id,
                template_slug='loan-approved',
                data={'amount': app_to_update.amount_requested}
            )
        elif new_status == 'Rechazada':
            notification_service.send_notification(
                user_id=app_to_update.user_id,
                template_slug='loan-rejected'
            )

        app_to_update.status = new_status
        app_to_update.decision_date = datetime.utcnow()

        try:
            audit_details = f"Loan ID {app_id} status changed from '{old_status}' to '{new_status}'."
            audit_service.log_action('LOAN_STATUS_CHANGE', user_id=current_user.id, details=audit_details)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({"message": f"Error al guardar en la base de datos: {str(e)}"}), 500

        return jsonify(app_to_update.to_dict())

    @app.route('/api/applications/<int:app_id>/contract-data', methods=['GET'])
    @jwt_required()
    def get_contract_data(app_id):
        application = LoanApplication.query.get_or_404(app_id)

        # Security check: only the applicant or an admin can view the contract
        current_user_email = get_jwt_identity()
        user = User.query.filter_by(email=current_user_email).first_or_404()
        claims = get_jwt()
        user_roles = claims.get('roles', [])

        if user.id != application.user_id and 'Admin' not in user_roles:
            return jsonify({"message": "Acceso no autorizado"}), 403

        # Regenerate loan calculation to get all details, including TEA
        loan_calculation = calculate_loan_details(
            principal=application.amount_requested,
            annual_interest_rate=application.product.interest_rate,
            term_months=application.term_months,
            commission_rate=application.product.commission_rate,
            commission_type=application.commission_calculation_method
        )
        amortization_table = loan_calculation['amortization_table']
        tea_annual = loan_calculation['tea_annual']

        # Company details (can be moved to a config file later)
        company_info = {
            "name": "GRUPO LAZO ARCE S.A.S. DE C.V.",
            "nit": "0614-123456-123-4",
            "address": "San Salvador, El Salvador",
            "legal_representative": "Nombre del Representante Legal"
        }

        contract_data = {
            "application": application.to_dict(),
            "client": {
                "full_name": application.applicant.full_name,
                "dui": application.applicant.dui,
                "nit": application.applicant.nit,
                "email": application.applicant.email,
            },
            "company": company_info,
            "amortization_table": amortization_table,
            "tea_annual": tea_annual
        }

        return jsonify(contract_data)

    @app.route('/api/applications/<int:app_id>/contract.pdf')
    @jwt_required()
    def download_contract_pdf(app_id):
        # This reuses the logic from get_contract_data to fetch and validate
        application = LoanApplication.query.get_or_404(app_id)
        current_user_email = get_jwt_identity()
        user = User.query.filter_by(email=current_user_email).first_or_404()
        claims = get_jwt()
        user_roles = claims.get('roles', [])

        if user.id != application.user_id and 'Admin' not in user_roles:
            return jsonify({"message": "Acceso no autorizado"}), 403

        # You could refactor this data gathering part into a helper function
        # to avoid repetition with the get_contract_data endpoint.
        amortization_table = calculate_loan_details(
            principal=application.amount_requested,
            annual_interest_rate=application.product.interest_rate,
            term_months=application.term_months,
            commission_rate=application.product.commission_rate,
            commission_type=application.commission_calculation_method
        )['amortization_table']

        company_info = {
            "name": "GRUPO LAZO ARCE S.A.S. DE C.V.",
            "nit": "0614-123456-123-4",
            "address": "San Salvador, El Salvador",
            "legal_representative": "Nombre del Representante Legal"
        }

        # The LoanProduct object needs to be converted to a dict to be serializable for the PDF generator
        product_dict = application.product.to_dict()

        contract_data = {
            "application": {**application.to_dict(), "product": product_dict},
            "client": {
                "full_name": application.applicant.full_name,
                "dui": application.applicant.dui,
                "nit": application.applicant.nit
            },
            "company": company_info,
            "amortization_table": amortization_table
        }

        pdf_bytes = generate_contract_pdf(contract_data)

        response = make_response(pdf_bytes)
        response.headers.set('Content-Type', 'application/pdf')
        response.headers.set('Content-Disposition', 'attachment', filename=f'contrato_{app_id}.pdf')
        return response

    # --- ACCOUNTING API ROUTES ---

    @app.route('/api/accounting/journal', methods=['GET'])
    @jwt_required()
    def get_journal_entries():
        claims = get_jwt()
        user_roles = claims.get('roles', [])
        if 'Admin' not in user_roles and 'Contador' not in user_roles:
            return jsonify({"message": "Acceso no autorizado"}), 403

        entries = JournalEntry.query.order_by(JournalEntry.date.desc()).all()
        return jsonify([entry.to_dict() for entry in entries])

    @app.route('/api/accounting/general-ledger', methods=['GET'])
    @jwt_required()
    def get_general_ledger():
        claims = get_jwt()
        user_roles = claims.get('roles', [])
        if 'Admin' not in user_roles and 'Contador' not in user_roles:
            return jsonify({"message": "Acceso no autorizado"}), 403

        accounts = Account.query.all()
        ledger = []
        for account in accounts:
            balance = 0.0
            for transaction in account.transactions:
                if transaction.type == account.normal_balance:
                    balance += transaction.amount
                else:
                    balance -= transaction.amount

            ledger.append({
                'account_id': account.id,
                'account_name': account.name,
                'account_category': account.category,
                'balance': round(balance, 2)
            })
        return jsonify(ledger)

    @app.route('/api/accounting/trial-balance', methods=['GET'])
    @jwt_required()
    def get_trial_balance():
        claims = get_jwt()
        user_roles = claims.get('roles', [])
        if 'Admin' not in user_roles and 'Contador' not in user_roles:
            return jsonify({"message": "Acceso no autorizado"}), 403

        accounts = Account.query.all()
        report = []
        total_debits = 0.0
        total_credits = 0.0

        for account in accounts:
            debits = sum(t.amount for t in account.transactions if t.type == 'Debit')
            credits = sum(t.amount for t in account.transactions if t.type == 'Credit')

            if debits > 0 or credits > 0:
                report.append({
                    'account_name': account.name,
                    'debits': round(debits, 2),
                    'credits': round(credits, 2)
                })
                total_debits += debits
                total_credits += credits

        return jsonify({
            'report': report,
            'total_debits': round(total_debits, 2),
            'total_credits': round(total_credits, 2),
            'is_balanced': round(total_debits, 2) == round(total_credits, 2)
        })

    @app.route('/api/accounting/balance-sheet', methods=['GET'])
    @jwt_required()
    def get_balance_sheet():
        claims = get_jwt()
        user_roles = claims.get('roles', [])
        if 'Admin' not in user_roles and 'Contador' not in user_roles:
            return jsonify({"message": "Acceso no autorizado"}), 403

        report = {'assets': [], 'liabilities': [], 'equity': []}
        totals = {'assets': 0.0, 'liabilities': 0.0, 'equity': 0.0}

        accounts = Account.query.filter(Account.category.in_(['Asset', 'Liability', 'Equity'])).all()

        for account in accounts:
            balance = 0.0
            for transaction in account.transactions:
                if transaction.type == account.normal_balance:
                    balance += transaction.amount
                else:
                    balance -= transaction.amount

            category_key = account.category.lower()
            report[category_key].append({'account_name': account.name, 'balance': round(balance, 2)})
            totals[category_key] += balance

        return jsonify({
            'report': report,
            'totals': {
                'assets': round(totals['assets'], 2),
                'liabilities': round(totals['liabilities'], 2),
                'equity': round(totals['equity'], 2),
                'liabilities_plus_equity': round(totals['liabilities'] + totals['equity'], 2)
            },
            'accounting_equation_balanced': round(totals['assets'], 2) == round(totals['liabilities'] + totals['equity'], 2)
        })

    @app.route('/api/accounting/income-statement', methods=['GET'])
    @jwt_required()
    def get_income_statement():
        claims = get_jwt()
        user_roles = claims.get('roles', [])
        if 'Admin' not in user_roles and 'Contador' not in user_roles:
            return jsonify({"message": "Acceso no autorizado"}), 403

        report = {'revenues': [], 'expenses': []}
        totals = {'revenues': 0.0, 'expenses': 0.0}

        accounts = Account.query.filter(Account.category.in_(['Revenue', 'Expense'])).all()

        for account in accounts:
            balance = 0.0
            # Simplified balance calculation for income statement accounts
            for trx in account.transactions:
                if trx.type == account.normal_balance:
                    balance += trx.amount
                else:
                    balance -= trx.amount

            category_key = account.category.lower() + 's' # revenues or expenses
            report[category_key].append({'account_name': account.name, 'balance': round(balance, 2)})
            totals[category_key] += balance

        net_income = totals['revenues'] - totals['expenses']

        return jsonify({
            'report': report,
            'totals': {
                'revenues': round(totals['revenues'], 2),
                'expenses': round(totals['expenses'], 2),
            },
            'net_income': round(net_income, 2)
        })

    # --- HR / Employee Management API ROUTES ---

    @app.route('/api/employees', methods=['GET', 'POST'])
    @jwt_required()
    def handle_employees():
        claims = get_jwt()
        if 'Admin' not in claims.get('roles', []):
            return jsonify({"message": "Acceso no autorizado"}), 403

        if request.method == 'POST':
            data = request.get_json()
            try:
                new_employee = Employee(
                    full_name=data['full_name'],
                    position=data['position'],
                    salary=float(data['salary']),
                    hire_date=date.fromisoformat(data['hire_date']),
                    dui=data.get('dui'),
                    nit=data.get('nit'),
                    isss_number=data.get('isss_number'),
                    afp_number=data.get('afp_number')
                )
                db.session.add(new_employee)
                db.session.commit()
                return jsonify(new_employee.to_dict()), 201
            except Exception as e:
                db.session.rollback()
                return jsonify({"message": f"Error al crear empleado: {str(e)}"}), 400

        # GET request
        employees = Employee.query.order_by(Employee.full_name).all()
        return jsonify([e.to_dict() for e in employees])

    @app.route('/api/employees/<int:employee_id>', methods=['GET', 'PUT', 'DELETE'])
    @jwt_required()
    def handle_employee(employee_id):
        claims = get_jwt()
        if 'Admin' not in claims.get('roles', []):
            return jsonify({"message": "Acceso no autorizado"}), 403

        employee = Employee.query.get_or_404(employee_id)

        if request.method == 'GET':
            return jsonify(employee.to_dict())

        if request.method == 'PUT':
            data = request.get_json()
            try:
                employee.full_name = data.get('full_name', employee.full_name)
                employee.position = data.get('position', employee.position)
                employee.salary = float(data.get('salary', employee.salary))
                employee.is_active = data.get('is_active', employee.is_active)
                employee.dui = data.get('dui', employee.dui)
                employee.nit = data.get('nit', employee.nit)
                employee.isss_number = data.get('isss_number', employee.isss_number)
                employee.afp_number = data.get('afp_number', employee.afp_number)
                db.session.commit()
                return jsonify(employee.to_dict())
            except Exception as e:
                db.session.rollback()
                return jsonify({"message": f"Error al actualizar empleado: {str(e)}"}), 400

        if request.method == 'DELETE':
            # Soft delete by marking as inactive
            employee.is_active = False
            db.session.commit()
            return jsonify({"message": "Empleado desactivado correctamente"})

    # --- CRM / Lead Management API ROUTES ---

    @app.route('/api/leads', methods=['GET', 'POST'])
    @jwt_required()
    def handle_leads():
        claims = get_jwt()
        user_roles = claims.get('roles', [])
        if 'Admin' not in user_roles and 'Ejecutivo de Crédito' not in user_roles:
            return jsonify({"message": "Acceso no autorizado"}), 403

        if request.method == 'POST':
            data = request.get_json()
            new_lead = Lead(
                full_name=data['full_name'],
                email=data.get('email'),
                phone=data.get('phone'),
                status=data.get('status', 'Nuevo'),
                source=data.get('source'),
                notes=data.get('notes')
            )
            db.session.add(new_lead)
            db.session.commit()
            return jsonify(new_lead.to_dict()), 201

        # GET request
        leads = Lead.query.order_by(Lead.created_at.desc()).all()
        return jsonify([lead.to_dict() for lead in leads])

    @app.route('/api/leads/<int:lead_id>', methods=['GET', 'PUT', 'DELETE'])
    @jwt_required()
    def handle_lead(lead_id):
        claims = get_jwt()
        user_roles = claims.get('roles', [])
        if 'Admin' not in user_roles and 'Ejecutivo de Crédito' not in user_roles:
            return jsonify({"message": "Acceso no autorizado"}), 403

        lead = Lead.query.get_or_404(lead_id)

        if request.method == 'GET':
            return jsonify(lead.to_dict())

        if request.method == 'PUT':
            data = request.get_json()
            lead.full_name = data.get('full_name', lead.full_name)
            lead.email = data.get('email', lead.email)
            lead.phone = data.get('phone', lead.phone)
            lead.status = data.get('status', lead.status)
            lead.source = data.get('source', lead.source)
            lead.notes = data.get('notes', lead.notes)
            db.session.commit()
            return jsonify(lead.to_dict())

        if request.method == 'DELETE':
            db.session.delete(lead)
            db.session.commit()
            return jsonify({"message": "Lead eliminado correctamente"})

    @app.route('/api/leads/<int:lead_id>/communications', methods=['POST', 'GET'])
    @jwt_required()
    def handle_lead_communications(lead_id):
        claims = get_jwt()
        user_roles = claims.get('roles', [])
        if 'Admin' not in user_roles and 'Ejecutivo de Crédito' not in user_roles:
            return jsonify({"message": "Acceso no autorizado"}), 403

        lead = Lead.query.get_or_404(lead_id)

        if request.method == 'POST':
            data = request.get_json()
            current_user_email = get_jwt_identity()
            # Communications should be logged by employees
            employee = Employee.query.filter_by(full_name=current_user_email).first() # This assumes user email is employee name, might need adjustment
            if not employee:
                 # Fallback to a generic admin user or handle appropriately
                admin_user = User.query.filter_by(email=current_user_email).first()
                if not admin_user:
                    return jsonify({"message": "Usuario empleado no encontrado para registrar comunicación."}), 400
                # This part is tricky; for now, we'll assume an admin can log. A better way is to link User and Employee.
                # For demo, we'll just use the first employee if the logger is an Admin.
                employee = Employee.query.first()
                if not employee: return jsonify({"message": "No hay empleados para asignar el registro."}), 400


            new_comm = CommunicationLog(
                lead_id=lead.id,
                employee_id=employee.id,
                type=data['type'],
                notes=data['notes']
            )
            db.session.add(new_comm)
            db.session.commit()
            return jsonify(new_comm.to_dict()), 201

        # GET Request
        comms = lead.communication_logs.order_by(CommunicationLog.timestamp.desc()).all()
        return jsonify([c.to_dict() for c in comms])


    @app.route('/api/leads/<int:lead_id>/convert', methods=['POST'])
    @jwt_required()
    def convert_lead_to_client(lead_id):
        claims = get_jwt()
        user_roles = claims.get('roles', [])
        if 'Admin' not in user_roles and 'Ejecutivo de Crédito' not in user_roles:
            return jsonify({"message": "Acceso no autorizado"}), 403

        lead = Lead.query.get_or_404(lead_id)

        if lead.status != 'Calificado':
            return jsonify({"message": "Solo los leads 'Calificados' pueden ser convertidos."}), 400

        if not lead.email:
            return jsonify({"message": "El lead debe tener un email para ser convertido a cliente."}), 400

        # Check if a user with this email already exists
        if User.query.filter_by(email=lead.email).first():
            return jsonify({"message": "Un cliente con este email ya existe."}), 409

        try:
            client_role = Role.query.filter_by(name='Cliente').first()
            # In a real scenario, you'd send an email to set the password.
            # Here, we'll use a default temporary password.
            temp_password = "password123"

            new_user = User(
                email=lead.email,
                full_name=lead.full_name,
                role_id=client_role.id
            )
            new_user.set_password(temp_password)

            # Mark the lead as converted
            lead.status = 'Convertido a Cliente'

            # Create a new opportunity for the converted lead
            new_opportunity = Opportunity(
                name=f"Oportunidad para {lead.full_name}",
                stage='Calificación', # Initial stage after conversion
                lead_id=lead.id,
                user_id=new_user.id
            )

            db.session.add(new_user)
            db.session.add(new_opportunity)
            db.session.commit()

            print(f"--- NOTIFICACIÓN SIMULADA: Lead {lead.full_name} convertido a cliente. Email: {lead.email}, Pass Temporal: {temp_password} ---")

            return jsonify({
                "message": "Lead convertido a cliente y oportunidad creada exitosamente.",
                "user_id": new_user.id,
                "opportunity_id": new_opportunity.id
            }), 200

        except Exception as e:
            db.session.rollback()
            return jsonify({"message": f"Error al convertir el lead: {str(e)}"}), 500

    # --- CRM / Opportunity Management API ROUTES ---

    @app.route('/api/opportunities', methods=['GET'])
    @jwt_required()
    def get_opportunities():
        claims = get_jwt()
        user_roles = claims.get('roles', [])
        if 'Admin' not in user_roles and 'Ejecutivo de Crédito' not in user_roles:
            return jsonify({"message": "Acceso no autorizado"}), 403

        opportunities = Opportunity.query.order_by(Opportunity.created_at.desc()).all()
        return jsonify([opp.to_dict() for opp in opportunities])

    @app.route('/api/opportunities/<int:opp_id>', methods=['PUT'])
    @jwt_required()
    def update_opportunity(opp_id):
        claims = get_jwt()
        user_roles = claims.get('roles', [])
        if 'Admin' not in user_roles and 'Ejecutivo de Crédito' not in user_roles:
            return jsonify({"message": "Acceso no autorizado"}), 403

        opp = Opportunity.query.get_or_404(opp_id)
        data = request.get_json()

        # For now, only stage updates are the primary use case
        if 'stage' in data:
            opp.stage = data['stage']

        db.session.commit()
        return jsonify(opp.to_dict())

    # --- HR / Payroll Processing API ROUTES ---

    @app.route('/api/payroll/calculate', methods=['POST'])
    @jwt_required()
    def calculate_payroll():
        claims = get_jwt()
        if 'Admin' not in claims.get('roles', []):
            return jsonify({"message": "Acceso no autorizado"}), 403

        data = request.get_json()
        try:
            start_date = date.fromisoformat(data['start_date'])
            end_date = date.fromisoformat(data['end_date'])
        except (ValueError, KeyError):
            return jsonify({"message": "Fechas de período inválidas."}), 400

        active_employees = Employee.query.filter_by(is_active=True).all()
        if not active_employees:
            return jsonify({"message": "No hay empleados activos para procesar."}), 404

        total_paid = 0

        try:
            # Create a log for this payroll run
            new_payroll_log = PayrollLog(
                period_start_date=start_date,
                period_end_date=end_date,
                total_paid=0 # Placeholder, will be updated
            )
            db.session.add(new_payroll_log)

            for emp in active_employees:
                payslip_details = payroll_service.calculate_payslip_details(emp.salary)

                new_payslip = PaySlip(
                    employee_id=emp.id,
                    payroll_log=new_payroll_log,
                    gross_salary=payslip_details['gross_salary'],
                    isss_deduction=payslip_details['isss_deduction'],
                    afp_deduction=payslip_details['afp_deduction'],
                    renta_deduction=payslip_details['renta_deduction'],
                    net_salary=payslip_details['net_salary']
                )
                db.session.add(new_payslip)
                total_paid += payslip_details['net_salary']

            new_payroll_log.total_paid = total_paid
            db.session.commit()

            return jsonify({
                "message": "Nómina calculada exitosamente.",
                "payroll_log_id": new_payroll_log.id,
                "employees_processed": len(active_employees),
                "total_net_paid": total_paid
            })

        except Exception as e:
            db.session.rollback()
            return jsonify({"message": f"Error al procesar la nómina: {str(e)}"}), 500

    @app.route('/api/payroll/<int:log_id>/payslips', methods=['GET'])
    @jwt_required()
    def get_payslips_for_log(log_id):
        claims = get_jwt()
        if 'Admin' not in claims.get('roles', []):
            return jsonify({"message": "Acceso no autorizado"}), 403

        payslips = PaySlip.query.filter_by(payroll_log_id=log_id).all()
        if not payslips:
            return jsonify({"message": "No se encontraron recibos para este registro de nómina."}), 404

        return jsonify([p.to_dict() for p in payslips])

    # --- COLLECTIONS / PAYMENTS API ROUTES ---

    @app.route('/api/applications/<int:application_id>/payments', methods=['POST'])
    @jwt_required()
    def add_payment_to_application(application_id):
        claims = get_jwt()
        user_roles = claims.get('roles', [])
        if not any(role in user_roles for role in ['Admin', 'Cobrador']):
            return jsonify({"message": "Acceso no autorizado"}), 403

        app = LoanApplication.query.get_or_404(application_id)
        if app.status != 'Desembolsada':
            return jsonify({"message": "Solo se pueden registrar pagos para préstamos desembolsados."}), 400

        data = request.get_json()

        # Find the employee who is logging this payment
        current_user_email = get_jwt_identity()
        employee = Employee.query.filter_by(full_name=current_user_email).first()
        if not employee:
            # Fallback for admin users who might not be in the employee table
            if 'Admin' in user_roles:
                employee = Employee.query.first()
                if not employee: return jsonify({"message": "No hay empleados para asignar el registro del pago."}), 400
            else:
                return jsonify({"message": "Usuario cobrador no encontrado en la lista de empleados."}), 400

        try:
            payment_date = date.fromisoformat(data['payment_date'])
            amount_paid = float(data['amount_paid'])

            # --- Accounting Integration for Payment ---
            payment_source_account = 'Caja' # Assume payments are received in cash by default

            transactions_data = [
                {'account_name': payment_source_account, 'type': 'Debit', 'amount': amount_paid},
                {'account_name': 'Cuentas por Cobrar Clientes', 'type': 'Credit', 'amount': amount_paid}
            ]
            description = f"Pago de cuota para préstamo ID {app.id} por {app.applicant.full_name}"
            journal_entry = accounting_service.create_journal_entry(datetime.combine(payment_date, datetime.min.time()), description, transactions_data)

            new_payment = Payment(
                application_id=app.id,
                amount_paid=amount_paid,
                payment_date=payment_date,
                type=data.get('type', 'Cuota'),
                registered_by_id=employee.id,
                journal_entry=journal_entry
            )

            db.session.add(new_payment)

            audit_details = f"Payment of ${amount_paid} registered for loan ID {app.id}."
            audit_service.log_action('PAYMENT_REGISTERED', user_id=employee.id, details=audit_details)

            db.session.commit()

            return jsonify(new_payment.to_dict()), 201

        except Exception as e:
            db.session.rollback()
            return jsonify({"message": f"Error al registrar el pago: {str(e)}"}), 500

    @app.route('/api/applications/<int:application_id>/statement', methods=['GET'])
    @jwt_required()
    def get_loan_statement(application_id):
        # Security check: only the applicant or an admin can view
        app = LoanApplication.query.get_or_404(application_id)
        current_user_email = get_jwt_identity()
        user = User.query.filter_by(email=current_user_email).first_or_404()
        claims = get_jwt()
        user_roles = claims.get('roles', [])

        if user.id != app.user_id and 'Admin' not in user_roles:
            return jsonify({"message": "Acceso no autorizado"}), 403

        try:
            loan_status = collections_service.get_loan_status(app.id)
            payments_query = Payment.query.filter_by(application_id=app.id).order_by(Payment.payment_date.desc()).all()
            payments_history = [p.to_dict() for p in payments_query]

            return jsonify({
                "loan_summary": app.to_dict(),
                "loan_status": loan_status,
                "payments_history": payments_history
            })
        except Exception as e:
            return jsonify({"message": f"Error al generar el estado de cuenta: {str(e)}"}), 500

    @app.route('/api/portfolio/status', methods=['GET'])
    @jwt_required()
    def get_portfolio_status():
        claims = get_jwt()
        user_roles = claims.get('roles', [])
        if not any(role in user_roles for role in ['Admin', 'Cobrador']):
            return jsonify({"message": "Acceso no autorizado"}), 403

        active_loans = LoanApplication.query.filter_by(status='Desembolsada').all()
        portfolio_status = []
        for loan in active_loans:
            try:
                status = collections_service.get_loan_status(loan.id)
                portfolio_status.append(status)
            except Exception as e:
                # Log error and continue
                print(f"Error processing status for loan {loan.id}: {e}")

        return jsonify(portfolio_status)

    # --- NOTIFICATION TEMPLATES API ROUTES ---

    @app.route('/api/templates', methods=['GET', 'POST'])
    @jwt_required()
    def handle_templates():
        claims = get_jwt()
        if 'Admin' not in claims.get('roles', []):
            return jsonify({"message": "Acceso no autorizado"}), 403

        if request.method == 'GET':
            templates = NotificationTemplate.query.all()
            return jsonify([t.to_dict() for t in templates])

        data = request.get_json()
        new_template = NotificationTemplate(
            slug=data['slug'],
            subject=data['subject'],
            body=data['body'],
            type=data.get('type', 'Email')
        )
        db.session.add(new_template)
        db.session.commit()
        return jsonify(new_template.to_dict()), 201

    @app.route('/api/templates/<int:template_id>', methods=['PUT'])
    @jwt_required()
    def handle_template(template_id):
        claims = get_jwt()
        if 'Admin' not in claims.get('roles', []):
            return jsonify({"message": "Acceso no autorizado"}), 403

        template = NotificationTemplate.query.get_or_404(template_id)
        data = request.get_json()

        template.subject = data.get('subject', template.subject)
        template.body = data.get('body', template.body)
        template.type = data.get('type', template.type)

        db.session.commit()
        return jsonify(template.to_dict())

    @app.route('/api/notifications/send-reminders', methods=['POST'])
    @jwt_required()
    def send_payment_reminders():
        claims = get_jwt()
        if 'Admin' not in claims.get('roles', []):
            return jsonify({"message": "Acceso no autorizado"}), 403

        # Find loans with upcoming payments (e.g., within the next 7 days)
        today = date.today()
        reminder_window = today + timedelta(days=7)

        active_loans = LoanApplication.query.filter_by(status='Desembolsada').all()
        sent_count = 0

        for loan in active_loans:
            status = collections_service.get_loan_status(loan.id)
            next_due_date = date.fromisoformat(status['next_due_date']) if status.get('next_due_date') != 'N/A' else None

            if next_due_date and today <= next_due_date <= reminder_window:
                notification_data = {
                    'payment_amount': status['current_due_balance'] if status['current_due_balance'] > 0 else loan.monthly_payment,
                    'due_date': next_due_date.strftime('%d-%m-%Y')
                }
                notification_service.send_notification(
                    user_id=loan.user_id,
                    template_slug='payment-reminder',
                    data=notification_data
                )
                sent_count += 1

        return jsonify({"message": f"Se enviaron {sent_count} recordatorios de pago."})

    # --- MARKETING / MAILING LIST API ROUTES ---

    @app.route('/api/mailing-lists', methods=['GET', 'POST'])
    @jwt_required()
    def handle_mailing_lists():
        claims = get_jwt()
        if 'Admin' not in claims.get('roles', []):
            return jsonify({"message": "Acceso no autorizado"}), 403

        if request.method == 'GET':
            lists = MailingList.query.all()
            return jsonify([l.to_dict() for l in lists])

        data = request.get_json()
        new_list = MailingList(name=data['name'], description=data.get('description'))
        db.session.add(new_list)
        db.session.commit()
        return jsonify(new_list.to_dict()), 201

    @app.route('/api/mailing-lists/<int:list_id>/members', methods=['POST', 'DELETE'])
    @jwt_required()
    def handle_mailing_list_members(list_id):
        claims = get_jwt()
        if 'Admin' not in claims.get('roles', []):
            return jsonify({"message": "Acceso no autorizado"}), 403

        mailing_list = MailingList.query.get_or_404(list_id)
        data = request.get_json()
        user = User.query.get_or_404(data['user_id'])

        if request.method == 'POST':
            if user in mailing_list.members:
                return jsonify({"message": "El usuario ya está en la lista."}), 409
            mailing_list.members.append(user)
            db.session.commit()
            return jsonify({"message": "Usuario añadido a la lista."})

        if request.method == 'DELETE':
            if user not in mailing_list.members:
                return jsonify({"message": "El usuario no está en la lista."}), 404
            mailing_list.members.remove(user)
            db.session.commit()
            return jsonify({"message": "Usuario eliminado de la lista."})

    # --- MARKETING API ROUTES ---

    @app.route('/api/mailing-lists', methods=['GET', 'POST'])
    @jwt_required()
    def handle_mailing_lists():
        claims = get_jwt()
        if 'Admin' not in claims.get('roles', []):
            return jsonify({"message": "Acceso no autorizado"}), 403

        if request.method == 'GET':
            lists = MailingList.query.all()
            return jsonify([l.to_dict() for l in lists])

        data = request.get_json()
        new_list = MailingList(name=data['name'], description=data.get('description'))
        db.session.add(new_list)
        db.session.commit()
        return jsonify(new_list.to_dict()), 201

    @app.route('/api/mailing-lists/<int:list_id>/members', methods=['POST', 'DELETE'])
    @jwt_required()
    def handle_mailing_list_members(list_id):
        claims = get_jwt()
        if 'Admin' not in claims.get('roles', []):
            return jsonify({"message": "Acceso no autorizado"}), 403

        mailing_list = MailingList.query.get_or_404(list_id)
        data = request.get_json()
        user = User.query.get_or_404(data['user_id'])

        if request.method == 'POST':
            if user in mailing_list.members:
                return jsonify({"message": "El usuario ya está en la lista."}), 409
            mailing_list.members.append(user)
            db.session.commit()
            return jsonify({"message": "Usuario añadido a la lista."})

        if request.method == 'DELETE':
            if user not in mailing_list.members:
                return jsonify({"message": "El usuario no está en la lista."}), 404
            mailing_list.members.remove(user)
            db.session.commit()
            return jsonify({"message": "Usuario eliminado de la lista."})

    @app.route('/api/campaigns', methods=['GET', 'POST'])
    @jwt_required()
    def handle_campaigns():
        claims = get_jwt()
        if 'Admin' not in claims.get('roles', []):
            return jsonify({"message": "Acceso no autorizado"}), 403

        if request.method == 'GET':
            campaigns = Campaign.query.all()
            return jsonify([c.to_dict() for c in campaigns])

        data = request.get_json()
        new_campaign = Campaign(
            name=data['name'],
            subject=data['subject'],
            mailing_list_id=data['mailing_list_id'],
            template_id=data['template_id']
        )
        db.session.add(new_campaign)
        db.session.commit()
        return jsonify(new_campaign.to_dict()), 201

    @app.route('/api/campaigns/<int:campaign_id>/send', methods=['POST'])
    @jwt_required()
    def send_campaign(campaign_id):
        claims = get_jwt()
        if 'Admin' not in claims.get('roles', []):
            return jsonify({"message": "Acceso no autorizado"}), 403

        campaign = Campaign.query.get_or_404(campaign_id)
        if campaign.status == 'Sent':
            return jsonify({"message": "Esta campaña ya ha sido enviada."}), 400

        members = campaign.mailing_list.members
        for member in members:
            # In a real app, you'd pass more context data if needed
            notification_service.send_notification(member.id, campaign.template.slug, {})

        campaign.status = 'Sent'
        campaign.sent_at = datetime.utcnow()
        db.session.commit()

        return jsonify({"message": f"Campaña '{campaign.name}' enviada a {len(members)} miembros."})

    # --- HELPDESK / TICKETING API ROUTES ---

    @app.route('/api/tickets', methods=['GET', 'POST'])
    @jwt_required()
    def handle_tickets():
        current_user = User.query.filter_by(email=get_jwt_identity()).first()
        claims = get_jwt()
        user_roles = claims.get('roles', [])

        if request.method == 'POST':
            data = request.get_json()
            new_ticket = Ticket(
                subject=data['subject'],
                user_id=current_user.id,
                priority=data.get('priority', 'Normal')
            )
            # The first comment is the ticket description
            first_comment = TicketComment(
                ticket=new_ticket,
                user_id=current_user.id,
                comment_text=data['description']
            )
            db.session.add(new_ticket)
            db.session.add(first_comment)
            db.session.commit()
            return jsonify(new_ticket.to_dict()), 201

        # GET request
        if 'Admin' in user_roles or 'Soporte' in user_roles: # Assuming a 'Soporte' role
            tickets = Ticket.query.order_by(Ticket.updated_at.desc()).all()
        else: # Regular client
            tickets = Ticket.query.filter_by(user_id=current_user.id).order_by(Ticket.updated_at.desc()).all()

        return jsonify([t.to_dict() for t in tickets])

    @app.route('/api/tickets/<int:ticket_id>', methods=['GET', 'PUT'])
    @jwt_required()
    def handle_ticket(ticket_id):
        ticket = Ticket.query.get_or_404(ticket_id)
        # Security checks...

        if request.method == 'GET':
            return jsonify(ticket.to_dict())

        if request.method == 'PUT':
            # Logic to update status, priority, assignment for support staff
            pass

    @app.route('/api/tickets/<int:ticket_id>/comments', methods=['GET', 'POST'])
    @jwt_required()
    def handle_ticket_comments(ticket_id):
        ticket = Ticket.query.get_or_404(ticket_id)
        # Security checks...

        if request.method == 'POST':
            data = request.get_json()
            current_user = User.query.filter_by(email=get_jwt_identity()).first()
            new_comment = TicketComment(
                ticket_id=ticket.id,
                user_id=current_user.id,
                comment_text=data['comment_text']
            )
            ticket.updated_at = datetime.utcnow() # Touch the ticket to bump it up
            db.session.add(new_comment)
            db.session.commit()
            return jsonify(new_comment.to_dict()), 201

        # GET request
        comments = ticket.comments.order_by(TicketComment.timestamp.asc()).all()
        return jsonify([c.to_dict() for c in comments])

    # --- AUDIT LOG API ROUTE ---
    @app.route('/api/audit-logs', methods=['GET'])
    @jwt_required()
    def get_audit_logs():
        claims = get_jwt()
        if 'Admin' not in claims.get('roles', []):
            return jsonify({"message": "Acceso no autorizado"}), 403

        logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).all()
        return jsonify([log.to_dict() for log in logs])

    # --- TESTING UTILITIES ---
    @app.route('/api/testing/generate-dummy-data', methods=['POST'])
    @jwt_required()
    def generate_dummy_data():
        claims = get_jwt()
        if 'Admin' not in claims.get('roles', []):
            return jsonify({"message": "Acceso no autorizado"}), 403

        try:
            # You can expand this logic to be more sophisticated
            from random import randint, choice

            # Create a dummy user
            dummy_email = f"testuser{randint(1000, 9999)}@lazoarce.com"
            client_role = Role.query.filter_by(name='Cliente').first()
            new_user = User(email=dummy_email, full_name=f"Cliente de Prueba {randint(1,100)}", dui="00000000-0", nit="0000-000000-000-0", role_id=client_role.id)
            new_user.set_password("testing123")
            db.session.add(new_user)
            db.session.flush() # Flush to get the new_user.id

            # Create a loan application for the user
            product = LoanProduct.query.first()
            if not product: return jsonify({"message": "No hay productos de préstamo para crear datos de prueba."}), 400

            new_app = LoanApplication(user_id=new_user.id, product_id=product.id, amount_requested=randint(1000, 5000), term_months=12, commission_calculation_method='A', status='Desembolsada', decision_date=datetime.utcnow())
            db.session.add(new_app)
            db.session.flush() # Flush to get new_app.id

            # Add a payment
            employee = Employee.query.first()
            if employee:
                new_payment = Payment(application_id=new_app.id, amount_paid=new_app.monthly_payment, payment_date=date.today(), registered_by_id=employee.id)
                db.session.add(new_payment)

            db.session.commit()
            return jsonify({"message": f"Datos de prueba creados para el usuario {dummy_email}."}), 201

        except Exception as e:
            db.session.rollback()
            return jsonify({"message": f"Error generando datos de prueba: {str(e)}"}), 500

    return app

def setup_database(app):
    """Creates database tables and seeds initial data."""
    with app.app_context():
        db.create_all()
        if not Role.query.first():
            roles = [
                Role(name='Admin'),
                Role(name='Cliente'),
                Role(name='Contador'),
                Role(name='Ejecutivo de Crédito'),
                Role(name='Cobrador')
            ]
            db.session.bulk_save_objects(roles)
            db.session.commit()
        if not User.query.filter_by(email='admin@lazoarce.com').first():
            admin_role = Role.query.filter_by(name='Admin').first()
            admin_user = User(email='admin@lazoarce.com', role_id=admin_role.id, full_name='Admin Lazo Arce')
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            db.session.commit()
        if not LoanProduct.query.first():
            # Add a default product for testing
            default_product = LoanProduct(
                name="Préstamo Personal Clásico",
                min_amount=500.00,
                max_amount=10000.00,
                interest_rate=0.12, # 12% annual
                commission_rate=0.01, # 1% monthly
                term_months=36
            )
            db.session.add(default_product)
            db.session.commit()

        if not Account.query.first():
            # Seed the chart of accounts
            accounts = [
                # Assets
                Account(name='Caja', category='Asset', normal_balance='Debit'),
                Account(name='Bancos', category='Asset', normal_balance='Debit'),
                Account(name='Cuentas por Cobrar Clientes', category='Asset', normal_balance='Debit'),
                Account(name='Intereses por Cobrar', category='Asset', normal_balance='Debit'),
                # Liabilities
                Account(name='Préstamos por Pagar', category='Liability', normal_balance='Credit'),
                # Equity
                Account(name='Capital Social', category='Equity', normal_balance='Credit'),
                # Revenue
                Account(name='Ingresos por Intereses', category='Revenue', normal_balance='Credit'),
                Account(name='Ingresos por Comisiones', category='Revenue', normal_balance='Credit'),
            ]
            db.session.bulk_save_objects(accounts)
            db.session.commit()

        if not NotificationTemplate.query.first():
            templates = [
                NotificationTemplate(
                    slug='loan-approved',
                    subject='¡Tu préstamo ha sido aprobado!',
                    body='Hola {customer_name},\n\nNos complace informarte que tu solicitud de préstamo por un monto de ${amount} ha sido aprobada. ¡Felicidades!\n\nSaludos,\nEl equipo de LAZOARCE UNIVERSAL'
                ),
                NotificationTemplate(
                    slug='loan-rejected',
                    subject='Actualización sobre tu solicitud de préstamo',
                    body='Hola {customer_name},\n\nDespués de una cuidadosa revisión, lamentamos informarte que no podemos aprobar tu solicitud de préstamo en este momento.\n\nGracias por tu interés.\n\nSaludos,\nEl equipo de LAZOARCE UNIVERSAL'
                ),
                NotificationTemplate(
                    slug='payment-reminder',
                    subject='Recordatorio de Pago',
                    body='Hola {customer_name},\n\nEste es un recordatorio amistoso de que tu próxima cuota de ${payment_amount} para tu préstamo vence el {due_date}.\n\nSaludos,\nEl equipo de LAZOARCE UNIVERSAL'
                )
            ]
            db.session.bulk_save_objects(templates)
            db.session.commit()

        if not SystemModule.query.first():
            modules = [
                SystemModule(module_code='LAN-SUB1', name='Gestión de Suscripciones', description='Administra los tenants y sus suscripciones a los módulos.'),
                SystemModule(module_code='LAN-FEV8', name='Firma Electrónica Avanzada', description='Permite la captura y almacenamiento de firmas electrónicas.')
            ]
            db.session.bulk_save_objects(modules)
            db.session.commit()

    # --- LAN-SUB1 (Subscription Management) API ROUTES ---

    @app.route('/api/subscriptions/tenants', methods=['GET', 'POST'])
    @module_access_required('LAN-SUB1')
    def handle_tenants():
        if request.method == 'POST':
            data = request.get_json()
            if Tenant.query.filter_by(name=data['name']).first():
                return jsonify({"message": "Tenant with that name already exists."}), 409
            new_tenant = Tenant(name=data['name'])
            db.session.add(new_tenant)
            db.session.commit()
            return jsonify(new_tenant.to_dict()), 201

        tenants = Tenant.query.all()
        return jsonify([t.to_dict() for t in tenants])

    @app.route('/api/subscriptions/modules', methods=['GET'])
    @module_access_required('LAN-SUB1')
    def handle_system_modules():
        modules = SystemModule.query.all()
        return jsonify([m.to_dict() for m in modules])

    @app.route('/api/subscriptions', methods=['POST'])
    @module_access_required('LAN-SUB1')
    def handle_create_subscription():
        data = request.get_json()
        try:
            start_date = date.fromisoformat(data['start_date'])
            end_date = date.fromisoformat(data['end_date']) if data.get('end_date') else None

            new_subscription = TenantSubscription(
                tenant_id=data['tenant_id'],
                module_id=data['module_id'],
                start_date=start_date,
                end_date=end_date,
                is_active=True
            )
            db.session.add(new_subscription)
            db.session.commit()
            return jsonify(new_subscription.to_dict()), 201
        except (ValueError, KeyError) as e:
            return jsonify({"message": f"Invalid data provided: {e}"}), 400

    @app.route('/api/subscriptions/tenants/<int:tenant_id>', methods=['GET'])
    @module_access_required('LAN-SUB1')
    def get_tenant_subscriptions(tenant_id):
        subscriptions = TenantSubscription.query.filter_by(tenant_id=tenant_id).all()
        return jsonify([s.to_dict() for s in subscriptions])

    # --- LAN-FEV8 (Electronic Signature) API ROUTES ---

    @app.route('/api/signatures', methods=['POST'])
    @module_access_required('LAN-FEV8')
    def submit_signature():
        data = request.get_json()
        current_user_email = get_jwt_identity()
        user = User.query.filter_by(email=current_user_email).first()

        if not user:
            return jsonify({"message": "User not found"}), 404

        try:
            signature = firma_service.save_signature(
                user_id=user.id,
                signature_data=data.get('signature_data')
            )
            return jsonify(signature.to_dict()), 201
        except ValueError as e:
            return jsonify({'message': str(e)}), 400

    @app.route('/api/signatures/user/<int:user_id>', methods=['GET'])
    @module_access_required('LAN-FEV8')
    def get_user_signatures(user_id):
        current_user_email = get_jwt_identity()
        requesting_user = User.query.filter_by(email=current_user_email).first()
        claims = get_jwt()
        user_roles = claims.get('roles', [])

        # Security check: Allow access only if the user is requesting their own signatures or is an Admin.
        if 'Admin' not in user_roles and requesting_user.id != user_id:
            return jsonify({"message": "Acceso no autorizado"}), 403

        signatures = firma_service.get_signatures_for_user(user_id)
        return jsonify([s.to_dict() for s in signatures]), 200

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        setup_database(app)
    app.run(debug=True, port=5001)