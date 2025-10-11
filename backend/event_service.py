from .models import db, Flow, LoanApplication, Opportunity
from datetime import datetime

def _execute_create_draft_application(data):
    """
    Action to create a draft loan application from a won opportunity.
    """
    try:
        opportunity_id = data.get('opportunity_id')
        opp = Opportunity.query.get(opportunity_id)
        if not opp or not opp.user_id:
            print(f"ACTION FAILED: Opportunity {opportunity_id} or its user not found.")
            return

        # Check if a loan application already exists for this opportunity/user
        existing_app = LoanApplication.query.filter_by(user_id=opp.user_id, status='Pendiente').first()
        if existing_app:
            print(f"ACTION SKIPPED: User {opp.user_id} already has a pending application.")
            return

        # Find a default product to create the application with
        default_product = db.session.query(Flow).first() # Simplified: using Flow table just to get a product
        if not default_product:
             default_product = db.session.query(Flow).first()
        if not default_product:
            print("ACTION FAILED: No loan products found to create a draft application.")
            return

        new_app = LoanApplication(
            user_id=opp.user_id,
            product_id=default_product.id,
            amount_requested=opp.amount or 1000, # Use opportunity amount or a default
            term_months=12, # Default term
            commission_calculation_method='A',
            status='Pendiente' # Or a new 'Borrador' status if needed
        )
        db.session.add(new_app)
        # The commit is handled by the calling route
        print(f"ACTION EXECUTED: Draft loan application created for user {opp.user_id} from opportunity {opp.id}.")
    except Exception as e:
        print(f"Error executing action 'CREATE_DRAFT_APPLICATION': {e}")


# --- Event Dispatcher ---

# A mapping of action strings to functions
ACTION_MAP = {
    'CREATE_DRAFT_APPLICATION': _execute_create_draft_application
}

def dispatch(event_name, data={}):
    """
    Receives an event and triggers any corresponding actions from active flows.
    """
    print(f"EVENT DISPATCHED: '{event_name}' with data: {data}")
    flow = Flow.query.filter_by(trigger_event=event_name, is_active=True).first()

    if flow:
        action_func = ACTION_MAP.get(flow.action_to_perform)
        if action_func:
            action_func(data)
        else:
            print(f"ACTION WARNING: No action function found for '{flow.action_to_perform}'.")
    else:
        print(f"No active flow found for event '{event_name}'.")