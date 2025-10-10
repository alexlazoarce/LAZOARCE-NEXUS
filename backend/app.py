import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, JWTManager, get_jwt

# Import the db instance and models from our models module
from models import db, User, Role, Account, LoanProduct, LoanApplication
# Import the accounting service
from accounting_service import get_general_ledger, create_disbursement_journal_entry

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

    # --- LOAN PRODUCT ROUTES ---
    @app.route('/api/loan-products', methods=['GET'])
    @jwt_required()
    def get_loan_products():
        products = LoanProduct.query.filter_by(is_active=True).all()
        return jsonify([{
            'id': p.id,
            'name': p.name,
            'min_amount': p.min_amount,
            'max_amount': p.max_amount,
            'interest_rate': p.interest_rate,
            'term_months': p.term_months
        } for p in products])

    # --- LOAN APPLICATION ROUTES ---
    @app.route('/api/loan-applications', methods=['GET', 'POST'])
    @jwt_required()
    def handle_loan_applications():
        current_user_email = get_jwt_identity()
        user = User.query.filter_by(email=current_user_email).first()

        if request.method == 'POST':
            data = request.get_json()
            new_application = LoanApplication(
                user_id=user.id,
                product_id=data['product_id'],
                requested_amount=float(data['requested_amount']),
                requested_term=int(data['requested_term'])
            )
            db.session.add(new_application)
            db.session.commit()
            return jsonify({"msg": "Loan application submitted successfully.", "id": new_application.id}), 201

        if request.method == 'GET':
            claims = get_jwt()
            if claims.get('role') == 'Admin':
                applications = LoanApplication.query.all()
            else:
                applications = LoanApplication.query.filter_by(user_id=user.id).all()

            return jsonify([{
                'id': app.id,
                'product_name': app.product.name,
                'requested_amount': app.requested_amount,
                'status': app.status,
                'application_date': app.application_date.isoformat()
            } for app in applications])

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
            roles = [Role(name='Contador'), Role(name='Admin')]
            db.session.bulk_save_objects(roles)
            db.session.commit()

        # Seed Test User
        if not User.query.filter_by(email='contador@test.com').first():
            print("Seeding test user ('Contador')...")
            contador_role = Role.query.filter_by(name='Contador').first()
            if contador_role:
                test_user = User(email='contador@test.com', role_id=contador_role.id)
                test_user.set_password('password123')
                db.session.add(test_user)
                db.session.commit()

        # Seed Admin User
        if not User.query.filter_by(email='admin@test.com').first():
            print("Seeding admin user...")
            admin_role = Role.query.filter_by(name='Admin').first()
            if admin_role:
                admin_user = User(email='admin@test.com', role_id=admin_role.id)
                admin_user.set_password('adminpass')
                db.session.add(admin_user)
                db.session.commit()

        # Seed Loan Product
        if not LoanProduct.query.first():
            print("Seeding default loan product...")
            default_product = LoanProduct(name="Préstamo Personal", min_amount=500, max_amount=10000, interest_rate=0.15, term_months=24, is_active=True)
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