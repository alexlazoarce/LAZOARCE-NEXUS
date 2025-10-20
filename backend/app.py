import os
import click
from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from flask_jwt_extended import create_access_token, JWTManager, jwt_required, get_jwt_identity, verify_jwt_in_request
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from functools import wraps
from datetime import datetime
from io import BytesIO

# Módulos locales y extensiones
from .database import db
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

def create_app(config_object=None):
    """
    Application Factory para crear y configurar la aplicación Flask.
    """
    app = Flask(__name__)
    CORS(app)

    # Cargar variables de entorno
    load_dotenv()

    # --- CONFIGURACIÓN ---
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'un-secreto-muy-seguro'),
        SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL', 'sqlite:///lazoarce.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        JWT_SECRET_KEY=os.environ.get('JWT_SECRET_KEY', 'otro-secreto-muy-seguro'),
        UPLOAD_FOLDER='uploads'
    )

    if config_object:
        app.config.from_object(config_object)

    # --- INICIALIZACIÓN DE EXTENSIONES ---
    db.init_app(app)
    jwt = JWTManager(app)

    # Importar modelos aquí para evitar dependencias circulares
    from .models import Role, User, LoanProduct, LoanApplication, Account, Transaction, JournalEntry, Cliente, ContratoIntegracion, ProductoCredito, Empleado, Planilla

    # --- DECORADORES DE AUTORIZACIÓN ---
    def role_required(required_roles):
        if not isinstance(required_roles, list):
            required_roles = [required_roles]

        def decorator(fn):
            @wraps(fn)
            def wrapper(*args, **kwargs):
                verify_jwt_in_request()
                user_email = get_jwt_identity()
                user = User.query.filter_by(email=user_email).first()
                if not user or user.role.name not in required_roles:
                    return jsonify({"msg": "Acceso no autorizado para este rol"}), 403
                return fn(*args, **kwargs)
            return wrapper
        return decorator

    # --- REGISTRO DE RUTAS ---
    @app.route('/')
    def index():
        return jsonify({"message": "Servidor del Sistema de Gestión Financiera en funcionamiento."})

    @app.route('/api/register', methods=['POST'])
    def register():
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
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        if not email or not password:
            return jsonify({"msg": "Email y contraseña son requeridos"}), 400
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            access_token = create_access_token(identity=user.email)
            return jsonify(access_token=access_token)
        return jsonify({"msg": "Credenciales inválidas"}), 401

    @app.route('/api/admin/test')
    @jwt_required()
    @role_required('Administrador General')
    def admin_test_route():
        user_email = get_jwt_identity()
        return jsonify(logged_in_as=user_email), 200

    # --- API DE CLIENTES (NUEVO CON FIRMA) ---
    @app.route('/api/clientes/nuevo', methods=['POST'])
    @jwt_required()
    def crear_nuevo_cliente():
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
                telefono=data['telefono'],
                direccion=data['direccion'],
                contrato_integracion_id=contrato_id,
                firma_electronica_id=resultado_firma['firma_id'],
                estado='ACTIVO'
            )
            db.session.add(cliente)
            db.session.commit()

            return jsonify({
                'success': True,
                'cliente_id': cliente.id,
                'contrato_id': contrato_id,
                'firma_id': resultado_firma['firma_id'],
                'certificado_id': resultado_firma['certificado_id'],
                'mensaje': 'Cliente creado y contrato firmado exitosamente con validación completa.'
            }), 201

        except Exception as e:
            db.session.rollback()
            print(f"ERROR FATAL en /api/clientes/nuevo: {str(e)}")
            return jsonify({'error': 'Ocurrió un error inesperado en el servidor.', 'detalle': str(e)}), 500

    # --- API DE DOCUMENTOS Y FIRMA MANUAL ---
    @app.route('/api/contratos/<string:contrato_id>/descargar', methods=['GET'])
    @jwt_required()
    def descargar_contrato_pdf(contrato_id):
        contrato = ContratoIntegracion.query.filter_by(contrato_id=contrato_id).first_or_404()
        pdf_bytes = convert_html_to_pdf(contrato.contrato_html)
        if not pdf_bytes:
            return jsonify({"error": "No se pudo generar el PDF del contrato."}), 500
        response = make_response(pdf_bytes)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=contrato_{contrato_id}.pdf'
        return response

    @app.route('/api/contratos/<string:contrato_id>/subir-firmado', methods=['POST'])
    @jwt_required()
    def subir_contrato_firmado(contrato_id):
        contrato = ContratoIntegracion.query.filter_by(contrato_id=contrato_id).first_or_404()
        if 'file' not in request.files:
            return jsonify({'error': 'No se encontró el archivo'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Ningún archivo seleccionado'}), 400
        if file:
            filename = f"manual_{contrato_id}_{file.filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])
            file.save(filepath)
            contrato.documento_firmado_url = filepath
            contrato.estado = 'PENDIENTE_VALIDACION_MANUAL'
            contrato.tipo_firma = 'MANUAL'
            db.session.commit()
            return jsonify({'success': True, 'mensaje': 'Documento subido, pendiente de validación.'})
        return jsonify({'error': 'Error al subir el archivo'}), 500

    @app.route('/api/contratos/<string:contrato_id>/validar-manual', methods=['POST'])
    @jwt_required()
    @role_required(['Administrador General', 'Super Administrador'])
    def validar_contrato_manual(contrato_id):
        contrato = ContratoIntegracion.query.filter_by(contrato_id=contrato_id).first_or_404()
        if contrato.estado != 'PENDIENTE_VALIDACION_MANUAL':
            return jsonify({'error': 'Este contrato no está pendiente de validación manual.'}), 400
        data = request.get_json()
        es_valido = data.get('es_valido', False)
        if es_valido:
            contrato.estado = 'FIRMADO_MANUALMENTE'
            contrato.fecha_firma = datetime.utcnow()
            cliente = Cliente.query.filter_by(contrato_integracion_id=contrato.contrato_id).first()
            if cliente:
                cliente.estado = 'ACTIVO'
            mensaje = 'Contrato validado y aceptado.'
        else:
            contrato.estado = 'RECHAZADO'
            mensaje = 'El contrato ha sido rechazado.'
        db.session.commit()
        return jsonify({'success': True, 'mensaje': mensaje})

    # --- API DE PERFIL DE USUARIO ---
    @app.route('/api/profile', methods=['GET'])
    @jwt_required()
    def get_profile():
        user_email = get_jwt_identity()
        user = User.query.filter_by(email=user_email).first_or_404()
        return jsonify({
            "email": user.email,
            "full_name": user.full_name,
            "dui": user.dui,
            "nit": user.nit,
            "role": user.role.name
        })

    @app.route('/api/profile', methods=['PUT'])
    @jwt_required()
    def update_profile():
        user_email = get_jwt_identity()
        user = User.query.filter_by(email=user_email).first_or_404()
        data = request.get_json()
        new_dui = data.get('dui')
        if new_dui and new_dui != user.dui and User.query.filter_by(dui=new_dui).first():
            return jsonify({"msg": "El DUI ya está registrado por otro usuario."}), 409
        new_nit = data.get('nit')
        if new_nit and new_nit != user.nit and User.query.filter_by(nit=new_nit).first():
            return jsonify({"msg": "El NIT ya está registrado por otro usuario."}), 409
        user.full_name = data.get('full_name', user.full_name)
        user.dui = new_dui or user.dui
        user.nit = new_nit or user.nit
        try:
            db.session.commit()
            return jsonify({"msg": "Perfil actualizado exitosamente."})
        except Exception:
            db.session.rollback()
            return jsonify({"msg": "Error al actualizar el perfil."}), 500

    # --- API PARA PRODUCTOS DE PRÉSTAMO (CRUD - Solo Admin) ---
    @app.route('/api/products', methods=['POST'])
    @jwt_required()
    @role_required('Administrador General')
    def create_loan_product():
        data = request.get_json()
        try:
            new_product = LoanProduct(
                name=data['name'],
                loan_type=data['loan_type'],
                min_amount=float(data['min_amount']),
                max_amount=float(data['max_amount']),
                default_interest_rate=float(data['default_interest_rate']),
                default_admin_commission=float(data['default_admin_commission'])
            )
            db.session.add(new_product)
            db.session.commit()
            return jsonify({"msg": "Producto de préstamo creado exitosamente", "product_id": new_product.id}), 201
        except (KeyError, ValueError):
            return jsonify({"msg": "Datos inválidos o incompletos."}), 400

    @app.route('/api/products', methods=['GET'])
    @jwt_required()
    def get_loan_products():
        products = LoanProduct.query.filter_by(is_active=True).all()
        return jsonify([{
            "id": p.id,
            "name": p.name,
            "loan_type": p.loan_type,
            "min_amount": p.min_amount,
            "max_amount": p.max_amount,
            "default_interest_rate": p.default_interest_rate,
            "default_admin_commission": p.default_admin_commission
        } for p in products])

    @app.route('/api/products/<int:product_id>', methods=['PUT'])
    @jwt_required()
    @role_required('Administrador General')
    def update_loan_product(product_id):
        product = LoanProduct.query.get_or_404(product_id)
        data = request.get_json()
        try:
            product.name = data.get('name', product.name)
            product.loan_type = data.get('loan_type', product.loan_type)
            product.min_amount = float(data.get('min_amount', product.min_amount))
            product.max_amount = float(data.get('max_amount', product.max_amount))
            product.default_interest_rate = float(data.get('default_interest_rate', product.default_interest_rate))
            product.default_admin_commission = float(data.get('default_admin_commission', product.default_admin_commission))
            db.session.commit()
            return jsonify({"msg": "Producto actualizado exitosamente."})
        except ValueError:
            return jsonify({"msg": "Datos inválidos."}), 400

    @app.route('/api/products/<int:product_id>', methods=['DELETE'])
    @jwt_required()
    @role_required('Administrador General')
    def deactivate_loan_product(product_id):
        product = LoanProduct.query.get_or_404(product_id)
        product.is_active = False
        db.session.commit()
        return jsonify({"msg": "Producto desactivado exitosamente."})

    # --- API PARA SOLICITUDES DE PRÉSTAMO ---
    @app.route('/api/applications', methods=['POST'])
    @jwt_required()
    def submit_loan_application():
        user_email = get_jwt_identity()
        user = User.query.filter_by(email=user_email).first_or_404()
        data = request.get_json()
        try:
            product_id = int(data['product_id'])
            requested_amount = float(data['requested_amount'])
            requested_term = int(data['requested_term'])
            product = LoanProduct.query.get(product_id)
            if not product or not product.is_active:
                return jsonify({"msg": "Producto de préstamo no válido o inactivo."}), 400
            if not (product.min_amount <= requested_amount <= product.max_amount):
                return jsonify({"msg": f"El monto solicitado debe estar entre {product.min_amount} y {product.max_amount}."}), 400
            new_application = LoanApplication(
                user_id=user.id,
                product_id=product_id,
                requested_amount=requested_amount,
                requested_term=requested_term,
                status='Solicitud Recibida'
            )
            db.session.add(new_application)
            db.session.commit()
            return jsonify({"msg": "Solicitud de préstamo enviada exitosamente.", "application_id": new_application.id}), 201
        except (KeyError, ValueError):
            return jsonify({"msg": "Datos inválidos o incompletos."}), 400

    @app.route('/api/applications', methods=['GET'])
    @jwt_required()
    def get_loan_applications():
        user_email = get_jwt_identity()
        user = User.query.filter_by(email=user_email).first_or_404()
        if user.role.name in ['Administrador General', 'Ejecutivo de Crédito', 'Super Administrador']:
            applications = LoanApplication.query.order_by(LoanApplication.application_date.desc()).all()
        else:
            applications = LoanApplication.query.filter_by(user_id=user.id).order_by(LoanApplication.application_date.desc()).all()
        return jsonify([{
            "id": app.id,
            "applicant_email": app.applicant.email,
            "product_name": app.product.name,
            "requested_amount": app.requested_amount,
            "requested_term": app.requested_term,
            "status": app.status,
            "application_date": app.application_date.isoformat()
        } for app in applications])

    @app.route('/api/applications/<int:application_id>/status', methods=['PUT'])
    @jwt_required()
    @role_required('Administrador General')
    def update_application_status(application_id):
        application = LoanApplication.query.get_or_404(application_id)
        data = request.get_json()
        new_status = data.get('status')
        if not new_status:
            return jsonify({"msg": "El campo 'status' es requerido."}), 400
        original_status = application.status
        if original_status == new_status:
            return jsonify({"msg": f"La solicitud ya se encuentra en el estado '{new_status}'."})
        application.status = new_status
        if new_status == 'Desembolsado':
            try:
                entries = [
                    {'account_code': '1201', 'debit': application.requested_amount, 'credit': 0},
                    {'account_code': '1102', 'debit': 0, 'credit': application.requested_amount}
                ]
                description = f"Desembolso de prestamo ID: {application.id}"
                create_journal_entry(description, entries)
                print(f"Asiento de diario creado para el desembolso del prestamo {application.id}")
            except Exception as e:
                db.session.rollback()
                return jsonify({"msg": f"Error al crear el asiento contable: {str(e)}"}), 500
        db.session.commit()
        return jsonify({"msg": f"Estado de la solicitud {application_id} actualizado a '{new_status}'."})

    # --- API DE CONTABILIDAD ---
    @app.route('/api/accounting/journal', methods=['GET'])
    @jwt_required()
    @role_required(['Contador', 'Administrador General'])
    def get_journal():
        transactions = Transaction.query.order_by(Transaction.date.desc()).all()
        result = []
        for t in transactions:
            entries = []
            for e in t.entries:
                entries.append({
                    "account_code": e.account.code,
                    "account_name": e.account.name,
                    "debit": e.debit,
                    "credit": e.credit
                })
            result.append({
                "transaction_id": t.id,
                "date": t.date.isoformat(),
                "description": t.description,
                "entries": entries
            })
        return jsonify(result)

    @app.route('/api/applications/<int:application_id>/contract-data', methods=['GET'])
    @jwt_required()
    def get_contract_data(application_id):
        user_email = get_jwt_identity()
        user = User.query.filter_by(email=user_email).first_or_404()
        application = LoanApplication.query.get_or_404(application_id)
        if application.user_id != user.id and user.role.name not in ['Administrador General', 'Super Administrador']:
            return jsonify({"msg": "Acceso no autorizado a esta solicitud."}), 403
        if application.status != 'Aprobado':
            return jsonify({"msg": "El contrato solo puede generarse para préstamos aprobados."}), 403
        applicant_data = {
            "full_name": application.applicant.full_name,
            "dui": application.applicant.dui,
            "nit": application.applicant.nit,
            "email": application.applicant.email
        }
        loan_details = {
            "application_id": application.id,
            "product_name": application.product.name,
            "requested_amount": application.requested_amount,
            "requested_term": application.requested_term,
            "interest_rate": application.product.default_interest_rate,
            "admin_commission": application.product.default_admin_commission,
            "application_date": application.application_date.isoformat()
        }
        company_info = {
            "name": "GRUPO LAZO ARCE S.A.S. DE C.V.",
            "nit": "0524-150825-101-2",
            "nrc": "369047-1",
            "address": "Dirección de la empresa, San Salvador",
            "contact": "support@lazoarce.com"
        }
        temp_product = ProductoCredito(
            tasa_interes_anual=application.product.default_interest_rate * 12,
            comision_administracion=application.product.default_admin_commission / 100,
            comision_apertura=0.0,
            seguro=0.0,
            comisiones_se_descuentan_capital=False,
            comisiones_se_agregan_capital=False,
            aplicar_tea=False
        )
        new_amortization_data = calcular_prestamo_completo(
            monto_solicitado=application.requested_amount,
            producto=temp_product,
            plazo_meses=application.requested_term
        )
        remapped_table = []
        if "tabla_amortizacion" in new_amortization_data:
            for row in new_amortization_data["tabla_amortizacion"]:
                remapped_table.append({
                    'Mes': row['mes'],
                    'Fecha Vencimiento': row['fecha_vencimiento'],
                    'Saldo Inicial': row['saldo_inicial'],
                    'Interes': row['interes'],
                    'Com. Adm.': row['comision_administracion'],
                    'Amortizacion': row['amortizacion'],
                    'Cuota': row['cuota_total']
                })
        amortization_data_for_pdf = {
            "summary": new_amortization_data.get("resumen_costos", {}),
            "amortization_table": remapped_table
        }
        contract_data = {
            "company": company_info,
            "client": applicant_data,
            "loan": loan_details,
            "amortization": amortization_data_for_pdf
        }
        return jsonify(contract_data)

    @app.route('/api/applications/<int:application_id>/contract.pdf')
    @jwt_required()
    def download_contract_pdf(application_id):
        user_email = get_jwt_identity()
        user = User.query.filter_by(email=user_email).first_or_404()
        application = LoanApplication.query.get_or_404(application_id)
        if application.user_id != user.id and user.role.name not in ['Administrador General', 'Super Administrador']:
            return jsonify({"msg": "Acceso no autorizado."}), 403
        if application.status != 'Aprobado':
            return jsonify({"msg": "El contrato solo puede generarse para préstamos aprobados."}), 403
        contract_data_response = get_contract_data(application_id)
        contract_data = contract_data_response.get_json()
        pdf_bytes = create_contract_pdf(contract_data)
        response = make_response(pdf_bytes)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=contrato_{application_id}.pdf'
        return response

    # --- API DE PLANILLAS (PAYROLL) ---
    @app.route('/api/payroll/calculate', methods=['POST'])
    @jwt_required()
    @role_required(['Contador', 'Administrador General'])
    def calculate_payroll_for_employee():
        data = request.get_json()
        empleado_id = data.get('empleado_id')
        if not empleado_id:
            return jsonify({'error': 'El campo empleado_id es requerido.'}), 400
        empleado = Empleado.query.get(empleado_id)
        if not empleado:
            return jsonify({'error': 'Empleado no encontrado.'}), 404
        resultado_calculo = calcular_planilla(empleado.salario_base)
        if not resultado_calculo.get('success'):
            return jsonify({'error': 'Error al calcular la planilla.', 'detalle': resultado_calculo.get('error')}), 500
        try:
            nueva_planilla = Planilla(
                empleado_id=empleado.id,
                salario_base=resultado_calculo['salario_base'],
                isss=resultado_calculo['isss'],
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

    @app.route('/api/loans/calculate', methods=['POST'])
    @jwt_required()
    def calculate_loan():
        try:
            data = request.get_json()
            monto = float(data.get('monto', 0))
            producto_id = int(data.get('producto_id', 0))
            plazo = int(data.get('plazo_meses', 0))
            comisiones_intereses = data.get('comisiones_generan_intereses', None)
            comisiones_agregan_capital = data.get('comisiones_se_agregan_capital', None)
            comisiones_descuentan_capital = data.get('comisiones_se_descuentan_capital', None)
            aplicar_tea = data.get('aplicar_tea', True)
            if monto <= 0 or plazo <= 0:
                return jsonify({"error": "Monto y plazo deben ser mayores a 0"}), 400
            producto = ProductoCredito.query.get(producto_id)
            if not producto:
                return jsonify({"error": "Producto no encontrado"}), 404
            if comisiones_intereses is not None:
                producto.comisiones_generan_intereses = comisiones_intereses
            if comisiones_agregan_capital is not None:
                producto.comisiones_se_agregan_capital = comisiones_agregan_capital
            if comisiones_descuentan_capital is not None:
                producto.comisiones_se_descuentan_capital = comisiones_descuentan_capital
            if aplicar_tea is not None:
                producto.aplicar_tea = aplicar_tea
            resultado = calcular_prestamo_completo(monto, producto, plazo)
            if "error" in resultado:
                return jsonify(resultado), 400
            return jsonify(resultado)
        except Exception as e:
            return jsonify({"error": f"Error en cálculo: {str(e)}"}), 500

    # --- REGISTRO DE COMANDOS CLI ---
    @app.cli.command("init-db")
    def init_db_command():
        """Inicializa la base de datos y crea los datos por defecto."""
        with app.app_context():
            db.create_all()
            if Role.query.first() is None:
                roles = ['Super Administrador', 'Administrador General', 'Ejecutivo de Crédito', 'Cobrador', 'Contador', 'Cliente']
                for role_name in roles:
                    db.session.add(Role(name=role_name))
                db.session.commit()
                print("Roles creados.")
            if not User.query.filter_by(email='admin@lazoarce.com').first():
                admin_role = Role.query.filter_by(name='Administrador General').first()
                if admin_role:
                    admin_user = User(email='admin@lazoarce.com', role_id=admin_role.id)
                    admin_user.set_password('admin')
                    db.session.add(admin_user)
                    db.session.commit()
                    print("Usuario administrador por defecto creado (admin@lazoarce.com / admin).")
            if not Account.query.first():
                accounts = [
                    {'code': '1101', 'name': 'Caja', 'account_type': 'Activo'},
                    {'code': '1102', 'name': 'Bancos', 'account_type': 'Activo'},
                    {'code': '1201', 'name': 'Cuentas por Cobrar - Préstamos', 'account_type': 'Activo'},
                    {'code': '3101', 'name': 'Capital Social', 'account_type': 'Patrimonio'},
                    {'code': '4101', 'name': 'Ingresos por Intereses', 'account_type': 'Ingreso'},
                ]
                for acc_data in accounts:
                    db.session.add(Account(**acc_data))
                db.session.commit()
                print("Plan de cuentas por defecto creado.")
            if not LoanProduct.query.first():
                default_product = LoanProduct(
                    name='Préstamo de Prueba', loan_type='Personal',
                    min_amount=500, max_amount=10000,
                    default_interest_rate=5, default_admin_commission=1
                )
                db.session.add(default_product)
                db.session.commit()
                print("Producto de prestamo por defecto creado.")
            if not ProductoCredito.query.first():
                default_credit_product = ProductoCredito(
                    nombre='Crédito Avanzado de Prueba',
                    tasa_interes_anual=24.0,
                    comision_apertura=0.02,
                    comision_administracion=0.005,
                    seguro=0.001,
                    plazo_maximo=60,
                    monto_minimo=1000,
                    monto_maximo=50000,
                    comisiones_se_descuentan_capital=True,
                    aplicar_tea=True
                )
                db.session.add(default_credit_product)
                db.session.commit()
                print("Producto de crédito avanzado por defecto creado.")
            if not Empleado.query.first():
                default_empleado = Empleado(
                    nombre='Juan Ejemplo Perez',
                    salario_base=1500.00
                )
                db.session.add(default_empleado)
                db.session.commit()
                print("Empleado de prueba creado.")
            click.echo("Base de datos inicializada y poblada con datos por defecto.")

    return app