"""
NEXUS-CB: Conciliación Bancaria Service
"""
from .models import db, Account, BankStatement, BankTransaction, Transaction
from datetime import date
import csv
import io

def parse_bank_statement_csv(account_id, csv_content, start_date, end_date, initial_balance, final_balance):
    """
    Parses a CSV file content representing a bank statement and creates the
    corresponding records in the database.

    Expected CSV format: Date,Description,Amount,Type
    Example: "2023-10-01","Deposit",1000.00,"credit"
    """
    account = Account.query.get_or_404(account_id)

    new_statement = BankStatement(
        account_id=account.id,
        start_date=date.fromisoformat(start_date),
        end_date=date.fromisoformat(end_date),
        initial_balance=float(initial_balance),
        final_balance=float(final_balance)
    )
    db.session.add(new_statement)

    # Use io.StringIO to treat the string content as a file
    csv_file = io.StringIO(csv_content)
    reader = csv.DictReader(csv_file)

    transactions = []
    for row in reader:
        transaction = BankTransaction(
            statement=new_statement,
            transaction_date=date.fromisoformat(row['Date']),
            description=row['Description'],
            amount=abs(float(row['Amount'])),
            transaction_type=row['Type'].lower() # 'debit' or 'credit'
        )
        transactions.append(transaction)

    db.session.add_all(transactions)

    return new_statement

def auto_reconcile_account(account_id, start_date, end_date):
    """
    Attempts to automatically reconcile bank transactions with internal transactions
    for a given account and period.

    This is a simplified matching logic. A real implementation would be more complex.
    """
    account = Account.query.get_or_404(account_id)
    start_date = date.fromisoformat(start_date)
    end_date = date.fromisoformat(end_date)

    # Find unreconciled bank transactions in the period
    unreconciled_bank_txs = BankTransaction.query.join(BankStatement).\
        filter(
            BankStatement.account_id == account.id,
            BankTransaction.transaction_date.between(start_date, end_date),
            BankTransaction.is_reconciled == False
        ).all()

    # Find internal transactions for the same account and period
    internal_txs = Transaction.query.filter(
            Transaction.account_id == account.id,
            db.func.date(Transaction.journal_entry.has(date.between(start_date, end_date)))
        ).all()

    matched_pairs = []

    # Simple matching logic: find pairs with the same date and amount
    for bank_tx in unreconciled_bank_txs:
        for internal_tx in internal_txs:
            if bank_tx.transaction_date == internal_tx.journal_entry.date.date() and \
               bank_tx.amount == internal_tx.amount:

                # Check if the type is compatible (e.g., bank credit = internal debit to bank)
                if (bank_tx.transaction_type == 'credit' and internal_tx.type == 'Debit') or \
                   (bank_tx.transaction_type == 'debit' and internal_tx.type == 'Credit'):

                    bank_tx.is_reconciled = True
                    bank_tx.internal_transaction_id = internal_tx.id
                    matched_pairs.append((bank_tx, internal_tx))
                    # Remove the internal transaction to avoid matching it again
                    internal_txs.remove(internal_tx)
                    break # Move to the next bank transaction

    # In a real app, you would create a Reconciliation object here to store the results.

    return {
        "matched_count": len(matched_pairs),
        "unmatched_bank_transactions": [bt.id for bt in unreconciled_bank_txs if not bt.is_reconciled]
    }
