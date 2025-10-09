import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Importar las extensiones y modelos desde los nuevos módulos
from .extensions import db, jwt
from .models import Role

def create_app():
    """
    Crea y configura una instancia de la aplicación Flask usando el patrón de Application Factory.
    """
    app = Flask(__name__, instance_relative_config=True)
    CORS(app)
    load_dotenv()

    # --- CONFIGURACIÓN ---
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'un-secreto-muy-seguro')

    # Asegurar que el directorio de instancia exista
    os.makedirs(app.instance_path, exist_ok=True)
    db_path = os.path.join(app.instance_path, 'lazoarce.db')

    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'otro-secreto-muy-seguro')

    # --- INICIALIZACIÓN DE EXTENSIONES CON LA APP ---
    db.init_app(app)
    jwt.init_app(app)

    # --- REGISTRO DE BLUEPRINTS ---
    # Las importaciones se hacen aquí para evitar dependencias circulares
    from .routes.auth import auth_bp
    from .routes.profile import profile_bp
    from .routes.products import products_bp
    from .routes.applications import applications_bp
    from .routes.loans import loans_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(applications_bp)
    app.register_blueprint(loans_bp)

    # --- RUTA DE BIENVENIDA ---
    @app.route('/')
    def index():
        return jsonify({"message": "Servidor del Sistema de Gestión Financiera en funcionamiento."})

    return app

def initialize_database(app):
    """
    Crea la base de datos y los roles iniciales si no existen.
    """
    with app.app_context():
        db.create_all()
        if Role.query.first() is None:
            roles = ['Super Administrador', 'Administrador General', 'Ejecutivo de Crédito', 'Cobrador', 'Contador', 'Cliente']
            for role_name in roles:
                db.session.add(Role(name=role_name))
            db.session.commit()
            print("Base de datos y roles inicializados.")

# Este bloque permite ejecutar la aplicación directamente para desarrollo
if __name__ == '__main__':
    app = create_app()
    initialize_database(app)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)