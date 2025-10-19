import csv
from datetime import datetime
from .models import db, BankAccountStatement, BankTransaction, Account, JournalEntry, Transaction

def process_bank_statement_csv(file_path, tenant_id, account_id, start_date, end_date, start_balance, end_balance):
    """
    Processes a CSV file containing bank transactions and creates the corresponding records in the database.
    """
    try:
        # Create the main statement record
        statement = BankAccountStatement(
            tenant_id=tenant_id,
            account_id=account_id,
            start_date=datetime.strptime(start_date, '%Y-%m-%d').date(),
            end_date=datetime.strptime(end_date, '%Y-%m-%d').date(),
            start_balance=float(start_balance),
            end_balance=float(end_balance),
            status='Processing'
        )
        db.session.add(statement)
        db.session.flush()  # Flush to get the statement ID for the transactions

        transactions_to_add = []
        with open(file_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Basic validation to ensure required columns are present
                if not all(k in row for k in ['Fecha', 'Descripcion', 'Debito', 'Credito']):
                    raise ValueError("El archivo CSV debe contener las columnas: Fecha, Descripcion, Debito, Credito")

                amount = float(row.get('Credito', 0)) - float(row.get('Debito', 0))
                transaction_type = 'Credit' if amount > 0 else 'Debit'

                transaction = BankTransaction(
                    tenant_id=tenant_id,
                    statement_id=statement.id,
                    transaction_date=datetime.strptime(row['Fecha'], '%Y-%m-%d').date(),
                    description=row['Descripcion'],
                    amount=abs(amount),
                    type=transaction_type,
                    status='Unreconciled'
                )
                transactions_to_add.append(transaction)

        db.session.bulk_save_objects(transactions_to_add)

        statement.status = 'Completed'
        db.session.commit()

        return {"message": "Extracto bancario procesado exitosamente.", "statement_id": statement.id}, 201

    except Exception as e:
        db.session.rollback()
        return {"error": f"Error al procesar el archivo: {str(e)}"}, 500

def reconcile_statement(statement_id, tenant_id):
    """
    Attempts to automatically reconcile the transactions of a given bank statement.
    """
    statement = BankAccountStatement.query.filter_by(id=statement_id, tenant_id=tenant_id).first_or_404()

    # Simple reconciliation logic: Find journal entry transactions with the same amount and a close date.
    for bank_trans in statement.transactions.filter_by(status='Unreconciled'):
        # Look for a matching transaction in the accounting system
        matching_transaction = db.session.query(Transaction).join(JournalEntry).filter(
            Transaction.tenant_id == tenant_id,
            Transaction.amount == bank_trans.amount,
            db.func.date(JournalEntry.date) == bank_trans.transaction_date
        ).first()

        if matching_transaction:
            bank_trans.status = 'Reconciled'
            bank_trans.journal_entry_id = matching_transaction.journal_entry_id

    db.session.commit()
    return {"message": "Proceso de conciliación completado.", "statement_id": statement.id}

def get_statement_details(statement_id, tenant_id):
    """
    Retrieves a bank statement and all its transactions.
    """
    statement = BankAccountStatement.query.filter_by(id=statement_id, tenant_id=tenant_id).first_or_404()
    transactions = [
        {
            "id": trans.id,
            "date": trans.transaction_date.isoformat(),
            "description": trans.description,
            "amount": trans.amount,
            "type": trans.type,
            "status": trans.status,
            "journal_entry_id": trans.journal_entry_id
        } for trans in statement.transactions
    ]

    return {
        "id": statement.id,
        "start_date": statement.start_date.isoformat(),
        "end_date": statement.end_date.isoformat(),
        "start_balance": statement.start_balance,
        "end_balance": statement.end_balance,
        "status": statement.status,
        "transactions": transactions
    }
