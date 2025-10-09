from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager

# Crear instancias de las extensiones de Flask
# Estas no están vinculadas a ninguna aplicación todavía.
# Serán vinculadas usando el patrón de "application factory".
db = SQLAlchemy()
jwt = JWTManager()