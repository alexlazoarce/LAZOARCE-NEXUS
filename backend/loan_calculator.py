from datetime import datetime
from dateutil.relativedelta import relativedelta

# --- Funciones de Cálculo de Comisiones ---

def calcular_comision_apertura(monto, producto):
    """
    Calcula comisión de apertura según configuración del producto.
    NOTA: La lógica asume que una comisión porcentual siempre será <= 1 (e.g., 0.05 para 5%),
    y un monto fijo será > 1. Esto puede ser ambiguo si un monto fijo es <= 1.
    """
    try:
        # Si la comisión es un porcentaje (asumido como <= 1)
        if 0 < producto.comision_apertura <= 1:
            return monto * producto.comision_apertura
        # Si es un monto fijo
        else:
            return producto.comision_apertura
    except Exception as e:
        print(f"Error calculando comisión apertura: {str(e)}")
        return 0.0

def calcular_comision_administracion(monto, producto):
    """
    Calcula comisión de administración mensual.
    Misma nota de ambigüedad que en comision_apertura.
    """
    try:
        if 0 < producto.comision_administracion <= 1:
            return monto * producto.comision_administracion
        else:
            return producto.comision_administracion
    except Exception as e:
        print(f"Error calculando comisión administración: {str(e)}")
        return 0.0

def calcular_seguro(monto, producto):
    """
    Calcula seguro mensual.
    Misma nota de ambigüedad que en comision_apertura.
    """
    try:
        if 0 < producto.seguro <= 1:
            return monto * producto.seguro
        else:
            return producto.seguro
    except Exception as e:
        print(f"Error calculando seguro: {str(e)}")
        return 0.0

# --- Funciones de Cálculo Financiero (TIR y TEA) ---

def calcular_tir(flujo_caja, precision=0.0001, max_iteraciones=100):
    """
    Calcula la Tasa Interna de Retorno usando el método de Newton-Raphson.
    """
    try:
        tasa = 0.1
        for _ in range(max_iteraciones):
            van = sum(flujo / ((1 + tasa) ** i) for i, flujo in enumerate(flujo_caja))
            van_derivada = sum(-i * flujo / ((1 + tasa) ** (i + 1)) for i, flujo in enumerate(flujo_caja) if i > 0)

            if abs(van_derivada) < precision:
                break

            nueva_tasa = tasa - van / van_derivada

            if abs(nueva_tasa - tasa) < precision:
                return nueva_tasa

            tasa = nueva_tasa
        return tasa
    except (ZeroDivisionError, OverflowError, ValueError):
        # Retorna None si no se puede calcular
        return None

def calcular_tea(tasa_mensual_nominal, plazo_meses, comision_apertura, capital_desembolsado):
    """
    Calcula la Tasa Efectiva Anual (TEA) usando el método de TIR.
    """
    try:
        if capital_desembolsado <= 0: return 0.0

        # Flujo de caja: desembolso inicial y cuotas de pago
        flujo_caja = [-capital_desembolsado]
        capital_a_financiar = capital_desembolsado + comision_apertura

        if tasa_mensual_nominal == 0:
            cuota = capital_a_financiar / plazo_meses if plazo_meses > 0 else 0
        else:
            factor = (1 + tasa_mensual_nominal) ** plazo_meses
            cuota = capital_a_financiar * tasa_mensual_nominal * factor / (factor - 1)

        flujo_caja.extend([cuota] * plazo_meses)

        tir_mensual = calcular_tir(flujo_caja)

        if tir_mensual is None: return 0.0

        # Convertir TIR mensual a TEA
        tea = ((1 + tir_mensual) ** 12) - 1
        return round(tea * 100, 2)
    except Exception as e:
        print(f"Error calculando TEA: {str(e)}")
        return 0.0

# --- Generación de Tabla de Amortización ---

def calcular_fecha_vencimiento(mes):
    return (datetime.now() + relativedelta(months=mes)).strftime('%Y-%m-%d')

