from .app import db, Account, Transaction, JournalEntry
from datetime import datetime

def create_journal_entry(description, entries, date=None):
    """
    Crea una transacción y sus asientos de diario correspondientes.

    Args:
        description (str): La descripción de la transacción.
        entries (list): Una lista de diccionarios, donde cada diccionario
                        representa un asiento con 'account_code', 'debit', 'credit'.
        date (datetime, optional): La fecha de la transacción. Si es None, se usa la fecha actual.

    Returns:
        Transaction: La transacción creada.

    Raises:
        ValueError: Si los débitos y créditos no cuadran o si una cuenta no existe.
    """
    total_debits = sum(entry.get('debit', 0) for entry in entries)
    total_credits = sum(entry.get('credit', 0) for entry in entries)

    if round(total_debits, 2) != round(total_credits, 2):
        raise ValueError("El total de debitos y creditos no cuadra.")

    if not date:
        date = datetime.utcnow()

    # Iniciar una transacción de base de datos
    try:
        new_transaction = Transaction(description=description, date=date)
        db.session.add(new_transaction)

        # Crear los asientos de diario
        for entry_data in entries:
            account_code = entry_data.get('account_code')
            account = Account.query.filter_by(code=account_code).first()

            if not account:
                raise ValueError(f"La cuenta con el codigo '{account_code}' no existe.")

            journal_entry = JournalEntry(
                transaction=new_transaction,
                account_id=account.id,
                debit=entry_data.get('debit', 0),
                credit=entry_data.get('credit', 0)
            )
            db.session.add(journal_entry)

        db.session.commit()
        return new_transaction

    except Exception as e:
        db.session.rollback()
        raise e