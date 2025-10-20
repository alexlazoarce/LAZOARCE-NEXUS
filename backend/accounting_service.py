from backend.models import db, Account, JournalEntry, Transaction, TaxType
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

def get_journal_entries_service():
    """Service to retrieve all journal entries, ordered by date."""
    return JournalEntry.query.order_by(JournalEntry.date.desc()).all()

def get_general_ledger_service():
    """Service to generate the general ledger."""
    accounts = Account.query.all()
    ledger = []
    for account in accounts:
        balance = Decimal('0.00')
        for transaction in account.transactions:
            amount = Decimal(str(transaction.amount))
            if transaction.type == account.normal_balance:
                balance += amount
            else:
                balance -= amount
        ledger.append({
            'account_id': account.id,
            'account_name': account.name,
            'account_category': account.category,
            'balance': float(balance.quantize(Decimal('0.01')))
        })
    return ledger

def get_trial_balance_service():
    """Service to generate the trial balance."""
    accounts = Account.query.all()
    report = []
    total_debits = Decimal('0.00')
    total_credits = Decimal('0.00')

    for account in accounts:
        debits = sum(Decimal(str(t.amount)) for t in account.transactions if t.type == 'Debit')
        credits = sum(Decimal(str(t.amount)) for t in account.transactions if t.type == 'Credit')
        if debits > 0 or credits > 0:
            report.append({
                'account_name': account.name,
                'debits': float(debits.quantize(Decimal('0.01'))),
                'credits': float(credits.quantize(Decimal('0.01')))
            })
            total_debits += debits
            total_credits += credits

    return {
        'report': report,
        'total_debits': float(total_debits.quantize(Decimal('0.01'))),
        'total_credits': float(total_credits.quantize(Decimal('0.01'))),
        'is_balanced': total_debits.quantize(Decimal('0.01')) == total_credits.quantize(Decimal('0.01'))
    }

def get_balance_sheet_service():
    """Service to generate the balance sheet."""
    report = {'assets': [], 'liabilities': [], 'equity': []}
    totals = {'assets': Decimal('0.00'), 'liabilities': Decimal('0.00'), 'equity': Decimal('0.00')}
    accounts = Account.query.filter(Account.category.in_(['Asset', 'Liability', 'Equity'])).all()

    for account in accounts:
        balance = Decimal('0.00')
        for transaction in account.transactions:
            if transaction.type == account.normal_balance:
                balance += Decimal(str(transaction.amount))
            else:
                balance -= Decimal(str(transaction.amount))

        category_key = account.category.lower()
        report[category_key].append({'account_name': account.name, 'balance': float(balance.quantize(Decimal('0.01')))})
        totals[category_key] += balance

    liabilities_plus_equity = totals['liabilities'] + totals['equity']
    return {
        'report': report,
        'totals': {
            'assets': float(totals['assets'].quantize(Decimal('0.01'))),
            'liabilities': float(totals['liabilities'].quantize(Decimal('0.01'))),
            'equity': float(totals['equity'].quantize(Decimal('0.01'))),
            'liabilities_plus_equity': float(liabilities_plus_equity.quantize(Decimal('0.01')))
        },
        'accounting_equation_balanced': totals['assets'].quantize(Decimal('0.01')) == liabilities_plus_equity.quantize(Decimal('0.01'))
    }

def get_income_statement_service():
    """Service to generate the income statement."""
    report = {'revenues': [], 'expenses': []}
    totals = {'revenues': Decimal('0.00'), 'expenses': Decimal('0.00')}
    accounts = Account.query.filter(Account.category.in_(['Revenue', 'Expense'])).all()

    for account in accounts:
        balance = Decimal('0.00')
        for trx in account.transactions:
            if trx.type == account.normal_balance:
                balance += Decimal(str(trx.amount))
            else:
                balance -= Decimal(str(trx.amount))

        category_key = account.category.lower() + 's'
        report[category_key].append({'account_name': account.name, 'balance': float(balance.quantize(Decimal('0.01')))})
        totals[category_key] += balance

    net_income = totals['revenues'] - totals['expenses']
    return {
        'report': report,
        'totals': {
            'revenues': float(totals['revenues'].quantize(Decimal('0.01'))),
            'expenses': float(totals['expenses'].quantize(Decimal('0.01'))),
        },
        'net_income': float(net_income.quantize(Decimal('0.01')))
    }

def get_tax_rate(tax_name, country_code):
    """Retrieves a tax rate for a given tax name and country."""
    tax = TaxType.query.filter_by(name=tax_name, country_code=country_code).first()
    if not tax:
        raise ValueError(f"Impuesto '{tax_name}' no encontrado para el país '{country_code}'.")
    return Decimal(str(tax.rate))

def calculate_taxes_for_invoice(invoice, country_code='SV'):
    """
    Calculates taxes for a given invoice.
    For now, it only calculates IVA.
    """
    iva_rate = get_tax_rate('IVA', country_code)
    subtotal = Decimal(str(invoice.total_amount))

    # Assuming the total_amount includes IVA. We need to calculate the base and the tax amount.
    base_amount = subtotal / (1 + iva_rate)
    iva_amount = subtotal - base_amount

    return {
        'subtotal': float(base_amount.quantize(Decimal('0.01'))),
        'iva_amount': float(iva_amount.quantize(Decimal('0.01'))),
        'total_amount': float(subtotal.quantize(Decimal('0.01')))
    }