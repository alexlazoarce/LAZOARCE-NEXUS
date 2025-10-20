from backend.models import db, SignatureRequest, User

def save_signature(user_id, signature_data):
    """
    Saves a user's signature data to the database.

    Args:
        user_id: The ID of the user submitting the signature.
        signature_data: The Base64 encoded signature data.

    Returns:
        The newly created SignatureRequest object.
    """
    if not user_id or not signature_data:
        raise ValueError("User ID and signature data are required.")

    user = User.query.get(user_id)
    if not user:
        raise ValueError("User not found.")

    new_signature = SignatureRequest(
        user_id=user_id,
        signature_data=signature_data
    )

    db.session.add(new_signature)
    db.session.commit()

    return new_signature

def get_signatures_for_user(user_id):
    """
    Retrieves all signatures for a given user.
    """
    return SignatureRequest.query.filter_by(user_id=user_id).order_by(SignatureRequest.created_at.desc()).all()
