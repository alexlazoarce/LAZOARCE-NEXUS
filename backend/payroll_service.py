from decimal import Decimal, ROUND_HALF_UP
from .models import Employee, User
from . import accounting_service
from datetime import date

# --- Constantes de Nómina para El Salvador (Valores de ejemplo, deben ser verificados) ---
ISSS_EMPLOYEE_RATE = Decimal('0.03')
ISSS_MAX_CONTRIBUTION = Decimal('30.00') # 3% sobre un máximo de $1000
AFP_EMPLOYEE_RATE = Decimal('0.0725')

# Tramos de Renta (mensual)
# Formato: (límite_inferior, límite_superior, tasa, cuota_fija, sobre_exceso_de)
RENTA_BRACKETS = [
    (Decimal('0.01'), Decimal('472.00'), Decimal('0.0'), Decimal('0.0'), Decimal('0.0')),
    (Decimal('472.01'), Decimal('895.24'), Decimal('0.10'), Decimal('17.67'), Decimal('472.00')),
    (Decimal('895.25'), Decimal('2038.10'), Decimal('0.20'), Decimal('60.00'), Decimal('895.24')),
    (Decimal('2038.11'), Decimal('999999.99'), Decimal('0.30'), Decimal('288.57'), Decimal('2038.10'))
]

def _quantize(d):
    """Redondea un Decimal a 2 decimales."""
    return d.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def calculate_payslip_details(monthly_salary):
    """
    Calcula las deducciones y el salario neto para un salario mensual dado.
    """
    salary = Decimal(str(monthly_salary))

    # 1. Calcular deducción de ISSS
    isss_deduction = min(salary * ISSS_EMPLOYEE_RATE, ISSS_MAX_CONTRIBUTION)

    # 2. Calcular deducción de AFP
    afp_deduction = salary * AFP_EMPLOYEE_RATE

    # 3. Calcular base imponible para Renta
    taxable_income = salary - isss_deduction - afp_deduction

    # 4. Calcular deducción de Renta
    renta_deduction = Decimal('0.0')
    if taxable_income > RENTA_BRACKETS[0][0]:
        for _, upper, rate, fixed_fee, excess_over in RENTA_BRACKETS:
            if taxable_income <= upper:
                renta_deduction = ((taxable_income - excess_over) * rate) + fixed_fee
                break

    # 5. Calcular Salario Neto
    total_deductions = isss_deduction + afp_deduction + renta_deduction
    net_salary = salary - total_deductions

    return {
        "gross_salary": float(_quantize(salary)),
        "isss_deduction": float(_quantize(isss_deduction)),
        "afp_deduction": float(_quantize(afp_deduction)),
        "renta_deduction": float(_quantize(renta_deduction)),
        "net_salary": float(_quantize(net_salary)),
    }

def process_payroll_for_tenant(tenant_id):
    """
    Processes payroll for all active employees in a given tenant and creates
    a consolidated journal entry.
    """
    employees = Employee.query.filter_by(tenant_id=tenant_id, is_active=True).all()

    total_gross = Decimal('0.00')
    total_isss = Decimal('0.00')
    total_afp = Decimal('0.00')
    total_renta = Decimal('0.00')
    total_net = Decimal('0.00')

    for emp in employees:
        payslip = calculate_payslip_details(emp.salary)
        total_gross += Decimal(str(payslip['gross_salary']))
        total_isss += Decimal(str(payslip['isss_deduction']))
        total_afp += Decimal(str(payslip['afp_deduction']))
        total_renta += Decimal(str(payslip['renta_deduction']))
        total_net += Decimal(str(payslip['net_salary']))

    if not employees:
        return {"message": "No hay empleados activos para procesar la nómina."}, 404

    try:
        run_date = date.today()
        journal_entry = accounting_service.create_payroll_journal_entry(
            run_date=run_date,
            total_gross_salary=float(total_gross),
            total_isss=float(total_isss),
            total_afp=float(total_afp),
            total_renta=float(total_renta),
            total_net_salary=float(total_net)
        )
        # The commit will be handled by the calling route
        return {"message": "Nómina procesada y asiento contable creado.", "journal_entry_id": journal_entry.id}, 201
    except ValueError as e:
        return {"error": str(e)}, 400