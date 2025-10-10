from models import db, Account, JournalEntry
from sqlalchemy import func

def get_general_ledger():
    """
    Calculates the general ledger (Libro Mayor) for all accounts.

    For each account in the chart of accounts, this function calculates the
    sum of all debit and credit entries and determines the final balance
    based on the account's type.

    Returns:
        A list of dictionaries, where each dictionary represents an account
        with its total debits, credits, and final balance.
    """
    # Get all accounts from the chart of accounts
    accounts = Account.query.order_by(Account.code).all()

    ledger = []

    for account in accounts:
        # For each account, calculate the sum of debits and credits from journal entries
        total_debits = db.session.query(func.sum(JournalEntry.debit)).filter(JournalEntry.account_id == account.id).scalar() or 0.0
        total_credits = db.session.query(func.sum(JournalEntry.credit)).filter(JournalEntry.account_id == account.id).scalar() or 0.0

        # Determine the final balance based on the account type's normal balance
        balance = 0.0
        if account.account_type in ['Activo', 'Gasto']:
            balance = total_debits - total_credits
        elif account.account_type in ['Pasivo', 'Patrimonio', 'Ingreso']:
            balance = total_credits - total_debits

        ledger.append({
            'account_code': account.code,
            'account_name': account.name,
            'account_type': account.account_type,
            'total_debits': total_debits,
            'total_credits': total_credits,
            'final_balance': balance
        })

    return ledger