from datetime import date, datetime
from models import Payment, LoanApplication
from loan_calculator import calculate_loan_details

def get_loan_status(application_id):
    """
    Calculates the current status of a loan, including balance, paid amount,
    and delinquency status.
    """
    app = LoanApplication.query.get_or_404(application_id)
    if app.status != 'Desembolsada':
        return {"message": "El préstamo no ha sido desembolsado."}

    # Regenerate the amortization schedule to ensure it's up-to-date
    # The disbursement date is the decision date for an approved loan
    disbursement_date = app.decision_date.date()
    schedule = calculate_loan_details(
        principal=app.amount_requested,
        annual_interest_rate=app.product.interest_rate,
        term_months=app.term_months,
        commission_rate=app.product.commission_rate,
        commission_type=app.commission_calculation_method,
        disbursement_date=disbursement_date
    )['amortization_table']

    total_paid = sum(p.amount_paid for p in app.payments)

    # --- Delinquency Calculation ---
    today = date.today()
    amount_due = 0.0
    next_due_date = None
    days_delinquent = 0

    for row in schedule:
        due_date = date.fromisoformat(row['due_date'])
        if due_date <= today:
            amount_due += row['payment']
        else:
            if not next_due_date:
                next_due_date = due_date
            break # Stop once we are in the future

    balance_due = amount_due - total_paid

    if balance_due > 0:
        # Find the first unpaid due date
        first_unpaid_due_date = None
        paid_so_far_iter = total_paid
        for row in schedule:
            if paid_so_far_iter >= row['payment']:
                paid_so_far_iter -= row['payment']
            else:
                first_unpaid_due_date = date.fromisoformat(row['due_date'])
                break

        if first_unpaid_due_date and first_unpaid_due_date < today:
            days_delinquent = (today - first_unpaid_due_date).days

    return {
        "loan_id": app.id,
        "customer_name": app.applicant.full_name,
        "total_loan_amount": app.amount_requested,
        "total_paid": round(total_paid, 2),
        "outstanding_balance": round(app.total_payment - total_paid, 2),
        "amount_due_to_date": round(amount_due, 2),
        "current_due_balance": round(balance_due, 2),
        "days_delinquent": days_delinquent,
        "status": "En Mora" if days_delinquent > 0 else "Al Día",
        "next_due_date": next_due_date.isoformat() if next_due_date else "N/A"
    }