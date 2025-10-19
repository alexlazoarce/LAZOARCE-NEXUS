from datetime import date, datetime
from .models import Payment, LoanApplication, User
from .loan_calculator import calculate_loan_details

def get_portfolio_status(user_id):
    """
    Calculates the portfolio status for a specific user, aggregating key metrics.
    """
    user = User.query.get(user_id)
    if not user:
        # This should ideally not happen if called from a @jwt_required route
        return {"error": "User not found"}, 404

    # It's more efficient to query applications related to the user directly
    # Assuming 'user_id' in LoanApplication links to the credit executive
    applications = LoanApplication.query.filter_by(user_id=user.id, status='Desembolsada').all()

    portfolio_details = []
    total_ventas = 0.0
    total_recuperado = 0.0

    for app in applications:
        # We can reuse the existing get_loan_status for detailed calculations
        status_details = get_loan_status(app.id)
        if "message" not in status_details:
            portfolio_details.append(status_details)
            # 'Ventas' is the total amount of loans disbursed
            total_ventas += app.amount_requested
            # 'Recuperado' is the total amount paid back across all loans
            total_recuperado += status_details['total_paid']

    summary = {
        "total_ventas": round(total_ventas, 2),
        "total_recuperado": round(total_recuperado, 2),
        "total_outstanding": round(total_ventas - total_recuperado, 2),
        "active_loans": len(portfolio_details)
    }

    return {
        "portfolio": portfolio_details,
        "summary": summary
    }


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