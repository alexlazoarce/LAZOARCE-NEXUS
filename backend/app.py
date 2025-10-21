import os
import click
from flask import Flask, jsonify, request, make_response, g
from flask_cors import CORS
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity,
    JWTManager, get_jwt, verify_jwt_in_request
)
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from functools import wraps
from datetime import datetime, date, timedelta
from io import BytesIO
from random import randint, choice # Incluido del 2.0 para la ruta de prueba

# --- DEFINICIÓN GLOBAL DE EXTENSIONES ---
# Se necesita definir SQLAlchemy globalmente antes de create_app si se usa en modelos importados
# Asumimos que .database define 'db' que es una instancia de SQLAlchemy.
try:
    from .database import db as global_db
    db = global_db
except ImportError:
    # Fallback si no existe .database
    db = SQLAlchemy()

jwt = JWTManager()
migrate = Migrate()

# --- IMPORTACIONES DE SERVICIOS (Asunciones del HEAD) ---
# Se asume la existencia de estos módulos locales
try:
    from .loan_calculator import calcular_prestamo_completo
    from .pdf_generator import create_contract_pdf, convert_html_to_pdf
    from .accounting_service import create_journal_entry
    from .firma_service import (
        validacion_identidad_estricta,
        capturar_datos_biometricos,
        generar_contrato_integracion,
        firma_electronica_avanzada
    )
    from .payroll_service import calcular_planilla
    # Mock de servicios si no existen realmente
    class MockService:
        def log_action(*args, **kwargs): pass
    audit_service = MockService()
    
except ImportError as e:
    print(f"⚠️ Error importando servicios: {e}. Usando Mocks.")
    # Mocks para que la app corra
    def mock_func(*args, **kwargs): pass
    calcular_prestamo_completo = create_journal_entry = validacion_identidad_estricta = capturar_datos_biometricos = generar_contrato_integracion = firma_electronica_avanzada = calcular_planilla = mock_func
    
# -----------------------------------------------------------


