"""
NEXUS-BI: Business Intelligence Service
"""
from .models import db, LoanApplication, Payment
from sqlalchemy import func
from datetime import date, timedelta

def get_loan_portfolio_kpis():
    """
    Calculates and returns key performance indicators for the loan portfolio.
    """
    # --- KPIs de Cartera ---

    # 1. Monto Total de la Cartera (Capital pendiente de pago)
    # Esto es una simplificación. Un cálculo real sumaría el `final_balance` de la última cuota de cada préstamo.
    # Por ahora, sumaremos el monto solicitado de todos los préstamos desembolsados.
    total_portfolio = db.session.query(func.sum(LoanApplication.amount_requested)).filter(
        LoanApplication.status == 'Desembolsada'
    ).scalar() or 0.0

    # 2. Número de Préstamos Activos
    active_loans_count = db.session.query(func.count(LoanApplication.id)).filter(
        LoanApplication.status == 'Desembolsada'
    ).scalar() or 0

    # 3. Monto en Mora (Préstamos con pagos atrasados)
    # Simplificación: consideraremos "en mora" cualquier préstamo desembolsado que no ha recibido un pago en los últimos 35 días.
    today = date.today()
    thirty_five_days_ago = today - timedelta(days=35)

    # Subquery to find the latest payment date for each loan
    latest_payments_sq = db.session.query(
        Payment.application_id,
        func.max(Payment.payment_date).label('last_payment_date')
    ).group_by(Payment.application_id).subquery()

    # Join LoanApplication with the subquery
    overdue_loans = db.session.query(LoanApplication).join(
        latest_payments_sq, LoanApplication.id == latest_payments_sq.c.application_id
    ).filter(
        LoanApplication.status == 'Desembolsada',
        latest_payments_sq.c.last_payment_date < thirty_five_days_ago
    ).all()

    overdue_amount = sum(loan.amount_requested for loan in overdue_loans) # Simplificación del capital pendiente

    # 4. Porcentaje de Mora
    overdue_percentage = (overdue_amount / total_portfolio) if total_portfolio > 0 else 0.0

    # 5. Monto Promedio de Préstamo
    average_loan_amount = total_portfolio / active_loans_count if active_loans_count > 0 else 0.0

    # --- KPIs Financieros (Simplificados) ---

    # 6. Total Desembolsado este mes
    start_of_month = today.replace(day=1)
    disbursed_this_month = db.session.query(func.sum(LoanApplication.amount_requested)).filter(
        LoanApplication.status == 'Desembolsada',
        LoanApplication.decision_date >= start_of_month
    ).scalar() or 0.0

    # 7. Total Cobrado este mes
    collected_this_month = db.session.query(func.sum(Payment.amount_paid)).filter(
        Payment.payment_date >= start_of_month
    ).scalar() or 0.0

    return {
        "total_portfolio": round(total_portfolio, 2),
        "active_loans_count": active_loans_count,
        "overdue_amount": round(overdue_amount, 2),
        "overdue_percentage": round(overdue_percentage, 4),
        "average_loan_amount": round(average_loan_amount, 2),
        "disbursed_this_month": round(disbursed_this_month, 2),
        "collected_this_month": round(collected_this_month, 2)
    }
