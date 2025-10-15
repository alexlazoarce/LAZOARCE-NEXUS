"""
NEXUS-BI: Business Intelligence Service
"""
from .models import db, LoanApplication
from . import collections_service
from sqlalchemy import func

def get_loan_portfolio_kpis():
    """
    Calculates and returns key performance indicators for the loan portfolio
    using the collections_service for accurate, up-to-date loan status.
    """
    active_loans = LoanApplication.query.filter(LoanApplication.status == 'Desembolsada').all()

    total_portfolio = 0.0
    overdue_amount = 0.0
    active_loans_count = len(active_loans)
    overdue_loans_count = 0

    if not active_loans:
        return {
            "total_portfolio": 0,
            "active_loans_count": 0,
            "overdue_loans_count": 0,
            "overdue_amount": 0,
            "overdue_percentage": 0,
            "average_loan_amount": 0,
        }

    for loan in active_loans:
        try:
            status = collections_service.get_loan_status(loan.id)
            # Use the more accurate 'outstanding_balance'
            total_portfolio += status.get('outstanding_balance', 0)
            if status.get('days_delinquent', 0) > 0:
                overdue_loans_count += 1
                overdue_amount += status.get('outstanding_balance', 0)
        except Exception as e:
            # Log the error and continue, so one bad loan doesn't break the dashboard
            print(f"Error calculating status for loan {loan.id}: {e}")

    overdue_percentage = (overdue_amount / total_portfolio) if total_portfolio > 0 else 0.0

    # This remains a simplification, but is acceptable for a BI overview
    total_disbursed_amount = db.session.query(func.sum(LoanApplication.amount_requested)).filter(
        LoanApplication.status == 'Desembolsada'
    ).scalar() or 0.0
    average_loan_amount = total_disbursed_amount / active_loans_count if active_loans_count > 0 else 0.0

    return {
        "total_portfolio": round(total_portfolio, 2),
        "active_loans_count": active_loans_count,
        "overdue_loans_count": overdue_loans_count,
        "overdue_amount": round(overdue_amount, 2),
        "overdue_percentage": round(overdue_percentage, 4),
        "average_loan_amount": round(average_loan_amount, 2),
    }
