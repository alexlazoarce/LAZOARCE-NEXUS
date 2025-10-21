from backend.extensions import db
from backend.models import ChartOfAccounts

def initialize_chart_of_accounts():
    """Insertar plan de cuentas inicial para GRUPO LAZO ARCE."""
    if ChartOfAccounts.query.first():
        print("El plan de cuentas ya ha sido inicializado.")
        return

    print("=== INICIALIZANDO PLAN DE CUENTAS ===")

    accounts_data = [
        {"account_code": "1-01-001", "account_name": "Caja General", "account_type": "Activo", "balance": 0},
        {"account_code": "1-01-003", "account_name": "Bancos - Cuenta Corriente", "account_type": "Activo", "balance": 0},
        {"account_code": "1-02-001", "account_name": "Préstamos Personales", "account_type": "Activo", "balance": 0},
        {"account_code": "1-02-012", "account_name": "Préstamos a Empleados", "account_type": "Activo", "balance": 0},
        {"account_code": "2-01-005", "account_name": "Retenciones por Entregar", "account_type": "Pasivo", "balance": 0},
        {"account_code": "2-02-001", "account_name": "Sueldos por Pagar", "account_type": "Pasivo", "balance": 0},
        {"account_code": "2-02-004", "account_name": "ISSS por Pagar", "account_type": "Pasivo", "balance": 0},
        {"account_code": "2-02-005", "account_name": "AFP por Pagar", "account_type": "Pasivo", "balance": 0},
        {"account_code": "5-01-001", "account_name": "Gastos de Salarios", "account_type": "Gasto", "balance": 0},
    ]

    for acc_data in accounts_data:
        account = ChartOfAccounts(**acc_data)
        db.session.add(account)

    db.session.commit()
    print("🎉 PLAN DE CUENTAS INICIALIZADO CORRECTAMENTE")