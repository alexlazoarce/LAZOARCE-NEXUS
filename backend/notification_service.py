from datetime import date, timedelta
from .models import LoanApplication, User

def send_payment_reminders():
    """
    Finds loans with upcoming payments and sends reminders.
    For now, it just prints the reminder to the console.
    """
    today = date.today()
    reminder_date = today + timedelta(days=5) # Send reminder 5 days before due date

    # This is a simplified query. A real implementation would need to parse the
    # amortization table for each loan to find the next due date.
    # For now, we'll simulate finding loans that need reminders.

    # Placeholder: In a real scenario, you'd query loans whose next payment is on reminder_date.
    # applications_to_remind = LoanApplication.query.filter(...)

    print(f"--- Running Payment Reminders for {today} ---")

    # Simulating finding a loan that needs a reminder
    # In a real implementation, you would loop through `applications_to_remind`

    # a_loan = LoanApplication.query.first() # Example loan
    # if a_loan:
    #     user = User.query.get(a_loan.user_id)
    #     message = f"Hola {user.full_name},\n\n"
    #     message += f"Este es un recordatorio de que tu próximo pago del préstamo ID {a_loan.id} por un monto de ${a_loan.monthly_payment:.2f} vence en 5 días.\n\n"
    #     message += "Gracias,\nLAZOARCE NEXUS"

    #     send_email(user.email, "Recordatorio de Pago", message)

    print("No loans found for reminders today (simulation).")
    print("--- Payment Reminders Finished ---")

def send_email(to_address, subject, body):
    """
    Simulates sending an email. In a real implementation, this would connect
    to an SMTP server or email service (like SendGrid, Mailgun, etc.).
    """
    print("======================================")
    print(f"MAIL ENVIADO (SIMULACIÓN)")
    print(f"Para: {to_address}")
    print(f"Asunto: {subject}")
    print("--------------------------------------")
    print(body)
    print("======================================")

# To run this service, you would typically have a scheduler (like APScheduler or a cron job)
# that calls send_payment_reminders() periodically (e.g., once a day).
