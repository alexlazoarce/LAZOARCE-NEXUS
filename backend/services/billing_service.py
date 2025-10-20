"""
Servicio para la lógica de negocio del Módulo de Facturación Recurrente (LAN-BIL9).
"""
from datetime import date
from dateutil.relativedelta import relativedelta
from backend.models import db, Subscription, SubscriptionPlan, User
from backend import invoicing_service

def create_subscription_service(data):
    """Crea una nueva suscripción para un usuario."""
    try:
        user = User.query.get(data['user_id'])
        plan = SubscriptionPlan.query.get(data['plan_id'])
        if not user or not plan:
            return None, "Usuario o plan no encontrado."

        # Calculate next billing date
        today = date.today()
        if plan.billing_interval == 'monthly':
            next_billing = today + relativedelta(months=1)
        elif plan.billing_interval == 'annually':
            next_billing = today + relativedelta(years=1)
        else:
            return None, "Intervalo de facturación no válido."

        new_subscription = Subscription(
            user_id=user.id,
            plan_id=plan.id,
            next_billing_date=next_billing
        )
        db.session.add(new_subscription)
        db.session.commit()
        return new_subscription, None
    except Exception as e:
        db.session.rollback()
        return None, str(e)

def cancel_subscription_service(subscription_id):
    """Cancela una suscripción activa."""
    subscription = Subscription.query.get(subscription_id)
    if not subscription:
        return None, "Suscripción no encontrada."

    subscription.status = 'cancelled'
    db.session.commit()
    return subscription, None

def process_recurring_invoices_service():
    """
    Procesa todas las suscripciones activas que deben facturarse hoy.
    """
    today = date.today()
    subscriptions_to_bill = Subscription.query.filter(
        Subscription.status == 'active',
        Subscription.next_billing_date <= today
    ).all()

    processed_count = 0
    errors = []

    for sub in subscriptions_to_bill:
        try:
            # 1. Generate the invoice data
            invoice_data = {
                'customer_name': sub.user.full_name,
                'customer_nit': sub.user.nit, # Assuming user has NIT
                'items': [{
                    'description': f"Suscripción: {sub.plan.name} ({sub.plan.billing_interval})",
                    'quantity': 1,
                    'price': sub.plan.price
                }]
            }

            # 2. Create the invoice using the invoicing service
            invoice, error = invoicing_service.create_invoice_service(invoice_data)
            if error:
                raise Exception(error)

            # 3. Update the next billing date for the subscription
            if sub.plan.billing_interval == 'monthly':
                sub.next_billing_date += relativedelta(months=1)
            elif sub.plan.billing_interval == 'annually':
                sub.next_billing_date += relativedelta(years=1)

            db.session.commit()
            processed_count += 1

        except Exception as e:
            db.session.rollback()
            errors.append(f"Error procesando suscripción ID {sub.id}: {str(e)}")

    return {
        "processed_count": processed_count,
        "errors": errors
    }
