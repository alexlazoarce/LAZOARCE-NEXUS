[Contenido truncado por brevedad]

rue)

    notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    # Optional: Assign a lead to a specific employee
    # assigned_to_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=True)
    # assigned_to = db.relationship('Employee')
    communication_logs = db.relationship('CommunicationLog', backref='lead', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'status': self.status,
            'source': self.source,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

class CommunicationLog(db.Model):
    """Represents a single interaction with a lead or client."""
    id = db.Column(db.Integer, primary_key=True)

    # Can be linked to a lead, a user, or both if the lead was converted
    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    # The employee who logged the communication
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    employee = db.relationship('Employee')

    # e.g., 'Llamada', 'Email', 'Reunión'
    type = db.Column(db.String(50), nullable=False)
    notes = db.Column(db.Text, nullable=False)

    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

    def to_dict(self):
        return {
            'id': self.id,
            'employee_name': self.employee.full_name,
            'type': self.type,
            'notes': self.notes,
            'timestamp': self.timestamp.isoformat(),
        }

# --- Collections Models ---

class Payment(db.Model):
    """Represents a payment made towards a loan."""
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('loan_application.id'), nullable=False)
    amount_paid = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.Date, nullable=False)

    # e.g., 'Cuota', 'Abono a Capital', 'Cancelación'
    type = db.Column(db.String(50), nullable=False, default='Cuota')

    # The employee who registered the payment
    registered_by_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    registered_by = db.relationship('Employee')

    # Link to the accounting entry for this payment
    journal_entry_id = db.Column(db.Integer, db.ForeignKey('journal_entry.id'), nullable=True)
    journal_entry = db.relationship('JournalEntry')

    def to_dict(self):
        return {
            'id': self.id,
            'application_id': self.application_id,
            'amount_paid': self.amount_paid,
            'payment_date': self.payment_date.isoformat(),
            'type': self.type,
            'registered_by': self.registered_by.full_name,
        }

# --- Notifications Models ---

class NotificationTemplate(db.Model):
    """Stores templates for emails or other notifications."""
    id = db.Column(db.Integer, primary_key=True)
    # A unique, code-friendly identifier, e.g., 'loan-approved'
    slug = db.Column(db.String(50), unique=True, nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False) # Can contain placeholders like {customer_name}
    type = db.Column(db.String(20), nullable=False, default='Email') # 'Email', 'SMS', etc.

    def to_dict(self):
        return {
            'id': self.id,
            'slug': self.slug,
            'subject': self.subject,
            'body': self.body,
            'type': self.type,
        }

# --- Auditing Models ---

class AuditLog(db.Model):
    """Logs critical actions performed in the system."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False) # e.g., 'LOAN_STATUS_CHANGED'
    details = db.Column(db.Text, nullable=True) # e.g., 'Loan 123 status changed from Pending to Approved'
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

    def to_dict(self):
        return {
            'id': self.id,
            'user_email': self.user.email,
            'action': self.action,
            'details': self.details,
            'timestamp': self.timestamp.isoformat(),
        }

class Opportunity(db.Model):
    """Represents a sales opportunity or a deal."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)

    # The value of the potential deal
    amount = db.Column(db.Float, nullable=True)

    # e.g., 'Calificación', 'Propuesta', 'Negociación', 'Ganada', 'Perdida'
    stage = db.Column(db.String(50), nullable=False, default='Calificación')

    close_date = db.Column(db.Date, nullable=True)

    # Link to the original lead and the converted user/client
    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'), nullable=True)
    lead = db.relationship('Lead')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    client = db.relationship('User')

    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'amount': self.amount,
            'stage': self.stage,
            'close_date': self.close_date.isoformat() if self.close_date else None,
            'client_name': self.client.full_name if self.client else (self.lead.full_name if self.lead else None)
        }

# --- Marketing Models ---

mailing_list_members = db.Table('mailing_list_members',
    db.Column('mailing_list_id', db.Integer, db.ForeignKey('mailing_list.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

class MailingList(db.Model):
    """Represents a list of users for marketing campaigns."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)

    members = db.relationship('User', secondary=mailing_list_members, lazy='dynamic',
                              backref=db.backref('mailing_lists', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'member_count': self.members.count()
        }

class Campaign(db.Model):
    """Represents a marketing email campaign."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    subject = db.Column(db.String(255), nullable=False)

    # e.g., 'Draft', 'Scheduled', 'Sent'
    status = db.Column(db.String(50), nullable=False, default='Draft')

    mailing_list_id = db.Column(db.Integer, db.ForeignKey('mailing_list.id'), nullable=False)
    mailing_list = db.relationship('MailingList')

    template_id = db.Column(db.Integer, db.ForeignKey('notification_template.id'), nullable=False)
    template = db.relationship('NotificationTemplate')

    sent_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'subject': self.subject,
            'status': self.status,
            'mailing_list_name': self.mailing_list.name,
            'template_slug': self.template.slug,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
        }

# --- Helpdesk / Ticketing Models ---

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(255), nullable=False)

    # e.g., 'Abierto', 'En Progreso', 'Cerrado'
    status = db.Column(db.String(50), nullable=False, default='Abierto')
    # e.g., 'Baja', 'Normal', 'Alta'
    priority = db.Column(db.String(50), nullable=False, default='Normal')

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=True)

    comments = db.relationship('TicketComment', backref='ticket', lazy='dynamic', cascade="all, delete-orphan")

    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    def to_dict(self):
        return {
            'id': self.id,
            'subject': self.subject,
            'status': self.status,
            'priority': self.priority,
            'created_by': self.created_by_user.full_name,
            'assigned_to': self.assigned_employee.full_name if self.assigned_employee else 'Sin asignar',
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

class TicketComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # User who made the comment
    comment_text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

    def to_dict(self):
        commenter = User.query.get(self.user_id)
        return {
            'id': self.id,
            'commenter_name': commenter.full_name,
            'comment_text': self.comment_text,
            'timestamp': self.timestamp.isoformat()
        }