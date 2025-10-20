[Contenido truncado por brevedad]

01

    @app.route('/api/campaigns/<int:campaign_id>/send', methods=['POST'])
    @jwt_required()
    def send_campaign(campaign_id):
        claims = get_jwt()
        if 'Admin' not in claims.get('roles', []):
            return jsonify({"message": "Acceso no autorizado"}), 403

        campaign = Campaign.query.get_or_404(campaign_id)
        if campaign.status == 'Sent':
            return jsonify({"message": "Esta campaña ya ha sido enviada."}), 400

        members = campaign.mailing_list.members
        for member in members:
            # In a real app, you'd pass more context data if needed
            notification_service.send_notification(member.id, campaign.template.slug, {})

        campaign.status = 'Sent'
        campaign.sent_at = datetime.utcnow()
        db.session.commit()

        return jsonify({"message": f"Campaña '{campaign.name}' enviada a {len(members)} miembros."})

    # --- HELPDESK / TICKETING API ROUTES ---

    @app.route('/api/tickets', methods=['GET', 'POST'])
    @jwt_required()
    def handle_tickets():
        current_user = User.query.filter_by(email=get_jwt_identity()).first()
        claims = get_jwt()
        user_roles = claims.get('roles', [])

        if request.method == 'POST':
            data = request.get_json()
            new_ticket = Ticket(
                subject=data['subject'],
                user_id=current_user.id,
                priority=data.get('priority', 'Normal')
            )
            # The first comment is the ticket description
            first_comment = TicketComment(
                ticket=new_ticket,
                user_id=current_user.id,
                comment_text=data['description']
            )
            db.session.add(new_ticket)
            db.session.add(first_comment)
            db.session.commit()
            return jsonify(new_ticket.to_dict()), 201

        # GET request
        if 'Admin' in user_roles or 'Soporte' in user_roles: # Assuming a 'Soporte' role
            tickets = Ticket.query.order_by(Ticket.updated_at.desc()).all()
        else: # Regular client
            tickets = Ticket.query.filter_by(user_id=current_user.id).order_by(Ticket.updated_at.desc()).all()

        return jsonify([t.to_dict() for t in tickets])

    @app.route('/api/tickets/<int:ticket_id>', methods=['GET', 'PUT'])
    @jwt_required()
    def handle_ticket(ticket_id):
        ticket = Ticket.query.get_or_404(ticket_id)
        # Security checks...

        if request.method == 'GET':
            return jsonify(ticket.to_dict())

        if request.method == 'PUT':
            # Logic to update status, priority, assignment for support staff
            pass

    @app.route('/api/tickets/<int:ticket_id>/comments', methods=['GET', 'POST'])
    @jwt_required()
    def handle_ticket_comments(ticket_id):
        ticket = Ticket.query.get_or_404(ticket_id)
        # Security checks...

        if request.method == 'POST':
            data = request.get_json()
            current_user = User.query.filter_by(email=get_jwt_identity()).first()
            new_comment = TicketComment(
                ticket_id=ticket.id,
                user_id=current_user.id,
                comment_text=data['comment_text']
            )
            ticket.updated_at = datetime.utcnow() # Touch the ticket to bump it up
            db.session.add(new_comment)
            db.session.commit()
            return jsonify(new_comment.to_dict()), 201

        # GET request
        comments = ticket.comments.order_by(TicketComment.timestamp.asc()).all()
        return jsonify([c.to_dict() for c in comments])

    # --- AUDIT LOG API ROUTE ---
    @app.route('/api/audit-logs', methods=['GET'])
    @jwt_required()
    def get_audit_logs():
        claims = get_jwt()
        if 'Admin' not in claims.get('roles', []):
            return jsonify({"message": "Acceso no autorizado"}), 403

        logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).all()
        return jsonify([log.to_dict() for log in logs])

    # --- TESTING UTILITIES ---
    @app.route('/api/testing/generate-dummy-data', methods=['POST'])
    @jwt_required()
    def generate_dummy_data():
        claims = get_jwt()
        if 'Admin' not in claims.get('roles', []):
            return jsonify({"message": "Acceso no autorizado"}), 403

        try:
            # You can expand this logic to be more sophisticated
            from random import randint, choice

            # Create a dummy user
            dummy_email = f"testuser{randint(1000, 9999)}@lazoarce.com"
            client_role = Role.query.filter_by(name='Cliente').first()
            new_user = User(email=dummy_email, full_name=f"Cliente de Prueba {randint(1,100)}", dui="00000000-0", nit="0000-000000-000-0", role_id=client_role.id)
            new_user.set_password("testing123")
            db.session.add(new_user)
            db.session.flush() # Flush to get the new_user.id

            # Create a loan application for the user
            product = LoanProduct.query.first()
            if not product: return jsonify({"message": "No hay productos de préstamo para crear datos de prueba."}), 400

            new_app = LoanApplication(user_id=new_user.id, product_id=product.id, amount_requested=randint(1000, 5000), term_months=12, commission_calculation_method='A', status='Desembolsada', decision_date=datetime.utcnow())
            db.session.add(new_app)
            db.session.flush() # Flush to get new_app.id

            # Add a payment
            employee = Employee.query.first()
            if employee:
                new_payment = Payment(application_id=new_app.id, amount_paid=new_app.monthly_payment, payment_date=date.today(), registered_by_id=employee.id)
                db.session.add(new_payment)

            db.session.commit()
            return jsonify({"message": f"Datos de prueba creados para el usuario {dummy_email}."}), 201

        except Exception as e:
            db.session.rollback()
            return jsonify({"message": f"Error generando datos de prueba: {str(e)}"}), 500

    return app

