import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, JWTManager, get_jwt

# Import the db instance and models from our models module
from models import db, User, Role, Account, LoanProduct, LoanApplication, Payment
# Import services
from accounting_service import get_general_ledger, create_disbursement_journal_entry, create_repayment_journal_entry
from loan_calculator import generate_amortization_table

def create_app():
    """
    Application factory function to create and configure the Flask app.
    """
    app = Flask(__name__)
    CORS(app)

    # --- CONFIGURATION ---
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a-very-secret-key')
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'another-very-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(app.instance_path, 'lazoarce.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # --- INITIALIZE EXTENSIONS ---
    db.init_app(app)
    jwt = JWTManager(app)

    # --- AUTHENTICATION ROUTES ---
    @app.route('/api/login', methods=['POST'])
    def login():
        data = request.get_json()
        email = data.get('email', None)
        password = data.get('password', None)

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            access_token = create_access_token(
                identity=email, additional_claims={'role': user.role.name}
            )
            return jsonify(access_token=access_token)

        return jsonify({"msg": "Bad email or password"}), 401

    # --- LOAN & PAYMENT ROUTES ---
    @app.route('/api/loan-products', methods=['GET'])
    @jwt_required()
    def get_loan_products():
        products = LoanProduct.query.filter_by(is_active=True).all()
        return jsonify([{'id': p.id, 'name': p.name, 'min_amount': p.min_amount, 'max_amount': p.max_amount, 'interest_rate': p.interest_rate, 'term_months': p.term_months} for p in products])

    @app.route('/api/loan-applications', methods=['GET', 'POST'])
    @jwt_required()
    def handle_loan_applications():
        current_user_email = get_jwt_identity()
        user = User.query.filter_by(email=current_user_email).first()

        if request.method == 'POST':
            data = request.get_json()
            new_application = LoanApplication(user_id=user.id, product_id=data['product_id'], requested_amount=float(data['requested_amount']), requested_term=int(data['requested_term']))
            db.session.add(new_application)
            db.session.commit()
            return jsonify({"msg": "Loan application submitted successfully.", "id": new_application.id}), 201

        if request.method == 'GET':
            claims = get_jwt()
            # Admins and Accountants can see all applications
            if claims.get('role') in ['Admin', 'Contador']:
                applications = LoanApplication.query.all()
            else:
                applications = LoanApplication.query.filter_by(user_id=user.id).all()

            return jsonify([{'id': app.id, 'applicant_email': app.applicant.email, 'product_name': app.product.name, 'requested_amount': app.requested_amount, 'status': app.status, 'application_date': app.application_date.isoformat()} for app in applications])

    @app.route('/api/loan-applications/<int:app_id>/status', methods=['PUT'])
    @jwt_required()
    def update_application_status(app_id):
        claims = get_jwt()
        if claims.get('role') != 'Admin':
            return jsonify({"msg": "Administration rights required"}), 403

        application = LoanApplication.query.get_or_404(app_id)
        data = request.get_json()
        new_status = data.get('status')

        if not new_status:
            return jsonify({"msg": "Status is required"}), 400

        application.status = new_status

        if new_status == 'Desembolsado':
            try:
                create_disbursement_journal_entry(application)
            except Exception as e:
                db.session.rollback()
                return jsonify({"msg": f"Failed to create accounting entry: {str(e)}"}), 500

        db.session.commit()
        return jsonify({"msg": f"Application status updated to {new_status}"})

    @app.route('/api/loan-applications/<int:app_id>/payments', methods=['POST'])
    @jwt_required()
    def record_payment(app_id):
        claims = get_jwt()
        if claims.get('role') not in ['Admin', 'Contador']:
            return jsonify({"msg": "Authorization required"}), 403

        data = request.get_json()
        amount = data.get('amount')
        if not amount or float(amount) <= 0:
            return jsonify({"msg": "Valid payment amount is required"}), 400

        application = LoanApplication.query.get_or_404(app_id)
        if application.status != 'Desembolsado':
            return jsonify({"msg": "Payments can only be recorded for disbursed loans"}), 400

        recorder = User.query.filter_by(email=get_jwt_identity()).first()
        new_payment = Payment(application_id=app_id, amount=float(amount), recorded_by_user_id=recorder.id)

        try:
            db.session.add(new_payment)
            create_repayment_journal_entry(new_payment)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({"msg": f"Failed to record payment: {str(e)}"}), 500
        return jsonify({"msg": "Payment recorded successfully", "payment_id": new_payment.id}), 201

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
                commission_type='A',
                admin_commission_rate=0.0
            )
            payments = Payment.query.filter_by(application_id=app_id).order_by(Payment.payment_date).all()
            amortization_data['payments'] = [{'amount': p.amount, 'date': p.payment_date.isoformat()} for p in payments]
            return jsonify(amortization_data)
        except ValueError as e:
            return jsonify({"msg": str(e)}), 400

    # --- ACCOUNTING ROUTES ---
    @app.route('/api/accounting/general-ledger', methods=['GET'])
    @jwt_required()
    def get_general_ledger_endpoint():
        ledger_data = get_general_ledger()
        return jsonify(ledger_data)

    # --- HEALTH CHECK ROUTE ---
    @app.route('/health')
    def health_check():
        return "Backend is running!"

    return app

def setup_database(app):
    """
    Creates database tables and seeds initial data within the app context.
    """
    with app.app_context():
        print("Initializing database...")
        db.create_all()

        # Seed Roles
        if not Role.query.first():
            print("Seeding roles...")
            roles = [Role(name='Contador'), Role(name='Admin'), Role(name='Cliente')]
            db.session.bulk_save_objects(roles)
            db.session.commit()

        # Seed Test Users
        if not User.query.filter_by(email='contador@test.com').first():
            print("Seeding test user ('Contador')...")
            contador_role = Role.query.filter_by(name='Contador').first()
            test_user = User(email='contador@test.com', role_id=contador_role.id)
            test_user.set_password('password123')
            db.session.add(test_user)

        if not User.query.filter_by(email='admin@test.com').first():
            print("Seeding admin user...")
            admin_role = Role.query.filter_by(name='Admin').first()
            admin_user = User(email='admin@test.com', role_id=admin_role.id)
            admin_user.set_password('adminpass')
            db.session.add(admin_user)

        if not User.query.filter_by(email='cliente@test.com').first():
            print("Seeding client user...")
            client_role = Role.query.filter_by(name='Cliente').first()
            client_user = User(email='cliente@test.com', role_id=client_role.id)
            client_user.set_password('clientpass')
            db.session.add(client_user)

        db.session.commit()

        # Seed Loan Product
        if not LoanProduct.query.first():
            print("Seeding default loan product...")
            default_product = LoanProduct(name="Préstamo Personal Rápido", min_amount=500, max_amount=10000, interest_rate=0.15, term_months=24, is_active=True)
            db.session.add(default_product)
            db.session.commit()

        # Seed Chart of Accounts
        if not Account.query.first():
            print("Seeding initial chart of accounts...")
            accounts_to_create = [
                {'code': '1101', 'name': 'Caja', 'account_type': 'Activo'},
                {'code': '1102', 'name': 'Bancos', 'account_type': 'Activo'},
                {'code': '1103', 'name': 'Cuentas por Cobrar Préstamos', 'account_type': 'Activo'},
            ]
            for acc_data in accounts_to_create:
                db.session.add(Account(**acc_data))
            db.session.commit()

        print("Database initialization complete.")


if __name__ == '__main__':
    app = create_app()
    setup_database(app)
    app.run(debug=True, port=5001)