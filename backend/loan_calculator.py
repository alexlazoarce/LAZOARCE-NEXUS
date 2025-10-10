import pandas as pd

def generate_amortization_table(capital, interest_rate, term_months, commission_type, admin_commission_rate):
    """
    Generates a French Method amortization schedule.

    Args:
        capital (float): The principal amount of the loan.
        interest_rate (float): The annual interest rate (e.g., 0.15 for 15%).
        term_months (int): The total number of months for the loan.
        commission_type (str): The type of administrative commission ('A', 'B', or 'C').
        admin_commission_rate (float): The administrative commission rate.

    Returns:
        A dictionary containing the amortization schedule (as a list of dicts)
        and a summary of totals.
    """
    if not all([capital > 0, interest_rate > 0, term_months > 0, admin_commission_rate >= 0]):
        raise ValueError("Loan parameters must be positive.")

    # Calculate monthly interest rate
    monthly_interest_rate = interest_rate / 12

    # Calculate the fixed monthly payment (annuity) using the formula
    if monthly_interest_rate > 0:
        monthly_payment = capital * (monthly_interest_rate * (1 + monthly_interest_rate)**term_months) / ((1 + monthly_interest_rate)**term_months - 1)
    else:
        monthly_payment = capital / term_months

    # Calculate administrative commission based on the selected type
    total_admin_commission = 0
    if commission_type == 'A': # On principal amount
        total_admin_commission = capital * admin_commission_rate
    elif commission_type == 'B': # On total interest
        total_interest_precalc = (monthly_payment * term_months) - capital
        total_admin_commission = total_interest_precalc * admin_commission_rate
    elif commission_type == 'C': # On principal + interest
        total_interest_precalc = (monthly_payment * term_months) - capital
        total_admin_commission = (capital + total_interest_precalc) * admin_commission_rate

    total_loan_cost = capital + (monthly_payment * term_months) - capital + total_admin_commission
    total_monthly_payment_with_commission = (monthly_payment * term_months + total_admin_commission) / term_months

    # Generate the schedule
    schedule = []
    remaining_balance = capital
    total_interest_paid = 0

    for i in range(1, term_months + 1):
        interest_for_month = remaining_balance * monthly_interest_rate
        principal_for_month = monthly_payment - interest_for_month
        remaining_balance -= principal_for_month
        total_interest_paid += interest_for_month

        schedule.append({
            'month': i,
            'payment': round(monthly_payment, 2),
            'principal': round(principal_for_month, 2),
            'interest': round(interest_for_month, 2),
            'balance': round(abs(remaining_balance), 2)
        })

    summary = {
        'total_principal': round(capital, 2),
        'total_interest': round(total_interest_paid, 2),
        'total_admin_commission': round(total_admin_commission, 2),
        'total_loan_cost': round(total_loan_cost, 2),
        'fixed_monthly_payment': round(monthly_payment, 2),
        'total_monthly_payment_with_commission': round(total_monthly_payment_with_commission, 2)
    }

    return {'schedule': schedule, 'summary': summary}