from .models import db, EmployeeOnboarding, OnboardingTemplate, OnboardingStep

def assign_onboarding_template_to_employee(employee_id, template_id):
    """
    Assigns an onboarding template to a new employee.
    """
    # Check if a template is already assigned
    existing = EmployeeOnboarding.query.filter_by(employee_id=employee_id).first()
    if existing:
        raise ValueError(f"El empleado {employee_id} ya tiene un proceso de onboarding asignado.")

    new_onboarding = EmployeeOnboarding(
        employee_id=employee_id,
        template_id=template_id,
        status='Pendiente',
        completed_steps=[]
    )
    db.session.add(new_onboarding)
    return new_onboarding

def get_employee_onboarding_status(employee_id):
    """
    Retrieves the onboarding status and checklist for an employee.
    """
    onboarding = EmployeeOnboarding.query.filter_by(employee_id=employee_id).first_or_404()

    template = onboarding.template
    steps = template.steps.order_by(OnboardingStep.order).all()

    checklist = [
        {
            "step_id": step.id,
            "name": step.name,
            "description": step.description,
            "type": step.step_type,
            "resource_link": step.resource_link,
            "completed": step.id in onboarding.completed_steps
        } for step in steps
    ]

    return {
        "status": onboarding.status,
        "checklist": checklist
    }

def complete_onboarding_step(employee_id, step_id):
    """
    Marks an onboarding step as completed for an employee.
    """
    onboarding = EmployeeOnboarding.query.filter_by(employee_id=employee_id).first_or_404()

    if step_id not in onboarding.completed_steps:
        # This is a naive way to handle JSON updates.
        # For production, a more robust method would be needed, especially on PostgreSQL.
        new_completed_steps = list(onboarding.completed_steps)
        new_completed_steps.append(step_id)
        onboarding.completed_steps = new_completed_steps

    # Check if all steps are completed
    all_step_ids = {step.id for step in onboarding.template.steps}
    if all_step_ids.issubset(set(onboarding.completed_steps)):
        onboarding.status = 'Completado'

    elif onboarding.completed_steps:
        onboarding.status = 'En Progreso'

    return onboarding
