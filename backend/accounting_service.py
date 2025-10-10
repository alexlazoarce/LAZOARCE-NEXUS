from models import db, Account, JournalEntry, Transaction
from sqlalchemy import func

def create_disbursement_journal_entry(application):
    """
    Creates a journal entry for a loan disbursement.
    - Debits 'Cuentas por Cobrar Préstamos'
    - Credits 'Bancos'
    """
    # Find the required accounts
    loan_receivable_account = Account.query.filter_by(name='Cuentas por Cobrar Préstamos').first()
    bancos_account = Account.query.filter_by(name='Bancos').first()

    if not loan_receivable_account or not bancos_account:
        raise Exception("Required accounts for disbursement are not configured in the chart of accounts.")

    # Create the main transaction record
    disbursement_transaction = Transaction(
        description=f"Desembolso de préstamo para solicitud #{application.id}"
    )
    db.session.add(disbursement_transaction)

    # Create the debit and credit entries
    debit_entry = JournalEntry(
        transaction=disbursement_transaction,
        account_id=loan_receivable_account.id,
        debit=application.requested_amount,
        credit=0.0
    )
    credit_entry = JournalEntry(
        transaction=disbursement_transaction,
        account_id=bancos_account.id,
        debit=0.0,
        credit=application.requested_amount
    )

    db.session.add_all([debit_entry, credit_entry])
    # The session will be committed in the route handler to ensure atomicity.

def create_repayment_journal_entry(payment):
    """
    Creates a journal entry for a loan repayment.
    - Debits 'Bancos' (or 'Caja' depending on method)
    - Credits 'Cuentas por Cobrar Préstamos'
    """
    # For now, we assume all payments go to 'Bancos'. This could be extended.
    cash_account = Account.query.filter_by(name='Bancos').first()
    loan_receivable_account = Account.query.filter_by(name='Cuentas por Cobrar Préstamos').first()

    if not cash_account or not loan_receivable_account:
        raise Exception("Required accounts for repayment are not configured in the chart of accounts.")

    # Create the main transaction record
    repayment_transaction = Transaction(
        description=f"Pago recibido para préstamo #{payment.application_id}"
    )
    db.session.add(repayment_transaction)

    # Create the debit and credit entries
    debit_entry = JournalEntry(
        transaction=repayment_transaction,
        account_id=cash_account.id,
        debit=payment.amount,
        credit=0.0
    )
    credit_entry = JournalEntry(
        transaction=repayment_transaction,
        account_id=loan_receivable_account.id,
        debit=0.0,
        credit=payment.amount
    )

    db.session.add_all([debit_entry, credit_entry])
    # The session will be committed in the route handler.

def create_payroll_journal_entry(payroll_log_id, totals):
    """
    Creates a comprehensive journal entry for a completed payroll run.
    - Debits salary and contribution expenses.
    - Credits cash and various withholding accounts.
    """
    # Define account names to look up
    account_names = {
        "salaries_expense": "Gastos por Salarios",
        "afp_employer_expense": "Gastos por Prestaciones (AFP Patronal)",
        "isss_employer_expense": "Gastos por Prestaciones (ISSS Patronal)",
        "cash": "Bancos", # Assuming payroll is paid from the bank
        "afp_payable": "Retenciones por Pagar (AFP)",
        "isss_payable": "Retenciones por Pagar (ISSS)",
        "renta_payable": "Retenciones por Pagar (Renta)"
    }

    # Fetch all necessary accounts in a single query
    accounts = Account.query.filter(Account.name.in_(account_names.values())).all()
    accounts_map = {acc.name: acc.id for acc in accounts}

    # Verify all accounts were found
    for name, acc_name in account_names.items():
        if acc_name not in accounts_map:
            raise Exception(f"La cuenta contable '{acc_name}' es necesaria para la planilla y no se encontró.")

    # Create the main transaction record
    payroll_transaction = Transaction(
        description=f"Partida de planilla para el período ID: {payroll_log_id}"
    )
    db.session.add(payroll_transaction)

    # Prepare all journal entries
    entries_to_add = [
        # Debits (Expenses)
        JournalEntry(transaction=payroll_transaction, account_id=accounts_map[account_names["salaries_expense"]], debit=totals['total_gross'], credit=0),
        JournalEntry(transaction=payroll_transaction, account_id=accounts_map[account_names["afp_employer_expense"]], debit=totals['total_afp_employer'], credit=0),
        JournalEntry(transaction=payroll_transaction, account_id=accounts_map[account_names["isss_employer_expense"]], debit=totals['total_isss_employer'], credit=0),

        # Credits (Liabilities and Cash Out)
        JournalEntry(transaction=payroll_transaction, account_id=accounts_map[account_names["cash"]], debit=0, credit=totals['total_net']),
        JournalEntry(transaction=payroll_transaction, account_id=accounts_map[account_names["afp_payable"]], debit=0, credit=totals['total_afp_employee'] + totals['total_afp_employer']),
        JournalEntry(transaction=payroll_transaction, account_id=accounts_map[account_names["isss_payable"]], debit=0, credit=totals['total_isss_employee'] + totals['total_isss_employer']),
        JournalEntry(transaction=payroll_transaction, account_id=accounts_map[account_names["renta_payable"]], debit=0, credit=totals['total_renta']),
    ]

    db.session.add_all(entries_to_add)
    # The session is committed in the route handler.

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