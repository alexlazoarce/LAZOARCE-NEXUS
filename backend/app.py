[Contenido truncado por brevedad]

data.get("resumen_costos", {}),
        "amortization_table": remapped_table
    }

    # --- Ensamblar la respuesta final ---
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
    """
    Genera y devuelve el contrato en formato PDF para su descarga.
    """
    # Reutilizar la lógica de obtención de datos del contrato
    # En una aplicación más grande, esto se refactorizaría a una función de servicio
    user_email = get_jwt_identity()
    user = User.query.filter_by(email=user_email).first_or_404()
    application = LoanApplication.query.get_or_404(application_id)

    if application.user_id != user.id and user.role.name not in ['Administrador General', 'Super Administrador']:
        return jsonify({"msg": "Acceso no autorizado."}), 403
    if application.status != 'Aprobado':
        return jsonify({"msg": "El contrato solo puede generarse para préstamos aprobados."}), 403

    # Obtener los datos del contrato llamando a la lógica existente
    # (Esto es una simplificación; idealmente se llamaría a una función interna)
    contract_data_response = get_contract_data(application_id)
    contract_data = contract_data_response.get_json()

    # Generar el PDF en memoria
    pdf_bytes = create_contract_pdf(contract_data)

    # Crear la respuesta HTTP para la descarga del archivo
    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=contrato_{application_id}.pdf'

    return response


# --- API DE PLANILLAS (PAYROLL) ---

