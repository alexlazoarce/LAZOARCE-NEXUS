 import os
from flask import Flask
from dotenv import load_dotenv

from backend.extensions import db, jwt
from backend.models import Role
import backend.models # Para que SQLAlchemy descubra todos los modelos

def create_app():
    load_dotenv()
    app = Flask(__name__)

    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///lazoarce.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')

    db.init_app(app)
    jwt.init_app(app)

    from backend.routes.auth import auth_bp
    from backend.routes.loan_management import loan_management_bp
    from backend.hr.routes import hr_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(loan_management_bp)
    app.register_blueprint(hr_bp)

    @app.route('/')
    def index():
        return "Servidor del Sistema de Gestión Financiera en funcionamiento."

    return app

from backend.scripts.initialize_accounts import initialize_chart_of_accounts

def initialize_database(app):
    with app.app_context():
        db.create_all()
        if not Role.query.first():
            roles = ['Super Administrador', 'Administrador General', 'Ejecutivo de Crédito', 'Cobrador', 'Contador', 'Cliente']
            for role_name in roles:
                db.session.add(Role(name=role_name))
            db.session.commit()
            print("Base de datos y roles inicializados.")

        initialize_chart_of_accounts()

if __name__ == '__main__':
    app = create_app()
    initialize_database(app)
    app.run(host='0.0.0.0', port=5000, debug=True)