def setup_database(app):
    """Creates database tables and seeds initial data."""
    with app.app_context():
        db.create_all()
        if not Role.query.first():
            roles = [
                Role(name='Admin'),
                Role(name='Cliente'),
                Role(name='Contador'),
                Role(name='Ejecutivo de Crédito'),
                Role(name='Cobrador')
            ]
            db.session.bulk_save_objects(roles)
            db.session.commit()
        if not User.query.filter_by(email='admin@lazoarce.com').first():
            admin_role = Role.query.filter_by(name='Admin').first()
            admin_user = User(email='admin@lazoarce.com', role_id=admin_role.id, full_name='Admin Lazo Arce')
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            db.session.commit()
        if not LoanProduct.query.first():
            # Add a default product for testing
            default_product = LoanProduct(
                name="Préstamo Personal Clásico",
                min_amount=500.00,
                max_amount=10000.00,
                interest_rate=0.12, # 12% annual
                commission_rate=0.01, # 1% monthly
                term_months=36
            )
            db.session.add(default_product)
            db.session.commit()

        if not Account.query.first():
            # Seed the chart of accounts
            accounts = [
                # Assets
                Account(name='Caja', category='Asset', normal_balance='Debit'),
                Account(name='Bancos', category='Asset', normal_balance='Debit'),
                Account(name='Cuentas por Cobrar Clientes', category='Asset', normal_balance='Debit'),
                Account(name='Intereses por Cobrar', category='Asset', normal_balance='Debit'),
                # Liabilities
                Account(name='Préstamos por Pagar', category='Liability', normal_balance='Credit'),
                # Equity
                Account(name='Capital Social', category='Equity', normal_balance='Credit'),
                # Revenue
                Account(name='Ingresos por Intereses', category='Revenue', normal_balance='Credit'),
                Account(name='Ingresos por Comisiones', category='Revenue', normal_balance='Credit'),
            ]
            db.session.bulk_save_objects(accounts)
            db.session.commit()

        if not NotificationTemplate.query.first():
            templates = [
                NotificationTemplate(
                    slug='loan-approved',
                    subject='¡Tu préstamo ha sido aprobado!',
                    body='Hola {customer_name},\n\nNos complace informarte que tu solicitud de préstamo por un monto de ${amount} ha sido aprobada. ¡Felicidades!\n\nSaludos,\nEl equipo de LAZOARCE UNIVERSAL'
                ),
                NotificationTemplate(
                    slug='loan-rejected',
                    subject='Actualización sobre tu solicitud de préstamo',
                    body='Hola {customer_name},\n\nDespués de una cuidadosa revisión, lamentamos informarte que no podemos aprobar tu solicitud de préstamo en este momento.\n\nGracias por tu interés.\n\nSaludos,\nEl equipo de LAZOARCE UNIVERSAL'
                ),
                NotificationTemplate(
                    slug='payment-reminder',
                    subject='Recordatorio de Pago',
                    body='Hola {customer_name},\n\nEste es un recordatorio amistoso de que tu próxima cuota de ${payment_amount} para tu préstamo vence el {due_date}.\n\nSaludos,\nEl equipo de LAZOARCE UNIVERSAL'
                )
            ]
            db.session.bulk_save_objects(templates)
            db.session.commit()

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        setup_database(app)
    app.run(debug=True, port=5001)