def generar_tabla_amortizacion(capital_base, plazo_meses, tasa_mensual, cuota_base, comision_administracion, seguro):
    """
    Genera tabla de amortización completa.
    """
    tabla, saldo = [], capital_base
    for mes in range(1, plazo_meses + 1):
        interes = saldo * tasa_mensual
        amortizacion = cuota_base - interes

        if mes == plazo_meses or (saldo - amortizacion) < 0.01:
            amortizacion = saldo
            cuota_base = interes + amortizacion

        cuota_total = cuota_base + comision_administracion + seguro
        saldo_anterior, saldo = saldo, saldo - amortizacion

        tabla.append({
            "mes": mes, "fecha_vencimiento": calcular_fecha_vencimiento(mes),
            "saldo_inicial": round(saldo_anterior, 2), "cuota_base": round(cuota_base, 2),
            "interes": round(interes, 2), "amortizacion": round(amortizacion, 2),
            "comision_administracion": round(comision_administracion, 2),
            "seguro": round(seguro, 2), "cuota_total": round(cuota_total, 2),
            "saldo_final": round(max(saldo, 0), 2)
        })
        if saldo < 0.01: break
    return tabla

# --- Función Principal de Cálculo ---

def calcular_prestamo_completo(monto_solicitado, producto, plazo_meses):
    """
    Calcula préstamo con todas las opciones de comisiones e intereses.
    Recibe el objeto 'producto' para evitar dependencias de la base de datos.
    """
    try:
        # 1. Calcular comisiones
        comision_apertura = calcular_comision_apertura(monto_solicitado, producto)
        comision_admin_mensual = calcular_comision_administracion(monto_solicitado, producto)
        seguro_mensual = calcular_seguro(monto_solicitado, producto)

        # 2. Determinar capital base y desembolso
        capital_base, capital_desembolsar = monto_solicitado, monto_solicitado
        if producto.comisiones_se_descuentan_capital:
            capital_desembolsar = monto_solicitado - comision_apertura
        elif producto.comisiones_se_agregan_capital:
            capital_base = monto_solicitado + comision_apertura

        # 3. Calcular tasas y TEA
        tasa_mensual = producto.tasa_interes_anual / 12 / 100
        tea = calcular_tea(tasa_mensual, plazo_meses, comision_apertura, capital_desembolsar) if producto.aplicar_tea else 0

        # 4. Calcular cuota base (Método Francés sobre el capital base)
        if tasa_mensual == 0:
            cuota_base = capital_base / plazo_meses if plazo_meses > 0 else 0
        else:
            factor = (1 + tasa_mensual) ** plazo_meses
            cuota_base = capital_base * tasa_mensual * factor / (factor - 1)

        # 5. Generar tabla de amortización
        tabla_amortizacion = generar_tabla_amortizacion(capital_base, plazo_meses, tasa_mensual, cuota_base, comision_admin_mensual, seguro_mensual)

        # 6. Calcular totales
        total_intereses = sum(c['interes'] for c in tabla_amortizacion)
        total_com_admin = sum(c['comision_administracion'] for c in tabla_amortizacion)
        total_seguro = sum(c['seguro'] for c in tabla_amortizacion)
        total_a_pagar = capital_base + total_intereses + comision_apertura + total_com_admin + total_seguro

        return {
            "success": True,
            "parametros": {
                "monto_solicitado": monto_solicitado, "capital_base_calculo": capital_base,
                "capital_a_desembolsar": capital_desembolsar, "plazo_meses": plazo_meses,
                "tasa_interes_anual": producto.tasa_interes_anual, "tasa_mensual_efectiva": round(tasa_mensual * 100, 4),
                "tea_calculada": tea
            },
            "resumen_costos": {
                "comision_por_apertura": comision_apertura, "total_comisiones_admin": total_com_admin,
                "total_seguro": total_seguro, "total_intereses": total_intereses,
                "costo_total_credito": total_a_pagar
            },
            "cuota_detalle": {"cuota_mensual_total_aprox": round(tabla_amortizacion[0]['cuota_total'], 2) if tabla_amortizacion else 0},
            "tabla_amortizacion": tabla_amortizacion
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": f"Error en el cálculo principal: {str(e)}"}