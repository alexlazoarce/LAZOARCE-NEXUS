from datetime import datetime
from dateutil.relativedelta import relativedelta
from decimal import Decimal, ROUND_HALF_UP
import math
import logging

# Configurar logging
logger = logging.getLogger(__name__)

# --- CONSTANTES ---
PRECISION_TIR = Decimal('0.0001')
MAX_ITERACIONES_TIR = 100
TOLERANCIA_SALDO = Decimal('0.01')

class CalculoPrestamoError(Exception):
    """Excepción personalizada para errores de cálculo de préstamos."""
    pass

# --- FUNCIONES DE CÁLCULO DE COMISIONES (MEJORADAS) ---

def es_porcentaje(valor: float) -> bool:
    """Determina si un valor es un porcentaje (0 < valor <= 1)."""
    return 0 < valor <= 1

def calcular_comision(monto: float, tasa_comision: float) -> float:
    """
    Calcula comisión ya sea como porcentaje o monto fijo.
    """
    if es_porcentaje(tasa_comision):
        return monto * tasa_comision
    return tasa_comision

def calcular_comision_apertura(monto: float, producto) -> float:
    """Calcula comisión de apertura."""
    try:
        return round(calcular_comision(monto, producto.comision_apertura), 2)
    except AttributeError:
        logger.warning("Producto sin comision_apertura definida, usando 0")
        return 0.0
    except Exception as e:
        logger.error(f"Error calculando comisión apertura: {e}")
        return 0.0

def calcular_comision_administracion(monto: float, producto) -> float:
    """Calcula comisión de administración mensual."""
    try:
        return round(calcular_comision(monto, getattr(producto, 'comision_administracion', 0)), 2)
    except Exception as e:
        logger.error(f"Error calculando comisión administración: {e}")
        return 0.0

def calcular_seguro(monto: float, producto) -> float:
    """Calcula seguro mensual."""
    try:
        return round(calcular_comision(monto, getattr(producto, 'seguro', 0)), 2)
    except Exception as e:
        logger.error(f"Error calculando seguro: {e}")
        return 0.0

# --- CÁLCULO DE TIR MEJORADO ---

def calcular_tir(flujo_caja: list, precision: float = 0.0001, max_iteraciones: int = 100) -> float | None:
    """
    Calcula TIR usando Newton-Raphson con mayor robustez.
    """
    try:
        if not flujo_caja or flujo_caja[0] >= 0:
            return None
        
        # Método de bisección como fallback si Newton falla
        def van(tasa: float) -> float:
            return sum(flujo / ((1 + tasa) ** i) for i, flujo in enumerate(flujo_caja))
        
        # Newton-Raphson
        tasa = 0.1
        for i in range(max_iteraciones):
            van_val = van(tasa)
            if abs(van_val) < precision:
                return tasa
            
            # Derivada del VAN
            van_derivada = sum(
                -i * flujo / ((1 + tasa) ** (i + 1)) 
                for i, flujo in enumerate(flujo_caja) 
                if i > 0 and abs(flujo) > 0
            )
            
            if abs(van_derivada) < precision:
                break
            
            nueva_tasa = tasa - van_val / van_derivada
            if nueva_tasa < 0:
                nueva_tasa = tasa * 0.9  # Evitar tasas negativas
            
            if abs(nueva_tasa - tasa) < precision:
                return round(nueva_tasa, 6)
            
            tasa = nueva_tasa
        
        # Fallback: método de bisección
        left, right = 0.0, 1.0
        while right - left > precision:
            mid = (left + right) / 2
            if van(mid) * van(right) > 0:
                left = mid
            else:
                right = mid
        return round((left + right) / 2, 6)
        
    except Exception as e:
        logger.error(f"Error calculando TIR: {e}")
        return None

# --- CÁLCULO DE TEA MEJORADO ---

