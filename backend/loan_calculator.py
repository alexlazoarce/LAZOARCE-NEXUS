import numpy_financial as npf

def generate_amortization_table(capital, interest_rate, term_months, commission_type='A', admin_commission_rate=0.0, include_iva=False):
    """
    Generates a French Method amortization schedule with advanced commission and TEA calculation.
    """
    if not all([capital > 0, interest_rate > 0, term_months > 0, admin_commission_rate >= 0]):
        raise ValueError("Loan parameters must be positive.")

    monthly_interest_rate = interest_rate / 12
    interest_calculation_capital = capital

    if monthly_interest_rate > 0:
        monthly_payment_interest_part = interest_calculation_capital * (monthly_interest_rate * (1 + monthly_interest_rate)**term_months) / ((1 + monthly_interest_rate)**term_months - 1)
    else:
        monthly_payment_interest_part = interest_calculation_capital / term_months

    total_interest_precalc = (monthly_payment_interest_part * term_months) - interest_calculation_capital

    commission_base = 0
    if commission_type == 'A':
        commission_base = capital
    elif commission_type == 'B':
        commission_base = total_interest_precalc
    elif commission_type == 'C':
        commission_base = capital + total_interest_precalc

    admin_commission = commission_base * admin_commission_rate
    iva_on_commission = admin_commission * 0.13 if include_iva else 0.0
    total_commission_and_iva = admin_commission + iva_on_commission

    schedule = []
    remaining_balance = interest_calculation_capital
    for i in range(1, term_months + 1):
        interest_for_month = remaining_balance * monthly_interest_rate
        principal_for_month = monthly_payment_interest_part - interest_for_month
        remaining_balance -= principal_for_month
        schedule.append({
            'month': i,
            'payment': round(monthly_payment_interest_part, 2),
            'principal': round(principal_for_month, 2),
            'interest': round(interest_for_month, 2),
            'balance': round(abs(remaining_balance), 2)
        })

    net_disbursement = -capital
    total_monthly_payment = monthly_payment_interest_part + (total_commission_and_iva / term_months)
    cash_flows = [net_disbursement] + [total_monthly_payment] * term_months

    monthly_tea = npf.irr(cash_flows)
    annual_tea = ((1 + monthly_tea) ** 12) - 1 if monthly_tea is not None and not isinstance(monthly_tea, complex) else 0.0

    total_paid = total_monthly_payment * term_months
    total_interest_paid = sum(item['interest'] for item in schedule)
    total_cost = total_interest_paid + total_commission_and_iva

    summary = {
        'requested_capital': round(capital, 2),
        'total_interest': round(total_interest_paid, 2),
        'admin_commission': round(admin_commission, 2),
        'iva_on_commission': round(iva_on_commission, 2),
        'total_commission_and_iva': round(total_commission_and_iva, 2),
        'total_cost_of_loan': round(total_cost, 2),
        'total_paid': round(total_paid, 2),
        'base_monthly_payment': round(monthly_payment_interest_part, 2),
        'total_monthly_payment': round(total_monthly_payment, 2),
        'tea': f"{annual_tea:.2%}"
    }

    return {'schedule': schedule, 'summary': summary}