import unittest
import json
from datetime import datetime
from backend.app import create_app
from backend.extensions import db
from backend.models import Role, User, ChartOfAccounts, AccountingEntry, EntryDetail
from backend.hr.models import Empleado, Nomina, PrestamoEmpleado
from flask_jwt_extended import create_access_token

class HrPayrollTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['JWT_SECRET_KEY'] = 'test-secret-key' # Clave secreta para pruebas
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            self.setup_initial_data()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def setup_initial_data(self):
        db.session.add(Role(name='Administrador General'))
        accounts_data = [
            {"account_code": "5-01-001", "account_name": "Gastos de Salarios", "account_type": "Gasto"},
            {"account_code": "2-02-001", "account_name": "Sueldos por Pagar", "account_type": "Pasivo"},
            {"account_code": "2-02-005", "account_name": "AFP por Pagar", "account_type": "Pasivo"},
            {"account_code": "2-02-004", "account_name": "ISSS por Pagar", "account_type": "Pasivo"},
            {"account_code": "2-01-005", "account_name": "Retenciones por Entregar", "account_type": "Pasivo"},
            {"account_code": "1-02-012", "account_name": "Préstamos a Empleados", "account_type": "Activo"},
        ]
        for acc_data in accounts_data:
            acc_data['account_class'] = 'N/A'
            db.session.add(ChartOfAccounts(**acc_data))
        db.session.commit()

    def _get_auth_token(self):
        role = Role.query.filter_by(name='Administrador General').first()
        admin_user = User.query.filter_by(email="admin_hr@test.com").first()
        if not admin_user:
            admin_user = User(email="admin_hr@test.com", role_id=role.id)
            admin_user.set_password("adminpass")
            db.session.add(admin_user)
            db.session.commit()

        identity = admin_user.email
        additional_claims = {"role": admin_user.role.name}
        return create_access_token(identity=identity, additional_claims=additional_claims)

    def test_payroll_generation(self):
        with self.app.app_context():
            token = self._get_auth_token()
            headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

            empleado_data = {
                "codigo_empleado": "EMP-001", "dui": "12345678-9",
                "nombre_completo": "Juan Perez", "fecha_ingreso": "2023-01-01",
                "cargo": "Desarrollador", "salario_base": 1000.00
            }
            res = self.client.post('/api/rrhh/empleados', data=json.dumps(empleado_data), headers=headers)
            self.assertEqual(res.status_code, 201)
            empleado_id = res.get_json()['id']

            nomina_data = { "empleado_id": empleado_id, "periodo": "2024-07" }
            res = self.client.post('/api/rrhh/nominas/generar', data=json.dumps(nomina_data), headers=headers)
            self.assertEqual(res.status_code, 200, f"Error: {res.get_json()}")

            nomina_id = res.get_json()['nomina_id']
            nomina = Nomina.query.get(nomina_id)
            self.assertIsNotNone(nomina)
            self.assertEqual(nomina.estado, 'CONTABILIZADA')

if __name__ == '__main__':
    unittest.main()