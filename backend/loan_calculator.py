from datetime import datetime, timedelta

def generate_amortization_table(
    capital_solicitado,
    meses,
    tasa_interes_mensual,
    comision_administracion=0,
    comisiones_iniciales=0,
    commission_method='no_interest'  # Opciones: 'no_interest', 'add_to_capital', 'subtract_from_capital'
):
    """
    Genera una tabla de amortización y un resumen del préstamo, soportando varios métodos de comisión.
    """
    tabla = []
    tasa_mensual = tasa_interes_mensual / 100
    com_adm_mensual_pct = comision_administracion / 100

    # --- Determinar la base de cálculo y el capital recibido según el método ---
    base_calculo = capital_solicitado
    capital_recibido = capital_solicitado
    comision_inicial_mensual = 0

    if commission_method == 'add_to_capital':
        base_calculo = capital_solicitado + comisiones_iniciales
    elif commission_method == 'subtract_from_capital':
        capital_recibido = capital_solicitado - comisiones_iniciales
        # El interés se calcula sobre el capital solicitado original.
        base_calculo = capital_solicitado
    elif commission_method == 'no_interest':
        comision_inicial_mensual = comisiones_iniciales / meses if meses > 0 else 0

    # --- Cálculo de la cuota base (Método Francés) ---
    if tasa_mensual == 0:
        cuota_base = base_calculo / meses if meses > 0 else 0
    else:
        factor = (1 + tasa_mensual) ** meses
        cuota_base = (base_calculo * tasa_mensual * factor) / (factor - 1) if factor != 1 else 0

    saldo_restante = base_calculo
    fecha_vencimiento = datetime.now()

    for mes in range(1, meses + 1):
        if saldo_restante <= 0.01:
            break

        interes_ordinario = saldo_restante * tasa_mensual
        comision_adm_monto = saldo_restante * com_adm_mensual_pct

        amortizacion = cuota_base - interes_ordinario - comision_adm_monto

        cuota_total = cuota_base + comision_inicial_mensual

        # Ajuste en la última cuota para que el saldo final sea exactamente 0
        if mes == meses or saldo_restante < cuota_base:
            amortizacion = saldo_restante
            cuota_total = amortizacion + interes_ordinario + comision_adm_monto + comision_inicial_mensual

        saldo_anterior = saldo_restante
        saldo_restante -= amortizacion

        if saldo_restante < 0:
            saldo_restante = 0

        fecha_vencimiento += timedelta(days=30)

        fila = {
            "Mes": mes,
            "Fecha Vencimiento": fecha_vencimiento.strftime('%Y-%m-%d'),
            "Saldo Inicial": round(saldo_anterior, 2),
            "Interés": round(interes_ordinario, 2),
            "Com. Adm": round(comision_adm_monto, 2),
            "Com. Inic": round(comision_inicial_mensual, 2),
            "Amortización": round(amortizacion, 2),
            "Cuota": round(cuota_total, 2),
            "Saldo Final": round(saldo_restante, 2),
        }
        tabla.append(fila)

    summary = {
        "capital_solicitado": round(capital_solicitado, 2),
        "capital_recibido_cliente": round(capital_recibido, 2),
        "base_calculo_intereses": round(base_calculo, 2),
        "total_a_pagar": round(sum(f['Cuota'] for f in tabla), 2),
        "total_intereses": round(sum(f['Interés'] for f in tabla), 2)
    }

    return {"summary": summary, "amortization_table": tabla}