@app.route('/api/payroll/calculate', methods=['POST'])
@jwt_required()
@role_required(['Contador', 'Administrador General'])
def calculate_payroll_for_employee():
    """
    Calcula la planilla para un empleado específico y guarda el registro.
    """
    data = request.get_json()
    empleado_id = data.get('empleado_id')

    if not empleado_id:
        return jsonify({'error': 'El campo empleado_id es requerido.'}), 400

    empleado = Empleado.query.get(empleado_id)
    if not empleado:
        return jsonify({'error': 'Empleado no encontrado.'}), 404

    # Realizar el cálculo usando el servicio de planillas
    resultado_calculo = calcular_planilla(empleado.salario_base)

    if not resultado_calculo.get('success'):
        return jsonify({'error': 'Error al calcular la planilla.', 'detalle': resultado_calculo.get('error')}), 500

    try:
        # Crear un nuevo registro de planilla
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

        # Devolver el resultado del cálculo
        return jsonify({
            "success": True,
            "planilla_id": nueva_planilla.id,
            "calculo": resultado_calculo
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error al guardar el registro de la planilla.', 'detalle': str(e)}), 500


@app.route('/api/loans/calculate', methods=['POST'])
@jwt_required()
def calculate_loan():
    """
    Endpoint para cálculo de préstamos con todas las opciones.
    """
    try:
        data = request.get_json()

        # Parámetros obligatorios
        monto = float(data.get('monto', 0))
        producto_id = int(data.get('producto_id', 0))
        plazo = int(data.get('plazo_meses', 0))

        # Opciones de cálculo (opcionales)
        comisiones_intereses = data.get('comisiones_generan_intereses', None)
        comisiones_agregan_capital = data.get('comisiones_se_agregan_capital', None)
        comisiones_descuentan_capital = data.get('comisiones_se_descuentan_capital', None)
        aplicar_tea = data.get('aplicar_tea', True)

        # Validaciones básicas
        if monto <= 0 or plazo <= 0:
            return jsonify({"error": "Monto y plazo deben ser mayores a 0"}), 400

        # Obtener producto y actualizar opciones si se enviaron
        producto = ProductoCredito.query.get(producto_id)
        if not producto:
            return jsonify({"error": "Producto no encontrado"}), 404

        # Sobrescribir configuración si se envió en la petición
        if comisiones_intereses is not None:
            producto.comisiones_generan_intereses = comisiones_intereses
        if comisiones_agregan_capital is not None:
            producto.comisiones_se_agregan_capital = comisiones_agregan_capital
        if comisiones_descuentan_capital is not None:
            producto.comisiones_se_descuentan_capital = comisiones_descuentan_capital
        if aplicar_tea is not None:
            producto.aplicar_tea = aplicar_tea

        # Realizar cálculo
        resultado = calcular_prestamo_completo(monto, producto, plazo)

        if "error" in resultado:
            return jsonify(resultado), 400

        return jsonify(resultado)

    except Exception as e:
        return jsonify({"error": f"Error en cálculo: {str(e)}"}), 500


# --- FUNCIONES AUXILIARES ---
def initialize_database():
    with app.app_context():
        db.create_all()
        if Role.query.first() is None:
            roles = ['Super Administrador', 'Administrador General', 'Ejecutivo de Crédito', 'Cobrador', 'Contador', 'Cliente']
            for role_name in roles:
                db.session.add(Role(name=role_name))
            db.session.commit()
            print("Base de datos y roles inicializados.")

        # Crear usuario admin por defecto si no existe
        if not User.query.filter_by(email='admin@lazoarce.com').first():
            print("Creando usuario administrador por defecto...")
            admin_role = Role.query.filter_by(name='Administrador General').first()
            if admin_role:
                admin_user = User(
                    email='admin@lazoarce.com',
                    role_id=admin_role.id
                )
                admin_user.set_password('admin')
                db.session.add(admin_user)
                db.session.commit()
                print("Usuario administrador creado.")
                print("\n************************************************************")
                print("*** ADVERTENCIA DE SEGURIDAD:                            ***")
                print("*** Se ha creado un usuario administrador por defecto.   ***")
                print("*** Email: admin@lazoarce.com                            ***")
                print("*** Contraseña: admin                                    ***")
                print("*** ¡CAMBIE ESTA CONTRASEÑA EN UN ENTORNO DE PRODUCCIÓN! ***")
                print("************************************************************\n")

        # Poblar el plan de cuentas si está vacío
        if not Account.query.first():
            print("Creando plan de cuentas por defecto...")
            accounts = [
                {'code': '1101', 'name': 'Caja', 'account_type': 'Activo'},
                {'code': '1102', 'name': 'Bancos', 'account_type': 'Activo'},
                {'code': '1201', 'name': 'Cuentas por Cobrar - Préstamos', 'account_type': 'Activo'},
                {'code': '3101', 'name': 'Capital Social', 'account_type': 'Patrimonio'},
                {'code': '4101', 'name': 'Ingresos por Intereses', 'account_type': 'Ingreso'},
            ]
            for acc_data in accounts:
                account = Account(**acc_data)
                db.session.add(account)
            db.session.commit()
            print("Plan de cuentas creado.")

        # Crear producto de préstamo por defecto si no existe
        if not LoanProduct.query.first():
            print("Creando producto de prestamo por defecto...")
            default_product = LoanProduct(
                name='Préstamo de Prueba', loan_type='Personal',
                min_amount=500, max_amount=10000,
                default_interest_rate=5, default_admin_commission=1
            )
            db.session.add(default_product)
            db.session.commit()
            print("Producto de prestamo por defecto creado.")

        # Crear producto de crédito avanzado por defecto si no existe
        if not ProductoCredito.query.first():
            print("Creando producto de crédito avanzado por defecto...")
            default_credit_product = ProductoCredito(
                nombre='Crédito Avanzado de Prueba',
                tasa_interes_anual=24.0,  # 24%
                comision_apertura=0.02, # 2%
                comision_administracion=0.005, # 0.5% mensual
                seguro=0.001, # 0.1% mensual
                plazo_maximo=60,
                monto_minimo=1000,
                monto_maximo=50000,
                comisiones_se_descuentan_capital=True,
                aplicar_tea=True
            )
            db.session.add(default_credit_product)
            db.session.commit()
            print("Producto de crédito avanzado por defecto creado.")

        # Crear un empleado de prueba si no existe
        if not Empleado.query.first():
            print("Creando empleado de prueba por defecto...")
            default_empleado = Empleado(
                nombre='Juan Ejemplo Perez',
                salario_base=1500.00
            )
            db.session.add(default_empleado)
            db.session.commit()
            print("Empleado de prueba creado.")

if __name__ == '__main__':
    initialize_database()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)