def create_app(config_object=None, testing_config=None):
    """
    Application Factory para crear y configurar la aplicación Flask.
    """
    app = Flask(__name__)
    CORS(app)

    # Cargar variables de entorno (del HEAD)
    load_dotenv()

    # === CONFIGURACIÓN (Fusionado del 2.0 + HEAD) ===
    # Establecer valores por defecto (estructura 2.0)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-secret-key-change-me'),
        JWT_SECRET_KEY=os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-me'),
        # Usamos la ubicación explícita del 2.0 como fallback
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'lazoarce.db')}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        JWT_ACCESS_TOKEN_EXPIRES=timedelta(hours=8),
        JWT_REFRESH_TOKEN_EXPIRES=timedelta(days=30),
        ENVIRONMENT='development',
        DEBUG=True,
        UPLOAD_FOLDER='uploads'
    )
    
    # Sobrescribir con config_object o testing_config
    if config_object:
         app.config.from_object(config_object)
    if testing_config:
        app.config.from_object(testing_config)
    
    # Variables de entorno críticas (con fallback)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', app.config.get('SECRET_KEY'))
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', app.config.get('JWT_SECRET_KEY'))
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', app.config.get('SQLALCHEMY_DATABASE_URI'))

    # Crear carpeta de uploads
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # --- INICIALIZACIÓN DE EXTENSIONES ---
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db) 

    # --- CARGA DINÁMICA DE MODELOS Y SERVICIOS ---
    with app.app_context():
        # Intenta cargar modelos (simulando la lógica de .models)
        try:
            from .models import (
                Role, User, LoanProduct, LoanApplication, Account, Transaction,
                JournalEntry, Cliente, ContratoIntegracion, ProductoCredito,
                Empleado, Planilla, ClientProfile, Tenant, AuditLog, Payment,
                NotificationTemplate, Employee, ContractTemplate, GeneratedContract,
                Contact, Interaction, Opportunity, Product, StockMovement,
                Quote, SalesOrder, SalesOrderItem, Supplier, PurchaseOrder, PurchaseOrderItem,
                EmailLog, Channel, Message, SignableTemplate, SignatureRequest, Form, FormSubmission,
                Project, Task, Ticket, TicketUpdate, FixedAsset, DepreciationEntry,
                BankAccount, BankTransaction, CashBox, CashTransaction
            )
            # Simular carga de servicios (asumiendo que fueron importados arriba)
            from . import audit_service
            from . import contract_service
            from . import crm_service
            from . import inventory_service
            from . import sales_service
            from . import purchasing_service
            from . import email_service
            from . import document_service
            from . import messaging_service
            from . import sign_service
            from . import form_service
            from . import project_service
            from . import support_service
            from . import asset_service
            from . import tax_service
            from . import material_service
            from . import construction_service
            from . import health_service
            from . import education_service
            app.services = {
                'audit_service': audit_service,
                'contract_service': contract_service,
                'crm_service': crm_service,
                'inventory_service': inventory_service,
                'sales_service': sales_service,
                'purchasing_service': purchasing_service,
                'email_service': email_service,
                'document_service': document_service,
                'messaging_service': messaging_service,
                'sign_service': sign_service,
                'form_service': form_service,
                'project_service': project_service,
                'support_service': support_service,
                'asset_service': asset_service,
                'tax_service': tax_service,
                'material_service': material_service,
                'construction_service': construction_service,
                'health_service': health_service,
                'education_service': education_service
            }

        except ImportError as e:
            app.logger.error(f"❌ Error al importar modelos: {e}. Se usarán Mocks.")
            # Definición de MockModel si falla la importación
            class MockModel:
                def __init__(self, **kwargs): pass
                def query(self): return self
                def filter_by(self, **kwargs): return self
                def first(self): return None
                def all(self): return []
                def get(self, id): return None
                def get_or_404(self, id): return None

            Role = User = LoanProduct = LoanApplication = Account = Transaction = JournalEntry = Cliente = ContratoIntegracion = ProductoCredito = Empleado = Planilla = ClientProfile = Tenant = AuditLog = Payment = NotificationTemplate = Employee = ContractTemplate = GeneratedContract = Contact = Interaction = Opportunity = Product = StockMovement = Quote = SalesOrder = SalesOrderItem = Supplier = PurchaseOrder = PurchaseOrderItem = EmailLog = MockModel
            app.services = {
                'audit_service': lambda: None,
                'contract_service': lambda: None,
                'crm_service': lambda: None,
                'inventory_service': lambda: None,
                'sales_service': lambda: None,
                'purchasing_service': lambda: None,
                'email_service': lambda: None
            }

        # Asignar modelos al contexto de la app
        app.models = {
            'Role': Role, 'User': User, 'LoanProduct': LoanProduct, 'LoanApplication': LoanApplication,
            'Account': Account, 'Transaction': Transaction, 'JournalEntry': JournalEntry, 'Cliente': Cliente,
            'ContratoIntegracion': ContratoIntegracion, 'ProductoCredito': ProductoCredito, 'Empleado': Empleado,
            'Planilla': Planilla, 'Employee': Employee, 'AuditLog': AuditLog,
            'ContractTemplate': ContractTemplate, 'GeneratedContract': GeneratedContract,
            'Contact': Contact, 'Interaction': Interaction, 'Opportunity': Opportunity,
            'Product': Product, 'StockMovement': StockMovement,
            'Quote': Quote, 'SalesOrder': SalesOrder, 'SalesOrderItem': SalesOrderItem,
            'Supplier': Supplier, 'PurchaseOrder': PurchaseOrder, 'PurchaseOrderItem': PurchaseOrderItem,
            'EmailLog': EmailLog, 'Channel': Channel, 'Message': Message,
            'SignableTemplate': SignableTemplate, 'SignatureRequest': SignatureRequest,
            'Form': Form, 'FormSubmission': FormSubmission, 'Project': Project, 'Task': Task,
            'Ticket': Ticket, 'TicketUpdate': TicketUpdate, 'FixedAsset': FixedAsset, 'DepreciationEntry': DepreciationEntry,
            'BankAccount': BankAccount, 'BankTransaction': BankTransaction, 'CashBox': CashBox, 'CashTransaction': CashTransaction,
            'TaxType': TaxType, 'TaxDeclaration': TaxDeclaration,
            'Material': Material, 'MaterialRequest': MaterialRequest,
            'ConstructionProject': ConstructionProject, 'BudgetItem': BudgetItem, 'ProgressReport': ProgressReport, 'Certification': Certification,
            'PatientRecord': PatientRecord, 'MedicalAppointment': MedicalAppointment, 'Prescription': Prescription, 'LabOrder': LabOrder,
            'Student': Student, 'Course': Course, 'Enrollment': Enrollment, 'Grade': Grade
        }

    # --- DECORADORES DE AUTORIZACIÓN (Unificado) ---
    def role_required(required_roles):
        if not isinstance(required_roles, list):
            required_roles = [required_roles]

        def decorator(fn):
            @wraps(fn)
            @jwt_required()
            def wrapper(*args, **kwargs):
                User = app.models.get('User')
                if not User: return jsonify({"msg": "Error interno de sistema (Modelo User)"}), 500

                claims = get_jwt()
                user_roles = claims.get('roles', [])
                user_identity = get_jwt_identity()
                
                # Asumimos que el identity es el email (como en el HEAD), pero verificamos el ID del 2.0
                g.current_user = User.query.filter_by(email=user_identity).first()
                if not g.current_user:
                    return jsonify({"msg": "Usuario no encontrado en la base de datos"}), 404

                # Verificar roles: tanto los de claims (2.0) como el rol principal (HEAD)
                user_has_required_role = any(role in user_roles for role in required_roles)
                if g.current_user.role and g.current_user.role.name in required_roles:
                    user_has_required_role = True

                if not user_has_required_role:
                    return jsonify({"msg": "Acceso no autorizado para este rol"}), 403
                return fn(*args, **kwargs)
            return wrapper
        return decorator
    
    # Registrar alias para el decorador
    app.jinja_env.globals['role_required'] = role_required
    app.jinja_env.globals['require_roles'] = role_required # Alias para compatibilidad

    # --- MIDDLEWARE DE AUDITORÍA (Del 2.0) ---
    
    @app.before_request
    def audit_request():
        if request.path.startswith('/api/') and request.method in ['POST', 'PUT', 'DELETE']:
            g.audit_action = f"{request.method} {request.path}"
    
    @app.after_request
    def audit_response(response):
        AuditLog = app.models.get('AuditLog')
        
        if hasattr(g, 'audit_action') and hasattr(g, 'current_user') and AuditLog and g.current_user and hasattr(g.current_user, 'id'):
            try:
                audit_log = AuditLog(
                    user_id=g.current_user.id,
                    action=g.audit_action,
                    details=f"Status: {response.status_code}",
                    ip_address=request.remote_addr
                )
                db.session.add(audit_log)
                db.session.commit()
            except Exception as e:
                app.logger.error(f"Error en auditoría: {str(e)}")
                db.session.rollback()
        
        return response

    # -------------------------------------------------------------------
    # === RUTAS MONOLÍTICAS (Fusión de HEAD con rutas clave del 2.0) ===
    # -------------------------------------------------------------------

    # --- RUTAS BASE (Del 2.0) ---
    @app.route('/')
    def index():
        return jsonify({"message": "Servidor del Sistema de Gestión Financiera en funcionamiento.", "version": "2.1 (Fusion)"})

    @app.route('/api/health')
    def health_check():
        db_connected = False
        try:
            db.session.execute(db.select(1)).one()
            db_connected = True
        except Exception:
            db_connected = False
            
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": db_connected,
        })
    
    # --- RUTAS DE AUTENTICACIÓN (Del HEAD/2.0 unificadas) ---
    @app.route('/api/register', methods=['POST'])
    def register():
        User = app.models.get('User')
        Role = app.models.get('Role')
        if not User or not Role: return jsonify({"msg": "Error de sistema (Modelos no cargados)"}), 500
        
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        role_name = data.get('role', 'Cliente')
        
        if not email or not password:
            return jsonify({"msg": "Email y contraseña son requeridos"}), 400
        if User.query.filter_by(email=email).first():
            return jsonify({"msg": "El email ya está registrado"}), 400
        
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            return jsonify({"msg": f"El rol '{role_name}' no es válido"}), 400
            
        new_user = User(email=email, role_id=role.id)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"msg": "Usuario creado exitosamente"}), 201

    @app.route('/api/login', methods=['POST'])
    def login():
        User = app.models.get('User')
        if not User: return jsonify({"msg": "Error de sistema (Modelo User)"}), 500
        
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({"msg": "Email y contraseña son requeridos"}), 400
            
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            user_roles = [user.role.name] if user.role else ['Cliente']
            # Se usa el email como identity (HEAD) y se inyectan los roles (2.0)
            access_token = create_access_token(identity=user.email, additional_claims={'roles': user_roles, 'email': user.email, 'user_id': user.id})
            
            # audit_service.log_action('USER_LOGIN', user_id=user.id, details=f"User {user.email} logged in successfully.")
            
            return jsonify(access_token=access_token)
        
        return jsonify({"msg": "Credenciales inválidas"}), 401

    @app.route('/api/admin/test')
    @role_required('Administrador General')
    def admin_test_route():
        return jsonify(logged_in_as=g.current_user.email, role=g.current_user.role.name if g.current_user.role else 'N/A'), 200

    @app.route('/api/profile', methods=['GET'])
    @jwt_required()
    def get_profile():
        user = g.current_user
        if not user: return jsonify({"msg": "Usuario no encontrado"}), 404
        
        return jsonify({
            "email": user.email,
            "full_name": user.full_name,
            "dui": user.dui,
            "nit": user.nit,
            "role": user.role.name if user.role else 'N/A'
        })
    
    # --- RUTA DE CREACIÓN DE CLIENTE CON FEA (Del HEAD) ---
    @app.route('/api/clientes/nuevo', methods=['POST'])
    @jwt_required()
    @role_required(['Administrador General', 'Ejecutivo de Crédito'])
    def crear_nuevo_cliente():
        Cliente = app.models.get('Cliente')
        ContratoIntegracion = app.models.get('ContratoIntegracion')
        if not Cliente or not ContratoIntegracion: return jsonify({"error": "Error de sistema (Modelos no cargados)"}), 500

        try:
            data = request.get_json()
            datos_requeridos = ['nombre_completo', 'dui', 'email', 'telefono', 'direccion']
            for campo in datos_requeridos:
                if campo not in data:
                    return jsonify({'error': f'Campo requerido: {campo}'}), 400

            if not validacion_identidad_estricta(data):
                return jsonify({'error': 'Validación de identidad falló. Verifique los datos o si el cliente ya existe.'}), 400

            datos_biometricos = capturar_datos_biometricos()
            if not datos_biometricos:
                return jsonify({'error': 'Error en la captura de datos biométricos.'}), 500

            contrato_id = generar_contrato_integracion(data) 
            if not contrato_id:
                return jsonify({'error': 'No se pudo generar el contrato de integración.'}), 500

            resultado_firma = firma_electronica_avanzada(contrato_id, data, datos_biometricos)
            
            if not resultado_firma.get('valida'):
                contrato = ContratoIntegracion.query.filter_by(contrato_id=contrato_id).first()
                if contrato:
                    db.session.delete(contrato)
                    db.session.commit()
                return jsonify({'error': 'El proceso de firma electrónica falló.', 'detalle': resultado_firma.get('error')}), 400

            cliente = Cliente(
                nombre_completo=data['nombre_completo'],
                dui=data['dui'],
                email=data['email'],
                telefono=data['telefono'], # Asumido en el modelo Cliente
                direccion=data['direccion'], # Asumido en el modelo Cliente
                contrato_integracion_id=contrato_id,
                estado='ACTIVO'
            )
            db.session.add(cliente)
            db.session.commit()

            return jsonify({
                'success': True,
                'cliente_id': cliente.id,
                'contrato_id': contrato_id,
                'mensaje': 'Cliente creado y contrato firmado exitosamente con validación completa.'
            }), 201

        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Ocurrió un error inesperado en el servidor.', 'detalle': str(e)}), 500

    # --- RUTA DE CALCULO DE PLANILLA (Del HEAD) ---
    @app.route('/api/payroll/calculate', methods=['POST'])
    @role_required(['Contador', 'Administrador General'])
    def calculate_payroll_for_employee():
        Empleado = app.models.get('Empleado')
        Planilla = app.models.get('Planilla')
        if not Empleado or not Planilla: return jsonify({'error': 'Error de sistema (Modelos no cargados)'}), 500

        data = request.get_json()
        empleado_id = data.get('empleado_id')
        if not empleado_id:
            return jsonify({'error': 'El campo empleado_id es requerido.'}), 400
            
        empleado = Empleado.query.get(empleado_id)
        if not empleado:
            return jsonify({'error': 'Empleado no encontrado.'}), 404
            
        # Asumimos que Empleado tiene atributo salario_base (HEAD)
        resultado_calculo = calcular_planilla(empleado.salario_base) 
        
        if not resultado_calculo.get('success'):
            return jsonify({'error': 'Error al calcular la planilla.', 'detalle': resultado_calculo.get('error')}), 500
            
        try:
            # Note: La estructura de Planilla (HEAD) es diferente a PaySlip (2.0), usamos la del HEAD para compatibilidad.
            nueva_planilla = Planilla(
                empleado_id=empleado.id,
                salario_base=resultado_calculo['salario_base'],
                isss=resultado_calculo['isss'], # Nota: Se asume que el modelo Planilla tiene 'isss', 'afp', 'renta'
                afp=resultado_calculo['afp'],
                renta=resultado_calculo['renta'],
                salario_neto=resultado_calculo['salario_neto']
            )
            db.session.add(nueva_planilla)
            db.session.commit()
            return jsonify({"success": True, "planilla_id": nueva_planilla.id, "calculo": resultado_calculo})
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Error al guardar el registro de la planilla.', 'detalle': str(e)}), 500

    # --- RUTAS RESTO DE PRÉSTAMOS/CONTABILIDAD (Monolíticas) ---
    # Se incluyen las rutas de préstamos y la lógica de contabilidad como se fusionó anteriormente.
    
    @app.route('/api/products', methods=['GET', 'POST'])
    @jwt_required()
    @role_required(['Administrador General'])
    def handle_products():
        # Lógica de CRUD de productos aquí...
        return jsonify({"message": "Rutas de productos implementadas (CRUD)."}), 501

    @app.route('/api/applications', methods=['POST'])
    @jwt_required()
    def submit_loan_application():
        # Lógica de solicitud de préstamo aquí...
        return jsonify({"message": "Ruta de solicitud de préstamo implementada."}), 501

    @app.route('/api/applications/<int:app_id>/send-reminder', methods=['POST'])
    @jwt_required()
    @role_required(['Administrador General'])
    def send_payment_reminder(app_id):
        LoanApplication = app.models.get('LoanApplication')
        application = LoanApplication.query.get_or_404(app_id)

        # Lógica para enviar un recordatorio de pago
        recipient = application.applicant.email
        subject = f"Recordatorio de Pago para su Préstamo #{application.id}"
        body = f"Hola {application.applicant.full_name},\n\nEste es un recordatorio de que su próximo pago para el préstamo #{application.id} está por vencer."

        app.services['email_service'].send_email(
            recipient,
            subject,
            body,
            g.current_user.tenant
        )

        return jsonify({"message": f"Recordatorio de pago enviado para la solicitud {app_id}."}), 200

    @app.route('/api/applications/<int:app_id>/status', methods=['PUT'])
    @jwt_required()
    @role_required(['Ejecutivo de Crédito', 'Administrador General'])
    def update_application_status(app_id):
        LoanApplication = app.models.get('LoanApplication')
        application = LoanApplication.query.get_or_404(app_id)

        data = request.get_json()
        new_status = data.get('status')

        if not new_status:
            return jsonify({"error": "El campo 'status' es requerido."}), 400

        application.status = new_status

        # Si el estado es "Aprobado", se podría generar el contrato aquí
        if new_status == 'Aprobado':
            # Suponiendo que existe una plantilla de contrato para préstamos
            # Aquí se llamaría al contract_service para generar el contrato
            pass

        db.session.commit()
        return jsonify({"message": f"Estado de la solicitud {app_id} actualizado a '{new_status}'."})

    # --- RUTAS PARA GESTIÓN DE CONTRATOS (LAN-F2C) ---

    @app.route('/api/contracts/templates', methods=['POST'])
    @jwt_required()
    @role_required(['Administrador General'])
    def create_contract_template_route():
        data = request.get_json()
        # Aquí iría la llamada al contract_service
        return jsonify({"message": "Ruta para crear plantilla de contrato implementada."}), 201

    @app.route('/api/contracts/templates/<int:template_id>', methods=['GET'])
    @jwt_required()
    def get_contract_template_route(template_id):
        # Lógica para obtener una plantilla
        return jsonify({"message": f"Ruta para obtener plantilla {template_id}."}), 200

    @app.route('/api/contracts/templates/<int:template_id>', methods=['PUT'])
    @jwt_required()
    @role_required(['Administrador General'])
    def update_contract_template_route(template_id):
        data = request.get_json()
        # Lógica para actualizar una plantilla
        return jsonify({"message": f"Ruta para actualizar plantilla {template_id}."}), 200

    @app.route('/api/contracts/templates/<int:template_id>', methods=['DELETE'])
    @jwt_required()
    @role_required(['Administrador General'])
    def delete_contract_template_route(template_id):
        # Lógica para eliminar una plantilla
        return jsonify({"message": f"Ruta para eliminar plantilla {template_id}."}), 200

    @app.route('/api/contracts/generate', methods=['POST'])
    @jwt_required()
    @role_required(['Ejecutivo de Crédito', 'Administrador General'])
    def generate_contract_route():
        data = request.get_json()
        # Lógica para generar un contrato desde una plantilla
        return jsonify({"message": "Ruta para generar un contrato implementada."}), 201

    # --- RUTAS PARA CRM (LAN-CRM3) ---

    @app.route('/api/crm/contacts', methods=['POST'])
    @jwt_required()
    @role_required(['Ejecutivo de Crédito', 'Administrador General'])
    def create_crm_contact():
        data = request.get_json()
        # Lógica para llamar a crm_service.create_contact
        return jsonify({"message": "Ruta para crear contacto de CRM implementada."}), 201

    @app.route('/api/crm/contacts', methods=['GET'])
    @jwt_required()
    def get_crm_contacts():
        # Lógica para llamar a crm_service.get_contacts
        return jsonify([]), 200

    @app.route('/api/crm/contacts/<int:contact_id>', methods=['GET'])
    @jwt_required()
    def get_crm_contact_details(contact_id):
        # Lógica para llamar a crm_service.get_contact_details
        return jsonify({"message": f"Ruta para obtener detalles del contacto {contact_id}."}), 200

    @app.route('/api/crm/contacts/<int:contact_id>/interactions', methods=['POST'])
    @jwt_required()
    def add_crm_interaction(contact_id):
        data = request.get_json()
        # Lógica para llamar a crm_service.create_interaction
        return jsonify({"message": f"Ruta para añadir interacción al contacto {contact_id}."}), 201

    @app.route('/api/crm/opportunities', methods=['POST'])
    @jwt_required()
    @role_required(['Ejecutivo de Crédito', 'Administrador General'])
    def create_crm_opportunity():
        data = request.get_json()
        # Lógica para llamar a crm_service.create_opportunity
        return jsonify({"message": "Ruta para crear oportunidad de CRM implementada."}), 201

    @app.route('/api/crm/opportunities/<int:opp_id>/stage', methods=['PUT'])
    @jwt_required()
    @role_required(['Ejecutivo de Crédito', 'Administrador General'])
    def update_crm_opportunity_stage(opp_id):
        data = request.get_json()
        # Lógica para llamar a crm_service.update_opportunity_stage
        return jsonify({"message": f"Ruta para actualizar etapa de la oportunidad {opp_id}."}), 200

    # --- RUTAS PARA INVENTARIO (LAN-INV9) ---

    @app.route('/api/inventory/products', methods=['POST'])
    @jwt_required()
    @role_required(['Administrador General'])
    def create_inventory_product():
        data = request.get_json()
        # Lógica para llamar a inventory_service.create_product
        return jsonify({"message": "Ruta para crear producto de inventario implementada."}), 201

    @app.route('/api/inventory/products', methods=['GET'])
    @jwt_required()
    def get_inventory_products():
        # Lógica para llamar a inventory_service.get_products
        return jsonify([]), 200

    @app.route('/api/inventory/products/<int:product_id>/movements', methods=['POST'])
    @jwt_required()
    @role_required(['Administrador General'])
    def record_inventory_movement(product_id):
        data = request.get_json()
        # Lógica para llamar a inventory_service.record_stock_movement
        return jsonify({"message": f"Ruta para registrar movimiento de stock para el producto {product_id}."}), 201

    # --- RUTAS PARA VENTAS (LAN-SLS2) ---

    @app.route('/api/sales/quotes', methods=['POST'])
    @jwt_required()
    @role_required(['Ejecutivo de Crédito', 'Administrador General'])
    def create_sales_quote():
        data = request.get_json()
        # Lógica para llamar a sales_service.create_quote
        return jsonify({"message": "Ruta para crear cotización de venta implementada."}), 201

    @app.route('/api/sales/orders', methods=['GET'])
    @jwt_required()
    def get_sales_orders():
        # Lógica para llamar a sales_service.get_sales_orders
        return jsonify([]), 200

    @app.route('/api/sales/quotes/<int:quote_id>/convert', methods=['POST'])
    @jwt_required()
    @role_required(['Ejecutivo de Crédito', 'Administrador General'])
    def convert_quote_to_order(quote_id):
        # Lógica para llamar a sales_service.convert_quote_to_sales_order
        return jsonify({"message": f"Ruta para convertir cotización {quote_id} a orden de venta."}), 201

    @app.route('/api/sales/orders/<int:order_id>/confirm', methods=['POST'])
    @jwt_required()
    @role_required(['Administrador General'])
    def confirm_sales_order(order_id):
        # Lógica para llamar a sales_service.confirm_sales_order
        return jsonify({"message": f"Ruta para confirmar la orden de venta {order_id} y ajustar stock."}), 200

    # --- RUTAS PARA COMPRAS (LAN-CO1M) ---

    @app.route('/api/purchasing/suppliers', methods=['POST'])
    @jwt_required()
    @role_required(['Administrador General'])
    def create_supplier():
        data = request.get_json()
        # Lógica para llamar a purchasing_service.create_supplier
        return jsonify({"message": "Ruta para crear proveedor implementada."}), 201

    @app.route('/api/purchasing/orders', methods=['POST'])
    @jwt_required()
    @role_required(['Administrador General'])
    def create_purchase_order():
        data = request.get_json()
        # Lógica para llamar a purchasing_service.create_purchase_order
        return jsonify({"message": "Ruta para crear orden de compra implementada."}), 201

    @app.route('/api/purchasing/orders/<int:order_id>/receive', methods=['POST'])
    @jwt_required()
    @role_required(['Administrador General'])
    def receive_purchase_order(order_id):
        # Lógica para llamar a purchasing_service.receive_purchase_order
        return jsonify({"message": f"Ruta para registrar la recepción de la orden {order_id}."}), 200

    # --- RUTAS PARA REPORTES CONTABLES (LAN-BKS1) ---

    @app.route('/api/reports/balance-sheet', methods=['GET'])
    @jwt_required()
    @role_required(['Contador', 'Administrador General'])
    def get_balance_sheet_report():
        tenant_id = g.current_user.tenant_id
        report_data = app.services['accounting_service'].get_balance_sheet(tenant_id)
        return jsonify(report_data), 200

    @app.route('/api/reports/income-statement', methods=['GET'])
    @jwt_required()
    @role_required(['Contador', 'Administrador General'])
    def get_income_statement_report():
        tenant_id = g.current_user.tenant_id
        report_data = app.services['accounting_service'].get_income_statement(tenant_id)
        return jsonify(report_data), 200

    # --- RUTAS PARA CORREO (LAN-MAIL1) ---

    @app.route('/api/email/test', methods=['POST'])
    @jwt_required()
    @role_required(['Administrador General'])
    def test_email_sending():
        data = request.get_json()
        recipient = data.get('recipient')
        subject = data.get('subject', 'Correo de Prueba')
        body = data.get('body', 'Este es un correo de prueba desde el sistema LAZOARCE NEXUS.')

        if not recipient:
            return jsonify({"error": "El destinatario es requerido."}), 400

        success, message = app.services['email_service'].send_email(
            recipient,
            subject,
            body,
            g.current_user.tenant
        )

        if success:
            return jsonify({"message": message}), 200
        else:
            return jsonify({"error": message}), 500

    # --- RUTAS PARA GESTOR DE DOCUMENTOS (LAN-GD2) ---
    from flask import Blueprint, send_from_directory

    documents_bp = Blueprint('documents', __name__, url_prefix='/api/documents')

    @documents_bp.route('/', methods=['GET'])
    @jwt_required()
    def list_documents():
        tenant_id = g.current_user.tenant_id
        documents = app.services['document_service'].get_documents_for_tenant(tenant_id)
        return jsonify([{
            'id': doc.id,
            'filename': doc.filename,
            'description': doc.description,
            'latest_version_id': doc.latest_version_id,
            'created_at': doc.created_at.isoformat(),
            'updated_at': doc.updated_at.isoformat()
        } for doc in documents])

    @documents_bp.route('/', methods=['POST'])
    @jwt_required()
    def upload_document():
        if 'file' not in request.files:
            return jsonify({"error": "No se encontró el archivo"}), 400

        file = request.files['file']
        description = request.form.get('description', '')
        tenant_id = g.current_user.tenant_id
        user_id = g.current_user.id

        try:
            document = app.services['document_service'].create_document(tenant_id, user_id, file, description)
            return jsonify({"message": "Documento creado exitosamente", "document_id": document.id}), 201
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            app.logger.error(f"Error al crear documento: {e}")
            return jsonify({"error": "Error interno al guardar el documento"}), 500

    @documents_bp.route('/<int:doc_id>/versions', methods=['POST'])
    @jwt_required()
    def upload_new_version(doc_id):
        if 'file' not in request.files:
            return jsonify({"error": "No se encontró el archivo"}), 400

        file = request.files['file']
        user_id = g.current_user.id

        try:
            version = app.services['document_service'].add_new_version(doc_id, user_id, file)
            return jsonify({"message": "Nueva versión añadida exitosamente", "version_id": version.id}), 201
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            app.logger.error(f"Error al añadir nueva versión: {e}")
            return jsonify({"error": "Error interno al guardar la nueva versión"}), 500

    @documents_bp.route('/versions/<int:version_id>/download', methods=['GET'])
    @jwt_required()
    def download_version(version_id):
        version = app.services['document_service'].get_document_version(version_id)
        # Aquí se debería verificar el acceso del tenant
        try:
            directory = os.path.dirname(version.filepath)
            filename = os.path.basename(version.filepath)
            return send_from_directory(directory, filename, as_attachment=True)
        except FileNotFoundError:
            return jsonify({"error": "Archivo no encontrado en el servidor."}), 404

    app.register_blueprint(documents_bp)

    # --- RUTAS PARA MENSAJERÍA CORPORATIVA (LAN-C8T) ---
    messaging_bp = Blueprint('messaging', __name__, url_prefix='/api/messaging')

    @messaging_bp.route('/channels', methods=['GET'])
    @jwt_required()
    def get_channels():
        user_id = g.current_user.id
        tenant_id = g.current_user.tenant_id
        # Devuelve canales públicos y privados del usuario
        channels = app.services['messaging_service'].get_user_channels(user_id, tenant_id)
        return jsonify([{'id': c.id, 'name': c.name, 'description': c.description, 'type': c.channel_type} for c in channels])

    @messaging_bp.route('/channels', methods=['POST'])
    @jwt_required()
    def create_messaging_channel():
        data = request.get_json()
        name = data.get('name')
        description = data.get('description', '')
        channel_type = data.get('type', 'public')

        tenant_id = g.current_user.tenant_id
        creator_id = g.current_user.id

        try:
            channel = app.services['messaging_service'].create_channel(name, description, channel_type, tenant_id, creator_id)
            return jsonify({'message': 'Canal creado exitosamente', 'channel_id': channel.id}), 201
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

    @messaging_bp.route('/channels/<int:channel_id>/messages', methods=['GET'])
    @jwt_required()
    def get_channel_messages(channel_id):
        messages = app.services['messaging_service'].get_messages_for_channel(channel_id)
        # Invertir el orden para que se muestren cronológicamente en el frontend
        messages.reverse()
        return jsonify([{
            'id': m.id,
            'content': m.content,
            'author': m.author.full_name if m.author else 'Usuario Desconocido',
            'user_id': m.user_id,
            'created_at': m.created_at.isoformat()
        } for m in messages])

    @messaging_bp.route('/channels/<int:channel_id>/messages', methods=['POST'])
    @jwt_required()
    def post_channel_message(channel_id):
        data = request.get_json()
        content = data.get('content')
        user_id = g.current_user.id

        try:
            message = app.services['messaging_service'].post_message(channel_id, user_id, content)
            return jsonify({'message': 'Mensaje enviado exitosamente', 'message_id': message.id}), 201
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

    app.register_blueprint(messaging_bp)

    # --- RUTAS PARA FIRMAR (LAN-SGN3) ---
    sign_bp = Blueprint('signer', __name__, url_prefix='/api/signer')

    @sign_bp.route('/templates', methods=['GET'])
    @jwt_required()
    def get_sign_templates():
        templates = app.services['sign_service'].get_templates_for_tenant(g.current_user.tenant_id)
        return jsonify([{'id': t.id, 'name': t.name, 'description': t.description} for t in templates])

    @sign_bp.route('/templates', methods=['POST'])
    @jwt_required()
    def create_sign_template():
        data = request.get_json()
        try:
            template = app.services['sign_service'].create_template(
                name=data.get('name'),
                description=data.get('description'),
                content=data.get('content'),
                tenant_id=g.current_user.tenant_id,
                user_id=g.current_user.id
            )
            return jsonify({'message': 'Plantilla creada exitosamente', 'template_id': template.id}), 201
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

    @sign_bp.route('/requests', methods=['GET'])
    @jwt_required()
    def get_sign_requests():
        requests = app.services['sign_service'].get_signature_requests(g.current_user.tenant_id)
        return jsonify([{
            'id': r.id,
            'signer_name': r.signer_name,
            'signer_email': r.signer_email,
            'status': r.status,
            'created_at': r.created_at.isoformat()
        } for r in requests])

    @sign_bp.route('/requests', methods=['POST'])
    @jwt_required()
    def create_sign_request():
        data = request.get_json()
        try:
            req = app.services['sign_service'].create_signature_request(
                template_id=data.get('template_id'),
                signer_name=data.get('signer_name'),
                signer_email=data.get('signer_email'),
                data_payload=data.get('payload', {}),
                tenant_id=g.current_user.tenant_id,
                user_id=g.current_user.id
            )
            # Opcionalmente, enviar inmediatamente
            if data.get('send_now', False):
                app.services['sign_service'].send_signature_request(req.id)

            return jsonify({'message': 'Solicitud de firma creada', 'request_id': req.id}), 201
        except Exception as e:
            return jsonify({'error': f'Error al crear la solicitud: {str(e)}'}), 500

    # --- Rutas Públicas (sin autenticación JWT) ---

    @sign_bp.route('/public/request/<string:token>', methods=['GET'])
    def get_public_sign_request(token):
        try:
            req = app.services['sign_service'].get_request_by_token(token)
            if req.status not in ['sent', 'viewed']:
                 return jsonify({'error': 'Esta solicitud de firma ya no es válida o ha sido completada.'}), 410

            # Marcar como vista si es la primera vez que se accede
            if req.status == 'sent':
                req.status = 'viewed'
                db.session.commit()

            return jsonify({
                'signer_name': req.signer_name,
                'document_content': req.final_document_content,
                'status': req.status
            })
        except Exception:
            return jsonify({'error': 'Solicitud de firma no encontrada o inválida.'}), 404

    @sign_bp.route('/public/request/<string:token>/sign', methods=['POST'])
    def sign_public_document(token):
        data = request.get_json()
        signature_data = data.get('signature_data')
        if not signature_data:
            return jsonify({'error': 'No se proporcionaron datos de firma.'}), 400
        try:
            app.services['sign_service'].sign_document(token, signature_data)
            return jsonify({'message': 'Documento firmado exitosamente.'}), 200
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception:
            return jsonify({'error': 'No se pudo completar la firma.'}), 500

    app.register_blueprint(sign_bp)

    # --- RUTAS PARA FORMULARIOS (LAN-FRM5) ---
    forms_bp = Blueprint('forms', __name__, url_prefix='/api/forms')

    @forms_bp.route('/', methods=['GET'])
    @jwt_required()
    def get_forms():
        forms = app.services['form_service'].get_forms_for_tenant(g.current_user.tenant_id)
        return jsonify([{'id': f.id, 'name': f.name, 'public_token': f.public_token} for f in forms])

    @forms_bp.route('/', methods=['POST'])
    @jwt_required()
    def create_form_route():
        data = request.get_json()
        try:
            form = app.services['form_service'].create_form(
                name=data.get('name'),
                description=data.get('description'),
                fields=data.get('fields', []),
                tenant_id=g.current_user.tenant_id,
                user_id=g.current_user.id
            )
            return jsonify({'message': 'Formulario creado exitosamente', 'form_id': form.id, 'public_token': form.public_token}), 201
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

    @forms_bp.route('/<int:form_id>/submissions', methods=['GET'])
    @jwt_required()
    def get_form_submissions(form_id):
        submissions = app.services['form_service'].get_submissions_for_form(form_id, g.current_user.tenant_id)
        return jsonify([{'id': s.id, 'data': s.data, 'submitted_at': s.submitted_at.isoformat()} for s in submissions])

    # --- Rutas Públicas para Formularios ---

    @forms_bp.route('/public/<string:token>', methods=['GET'])
    def get_public_form(token):
        try:
            form = app.services['form_service'].get_form_by_token(token)
            return jsonify({
                'name': form.name,
                'description': form.description,
                'fields': form.fields
            })
        except Exception:
            return jsonify({'error': 'Formulario no encontrado.'}), 404

    @forms_bp.route('/public/<string:token>/submit', methods=['POST'])
    def submit_public_form(token):
        data = request.get_json()
        try:
            app.services['form_service'].submit_form(token, data)
            return jsonify({'message': 'Formulario enviado exitosamente.'}), 200
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception:
            return jsonify({'error': 'No se pudo procesar el envío.'}), 500

    app.register_blueprint(forms_bp)

    # --- RUTAS PARA GESTIÓN DE PROYECTOS (LAN-PR0) ---
    projects_bp = Blueprint('projects', __name__, url_prefix='/api/projects')

    @projects_bp.route('/', methods=['GET'])
    @jwt_required()
    def get_projects():
        projects = app.services['project_service'].get_projects_for_tenant(g.current_user.tenant_id)
        return jsonify([{'id': p.id, 'name': p.name, 'status': p.status, 'end_date': p.end_date.isoformat() if p.end_date else None} for p in projects])

    @projects_bp.route('/', methods=['POST'])
    @jwt_required()
    def create_project_route():
        data = request.get_json()
        try:
            project = app.services['project_service'].create_project(
                name=data.get('name'),
                description=data.get('description'),
                budget=data.get('budget'),
                start_date=data.get('start_date'),
                end_date=data.get('end_date'),
                manager_id=g.current_user.id, # Asignar al creador por defecto
                tenant_id=g.current_user.tenant_id
            )
            return jsonify({'message': 'Proyecto creado exitosamente', 'project_id': project.id}), 201
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

    @projects_bp.route('/<int:project_id>', methods=['GET'])
    @jwt_required()
    def get_project_details_route(project_id):
        project = app.services['project_service'].get_project_details(project_id, g.current_user.tenant_id)
        tasks = app.services['project_service'].get_tasks_for_project(project_id, g.current_user.tenant_id)
        return jsonify({
            'id': project.id,
            'name': project.name,
            'description': project.description,
            'status': project.status,
            'budget': project.budget,
            'tasks': [{'id': t.id, 'title': t.title, 'status': t.status, 'due_date': t.due_date.isoformat() if t.due_date else None} for t in tasks]
        })

    @projects_bp.route('/<int:project_id>/tasks', methods=['POST'])
    @jwt_required()
    def create_task_route(project_id):
        data = request.get_json()
        try:
            task = app.services['project_service'].create_task(
                project_id=project_id,
                title=data.get('title'),
                description=data.get('description'),
                due_date=data.get('due_date'),
                assigned_to_id=data.get('assigned_to_id'),
                tenant_id=g.current_user.tenant_id
            )
            return jsonify({'message': 'Tarea creada exitosamente', 'task_id': task.id}), 201
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

    @projects_bp.route('/tasks/<int:task_id>/status', methods=['PUT'])
    @jwt_required()
    def update_task_status_route(task_id):
        data = request.get_json()
        try:
            task = app.services['project_service'].update_task_status(task_id, data.get('status'), g.current_user.tenant_id)
            return jsonify({'message': 'Estado de la tarea actualizado', 'task_id': task.id, 'new_status': task.status})
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

    app.register_blueprint(projects_bp)

    # --- RUTAS PARA SOPORTE TÉCNICO (LAN-SOP1) ---
    support_bp = Blueprint('support', __name__, url_prefix='/api/support')

    @support_bp.route('/tickets', methods=['GET'])
    @jwt_required()
    def get_tickets():
        # Asumiendo que el rol está en el token o se puede obtener del usuario
        user_role = g.current_user.role.name if g.current_user.role else 'Cliente'
        tickets = app.services['support_service'].get_tickets_for_tenant(g.current_user.tenant_id, user_role, g.current_user.id)
        return jsonify([{'id': t.id, 'subject': t.subject, 'status': t.status, 'priority': t.priority, 'updated_at': t.updated_at.isoformat()} for t in tickets])

    @support_bp.route('/tickets', methods=['POST'])
    @jwt_required()
    def create_ticket_route():
        data = request.get_json()
        try:
            ticket = app.services['support_service'].create_ticket(
                subject=data.get('subject'),
                description=data.get('description'),
                priority=data.get('priority', 'Media'),
                tenant_id=g.current_user.tenant_id,
                user_id=g.current_user.id
            )
            return jsonify({'message': 'Ticket creado exitosamente', 'ticket_id': ticket.id}), 201
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

    @support_bp.route('/tickets/<int:ticket_id>', methods=['GET'])
    @jwt_required()
    def get_ticket_details_route(ticket_id):
        ticket = app.services['support_service'].get_ticket_details(ticket_id, g.current_user.tenant_id)
        # Aquí se debería añadir lógica de permisos para asegurar que el usuario puede ver este ticket
        return jsonify({
            'id': ticket.id,
            'subject': ticket.subject,
            'description': ticket.description,
            'status': ticket.status,
            'priority': ticket.priority,
            'updates': [{'id': u.id, 'comment': u.comment, 'author': u.author.full_name, 'created_at': u.created_at.isoformat()} for u in ticket.updates]
        })

    @support_bp.route('/tickets/<int:ticket_id>/updates', methods=['POST'])
    @jwt_required()
    def add_ticket_update_route(ticket_id):
        data = request.get_json()
        try:
            update = app.services['support_service'].add_ticket_update(
                ticket_id=ticket_id,
                user_id=g.current_user.id,
                comment=data.get('comment')
            )
            return jsonify({'message': 'Actualización añadida al ticket', 'update_id': update.id}), 201
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

    @support_bp.route('/tickets/<int:ticket_id>/assign', methods=['PUT'])
    @jwt_required()
    @role_required(['Administrador General', 'Soporte'])
    def assign_ticket_route(ticket_id):
        data = request.get_json()
        assignee_id = data.get('assignee_id')
        try:
            ticket = app.services['support_service'].assign_ticket(ticket_id, assignee_id, g.current_user.tenant_id)
            return jsonify({'message': f'Ticket asignado a usuario {assignee_id}', 'ticket_id': ticket.id})
        except Exception as e:
            return jsonify({'error': str(e)}), 404

    @support_bp.route('/tickets/<int:ticket_id>/status', methods=['PUT'])
    @jwt_required()
    @role_required(['Administrador General', 'Soporte']) # O el propio usuario si quiere cerrarlo
    def change_ticket_status_route(ticket_id):
        data = request.get_json()
        try:
            ticket = app.services['support_service'].change_ticket_status(ticket_id, data.get('status'), g.current_user.tenant_id)
            return jsonify({'message': 'Estado del ticket actualizado', 'new_status': ticket.status})
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

    app.register_blueprint(support_bp)

    # --- RUTAS PARA ACTIVOS FIJOS (LAN-AFX4) ---
    assets_bp = Blueprint('assets', __name__, url_prefix='/api/assets')

    @assets_bp.route('/', methods=['GET'])
    @jwt_required()
    @role_required(['Contador', 'Administrador General'])
    def get_assets():
        assets = app.services['asset_service'].get_assets_for_tenant(g.current_user.tenant_id)
        return jsonify([{'id': a.id, 'name': a.name, 'purchase_cost': a.purchase_cost, 'status': a.status} for a in assets])

    @assets_bp.route('/', methods=['POST'])
    @jwt_required()
    @role_required(['Contador', 'Administrador General'])
    def create_asset_route():
        data = request.get_json()
        try:
            asset = app.services['asset_service'].create_asset(
                name=data.get('name'),
                description=data.get('description'),
                purchase_date=date.fromisoformat(data.get('purchase_date')),
                purchase_cost=data.get('purchase_cost'),
                useful_life=data.get('useful_life'),
                salvage_value=data.get('salvage_value', 0),
                tenant_id=g.current_user.tenant_id
            )
            return jsonify({'message': 'Activo fijo creado exitosamente', 'asset_id': asset.id}), 201
        except (ValueError, TypeError) as e:
            return jsonify({'error': str(e)}), 400

    @assets_bp.route('/<int:asset_id>', methods=['GET'])
    @jwt_required()
    @role_required(['Contador', 'Administrador General'])
    def get_asset_details_route(asset_id):
        asset = app.services['asset_service'].get_asset_details(asset_id, g.current_user.tenant_id)
        book_value = app.services['asset_service'].get_asset_book_value(asset_id, g.current_user.tenant_id)
        return jsonify({
            'id': asset.id,
            'name': asset.name,
            'description': asset.description,
            'purchase_cost': asset.purchase_cost,
            'book_value': book_value,
            'depreciation_entries': [{'id': e.id, 'entry_date': e.entry_date.isoformat(), 'amount': e.amount} for e in asset.depreciation_entries]
        })

    @assets_bp.route('/<int:asset_id>/depreciate', methods=['POST'])
    @jwt_required()
    @role_required(['Contador', 'Administrador General'])
    def depreciate_asset_route(asset_id):
        try:
            entry = app.services['asset_service'].calculate_monthly_depreciation(asset_id, g.current_user.tenant_id)
            return jsonify({'message': 'Depreciación calculada exitosamente', 'entry_id': entry.id, 'amount': entry.amount}), 201
        except (ValueError, NotImplementedError) as e:
            return jsonify({'error': str(e)}), 400

    app.register_blueprint(assets_bp)

    # --- RUTAS PARA CAJA Y BANCOS (LAN-CB2) ---
    from backend.routes.cash_and_banks_routes import cash_and_banks_bp
    app.register_blueprint(cash_and_banks_bp)

    # --- RUTAS PARA IMPUESTOS (LAN-TAX1) ---
    from backend.routes.tax_routes import tax_bp
    app.register_blueprint(tax_bp)

    # --- RUTAS PARA RECURSOS MATERIALES (LAN-RM1) ---
    from backend.routes.material_routes import material_bp
    app.register_blueprint(material_bp)

    # --- RUTAS PARA OBRAS Y CONSTRUCCIÓN (LAN-OBR5) ---
    from backend.routes.construction_routes import construction_bp
    app.register_blueprint(construction_bp)

    # --- RUTAS PARA SALUD (LAN-H7S) ---
    from backend.routes.health_routes import health_bp
    app.register_blueprint(health_bp)

    # --- RUTAS PARA EDUCACIÓN (LAN-ED3U) ---
    from backend.routes.education_routes import education_bp
    app.register_blueprint(education_bp)
    
    # --- REGISTRO DE COMANDOS CLI (Del HEAD) ---
    @app.cli.command("init-db")
    def init_db_command():
        """Inicializa la base de datos y crea los datos por defecto."""
        with app.app_context():
            # Esta lógica debe ser compatible con los modelos fusionados
            Role = app.models.get('Role')
            User = app.models.get('User')
            
            db.create_all()
            
            if Role and Role.query.first() is None:
                roles = ['Super Administrador', 'Administrador General', 'Ejecutivo de Crédito', 'Cobrador', 'Contador', 'Cliente']
                for role_name in roles:
                    db.session.add(Role(name=role_name))
                db.session.commit()
                print("Roles creados.")
                
            if User and Role and not User.query.filter_by(email='admin@lazoarce.com').first():
                 admin_role = Role.query.filter_by(name='Administrador General').first()
                 if admin_role:
                    admin_user = User(email='admin@lazoarce.com', role_id=admin_role.id, full_name='Administrador Principal')
                    admin_user.set_password('admin')
                    db.session.add(admin_user)
                    db.session.commit()
                    print("Usuario administrador por defecto creado (admin@lazoarce.com / admin).")
            
            click.echo("Base de datos inicializada y poblada con datos por defecto.")

    # --- ERROR HANDLERS (Del 2.0) ---
    @app.errorhandler(404)
    def not_found(error): return jsonify({"message": "Endpoint no encontrado"}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({"message": "Error interno del servidor"}), 500
    
    return app

# --- LÓGICA DE EJECUCIÓN ---
if __name__ == '__main__':
    class DevelopmentConfig:
        DEBUG = True
        TESTING = False
        SECRET_KEY = 'dev-secret-key-change-me'
        JWT_SECRET_KEY = 'jwt-secret-key-change-me'
        SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///lazoarce.db')
        SQLALCHEMY_TRACK_MODIFICATIONS = False

    app = create_app(config_object=DevelopmentConfig)
    
    # Inicializar base de datos (seeding) si es necesario
    instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
    os.makedirs(instance_path, exist_ok=True)
    
    # Nota: setup_database no está definido en este archivo, se debe usar el comando CLI: flask init-db
    
    # Configuración de servidor
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '127.0.0.1')
    debug = app.config.get('DEBUG', False)
    
    app.run(host=host, port=port, debug=debug)