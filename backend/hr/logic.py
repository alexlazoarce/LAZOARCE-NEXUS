from datetime import date, datetime
from backend.extensions import db
from backend.hr.models import Empleado, PrestamoEmpleado, Nomina
from backend.models import AccountingEntry, EntryDetail, ChartOfAccounts

def calcular_retencion_renta(salario_renta):
    if salario_renta <= 487.60: return 0.0
    elif salario_renta <= 642.85: return (salario_renta - 487.60) * 0.10
    elif salario_renta <= 915.81: return (salario_renta - 642.85) * 0.20 + 15.53
    elif salario_renta <= 2058.67: return (salario_renta - 915.81) * 0.30 + 70.31
    else: return (salario_renta - 2058.67) * 0.35 + 484.62

def calcular_descuentos_legales(salario_bruto):
    base_isss = min(salario_bruto, 1000.00)
    descuento_isss = base_isss * 0.03
    base_afp = min(salario_bruto, 6500.00)
    descuento_afp = base_afp * 0.0725
    salario_renta = salario_bruto - descuento_isss - descuento_afp
    renta = calcular_retencion_renta(salario_renta)
    return {'descuento_afp': round(descuento_afp, 2), 'descuento_isss': round(descuento_isss, 2), 'renta': round(renta, 2)}

def calcular_descuento_prestamos(empleado_id):
    prestamos = PrestamoEmpleado.query.filter_by(empleado_id=empleado_id, estado='VIGENTE').all()
    return sum(min(p.cuota_mensual, p.saldo_pendiente) for p in prestamos if p.saldo_pendiente > 0)

def generar_asiento_contable_nomina(nomina):
    empleado = nomina.empleado
    asiento = AccountingEntry(entry_date=nomina.fecha_pago, description=f"Nómina {nomina.periodo} - {empleado.nombre_completo}", reference=f"NOM-{nomina.id}", created_by_user_id=1)
    db.session.add(asiento)
    db.session.flush()
    def add_detail(account_code, debit=0.0, credit=0.0):
        account = ChartOfAccounts.query.filter_by(account_code=account_code).one()
        db.session.add(EntryDetail(entry_id=asiento.id, account_id=account.id, debit=debit, credit=credit))
    add_detail(empleado.cuenta_contable_salarios, debit=nomina.total_ingresos)
    add_detail("2-02-001", credit=nomina.liquido_pagar)
    if nomina.descuento_afp > 0: add_detail("2-02-005", credit=nomina.descuento_afp)
    if nomina.descuento_isss > 0: add_detail("2-02-004", credit=nomina.descuento_isss)
    if nomina.renta > 0: add_detail("2-01-005", credit=nomina.renta)
    if nomina.descuento_prestamos > 0:
        cuenta_prestamo = empleado.prestamos[0].cuenta_contable if empleado.prestamos else "1-02-012"
        add_detail(cuenta_prestamo, credit=nomina.descuento_prestamos)
    return asiento.id

def generar_nomina_empleado(empleado_id, periodo, horas_extra=0, comisiones=0, bonificaciones=0):
    empleado = Empleado.query.get_or_404(empleado_id)
    salario_base = empleado.salario_base
    pago_horas_extra = horas_extra * (salario_base / 30 / 8 * 1.5)
    total_ingresos = salario_base + pago_horas_extra + comisiones + bonificaciones
    descuentos_legales = calcular_descuentos_legales(total_ingresos)
    descuento_prestamos = calcular_descuento_prestamos(empleado_id)
    total_descuentos = sum(descuentos_legales.values()) + descuento_prestamos
    liquido_pagar = total_ingresos - total_descuentos
    nomina = Nomina(
        empleado_id=empleado_id, periodo=periodo, fecha_pago=date.today(),
        salario_base=salario_base, horas_extra=pago_horas_extra, comisiones=comisiones,
        bonificaciones=bonificaciones, total_ingresos=total_ingresos,
        descuento_afp=descuentos_legales['descuento_afp'], descuento_isss=descuentos_legales['descuento_isss'],
        renta=descuentos_legales['renta'], descuento_prestamos=descuento_prestamos,
        total_descuentos=total_descuentos, liquido_pagar=liquido_pagar, estado='GENERADA'
    )
    db.session.add(nomina)
    db.session.flush()
    asiento_id = generar_asiento_contable_nomina(nomina)
    if asiento_id:
        nomina.asiento_contable_id = asiento_id
        nomina.estado = 'CONTABILIZADA'
    return nomina

def generar_boleta_pago(nomina_id):
    nomina = Nomina.query.get_or_404(nomina_id)
    empleado = nomina.empleado
    return f"""
    <!DOCTYPE html><html><head><title>Boleta de Pago - {empleado.nombre_completo}</title></head>
    <body><h1>Boleta de Pago</h1><p><strong>Empleado:</strong> {empleado.nombre_completo}</p>
    <p><strong>Período:</strong> {nomina.periodo}</p>
    <h2>LÍQUIDO A PAGAR: ${nomina.liquido_pagar:,.2f}</h2></body></html>
    """