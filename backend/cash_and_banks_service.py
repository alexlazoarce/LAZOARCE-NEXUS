from .models import db, BankAccount, BankTransaction, CashBox, CashTransaction
from sqlalchemy.exc import SQLAlchemyError
from flask_jwt_extended import get_jwt_identity

def get_tenant_id():
    """Extrae el tenant_id de la identidad del JWT."""
    current_user = get_jwt_identity()
    return current_user.get('tenant_id')

# Bank Account Services
def create_bank_account_service(data):
    tenant_id = get_tenant_id()
    try:
        new_account = BankAccount(
            tenant_id=tenant_id,
            account_name=data['account_name'],
            account_number=data['account_number'],
            bank_name=data['bank_name'],
            initial_balance=data.get('initial_balance', 0.0)
        )
        db.session.add(new_account)
        db.session.commit()
        return {'message': 'Bank account created successfully', 'account_id': new_account.id}, 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return {'error': str(e)}, 500

def get_bank_accounts_service():
    tenant_id = get_tenant_id()
    try:
        accounts = BankAccount.query.filter_by(tenant_id=tenant_id).all()
        return [acc.to_dict() for acc in accounts], 200
    except SQLAlchemyError as e:
        return {'error': str(e)}, 500

# Bank Transaction Services
def create_bank_transaction_service(data):
    tenant_id = get_tenant_id()
    try:
        new_transaction = BankTransaction(
            tenant_id=tenant_id,
            bank_account_id=data['bank_account_id'],
            transaction_type=data['transaction_type'],
            amount=data['amount'],
            description=data.get('description', '')
        )
        db.session.add(new_transaction)
        db.session.commit()
        return {'message': 'Bank transaction created successfully', 'transaction_id': new_transaction.id}, 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return {'error': str(e)}, 500

def get_bank_transactions_service(account_id):
    tenant_id = get_tenant_id()
    try:
        transactions = BankTransaction.query.filter_by(tenant_id=tenant_id, bank_account_id=account_id).all()
        return [trans.to_dict() for trans in transactions], 200
    except SQLAlchemyError as e:
        return {'error': str(e)}, 500

# Cash Box Services
def create_cash_box_service(data):
    tenant_id = get_tenant_id()
    try:
        new_cash_box = CashBox(
            tenant_id=tenant_id,
            box_name=data['box_name'],
            initial_balance=data.get('initial_balance', 0.0)
        )
        db.session.add(new_cash_box)
        db.session.commit()
        return {'message': 'Cash box created successfully', 'cash_box_id': new_cash_box.id}, 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return {'error': str(e)}, 500

def get_cash_boxes_service():
    tenant_id = get_tenant_id()
    try:
        cash_boxes = CashBox.query.filter_by(tenant_id=tenant_id).all()
        return [cb.to_dict() for cb in cash_boxes], 200
    except SQLAlchemyError as e:
        return {'error': str(e)}, 500

# Cash Transaction Services
def create_cash_transaction_service(data):
    tenant_id = get_tenant_id()
    try:
        new_transaction = CashTransaction(
            tenant_id=tenant_id,
            cash_box_id=data['cash_box_id'],
            transaction_type=data['transaction_type'],
            amount=data['amount'],
            description=data.get('description', '')
        )
        db.session.add(new_transaction)
        db.session.commit()
        return {'message': 'Cash transaction created successfully', 'transaction_id': new_transaction.id}, 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return {'error': str(e)}, 500

def get_cash_transactions_for_box_service(cash_box_id):
    tenant_id = get_tenant_id()
    try:
        transactions = CashTransaction.query.filter_by(tenant_id=tenant_id, cash_box_id=cash_box_id).all()
        return [trans.to_dict() for trans in transactions], 200
    except SQLAlchemyError as e:
        return {'error': str(e)}, 500
