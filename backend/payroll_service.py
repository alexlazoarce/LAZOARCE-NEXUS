from models import db, Employee, PayrollLog, PaySlip

def calculate_payslip_details(base_salary):
    """
    Calculates all payroll components for a single employee based on Salvadoran law.

    Args:
        base_salary (float): The employee's monthly base salary.

    Returns:
        dict: A dictionary containing all calculated salary components.
    """
    # Constants for Salvadoran payroll
    ISSS_EMPLOYEE_RATE = 0.03
    ISSS_EMPLOYER_RATE = 0.075
    ISSS_MAX_CONTRIBUTION_BASE = 1000.00
    AFP_EMPLOYEE_RATE = 0.0725
    AFP_EMPLOYER_RATE = 0.0875

    # 1. Calculate ISSS deduction
    isss_contribution_base = min(base_salary, ISSS_MAX_CONTRIBUTION_BASE)
    isss_employee = isss_contribution_base * ISSS_EMPLOYEE_RATE
    isss_employer = isss_contribution_base * ISSS_EMPLOYER_RATE

    # 2. Calculate AFP deduction
    afp_employee = base_salary * AFP_EMPLOYEE_RATE
    afp_employer = base_salary * AFP_EMPLOYER_RATE

    # 3. Calculate taxable income
    taxable_income = base_salary - isss_employee - afp_employee

    # 4. Calculate Renta (Income Tax) based on monthly brackets
    renta_tax = 0.00
    if taxable_income > 2038.10:
        renta_tax = ((taxable_income - 2038.10) * 0.30) + 288.57
    elif taxable_income > 895.24:
        renta_tax = ((taxable_income - 895.24) * 0.20) + 60.00
    elif taxable_income > 472.00:
        renta_tax = ((taxable_income - 472.00) * 0.10) + 17.67

    # Ensure renta is not negative
    renta_tax = max(0, renta_tax)

    # 5. Calculate net salary
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
    Calculates payroll for all active employees for a given period,
    creates a PayrollLog, and generates a PaySlip for each employee.
    """
    active_employees = Employee.query.filter_by(is_active=True).all()
    if not active_employees:
        raise ValueError("No active employees found to run payroll for.")

    # Create a new log for this payroll run
    new_payroll_log = PayrollLog(
        period_name=period_name,
        created_by_user_id=created_by_user_id
    )
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
            gross_salary=payslip_data['gross_salary'],
            afp_employee=payslip_data['afp_employee'],
            isss_employee=payslip_data['isss_employee'],
            renta_tax=payslip_data['renta_tax'],
            net_salary=payslip_data['net_salary'],
            afp_employer=payslip_data['afp_employer'],
            isss_employer=payslip_data['isss_employer']
        )
        db.session.add(new_payslip)

        # Aggregate totals
        totals["total_gross"] += payslip_data['gross_salary']
        totals["total_net"] += payslip_data['net_salary']
        totals["total_isss_employee"] += payslip_data['isss_employee']
        totals["total_afp_employee"] += payslip_data['afp_employee']
        totals["total_renta"] += payslip_data['renta_tax']
        totals["total_isss_employer"] += payslip_data['isss_employer']
        totals["total_afp_employer"] += payslip_data['afp_employer']

    # The session is committed in the route after this function and the accounting entry are done
    return new_payroll_log, totals