def calcular_tea(tasa_mensual_nominal: float, plazo_meses: int, 
                comision_apertura: float, capital_desembolsado: float) -> float:
    """Calcula TEA usando TIR con validaciones mejoradas."""
    try:
        if capital_desembolsado <= 0 or plazo_meses <= 0:
            return 0.0

        # Construir flujo de caja
        flujo_caja = [Decimal('-' + str(capital_desembolsado))]
        capital_a_financiar = capital_desembolsado + comision_apertura

        if tasa_mensual_nominal == 0:
            cuota = capital_a_financiar / plazo_meses
        else:
            factor = (1 + tasa_mensual_nominal) ** plazo_meses
            cuota = capital_a_financiar * tasa_mensual_nominal * factor / (factor - 1)

        flujo_caja.extend([Decimal(str(cuota))] * plazo_meses)
        
        # Convertir a float para TIR
        flujo_float = [float(f) for f in flujo_caja]
        tir_mensual = calcular_tir(flujo_float)
        
        if tir_mensual is None:
            return 0.0

        tea = ((1 + tir_mensual) ** 12 - 1) * 100
        return round(float(tea), 2)
        
    except Exception as e:
        logger.error(f"Error calculando TEA: {e}")
        return 0.0

# --- TABLA DE AMORTIZACIÓN MEJORADA ---

def calcular_fecha_vencimiento(fecha_inicio: datetime, mes: int) -> str:
    """Calcula fecha de vencimiento con precisión."""
    fecha_venc = fecha_inicio + relativedelta(months=mes)
    return fecha_venc.strftime('%Y-%m-%d')

