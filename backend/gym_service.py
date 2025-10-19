# backend/gym_service.py
from datetime import date, timedelta
from backend.models import db, GymMembershipPlan, GymMember, GymClass, ClassAttendance

def create_membership_plan(tenant_id, data):
    """Creates a new gym membership plan for a tenant."""
    new_plan = GymMembershipPlan(
        tenant_id=tenant_id,
        name=data['name'],
        price=data['price'],
        duration_days=data['duration_days'],
        description=data.get('description')
    )
    db.session.add(new_plan)
    db.session.commit()
    return new_plan

def get_membership_plans(tenant_id):
    """Retrieves all membership plans for a tenant."""
    return GymMembershipPlan.query.filter_by(tenant_id=tenant_id).all()

def register_member(tenant_id, data):
    """Registers a new member for a tenant's gym."""
    new_member = GymMember(
        tenant_id=tenant_id,
        full_name=data['full_name'],
        email=data.get('email'),
        phone=data.get('phone')
    )
    db.session.add(new_member)
    db.session.commit()
    return new_member

def get_members(tenant_id):
    """Retrieves all members for a tenant's gym."""
    return GymMember.query.filter_by(tenant_id=tenant_id).order_by(GymMember.full_name).all()

def assign_membership_to_member(tenant_id, member_id, plan_id):
    """Assigns a membership plan to a member and activates it."""
    member = GymMember.query.filter_by(id=member_id, tenant_id=tenant_id).first_or_404()
    plan = GymMembershipPlan.query.filter_by(id=plan_id, tenant_id=tenant_id).first_or_404()

    start_date = date.today()
    end_date = start_date + timedelta(days=plan.duration_days)

    member.membership_plan_id = plan.id
    member.membership_start_date = start_date
    member.membership_end_date = end_date
    member.status = 'active'

    # Here you might add logic to create an invoice or a journal entry for the payment.

    db.session.commit()
    return member

def create_gym_class(tenant_id, data):
    """Creates a new gym class."""
    new_class = GymClass(
        tenant_id=tenant_id,
        name=data['name'],
        instructor=data.get('instructor'),
        schedule=data.get('schedule'),
        capacity=data.get('capacity')
    )
    db.session.add(new_class)
    db.session.commit()
    return new_class

def get_gym_classes(tenant_id):
    """Retrieves all gym classes for a tenant."""
    return GymClass.query.filter_by(tenant_id=tenant_id).order_by(GymClass.name).all()

def record_class_attendance(tenant_id, class_id, member_id):
    """Records a member's attendance to a class."""
    # Ensure both class and member belong to the tenant
    gym_class = GymClass.query.filter_by(id=class_id, tenant_id=tenant_id).first_or_404()
    member = GymMember.query.filter_by(id=member_id, tenant_id=tenant_id).first_or_404()

    new_attendance = ClassAttendance(
        tenant_id=tenant_id,
        class_id=gym_class.id,
        member_id=member.id
    )
    db.session.add(new_attendance)
    db.session.commit()
    return new_attendance
