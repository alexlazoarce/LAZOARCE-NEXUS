import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, JWTManager, get_jwt

# Import models
from models import db, User, Role, Account, LoanProduct, LoanApplication, Payment, Employee, PayrollLog, PaySlip
# Import services
from accounting_service import get_general_ledger, create_disbursement_journal_entry, create_repayment_journal_entry, create_payroll_journal_entry
from loan_calculator import generate_amortization_table
from payroll_service import calculate_payroll_for_all
from pdf_generator import create_contract_pdf
import firma_service
from flask import make_response

def create_app():
    """Application factory function."""
    app = Flask(__name__)
    CORS(app)

    # --- CONFIGURATION ---
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a-very-secret-key')
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'another-very-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(app.instance_path, 'lazoarce.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    db.init_app(app)
    jwt = JWTManager(app)

    # --- ROUTES ---

    @app.route('/api/login', methods=['POST'])
    def login():
        data = request.get_json()
        user = User.query.filter_by(email=data.get('email')).first()
        if user and user.check_password(data.get('password')):
            access_token = create_access_token(identity=user.email, additional_claims={'role': user.role.name})
            return jsonify(access_token=access_token)
        return jsonify({"msg": "Bad email or password"}), 401

    # --- Loan Simulator ---
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

    # --- Existing routes for HR, Loans, etc. ---
    # ... (They remain the same, but now the amortization/contract routes will use the new calculator)

    @app.route('/api/loan-applications/<int:app_id>/amortization', methods=['GET'])
    @jwt_required()
    def get_amortization_schedule(app_id):
        application = LoanApplication.query.get_or_404(app_id)
        product = application.product
        try:
            amortization_data = generate_amortization_table(
                capital=application.requested_amount,
                interest_rate=product.interest_rate,
                term_months=application.requested_term,
                commission_type=product.commission_type,
                admin_commission_rate=product.admin_commission_rate,
                include_iva=True # Asumir que para contratos formales siempre se incluye IVA
            )
            payments = Payment.query.filter_by(application_id=app_id).order_by(Payment.payment_date).all()
            amortization_data['payments'] = [{'amount': p.amount, 'date': p.payment_date.isoformat()} for p in payments]
            return jsonify(amortization_data)
        except ValueError as e:
            return jsonify({"msg": str(e)}), 400

    @app.route('/api/loan-applications/<int:app_id>/contract-data', methods=['GET'])
    @jwt_required()
    def get_contract_data(app_id):
        application = LoanApplication.query.get_or_404(app_id)
        # (Security checks omitted for brevity)
        product = application.product
        applicant = application.applicant

        amortization_data = generate_amortization_table(
            capital=application.requested_amount,
            interest_rate=product.interest_rate,
            term_months=application.requested_term,
            commission_type=product.commission_type,
            admin_commission_rate=product.admin_commission_rate,
            include_iva=True
        )

        contract_data = {
            "client": {"name": applicant.full_name, "dui": applicant.dui, "nit": applicant.nit},
            "loan": {
                "id": application.id,
                "amount_text": f"${application.requested_amount:,.2f}",
                "term_months": application.requested_term,
                "interest_rate_annual": f"{(product.interest_rate * 100):.2f}%",
                "monthly_payment": f"${amortization_data['summary']['total_monthly_payment']:,.2f}",
                "signature_status": application.signature_status,
                "tea": amortization_data['summary']['tea']
            },
            # ... other contract data
        }
        return jsonify(contract_data)

    # (Other routes like /employees, /payroll, etc. are omitted for brevity but are still part of the app)
    # --- All other routes from previous steps are assumed to be here ---

    return app

def setup_database(app):
    """Creates database tables and seeds initial data."""
    with app.app_context():
        print("Initializing database...")
        db.create_all()

        if not Role.query.first():
            print("Seeding roles...")
            db.session.bulk_save_objects([Role(name='Contador'), Role(name='Admin'), Role(name='Cliente'), Role(name='Empleado')])
            db.session.commit()

        if not User.query.filter_by(email='admin@test.com').first():
            print("Seeding admin user...")
            admin_role = Role.query.filter_by(name='Admin').first()
            admin_user = User(email='admin@test.com', role_id=admin_role.id, full_name='Admin de Prueba')
            admin_user.set_password('adminpass')
            db.session.add(admin_user)
            db.session.commit()

        if not LoanProduct.query.first():
            print("Seeding default loan product...")
            default_product = LoanProduct(
                name="Préstamo Personal Avanzado",
                min_amount=500,
                max_amount=10000,
                interest_rate=0.15,
                term_months=24,
                commission_type='A', # Sobre capital
                admin_commission_rate=0.05, # 5%
                is_active=True
            )
            db.session.add(default_product)
            db.session.commit()

        # (Other seeding logic remains)
        print("Database initialization complete.")


if __name__ == '__main__':
    app = create_app()
    # For a clean start, it's better to manage db creation separately
    # setup_database(app)
    app.run(debug=True, port=5001)