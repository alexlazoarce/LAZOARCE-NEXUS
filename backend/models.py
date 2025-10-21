[Contenido truncado por brevedad]

late_id = db.Column(db.Integer, db.ForeignKey('onboarding_template.id'), nullable=False)
    template = db.relationship('OnboardingTemplate')
    status = db.Column(db.String(50), default='Pendiente', nullable=False) # Pendiente, En Progreso, Completado
    completed_steps = db.Column(db.JSON, default=[]) # List of completed step IDs

# --- Recruitment Models (LAN-REC7) ---

class JobVacancy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='Abierta', nullable=False) # Abierta, Cerrada
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_by = db.relationship('User')
    applications = db.relationship('Application', backref='job_vacancy', lazy='dynamic')

class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    full_name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(50), nullable=True)
    resume_url = db.Column(db.String(255), nullable=True)
    applications = db.relationship('Application', backref='candidate', lazy='dynamic')
    __table_args__ = (db.UniqueConstraint('email', 'tenant_id'),)

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'), nullable=False)
    job_vacancy_id = db.Column(db.Integer, db.ForeignKey('job_vacancy.id'), nullable=False)
    application_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    status = db.Column(db.String(50), default='Nuevo', nullable=False) # Nuevo, Revisión, Entrevista, Oferta, Contratado, Rechazado

# --- Subscription Management Models (LAN-SUB1) ---

class SystemModule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    module_code = db.Column(db.String(20), unique=True, nullable=False) # e.g., 'LAN-GP1', 'LAN-REC7'
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)

class TenantSubscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    module_id = db.Column(db.Integer, db.ForeignKey('system_module.id'), nullable=False)
    start_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    end_date = db.Column(db.DateTime, nullable=True) # Null for perpetual or manually managed subscriptions
    status = db.Column(db.String(50), default='active', nullable=False) # active, expired, cancelled

    tenant = db.relationship('Tenant')
    module = db.relationship('SystemModule')
    __table_args__ = (db.UniqueConstraint('tenant_id', 'module_id'),)

# --- Gym Management Models (LAN-GYM1) ---

class GymMembershipPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    duration_days = db.Column(db.Integer, nullable=False) # e.g., 30 for monthly, 90 for quarterly, 365 for annual
    description = db.Column(db.Text, nullable=True)
    members = db.relationship('GymMember', backref='membership_plan', lazy='dynamic')
    __table_args__ = (db.UniqueConstraint('name', 'tenant_id'),)

class GymMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    full_name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    join_date = db.Column(db.Date, nullable=False, default=db.func.current_date())
    membership_plan_id = db.Column(db.Integer, db.ForeignKey('gym_membership_plan.id'), nullable=True)
    membership_start_date = db.Column(db.Date, nullable=True)
    membership_end_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(50), default='active', nullable=False) # active, inactive, frozen
    attendance = db.relationship('ClassAttendance', backref='member', lazy='dynamic', cascade="all, delete-orphan")
    __table_args__ = (db.UniqueConstraint('email', 'tenant_id'),)

class GymClass(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    instructor = db.Column(db.String(100), nullable=True)
    schedule = db.Column(db.String(255), nullable=True) # e.g., "Lunes, Miércoles 18:00 - 19:00"
    capacity = db.Column(db.Integer, nullable=True)
    attendees = db.relationship('ClassAttendance', backref='gym_class', lazy='dynamic', cascade="all, delete-orphan")
    __table_args__ = (db.UniqueConstraint('name', 'schedule', 'tenant_id'),)

class ClassAttendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('gym_class.id'), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey('gym_member.id'), nullable=False)
    attendance_date = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())

# --- Barbershop Management Models (LAN-BAR1) ---

class Stylist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    specialty = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    appointments = db.relationship('Appointment', backref='stylist', lazy='dynamic')
    __table_args__ = (db.UniqueConstraint('name', 'tenant_id'),)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    stylist_id = db.Column(db.Integer, db.ForeignKey('stylist.id'), nullable=False)
    client_name = db.Column(db.String(200), nullable=False)
    client_phone = db.Column(db.String(50), nullable=False)
    client_email = db.Column(db.String(120), nullable=True)
    appointment_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(50), default='scheduled', nullable=False) # scheduled, completed, cancelled, no-show
    booking_fee = db.Column(db.Float, default=0.0)
    fee_paid = db.Column(db.Boolean, default=False)

# --- Automation Models (LAN-AGT5 & LAN-N8N1) ---

class N8nCredential(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    # Encrypted value for the credential. The encryption key should be managed securely.
    encrypted_value = db.Column(db.Text, nullable=False)
    __table_args__ = (db.UniqueConstraint('name', 'tenant_id'),)

class N8nWorkflow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    trigger_event = db.Column(db.String(100), nullable=False, index=True) # e.g., 'whatsapp_message_received'
    workflow_json = db.Column(db.JSON, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    __table_args__ = (db.UniqueConstraint('name', 'tenant_id'),)

# --- Make.com Integration Models (LAN-MKE1) ---

class MakeConnection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    # As with n8n, this would be encrypted in a real implementation.
    encrypted_credentials = db.Column(db.Text, nullable=False)
    __table_args__ = (db.UniqueConstraint('name', 'tenant_id'),)

class MakeScenario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    # The 'blueprint' of the scenario in JSON format.
    scenario_blueprint = db.Column(db.JSON, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    __table_args__ = (db.UniqueConstraint('name', 'tenant_id'),)

# --- Document Management Models (LAN-GD2) ---

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    latest_version_id = db.Column(db.Integer, nullable=True) # Set after first version is created
    versions = db.relationship('DocumentVersion', backref='document', lazy='dynamic', cascade="all, delete-orphan")
    __table_args__ = (db.UniqueConstraint('filename', 'tenant_id'),)

class DocumentVersion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=False)
    version_number = db.Column(db.Integer, nullable=False)
    filepath = db.Column(db.String(512), nullable=False) # Path in the file storage
    uploaded_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    uploaded_by = db.relationship('User')