def calcular_cuota_frances(capital: float, tasa_mensual: float, plazo_meses: int) -> float:
    """Calcula cuota francesa con precisión decimal."""
    if tasa_mensual == 0:
        return capital / plazo_meses
    
    capital_dec = Decimal(str(capital))
    tasa_dec = Decimal(str(tasa_mensual))
    plazo_dec = Decimal(str(plazo_meses))
    
    factor = (Decimal(1) + tasa_dec) ** plazo_dec
    cuota = capital_dec * tasa_dec * factor / (factor - 1)
    
    return float(cuota.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

def generar_tabla_amortizacion(
    capital_base: float, 
    plazo_meses: int, 
    tasa_mensual: float, 
    cuota_base: float, 
    comision_administracion: float, 
    seguro: float,
    fecha_inicio: datetime = None
) -> list:
    """
    Genera tabla de amortización con precisión y redondeo correcto.
    """
    if fecha_inicio is None:
        fecha_inicio = datetime.now()
    
    tabla = []
    saldo = Decimal(str(capital_base))
    cuota_base_dec = Decimal(str(cuota_base))
    
    for mes in range(1, plazo_meses + 1):
        # Cálculos con Decimal para precisión
        interes_dec = saldo * Decimal(str(tasa_mensual))
        amortizacion_dec = cuota_base_dec - interes_dec
        
        # Ajuste final
        if mes == plazo_meses or saldo < amortizacion_dec + TOLERANCIA_SALDO:
            amortizacion_dec = saldo
            cuota_base_dec = interes_dec + amortizacion_dec
        
        saldo_anterior = saldo
        saldo = (saldo - amortizacion_dec).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # Convertir a float para la tabla
        fila = {
            "mes": mes,
            "fecha_vencimiento": calcular_fecha_vencimiento(fecha_inicio, mes),
            "saldo_inicial": float(saldo_anterior.quantize(Decimal('0.01'))),
            "cuota_base": float(cuota_base_dec.quantize(Decimal('0.01'))),
            "interes": float(interes_dec.quantize(Decimal('0.01'))),
            "amortizacion": float(amortizacion_dec.quantize(Decimal('0.01'))),
            "comision_administracion": float(Decimal(str(comision_administracion)).quantize(Decimal('0.01'))),
            "seguro": float(Decimal(str(seguro)).quantize(Decimal('0.01'))),
            "cuota_total": float((
                cuota_base_dec + 
                Decimal(str(comision_administracion)) + 
                Decimal(str(seguro))
            ).quantize(Decimal('0.01'))),
            "saldo_final": max(float(saldo), 0)
        }
        
        tabla.append(fila)
        
        if saldo <= 0:
            break
    
    return tabla

# --- FUNCIÓN PRINCIPAL MEJORADA ---

def calcular_prestamo_completo(
    monto_solicitado: float, 
    producto, 
    plazo_meses: int,
    fecha_aprobacion: datetime = None
) -> dict:
    """
    Función principal mejorada con validaciones completas.
    """
    if fecha_aprobacion is None:
        fecha_aprobacion = datetime.now()
    
    try:
        # Validaciones iniciales
        if monto_solicitado <= 0:
            raise CalculoPrestamoError("Monto solicitado debe ser mayor a 0")
        if plazo_meses <= 0:
            raise CalculoPrestamoError("Plazo debe ser mayor a 0")
        if not hasattr(producto, 'tasa_interes_anual'):
            raise CalculoPrestamoError("Producto debe tener tasa_interes_anual definida")
        
        # 1. Calcular comisiones
        comision_apertura = calcular_comision_apertura(monto_solicitado, producto)
        comision_admin_mensual = calcular_comision_administracion(monto_solicitado, producto)
        seguro_mensual = calcular_seguro(monto_solicitado, producto)

        # 2. Determinar capital base y desembolso
        capital_base = monto_solicitado
        capital_desembolsar = monto_solicitado
        
        if getattr(producto, 'comisiones_se_descuentan_capital', False):
            capital_desembolsar = max(0, monto_solicitado - comision_apertura)
        elif getattr(producto, 'comisiones_se_agregan_capital', False):
            capital_base = monto_solicitado + comision_apertura

        # 3. Calcular tasas
        tasa_mensual = producto.tasa_interes_anual / 12 / 100
        tea = calcular_tea(
            tasa_mensual, 
            plazo_meses, 
            comision_apertura, 
            capital_desembolsar
        ) if getattr(producto, 'aplicar_tea', True) else 0

        # 4. Calcular cuota base
        cuota_base = calcular_cuota_frances(capital_base, tasa_mensual, plazo_meses)

        # 5. Generar tabla de amortización
        tabla_amortizacion = generar_tabla_amortizacion(
            capital_base, plazo_meses, tasa_mensual, cuota_base,
            comision_admin_mensual, seguro_mensual, fecha_aprobacion
        )

        # 6. Calcular totales
        total_intereses = sum(row['interes'] for row in tabla_amortizacion)
        total_com_admin = sum(row['comision_administracion'] for row in tabla_amortizacion)
        total_seguro = sum(row['seguro'] for row in tabla_amortizacion)
        total_a_pagar = sum(row['cuota_total'] for row in tabla_amortizacion)

        return {
            "success": True,
            "parametros": {
                "monto_solicitado": round(monto_solicitado, 2),
                "capital_base_calculo": round(capital_base, 2),
                "capital_a_desembolsar": round(capital_desembolsar, 2),
                "plazo_meses": plazo_meses,
                "tasa_interes_anual": round(producto.tasa_interes_anual, 2),
                "tasa_mensual_efectiva": round(tasa_mensual * 100, 4),
                "tea_calculada": tea
            },
            "resumen_costos": {
                "comision_por_apertura": round(comision_apertura, 2),
                "total_comisiones_admin": round(total_com_admin, 2),
                "total_seguro": round(total_seguro, 2),
                "total_intereses": round(total_intereses, 2),
                "costo_total_credito": round(total_a_pagar, 2)
            },
            "cuota_detalle": {
                "cuota_mensual_total_aprox": round(tabla_amortizacion[0]['cuota_total'], 2)
            },
            "tabla_amortizacion": tabla_amortizacion,
            "fecha_aprobacion": fecha_aprobacion.isoformat()
        }
        
    except CalculoPrestamoError as e:
        logger.error(f"Error de validación en cálculo: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"Error inesperado en cálculo: {e}", exc_info=True)
        return {"success": False, "error": f"Error interno: {str(e)}"}

# --- FUNCIÓN DE PRUEBA ---
def ejemplo_uso():
    """Ejemplo de uso con datos de prueba."""
    class ProductoTest:
        tasa_interes_anual = 12.0
        comision_apertura = 0.02  # 2%
        comision_administracion = 10.0  # Monto fijo
        seguro = 5.0  # Monto fijo
        comisiones_se_descuentan_capital = True
        aplicar_tea = True
    
    resultado = calcular_prestamo_completo(10000, ProductoTest(), 12)
    print("=== RESULTADO DEL CÁLCULO ===")
    print(f"Éxito: {resultado['success']}")
    if resultado['success']:
        print(f"Capital a desembolsar: ${resultado['parametros']['capital_a_desembolsar']:,}")
        print(f"Cuota mensual: ${resultado['cuota_detalle']['cuota_mensual_total_aprox']:,}")
        print(f"TEA: {resultado['parametros']['tea_calculada']}%")
        print(f"Total a pagar: ${resultado['resumen_costos']['costo_total_credito']:,}")
    else:
        print(f"Error: {resultado['error']}")

if __name__ == "__main__":
    ejemplo_uso()
