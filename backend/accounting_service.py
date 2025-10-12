from models import db, Account, JournalEntry, Transaction
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