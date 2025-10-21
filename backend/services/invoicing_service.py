"""
Servicio para la lógica de negocio del Módulo de Facturación (LAN-FE2).
"""
from datetime import datetime
from backend.models import db, Invoice, InvoiceItem
from backend import accounting_service

def create_invoice_service(data):
    """
    Crea una nueva factura y su asiento contable correspondiente.
    """
    try:
        # Aquí iría la lógica para conectarse al sistema de facturación electrónica
        # del país correspondiente (FEL, FACE, CFDI, etc.)
        # Por ahora, simularemos la creación y guardado en la base de datos.

        new_invoice = Invoice(
            customer_name=data['customer_name'],
            customer_nit=data['customer_nit'],
            total_amount=sum(item['price'] * item['quantity'] for item in data['items']),
            status='issued'
        )
        db.session.add(new_invoice)

        for item_data in data['items']:
            item = InvoiceItem(
                invoice=new_invoice,
                description=item_data['description'],
                quantity=item_data['quantity'],
                price=item_data['price']
            )
            db.session.add(item)

        # --- Integración Contable ---
        # Crear el asiento contable para la venta.
        # Asumimos que la venta es a crédito.
        transactions_data = [
            {
                'account_name': 'Cuentas por Cobrar Clientes',
                'type': 'Debit',
                'amount': new_invoice.total_amount
            },
            {
                'account_name': 'Ingresos por Servicios', # Asumimos una cuenta de ingresos genérica
                'type': 'Credit',
                'amount': new_invoice.total_amount
            }
        ]
        description = f"Venta según factura No. {new_invoice.id} a {new_invoice.customer_name}"
        journal_entry = accounting_service.create_journal_entry(
            date=datetime.utcnow(),
            description=description,
            transactions_data=transactions_data
        )
        new_invoice.journal_entry_id = journal_entry.id

        db.session.commit()
        return new_invoice, None
    except Exception as e:
        db.session.rollback()
        return None, str(e)
