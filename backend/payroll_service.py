def calculate_renta_tax(taxable_income):
    """
    Calcula el Impuesto sobre la Renta mensual según la tabla progresiva de El Salvador.
    """
    if taxable_income <= 472.00:
        return 0.0
    elif taxable_income <= 895.24:
        # Tramo II: 10% sobre el exceso de 472.00 + cuota fija de 17.67
        return ((taxable_income - 472.00) * 0.10) + 17.67
    elif taxable_income <= 2038.10:
        # Tramo III: 20% sobre el exceso de 895.24 + cuota fija de 60.00
        return ((taxable_income - 895.24) * 0.20) + 60.00
    else:
        # Tramo IV: 30% sobre el exceso de 2038.10 + cuota fija de 288.57
        return ((taxable_income - 2038.10) * 0.30) + 288.57

def calculate_payslip_details(base_salary):
    """
    Calcula el desglose completo de una boleta de pago para un salario base.
    """
    gross_salary = base_salary

    # Constantes de ley
    AFP_EMPLOYEE_RATE = 0.0725
    AFP_EMPLOYER_RATE = 0.0775
    ISSS_EMPLOYEE_RATE = 0.03
    ISSS_EMPLOYER_RATE = 0.075
    ISSS_SALARY_CAP = 1000.00

    # Calcular deducciones del empleado
    isss_base = min(gross_salary, ISSS_SALARY_CAP)
    afp_employee = gross_salary * AFP_EMPLOYEE_RATE
    isss_employee = isss_base * ISSS_EMPLOYEE_RATE

    # Calcular base imponible para Renta
    taxable_income = gross_salary - afp_employee - isss_employee

    # Calcular Renta
    renta_tax = calculate_renta_tax(taxable_income)

    # Calcular salario neto
    total_deductions = afp_employee + isss_employee + renta_tax
    net_salary = gross_salary - total_deductions

    # Calcular aportes del patrono
    afp_employer = gross_salary * AFP_EMPLOYER_RATE
    isss_employer = isss_base * ISSS_EMPLOYER_RATE

    return {
        "gross_salary": round(gross_salary, 2),
        "afp_employee": round(afp_employee, 2),
        "isss_employee": round(isss_employee, 2),
        "renta_tax": round(renta_tax, 2),
        "net_salary": round(net_salary, 2),
        "afp_employer": round(afp_employer, 2),
        "isss_employer": round(isss_employer, 2),
    }