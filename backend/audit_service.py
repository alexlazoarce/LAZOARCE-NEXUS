from models import db, AuditLog, User

def log_action(action, user_id, details=""):
    """
    Logs an action performed by a user.

    :param action: A string identifying the action, e.g., 'USER_LOGIN'.
    :param user_id: The ID of the user performing the action.
    :param details: A string with more details about the action.
    """
    try:
        # We fetch the user to ensure the user_id is valid
        user = User.query.get(user_id)
        if user:
            log_entry = AuditLog(
                user_id=user_id,
                action=action,
                details=details
            )
            db.session.add(log_entry)
            # The commit will be handled by the calling route's session management.
            print(f"AUDIT LOG: User {user.email} performed action '{action}'. Details: {details}")
        else:
            print(f"AUDIT LOG FAILED: User with ID {user_id} not found for action '{action}'.")
    except Exception as e:
        print(f"Error logging audit event: {e}")