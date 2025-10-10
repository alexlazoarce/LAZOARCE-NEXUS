import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, JWTManager

# Import the db instance and models from our models module
from models import db, User, Role, Account
# Import the accounting service
from accounting_service import get_general_ledger

def create_app():
    """
    Application factory function to create and configure the Flask app.
    """
    app = Flask(__name__)
    CORS(app)

    # --- CONFIGURATION ---
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a-very-secret-key')
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'another-very-secret-key')
    # Use an instance-relative config to ensure the db is in a known location
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
            access_token = create_access_token(identity=email)
            return jsonify(access_token=access_token)

        return jsonify({"msg": "Bad email or password"}), 401

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

        # Seed Roles if they don't exist
        if not Role.query.first():
            print("Seeding roles...")
            roles = [Role(name='Contador'), Role(name='Admin')]
            db.session.bulk_save_objects(roles)
            db.session.commit()

        # Seed Test User if it doesn't exist
        if not User.query.filter_by(email='contador@test.com').first():
            print("Seeding test user ('Contador')...")
            contador_role = Role.query.filter_by(name='Contador').first()
            if contador_role:
                test_user = User(email='contador@test.com', role_id=contador_role.id)
                test_user.set_password('password123')
                db.session.add(test_user)
                db.session.commit()

        # Seed Chart of Accounts if it doesn't exist
        if not Account.query.first():
            print("Seeding initial chart of accounts...")
            accounts_to_create = [
                {'code': '1101', 'name': 'Caja', 'account_type': 'Activo'},
                {'code': '1102', 'name': 'Bancos', 'account_type': 'Activo'},
            ]
            for acc_data in accounts_to_create:
                db.session.add(Account(**acc_data))
            db.session.commit()

        print("Database initialization complete.")


if __name__ == '__main__':
    app = create_app()
    setup_database(app)
    app.run(debug=True, port=5001)