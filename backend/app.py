import os
from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, JWTManager, get_jwt

# Import models and services
from models import db, User, Role, Account, LoanProduct, LoanApplication, Payment, Employee, PayrollLog, PaySlip
from accounting_service import get_general_ledger, create_disbursement_journal_entry, create_repayment_journal_entry, create_payroll_journal_entry
from loan_calculator import generate_amortization_table
from payroll_service import calculate_payroll_for_all
from pdf_generator import create_contract_pdf
import firma_service

def create_app():
    """Application factory function."""
    app = Flask(__name__)
    CORS(app)

    # --- CONFIGURATION ---
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a-very-secret-key-that-is-secure')
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'another-super-secret-key')
    instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
    os.makedirs(instance_path, exist_ok=True)
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(instance_path, 'lazoarce.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    jwt = JWTManager(app)

    # --- API ROUTES ---

    @app.route('/api/login', methods=['POST'])
    def login():
        data = request.get_json()
        user = User.query.filter_by(email=data.get('email')).first()
        if user and user.check_password(data.get('password')):
            access_token = create_access_token(identity=user.email, additional_claims={'role': user.role.name})
            return jsonify(access_token=access_token)
        return jsonify({"msg": "Bad email or password"}), 401

    @app.route('/api/profile', methods=['GET', 'PUT'])
    @jwt_required()
    def user_profile():
        user = User.query.filter_by(email=get_jwt_identity()).first_or_404()
        if request.method == 'GET':
            return jsonify({"full_name": user.full_name, "dui": user.dui, "nit": user.nit, "email": user.email})

        data = request.get_json()
        user.full_name = data.get('full_name', user.full_name)
        user.dui = data.get('dui', user.dui)
        user.nit = data.get('nit', user.nit)
        db.session.commit()
        return jsonify({"msg": "Profile updated successfully."})

    @app.route('/api/loan-simulator', methods=['POST'])
    def loan_simulator():
        data = request.get_json()
        try:
            result = generate_amortization_table(
                capital=float(data['capital']),
                interest_rate=float(data['interest_rate']),
                term_months=int(data['term_months']),
                commission_type=data.get('commission_type', 'A'),
                admin_commission_rate=float(data.get('admin_commission_rate', 0.0)),
                include_iva=bool(data.get('include_iva', False))
            )
            return jsonify(result)
        except (ValueError, KeyError) as e:
            return jsonify({"msg": f"Invalid input: {e}"}), 400

    @app.route('/api/loan-products', methods=['GET'])
    @jwt_required()
    def get_loan_products():
        products = LoanProduct.query.filter_by(is_active=True).all()
        return jsonify([{'id': p.id, 'name': p.name, 'min_amount': p.min_amount, 'max_amount': p.max_amount, 'interest_rate': p.interest_rate, 'term_months': p.term_months} for p in products])

    @app.route('/api/loan-applications', methods=['GET', 'POST'])
    @jwt_required()
    def handle_loan_applications():
        user = User.query.filter_by(email=get_jwt_identity()).first_or_404()
        if request.method == 'POST':
            data = request.get_json()
            app = LoanApplication(user_id=user.id, product_id=data['product_id'], requested_amount=float(data['requested_amount']), requested_term=int(data['requested_term']))
            db.session.add(app)
            db.session.commit()
            return jsonify({"msg": "Loan application submitted.", "id": app.id}), 201

        claims = get_jwt()
        if claims.get('role') in ['Admin', 'Contador']:
            apps = LoanApplication.query.all()
        else:
            apps = LoanApplication.query.filter_by(user_id=user.id).all()
        return jsonify([{'id': a.id, 'applicant_email': a.applicant.email, 'product_name': a.product.name, 'requested_amount': a.requested_amount, 'status': a.status, 'signature_status': a.signature_status, 'application_date': a.application_date.isoformat()} for a in apps])

    @app.route('/api/loan-applications/<int:app_id>/status', methods=['PUT'])
    @jwt_required()
    def update_application_status(app_id):
        if get_jwt().get('role') != 'Admin': return jsonify({"msg": "Unauthorized"}), 403
        app = LoanApplication.query.get_or_404(app_id)
        app.status = request.json['status']
        if app.status == 'Desembolsado':
            create_disbursement_journal_entry(app)
        db.session.commit()
        return jsonify({"msg": f"Status updated to {app.status}"})

    @app.route('/api/loan-applications/<int:app_id>/payments', methods=['POST'])
    @jwt_required()
    def record_payment(app_id):
        if get_jwt().get('role') not in ['Admin', 'Contador']: return jsonify({"msg": "Unauthorized"}), 403
        app = LoanApplication.query.get_or_404(app_id)
        if app.status != 'Desembolsado': return jsonify({"msg": "Loan not disbursed"}), 400
        user = User.query.filter_by(email=get_jwt_identity()).first_or_404()
        payment = Payment(application_id=app_id, amount=float(request.json['amount']), recorded_by_user_id=user.id)
        db.session.add(payment)
        create_repayment_journal_entry(payment)
        db.session.commit()
        return jsonify({"msg": "Payment recorded.", "id": payment.id}), 201

    @app.route('/api/loan-applications/<int:app_id>/amortization', methods=['GET'])
    @jwt_required()
    def get_amortization_schedule(app_id):
        app = LoanApplication.query.get_or_404(app_id)
        data = generate_amortization_table(app.requested_amount, app.product.interest_rate, app.requested_term, app.product.commission_type, app.product.admin_commission_rate, True)
        data['payments'] = [{'amount': p.amount, 'date': p.payment_date.isoformat()} for p in app.payments]
        return jsonify(data)

    @app.route('/api/loan-applications/<int:app_id>/contract-data', methods=['GET'])
    @jwt_required()
    def get_contract_data(app_id):
        app = LoanApplication.query.get_or_404(app_id)
        amortization = generate_amortization_table(app.requested_amount, app.product.interest_rate, app.requested_term, app.product.commission_type, app.product.admin_commission_rate, True)
        return jsonify({
            "client": {"name": app.applicant.full_name, "dui": app.applicant.dui, "nit": app.applicant.nit},
            "loan": {"id": app.id, "amount_text": f"${app.requested_amount:,.2f}", "term_months": app.requested_term, "interest_rate_annual": f"{(app.product.interest_rate * 100):.2f}%", "monthly_payment": f"${amortization['summary']['total_monthly_payment']:,.2f}", "signature_status": app.signature_status, "tea": amortization['summary']['tea']},
            "company": {"name": "GRUPO LAZO ARCE S.A.S. DE C.V.", "legal_rep": "Admin Lazo Arce"},
            "amortization_table": amortization['schedule']
        })

    @app.route('/api/loan-applications/<int:app_id>/contract.pdf', methods=['GET'])
    @jwt_required()
    def download_contract_pdf(app_id):
        app = LoanApplication.query.get_or_404(app_id)
        amortization = generate_amortization_table(app.requested_amount, app.product.interest_rate, app.requested_term, app.product.commission_type, app.product.admin_commission_rate, True)
        contract_data = {"client": {"name": app.applicant.full_name, "dui": app.applicant.dui, "nit": app.applicant.nit}, "loan": {"amount_text": f"${app.requested_amount:,.2f}","term_months": app.requested_term,"interest_rate_annual": f"{(app.product.interest_rate * 100):.2f}%","monthly_payment": f"${amortization['summary']['total_monthly_payment']:,.2f}"}, "company": {"name": "GRUPO LAZO ARCE S.A.S. DE C.V."}, "amortization_table": amortization['schedule']}
        pdf_buffer = create_contract_pdf(contract_data)
        response = make_response(pdf_buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=contrato_{app_id}.pdf'
        return response

    @app.route('/api/loan-applications/<int:app_id>/request-signature', methods=['POST'])
    @jwt_required()
    def request_signature(app_id):
        url = firma_service.request_electronic_signature(app_id)
        return jsonify({"msg": "Signature process initiated.", "signature_url": url})

    @app.route('/api/loan-applications/<int:app_id>/upload-signed-document', methods=['POST'])
    @jwt_required()
    def upload_signed_document(app_id):
        result = firma_service.handle_manual_upload(app_id, request.json['file_url'])
        return jsonify(result)

    @app.route('/api/loan-applications/<int:app_id>/validate-signature', methods=['POST'])
    @jwt_required()
    def validate_signature(app_id):
        if get_jwt().get('role') != 'Admin': return jsonify({"msg": "Unauthorized"}), 403
        result = firma_service.validate_manual_signature(app_id)
        return jsonify(result)

    @app.route('/api/accounting/general-ledger', methods=['GET'])
    @jwt_required()
    def get_general_ledger_endpoint():
        return jsonify(get_general_ledger())

    @app.route('/api/employees', methods=['GET', 'POST'])
    @jwt_required()
    def manage_employees():
        if get_jwt().get('role') != 'Admin': return jsonify({"msg": "Unauthorized"}), 403
        if request.method == 'POST':
            data = request.get_json()
            if User.query.filter_by(email=data['email']).first(): return jsonify({"msg": "User already exists"}), 409
            role = Role.query.filter_by(name='Empleado').first()
            user = User(email=data['email'], role_id=role.id, full_name=data.get('full_name'))
            user.set_password('password123')
            emp = Employee(user=user, position=data['position'], base_salary=data['base_salary'])
            db.session.add(user)
            db.session.add(emp)
            db.session.commit()
            return jsonify({"msg": "Employee created.", "id": emp.id}), 201

        employees = Employee.query.all()
        return jsonify([{"id": e.id, "user_id": e.user_id, "full_name": e.user.full_name, "email": e.user.email, "position": e.position, "base_salary": e.base_salary, "is_active": e.is_active} for e in employees])

    @app.route('/api/employees/<int:emp_id>', methods=['PUT'])
    @jwt_required()
    def update_employee(emp_id):
        if get_jwt().get('role') != 'Admin': return jsonify({"msg": "Unauthorized"}), 403
        emp = Employee.query.get_or_404(emp_id)
        data = request.get_json()
        emp.position = data.get('position', emp.position)
        emp.base_salary = data.get('base_salary', emp.base_salary)
        emp.is_active = data.get('is_active', emp.is_active)
        if emp.user:
            emp.user.full_name = data.get('full_name', emp.user.full_name)
            emp.user.email = data.get('email', emp.user.email)
        db.session.commit()
        return jsonify({"msg": "Employee updated."})

    @app.route('/api/payroll/calculate', methods=['POST'])
    @jwt_required()
    def run_payroll_calculation():
        if get_jwt().get('role') != 'Admin': return jsonify({"msg": "Unauthorized"}), 403
        user = User.query.filter_by(email=get_jwt_identity()).first_or_404()
        log, totals = calculate_payroll_for_all(request.json['period_name'], user.id)
        create_payroll_journal_entry(log.id, totals)
        db.session.commit()
        return jsonify({"msg": "Payroll calculated and posted to accounting.", "log_id": log.id, "totals": totals})

    return app

# (setup_database function remains the same)
def setup_database(app):
    with app.app_context():
        db.create_all()
        if not Role.query.first():
            # ... (seeding logic) ...
            pass

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        setup_database(app) # Ensure db is created and seeded
    app.run(debug=True, port=5001)