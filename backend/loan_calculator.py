from decimal import Decimal, ROUND_HALF_UP
import numpy_financial as npf
from datetime import date
from dateutil.relativedelta import relativedelta

def _quantize(d):
    """Redondea un Decimal a 2 decimales para consistencia."""
    return d.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def calculate_loan_details(principal, annual_interest_rate, term_months, commission_rate, commission_type, disbursement_date=None):
    """
    Calcula los detalles completos de un préstamo, incluyendo la tabla de amortización,
    la TIR (Tasa Interna de Retorno) y la TEA (Tasa Efectiva Anual).
    """
    if disbursement_date is None:
        disbursement_date = date.today()

    principal = Decimal(str(principal))
    annual_interest_rate = Decimal(str(annual_interest_rate))
    monthly_interest_rate = annual_interest_rate / Decimal('12')
    term_months = int(term_months)
    commission_rate = Decimal(str(commission_rate))

    if monthly_interest_rate > 0:
        factor = (1 + monthly_interest_rate) ** term_months
        monthly_payment = principal * (monthly_interest_rate * factor) / (factor - 1)
    else:
        monthly_payment = principal / Decimal(term_months)

    amortization_table = []
    current_balance = principal
    total_payment = Decimal('0.00')
    cash_flows = [-float(principal)]

    for month in range(1, term_months + 1):
        interest_for_month = _quantize(current_balance * monthly_interest_rate)

        commission_for_month = Decimal('0.00')
        if commission_type == 'A':
            commission_for_month = _quantize(current_balance * commission_rate)
        elif commission_type == 'B' or commission_type == 'C':
            commission_for_month = _quantize(principal * commission_rate)

        total_monthly_payment = monthly_payment + commission_for_month
        principal_paid = total_monthly_payment - interest_for_month - commission_for_month

        if month == term_months:
            principal_paid = current_balance
            total_monthly_payment = principal_paid + interest_for_month + commission_for_month

        current_balance -= principal_paid
        total_payment += total_monthly_payment
        cash_flows.append(float(total_monthly_payment))

        due_date = disbursement_date + relativedelta(months=month)

        amortization_table.append({
            "month": month,
            "due_date": due_date.isoformat(),
            "initial_balance": float(current_balance + principal_paid),
            "payment": float(total_monthly_payment),
            "interest": float(interest_for_month),
            "commission": float(commission_for_month),
            "principal": float(principal_paid),
            "final_balance": float(current_balance)
        })

    try:
        monthly_tir = npf.irr(cash_flows)
        annual_tea = (1 + monthly_tir) ** 12 - 1
    except Exception:
        monthly_tir = 0.0
        annual_tea = 0.0

    return {
        "monthly_payment": float(_quantize(monthly_payment)),
        "total_payment": float(_quantize(total_payment)),
        "amortization_table": amortization_table,
        "tir_monthly": round(monthly_tir, 6),
        "tea_annual": round(annual_tea, 4)
    }