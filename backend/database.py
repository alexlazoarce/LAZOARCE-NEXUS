from flask_sqlalchemy import SQLAlchemy

# Initialize the SQLAlchemy object.
# This object will be imported by both the main application and the models.
db = SQLAlchemy()