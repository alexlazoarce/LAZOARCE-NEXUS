from models import db, Account, JournalEntry, Transaction
from sqlalchemy import func

def get_general_ledger():
    """Calculates the general ledger for all accounts."""
    accounts = Account.query.order_by(Account.code).all()
    ledger = []
    for account in accounts:
        total_debits = db.session.query(func.sum(JournalEntry.debit)).filter(JournalEntry.account_id == account.id).scalar() or 0.0
        total_credits = db.session.query(func.sum(JournalEntry.credit)).filter(JournalEntry.account_id == account.id).scalar() or 0.0
        balance = 0.0
        if account.account_type in ['Activo', 'Gasto']:
            balance = total_debits - total_credits
        else:
            balance = total_credits - total_debits
        ledger.append({
            'account_code': account.code,
            'account_name': account.name,
            'total_debits': round(total_debits, 2),
            'total_credits': round(total_credits, 2),
            'final_balance': round(balance, 2)
        })
    return ledger

def create_disbursement_journal_entry(application):
    """Creates a journal entry for a loan disbursement."""
    loan_receivable_account = Account.query.filter_by(name='Cuentas por Cobrar Préstamos').first()
    bancos_account = Account.query.filter_by(name='Bancos').first()
    if not loan_receivable_account or not bancos_account:
        raise Exception("Required accounts for disbursement not found.")

    transaction = Transaction(description=f"Desembolso de préstamo para solicitud #{application.id}")
    db.session.add(transaction)

    debit = JournalEntry(transaction=transaction, account_id=loan_receivable_account.id, debit=application.requested_amount, credit=0.0)
    credit = JournalEntry(transaction=transaction, account_id=bancos_account.id, debit=0.0, credit=application.requested_amount)
    db.session.add_all([debit, credit])

def create_repayment_journal_entry(payment):
    """Creates a journal entry for a loan repayment."""
    bancos_account = Account.query.filter_by(name='Bancos').first()
    loan_receivable_account = Account.query.filter_by(name='Cuentas por Cobrar Préstamos').first()
    if not bancos_account or not loan_receivable_account:
        raise Exception("Required accounts for repayment not found.")

    transaction = Transaction(description=f"Pago recibido para préstamo #{payment.application_id}")
    db.session.add(transaction)

    debit = JournalEntry(transaction=transaction, account_id=bancos_account.id, debit=payment.amount, credit=0.0)
    credit = JournalEntry(transaction=transaction, account_id=loan_receivable_account.id, debit=0.0, credit=payment.amount)
    db.session.add_all([debit, credit])

def create_payroll_journal_entry(payroll_log_id, totals):
    """Creates a journal entry for a payroll run."""
    account_names = {
        "salaries_expense": "Gastos por Salarios",
        "afp_employer_expense": "Gastos por Prestaciones (AFP Patronal)",
        "isss_employer_expense": "Gastos por Prestaciones (ISSS Patronal)",
        "cash": "Bancos",
        "afp_payable": "Retenciones por Pagar (AFP)",
        "isss_payable": "Retenciones por Pagar (ISSS)",
        "renta_payable": "Retenciones por Pagar (Renta)"
    }
    accounts = Account.query.filter(Account.name.in_(account_names.values())).all()
    accounts_map = {acc.name: acc.id for acc in accounts}

    for name, acc_name in account_names.items():
        if acc_name not in accounts_map:
            raise Exception(f"Account '{acc_name}' not found.")

    transaction = Transaction(description=f"Partida de planilla para el período ID: {payroll_log_id}")
    db.session.add(transaction)

    entries = [
        JournalEntry(transaction=transaction, account_id=accounts_map[account_names["salaries_expense"]], debit=totals['total_gross'], credit=0),
        JournalEntry(transaction=transaction, account_id=accounts_map[account_names["afp_employer_expense"]], debit=totals['total_afp_employer'], credit=0),
        JournalEntry(transaction=transaction, account_id=accounts_map[account_names["isss_employer_expense"]], debit=totals['total_isss_employer'], credit=0),
        JournalEntry(transaction=transaction, account_id=accounts_map[account_names["cash"]], debit=0, credit=totals['total_net']),
        JournalEntry(transaction=transaction, account_id=accounts_map[account_names["afp_payable"]], debit=0, credit=totals['total_afp_employee'] + totals['total_afp_employer']),
        JournalEntry(transaction=transaction, account_id=accounts_map[account_names["isss_payable"]], debit=0, credit=totals['total_isss_employee'] + totals['total_isss_employer']),
        JournalEntry(transaction=transaction, account_id=accounts_map[account_names["renta_payable"]], debit=0, credit=totals['total_renta']),
    ]
    db.session.add_all(entries)