from backend.models import db, Account, JournalEntry, Transaction, TaxType
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
import os # Se incluye os por si es necesario para alguna configuración futura

def create_journal_entry(date, description, transactions_data, reference=None, created_by_id=None):
    """
    Creates a new journal entry with the given transactions.
    Ensures that the entry is balanced before committing.

    :param date: The date of the journal entry (datetime.date or datetime.datetime).
    :param description: A description of the entry.
    :param transactions_data: A list of dicts, where each dict is:
                              {'account_name': str, 'type': 'Debit'/'Credit', 'amount': float}
    :param reference: Optional reference string (e.g., invoice number).
    :param created_by_id: Optional User ID who created the entry.
    :return: The newly created JournalEntry object.
    :raises ValueError: If the journal entry is not balanced or an account is not found.
    """
    total_debits = Decimal('0.00')
    total_credits = Decimal('0.00')

    # Validación inicial de balance y recolección de cuentas
    for t_data in transactions_data:
        try:
            # Uso de Decimal para precisión
            amount = Decimal(str(t_data['amount'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        except Exception:
            raise ValueError("El campo 'amount' debe ser un número válido.")
            
        if t_data['type'] == 'Debit':
            total_debits += amount
        elif t_data['type'] == 'Credit':
            total_credits += amount
        else:
            raise ValueError(f"Tipo de transacción inválido: {t_data.get('type')}. Debe ser 'Debit' o 'Credit'.")

    if total_debits != total_credits:
        raise ValueError(f"El asiento contable no está balanceado. Débitos: {total_debits}, Créditos: {total_credits}")

    # Si está balanceado, crear el asiento y las transacciones
    new_entry = JournalEntry(date=date, description=description, reference=reference, created_by_id=created_by_id)
    db.session.add(new_entry)

    for t_data in transactions_data:
        # Se asume que el Account tiene un campo 'name' o 'account_code'
        # Usaremos 'name' como en la versión fusionada, pero se puede mejorar con 'account_code'
        account = Account.query.filter_by(name=t_data['account_name']).first() 
        
        if not account:
            raise ValueError(f"La cuenta '{t_data['account_name']}' no fue encontrada.")

        # Usamos el valor float/decimal original
        transaction = Transaction(
            journal_entry=new_entry,
            account_id=account.id,
            type=t_data['type'],
            amount=float(t_data['amount']) # Se convierte a float para el modelo, pero se maneja la precisión con Decimal
        )
        db.session.add(transaction)

    # El commit de la sesión se hace en el controlador (route) después de llamar a este servicio.
    return new_entry

# --- REPORTES CONTABLES ---
---

def get_journal_entries_service():
    """Service to retrieve all journal entries, ordered by date."""
    return JournalEntry.query.order_by(JournalEntry.date.desc()).all()

def get_general_ledger_service():
    """Service to generate the general ledger (Mayor General)."""
    accounts = Account.query.all()
    ledger = []
    
    for account in accounts:
        balance = Decimal('0.00')
        transactions_detail = []
        
        # Filtra solo las transacciones posteables (si JournalEntry tiene is_posted=True)
        # Se asume que solo las transacciones que tienen un JournalEntry existen.
        for transaction in account.transactions.join(JournalEntry).filter(JournalEntry.is_posted == True):
            amount = Decimal(str(transaction.amount))
            
            if transaction.type == account.normal_balance:
                balance += amount
            else:
                balance -= amount
            
            transactions_detail.append({
                'entry_date': transaction.journal_entry.date,
                'description': transaction.journal_entry.description,
                'type': transaction.type,
                'amount': float(amount.quantize(Decimal('0.01'))),
                'balance_after': float(balance.quantize(Decimal('0.01')))
            })

        ledger.append({
            'account_id': account.id,
            'account_name': account.name,
            'account_category': account.category,
            'normal_balance': account.normal_balance,
            'final_balance': float(balance.quantize(Decimal('0.01'))),
            'transactions': transactions_detail
        })
    return ledger

def get_trial_balance_service():
    """Service to generate the trial balance (Balance de Comprobación)."""
    accounts = Account.query.all()
    report = []
    total_debits = Decimal('0.00')
    total_credits = Decimal('0.00')

    for account in accounts:
        # Se asume que solo contamos transacciones posteadas
        transactions = account.transactions.join(JournalEntry).filter(JournalEntry.is_posted == True).all()
        
        debits = sum(Decimal(str(t.amount)) for t in transactions if t.type == 'Debit')
        credits = sum(Decimal(str(t.amount)) for t in transactions if t.type == 'Credit')
        
        if debits > 0 or credits > 0:
            report.append({
                'account_name': account.name,
                'account_code': getattr(account, 'account_code', 'N/A'), # Asumiendo que el modelo Account tiene account_code
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
    """Service to generate the balance sheet (Balance General)."""
    # Se reusa la lógica de get_general_ledger_service para obtener los saldos
    general_ledger = get_general_ledger_service()
    
    report = {'assets': [], 'liabilities': [], 'equity': []}
    totals = {'assets': Decimal('0.00'), 'liabilities': Decimal('0.00'), 'equity': Decimal('0.00')}

    # Asumimos que los reportes se basan en la categoría del Account
    category_map = {'Asset': 'assets', 'Liability': 'liabilities', 'Equity': 'equity'}

    for account_data in general_ledger:
        category = account_data['account_category']
        if category in category_map:
            key = category_map[category]
            balance = Decimal(str(account_data['final_balance']))

            report[key].append({
                'account_name': account_data['account_name'],
                'balance': float(balance.quantize(Decimal('0.01')))
            })
            totals[key] += balance

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
    """Service to generate the income statement (Estado de Resultados)."""
    general_ledger = get_general_ledger_service()

    report = {'revenues': [], 'expenses': []}
    totals = {'revenues': Decimal('0.00'), 'expenses': Decimal('0.00')}

    category_map = {'Revenue': 'revenues', 'Expense': 'expenses'}

    for account_data in general_ledger:
        category = account_data['account_category']
        if category in category_map:
            key = category_map[category]
            balance = Decimal(str(account_data['final_balance']))

            report[key].append({
                'account_name': account_data['account_name'],
                'balance': float(balance.quantize(Decimal('0.01')))
            })
            totals[key] += balance

    net_income = totals['revenues'] - totals['expenses']

    return {
        'report': report,
        'totals': {
            'revenues': float(totals['revenues'].quantize(Decimal('0.01'))),
            'expenses': float(totals['expenses'].quantize(Decimal('0.01'))),
        },
        'net_income': float(net_income.quantize(Decimal('0.01')))
    }

# --- SERVICIOS DE IMPUESTOS ---
---

def get_tax_rate(tax_name, country_code):
    """Retrieves a tax rate for a given tax name and country."""
    TaxType = db.Model.metadata.tables.get('tax_type')
    if not TaxType:
        # Fallback si TaxType no está cargado.
        if tax_name == 'IVA' and country_code == 'SV':
            return Decimal('0.13')
        raise ValueError(f"Modelo TaxType no cargado y no hay tasa de impuesto por defecto para '{tax_name}'.")

    tax = TaxType.query.filter_by(name=tax_name, country_code=country_code).first()
    if not tax:
        raise ValueError(f"Impuesto '{tax_name}' no encontrado para el país '{country_code}'.")
    return Decimal(str(tax.rate))

def calculate_taxes_for_invoice(invoice, country_code='SV'):
    """
    Calculates taxes for a given invoice.
    
    :param invoice: An object with a 'total_amount' attribute (float or Decimal).
    :param country_code: Country code (e.g., 'SV').
    :return: Dict with subtotal, iva_amount, and total_amount.
    """
    iva_rate = get_tax_rate('IVA', country_code)
    
    # Aseguramos que el total_amount sea Decimal
    try:
        subtotal = Decimal(str(invoice.total_amount))
    except AttributeError:
        raise ValueError("El objeto 'invoice' debe tener un atributo 'total_amount'.")
    
    # Asume que el total_amount *incluye* IVA y que la fórmula es (Base * (1 + Tasa))
    base_amount = subtotal / (Decimal('1.00') + iva_rate)
    iva_amount = subtotal - base_amount

    return {
        'subtotal': float(base_amount.quantize(Decimal('0.01'))),
        'iva_amount': float(iva_amount.quantize(Decimal('0.01'))),
        'total_amount': float(subtotal.quantize(Decimal('0.01')))
    }