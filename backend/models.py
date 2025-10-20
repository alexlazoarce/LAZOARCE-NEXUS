 from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

from .database import db

# --- MODELOS DE BASE DE DATOS ---
class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    users = db.relationship('User', backref='role', lazy=True)

    def __repr__(self):
        return f'<Role {self.name}>'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)

    # --- Campos de perfil para contratos ---
    full_name = db.Column(db.String(120), nullable=True)
    dui = db.Column(db.String(20), nullable=True, unique=True)
    nit = db.Column(db.String(20), nullable=True, unique=True)

    loan_applications = db.relationship('LoanApplication', backref='applicant', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email}>'

class LoanProduct(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    loan_type = db.Column(db.String(50), nullable=False) # 'Personal', 'Grupal', etc.
    min_amount = db.Column(db.Float, nullable=False)
    max_amount = db.Column(db.Float, nullable=False)
    default_interest_rate = db.Column(db.Float, nullable=False) # Tasa mensual
    default_admin_commission = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    applications = db.relationship('LoanApplication', backref='product', lazy=True)

    def __repr__(self):
        return f'<LoanProduct {self.name}>'

class LoanApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('loan_product.id'), nullable=False)
    requested_amount = db.Column(db.Float, nullable=False)
    requested_term = db.Column(db.Integer, nullable=False) # En meses
    status = db.Column(db.String(50), default='Solicitud', nullable=False) # Solicitud, Análisis, Aprobación, etc.
    application_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<LoanApplication ID: {self.id} - Status: {self.status}>'

# --- Modelos de Contabilidad ---
class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    account_type = db.Column(db.String(50), nullable=False) # e.g., Activo, Pasivo, Ingreso

    def __repr__(self):
        return f'<Account {self.code} - {self.name}>'

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    description = db.Column(db.String(255), nullable=False)
    entries = db.relationship('JournalEntry', backref='transaction', lazy=True, cascade="all, delete-orphan")

class JournalEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    debit = db.Column(db.Float, nullable=False, default=0.0)
    credit = db.Column(db.Float, nullable=False, default=0.0)
    account = db.relationship('Account')


# --- Modelos de Clientes y Firma Electrónica ---

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre_completo = db.Column(db.String(200), nullable=False)
    dui = db.Column(db.String(12), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    direccion = db.Column(db.String(255), nullable=False)
    estado = db.Column(db.String(20), default='PENDIENTE', nullable=False) # PENDIENTE, ACTIVO, INACTIVO
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    contrato_integracion_id = db.Column(db.String(50), db.ForeignKey('contrato_integracion.contrato_id'))
    firma_electronica_id = db.Column(db.String(50), db.ForeignKey('firma_electronica.firma_id'))

class ContratoIntegracion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contrato_id = db.Column(db.String(50), unique=True, nullable=False)
    cliente_dui = db.Column(db.String(12), nullable=False)
    cliente_nombre = db.Column(db.String(200), nullable=False)
    cliente_email = db.Column(db.String(120), nullable=False)
    contrato_html = db.Column(db.Text, nullable=False)
    # Estados: PENDIENTE_FIRMA, FIRMADO_ELECTRONICAMENTE, PENDIENTE_VALIDACION_MANUAL, FIRMADO_MANUALMENTE, RECHAZADO
    estado = db.Column(db.String(50), default="PENDIENTE_FIRMA")
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_firma = db.Column(db.DateTime)

    # Campos para soportar firma manual y generalización
    tipo_firma = db.Column(db.String(20))  # ELECTRONICA, MANUAL
    documento_firmado_url = db.Column(db.String(255)) # Path al archivo subido

class FirmaElectronica(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firma_id = db.Column(db.String(50), unique=True, nullable=False)
    documento_id = db.Column(db.String(50), nullable=False)
    cliente_dui = db.Column(db.String(12), nullable=False)
    hash_documento = db.Column(db.String(64), nullable=False)
    fecha_firma = db.Column(db.DateTime, nullable=False)

    # DATOS DE TRAZABILIDAD
    ip_cliente = db.Column(db.String(45), nullable=False)
    user_agent = db.Column(db.Text, nullable=False)
    ubicacion_aprox = db.Column(db.String(100))
    timestamp_servidor = db.Column(db.DateTime, default=datetime.utcnow)

    # DATOS BIOMÉTRICOS (hash de datos biométricos)
    hash_biometrico = db.Column(db.String(64))
    tipo_biometria = db.Column(db.String(20))  # facial, huella, voz

    # VALIDACIÓN DE IDENTIDAD
    score_confianza = db.Column(db.Float)  # 0-100%
    metodo_validacion = db.Column(db.String(50))
    dispositivo_id = db.Column(db.String(100))

class CertificadoValidacion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    certificado_id = db.Column(db.String(50), unique=True, nullable=False)
    firma_id = db.Column(db.String(50), nullable=False)
    documento_id = db.Column(db.String(50), nullable=False)
    cliente_dui = db.Column(db.String(12), nullable=False)
    pdf_certificado = db.Column(db.Text)  # Base64 del PDF
    fecha_generacion = db.Column(db.DateTime, default=datetime.utcnow)
    valido_hasta = db.Column(db.DateTime)


class ProductoCredito(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    tasa_interes_anual = db.Column(db.Float, nullable=False)
    comision_apertura = db.Column(db.Float, default=0.0)  # Porcentaje o monto fijo
    comision_administracion = db.Column(db.Float, default=0.0)  # Porcentaje mensual
    seguro = db.Column(db.Float, default=0.0)  # Porcentaje mensual
    plazo_maximo = db.Column(db.Integer, nullable=False)  # En meses
    monto_minimo = db.Column(db.Float, nullable=False)
    monto_maximo = db.Column(db.Float, nullable=False)

    # OPCIONES DE CÁLCULO
    comisiones_generan_intereses = db.Column(db.Boolean, default=False)
    comisiones_se_agregan_capital = db.Column(db.Boolean, default=False)
    comisiones_se_descuentan_capital = db.Column(db.Boolean, default=True)
    aplicar_tea = db.Column(db.Boolean, default=True)

    estado = db.Column(db.String(20), default='ACTIVO')


# --- Modelos de Planillas (Payroll) ---

class Empleado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    salario_base = db.Column(db.Float, nullable=False)
    # Se pueden agregar otros campos relevantes como DUI, NIT, cargo, etc.
    planillas = db.relationship('Planilla', backref='empleado', lazy=True)

class Planilla(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    empleado_id = db.Column(db.Integer, db.ForeignKey('empleado.id'), nullable=False)
    salario_base = db.Column(db.Float, nullable=False)
    isss = db.Column(db.Float, nullable=False)
    afp = db.Column(db.Float, nullable=False)
    renta = db.Column(db.Float, nullable=False)
    salario_neto = db.Column(db.Float, nullable=False)
    fecha_calculo = db.Column(db.DateTime, default=datetime.utcnow)