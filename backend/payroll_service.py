# backend/payroll_service.py

def calcular_isss(salario_base):
    """
    Calcula la deducción del ISSS.
    El techo para el cálculo es de $1000.
    """
    techo_isss = 1000.0
    tasa_isss = 0.03

    salario_gravable = min(salario_base, techo_isss)
    return round(salario_gravable * tasa_isss, 2)

def calcular_afp(salario_base):
    """
    Calcula la deducción de la AFP.
    El techo para el cálculo es de $7,045.06.
    """
    techo_afp = 7045.06
    tasa_afp = 0.0725

    salario_gravable = min(salario_base, techo_afp)
    return round(salario_gravable * tasa_afp, 2)

def calcular_renta(salario_base, isss, afp):
    """
    Calcula la deducción de la Renta sobre la renta.
    """
    salario_descontado = salario_base - isss - afp

    # Tabla de Renta (periodo mensual)
    # Tramo I: $0.01 - $472.00 (Sin retención)
    if salario_descontado <= 472.00:
        return 0.0
    # Tramo II: $472.01 - $895.24
    elif 472.01 <= salario_descontado <= 895.24:
        exceso = salario_descontado - 472.00
        retencion = (exceso * 0.10) + 17.67
        return round(retencion, 2)
    # Tramo III: $895.25 - $2038.10
    elif 895.25 <= salario_descontado <= 2038.10:
        exceso = salario_descontado - 895.24
        retencion = (exceso * 0.20) + 60.00
        return round(retencion, 2)
    # Tramo IV: $2038.11 en adelante
    else: # > 2038.10
        exceso = salario_descontado - 2038.10
        retencion = (exceso * 0.30) + 288.57
        return round(retencion, 2)

def calcular_planilla(salario_base):
    """
    Orquesta el cálculo completo de la planilla para un salario dado.
    """
    try:
        isss = calcular_isss(salario_base)
        afp = calcular_afp(salario_base)
        renta = calcular_renta(salario_base, isss, afp)

        salario_neto = salario_base - isss - afp - renta

        return {
            "success": True,
            "salario_base": salario_base,
            "isss": isss,
            "afp": afp,
            "renta": renta,
            "total_deducciones": round(isss + afp + renta, 2),
            "salario_neto": round(salario_neto, 2)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}