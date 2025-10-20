from backend.extensions import db

class Empleado(db.Model):
    __tablename__ = 'empleado'
    id = db.Column(db.Integer, primary_key=True)
    codigo_empleado = db.Column(db.String(20), unique=True, nullable=False)
    dui = db.Column(db.String(12), unique=True, nullable=False)
    nit = db.Column(db.String(20))
    isss = db.Column(db.String(20))
    afp = db.Column(db.String(20))
    nombre_completo = db.Column(db.String(200), nullable=False)
    fecha_ingreso = db.Column(db.Date, nullable=False)
    cargo = db.Column(db.String(100), nullable=False)
    salario_base = db.Column(db.Float, nullable=False)
    tipo_contrato = db.Column(db.String(50))
    estado = db.Column(db.String(20), default='ACTIVO')
    cuenta_contable_salarios = db.Column(db.String(10), default='5-01-001')

    prestamos = db.relationship('PrestamoEmpleado', backref='empleado', lazy=True)
    nominas = db.relationship('Nomina', backref='empleado', lazy=True)

class PrestamoEmpleado(db.Model):
    __tablename__ = 'prestamo_empleado'
    id = db.Column(db.Integer, primary_key=True)
    empleado_id = db.Column(db.Integer, db.ForeignKey('empleado.id'), nullable=False)
    monto_prestamo = db.Column(db.Float, nullable=False)
    tasa_interes = db.Column(db.Float, default=0.0)
    plazo_meses = db.Column(db.Integer, nullable=False)
    cuota_mensual = db.Column(db.Float, nullable=False)
    saldo_pendiente = db.Column(db.Float, nullable=False)
    fecha_desembolso = db.Column(db.Date, nullable=False)
    estado = db.Column(db.String(20), default='VIGENTE')
    cuenta_contable = db.Column(db.String(10), default='1-02-012')

class Nomina(db.Model):
    __tablename__ = 'nomina'
    id = db.Column(db.Integer, primary_key=True)
    empleado_id = db.Column(db.Integer, db.ForeignKey('empleado.id'), nullable=False)
    periodo = db.Column(db.String(7), nullable=False)
    fecha_pago = db.Column(db.Date, nullable=False)

    salario_base = db.Column(db.Float, nullable=False)
    horas_extra = db.Column(db.Float, default=0.0)
    comisiones = db.Column(db.Float, default=0.0)
    bonificaciones = db.Column(db.Float, default=0.0)
    total_ingresos = db.Column(db.Float, nullable=False)

    descuento_afp = db.Column(db.Float, default=0.0)
    descuento_isss = db.Column(db.Float, default=0.0)
    renta = db.Column(db.Float, default=0.0)

    descuento_prestamos = db.Column(db.Float, default=0.0)
    otros_descuentos = db.Column(db.Float, default=0.0)
    total_descuentos = db.Column(db.Float, nullable=False)

    liquido_pagar = db.Column(db.Float, nullable=False)

    asiento_contable_id = db.Column(db.Integer, db.ForeignKey('accounting_entry.id'))
    estado = db.Column(db.String(20), default='PENDIENTE')