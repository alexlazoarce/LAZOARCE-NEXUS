import unittest
import json

# Las importaciones ahora son directas, sin manipulación de sys.path
from backend.app import create_app
from backend.extensions import db
from backend.models import Role, User, Loan
from flask_jwt_extended import create_access_token

class ApiTestCase(unittest.TestCase):
    """
    Clase de pruebas para la API de Flask.
    """
    def setUp(self):
        """
        Configuración inicial para cada prueba.
        """
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            if not Role.query.filter_by(name='Cliente').first():
                db.session.add(Role(name='Cliente'))
            if not Role.query.filter_by(name='Administrador General').first():
                db.session.add(Role(name='Administrador General'))
            db.session.commit()

    def tearDown(self):
        """
        Limpieza después de cada prueba.
        """
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_index_route(self):
        """Prueba que la ruta raíz ('/') funciona."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['message'], "Servidor del Sistema de Gestión Financiera en funcionamiento.")

    def test_user_registration(self):
        """Prueba el registro de un nuevo usuario."""
        new_user = {"email": "testuser@example.com", "password": "password123", "role": "Cliente"}
        response = self.client.post('/api/register', data=json.dumps(new_user), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()['msg'], "Usuario creado exitosamente")

        response = self.client.post('/api/register', data=json.dumps(new_user), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()['msg'], "El email ya está registrado")

    def _get_auth_token(self, email, password, role_name='Cliente'):
        """
        Helper robusto para crear un usuario y generar un token directamente.
        """
        with self.app.app_context():
            role = Role.query.filter_by(name=role_name).first()
            self.assertIsNotNone(role, f"Rol '{role_name}' no encontrado en la BD de prueba.")

            user = User(email=email, role_id=role.id)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            identity = user.email
            additional_claims = {"role": user.role.name}
            token = create_access_token(identity=identity, additional_claims=additional_claims)
            return token

    def test_profile_management(self):
        """Prueba la creación y obtención de un perfil de cliente."""
        token = self._get_auth_token("profileuser@example.com", "password")
        headers = {'Authorization': f'Bearer {token}'}

        response = self.client.get('/api/profile', headers=headers)
        self.assertEqual(response.status_code, 404, f"Respuesta inesperada: {response.get_json()}")

        profile_data = {"full_name": "Test User Name", "phone_number": "1234567890", "address": "123 Test St"}
        response = self.client.post('/api/profile', data=json.dumps(profile_data), headers=headers, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()['msg'], "Perfil creado exitosamente.")

        response = self.client.get('/api/profile', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['full_name'], "Test User Name")

    def test_loan_approval_flow_and_payments(self):
        """Prueba el flujo completo: producto -> solicitud -> aprobación -> pago."""
        admin_token = self._get_auth_token("admin@test.com", "adminpass", role_name='Administrador General')
        client_token = self._get_auth_token("client@test.com", "clientpass", role_name='Cliente')

        admin_headers = {'Authorization': f'Bearer {admin_token}'}
        client_headers = {'Authorization': f'Bearer {client_token}'}

        product_data = {"name": "Préstamo Test", "loan_type": "Personal", "min_amount": 100, "max_amount": 5000, "default_interest_rate": 5.0, "default_admin_commission": 1.0}
        response = self.client.post('/api/products', data=json.dumps(product_data), headers=admin_headers, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        product_id = response.get_json()['product_id']

        app_data = {"product_id": product_id, "requested_amount": 1500, "requested_term": 12}
        response = self.client.post('/api/applications', data=json.dumps(app_data), headers=client_headers, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        app_id = response.get_json()['application_id']

        status_data = {"status": "Aprobada"}
        response = self.client.put(f'/api/applications/{app_id}/status', data=json.dumps(status_data), headers=admin_headers, content_type='application/json')
        self.assertEqual(response.status_code, 200, f"Fallo en la aprobación: {response.get_json()}")
        self.assertIn("Préstamo con ID", response.get_json()['msg'])

        with self.app.app_context():
            loan = Loan.query.filter_by(application_id=app_id).first()
            self.assertIsNotNone(loan)
            loan_id = loan.id

        payment_data = {"amount": 150.0, "payment_method": "Transferencia"}
        response = self.client.post(f'/api/loans/{loan_id}/payments', data=json.dumps(payment_data), headers=client_headers, content_type='application/json')
        self.assertEqual(response.status_code, 201)

        response = self.client.get(f'/api/loans/{loan_id}/payments', headers=client_headers)
        self.assertEqual(response.status_code, 200)
        payments = response.get_json()
        self.assertEqual(len(payments), 1)
        self.assertEqual(payments[0]['amount'], 150.0)

if __name__ == '__main__':
    unittest.main()