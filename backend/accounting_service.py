from .models import db, Account, JournalEntry, Transaction
from decimal import Decimal, ROUND_HALF_UP

def create_journal_entry(date, description, transactions_data):
    """
    Creates a new journal entry with the given transactions.
    Ensures that the entry is balanced before committing.

    :param date: The date of the journal entry.
    :param description: A description of the entry.
    :param transactions_data: A list of dicts, where each dict is:
                              {'account_name': str, 'type': 'Debit'/'Credit', 'amount': float}
    :return: The newly created JournalEntry object.
    :raises ValueError: If the journal entry is not balanced.
    """
    total_debits = Decimal('0.00')
    total_credits = Decimal('0.00')

    for t_data in transactions_data:
        amount = Decimal(str(t_data['amount'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        if t_data['type'] == 'Debit':
            total_debits += amount
        elif t_data['type'] == 'Credit':
            total_credits += amount

    if total_debits != total_credits:
        raise ValueError(f"El asiento contable no está balanceado. Débitos: {total_debits}, Créditos: {total_credits}")

    # If balanced, create the entry and transactions
    new_entry = JournalEntry(date=date, description=description)
    db.session.add(new_entry)

    for t_data in transactions_data:
        account = Account.query.filter_by(name=t_data['account_name']).first()
        if not account:
            raise ValueError(f"La cuenta '{t_data['account_name']}' no fue encontrada.")

        transaction = Transaction(
            journal_entry=new_entry,
            account_id=account.id,
            type=t_data['type'],
            amount=float(t_data['amount'])
        )
        db.session.add(transaction)

    # The session commit will happen in the route after calling this service
    return new_entry

def create_disbursement_journal_entry(application, disbursement_source_account_name):
    """
    Creates a specific journal entry for a loan disbursement.
    """
    description = f"Desembolso de préstamo ID {application.id} para {application.applicant.full_name}"

    # The name of the loan portfolio account might be standardized or based on the product
    loan_portfolio_account_name = "Préstamos por Cobrar"

    transactions = [
        {
            "account_name": loan_portfolio_account_name,
            "type": "Debit",
            "amount": application.amount_requested
        },
        {
            "account_name": disbursement_source_account_name,
            "type": "Credit",
            "amount": application.amount_requested
        }
    ]

    return create_journal_entry(application.disbursement_date, description, transactions)

def create_payroll_journal_entry(run_date, total_gross_salary, total_isss, total_afp, total_renta, total_net_salary):
    """
    Creates a consolidated journal entry for a payroll run.
    """
    description = f"Asiento de nómina para el período que termina en {run_date.strftime('%Y-%m-%d')}"

    transactions = [
        # Debit the salary expense
        {
            "account_name": "Gastos de Salarios",
            "type": "Debit",
            "amount": total_gross_salary
        },
        # Credit the corresponding liability and cash accounts
        {
            "account_name": "Retenciones ISSS por Pagar",
            "type": "Credit",
            "amount": total_isss
        },
        {
            "account_name": "Retenciones AFP por Pagar",
            "type": "Credit",
            "amount": total_afp
        },
        {
            "account_name": "Retenciones de Renta por Pagar",
            "type": "Credit",
            "amount": total_renta
        },
        {
            "account_name": "Bancos", # Assuming payroll is paid from the bank
            "type": "Credit",
            "amount": total_net_salary
        }
    ]

    return create_journal_entry(run_date, description, transactions)

def get_account_balance(account_id, tenant_id):
    """Calculates the balance of a single account."""
    account = Account.query.filter_by(id=account_id, tenant_id=tenant_id).first()
    if not account:
        return Decimal('0.00')

    total_debits = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.account_id == account_id,
        Transaction.type == 'Debit'
    ).scalar() or Decimal('0.00')

    total_credits = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.account_id == account_id,
        Transaction.type == 'Credit'
    ).scalar() or Decimal('0.00')

    total_debits = Decimal(str(total_debits))
    total_credits = Decimal(str(total_credits))

    if account.normal_balance == 'Debit':
        return total_debits - total_credits
    else: # normal_balance == 'Credit'
        return total_credits - total_debits

def get_balance_sheet(tenant_id):
    """Generates the data for a Balance Sheet report."""
    assets = Account.query.filter_by(tenant_id=tenant_id, category='Activo').all()
    liabilities = Account.query.filter_by(tenant_id=tenant_id, category='Pasivo').all()
    equity = Account.query.filter_by(tenant_id=tenant_id, category='Patrimonio').all()

    report = {
        'assets': [{'name': acc.name, 'balance': float(get_account_balance(acc.id, tenant_id))} for acc in assets],
        'liabilities': [{'name': acc.name, 'balance': float(get_account_balance(acc.id, tenant_id))} for acc in liabilities],
        'equity': [{'name': acc.name, 'balance': float(get_account_balance(acc.id, tenant_id))} for acc in equity]
    }

    report['total_assets'] = sum(a['balance'] for a in report['assets'])
    report['total_liabilities'] = sum(l['balance'] for l in report['liabilities'])
    report['total_equity'] = sum(e['balance'] for e in report['equity'])
    report['total_liabilities_and_equity'] = report['total_liabilities'] + report['total_equity']

    return report

def get_income_statement(tenant_id):
    """Generates the data for an Income Statement report."""
    income = Account.query.filter_by(tenant_id=tenant_id, category='Ingresos').all()
    expenses = Account.query.filter_by(tenant_id=tenant_id, category='Gastos').all()

    report = {
        'income': [{'name': acc.name, 'balance': float(get_account_balance(acc.id, tenant_id))} for acc in income],
        'expenses': [{'name': acc.name, 'balance': float(get_account_balance(acc.id, tenant_id))} for acc in expenses]
    }

    report['total_income'] = sum(i['balance'] for i in report['income'])
    report['total_expenses'] = sum(e['balance'] for e in report['expenses'])
    report['net_income'] = report['total_income'] - report['total_expenses']

    return report