from models import db, Employee, PayrollLog, PaySlip

def calculate_payslip_details(base_salary):
    """Calculates all payroll components for a single employee based on Salvadoran law."""
    ISSS_EMPLOYEE_RATE = 0.03
    ISSS_EMPLOYER_RATE = 0.075
    ISSS_MAX_CONTRIBUTION_BASE = 1000.00
    AFP_EMPLOYEE_RATE = 0.0725
    AFP_EMPLOYER_RATE = 0.0875

    isss_contribution_base = min(base_salary, ISSS_MAX_CONTRIBUTION_BASE)
    isss_employee = isss_contribution_base * ISSS_EMPLOYEE_RATE
    isss_employer = isss_contribution_base * ISSS_EMPLOYER_RATE

    afp_employee = base_salary * AFP_EMPLOYEE_RATE
    afp_employer = base_salary * AFP_EMPLOYER_RATE

    taxable_income = base_salary - isss_employee - afp_employee

    renta_tax = 0.00
    if taxable_income > 2038.10:
        renta_tax = ((taxable_income - 2038.10) * 0.30) + 288.57
    elif taxable_income > 895.24:
        renta_tax = ((taxable_income - 895.24) * 0.20) + 60.00
    elif taxable_income > 472.00:
        renta_tax = ((taxable_income - 472.00) * 0.10) + 17.67

    renta_tax = max(0, renta_tax)

    total_deductions = isss_employee + afp_employee + renta_tax
    net_salary = base_salary - total_deductions

    return {
        "gross_salary": base_salary,
        "isss_employee": round(isss_employee, 2),
        "afp_employee": round(afp_employee, 2),
        "renta_tax": round(renta_tax, 2),
        "net_salary": round(net_salary, 2),
        "isss_employer": round(isss_employer, 2),
        "afp_employer": round(afp_employer, 2),
        "total_deductions": round(total_deductions, 2)
    }

def calculate_payroll_for_all(period_name, created_by_user_id):
    """
    Calculates payroll for all active employees, creating logs and payslips.
    """
    active_employees = Employee.query.filter_by(is_active=True).all()
    if not active_employees:
        raise ValueError("No active employees found.")

    new_payroll_log = PayrollLog(period_name=period_name, created_by_user_id=created_by_user_id)
    db.session.add(new_payroll_log)

    totals = {
        "total_gross": 0.0, "total_net": 0.0, "total_isss_employee": 0.0,
        "total_afp_employee": 0.0, "total_renta": 0.0, "total_isss_employer": 0.0,
        "total_afp_employer": 0.0
    }

    for employee in active_employees:
        payslip_data = calculate_payslip_details(employee.base_salary)

        new_payslip = PaySlip(
            payroll_log=new_payroll_log,
            employee_id=employee.id,
            **payslip_data
        )
        db.session.add(new_payslip)

        for key, value in payslip_data.items():
            if key.startswith('total_'):
                totals[key] += value
            elif key in ['gross_salary', 'net_salary', 'isss_employee', 'afp_employee', 'renta_tax', 'isss_employer', 'afp_employer']:
                 totals[f"total_{key.replace('_salary','').replace('_employee','_emp').replace('_employer','_empr')}"] += value


    # Round totals to 2 decimal places
    for key in totals:
        totals[key] = round(totals[key], 2)

    return new_payroll_log, totals