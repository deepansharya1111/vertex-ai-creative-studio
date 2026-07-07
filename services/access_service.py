import datetime
from typing import TypedDict, List
from google.cloud import firestore
from common.analytics import get_logger
from config.default import Default
from config.firebase_config import FirebaseClient

config = Default()
db = FirebaseClient(database_id=config.GENMEDIA_FIREBASE_DB).get_client()
logger = get_logger(__name__)

COLLECTION_NAME = "user_access_controls"

class UserAccess(TypedDict):
    email: str
    allowed_features: List[str]
    expiration_date: str
    is_admin: bool
    image_quota: int
    video_quota: int
    audio_quota: int
    image_usage: int
    video_usage: int
    audio_usage: int

def get_user_access(email: str) -> UserAccess | None:
    """Retrieve access controls for a specific user email."""
    email = email.lower().strip()
    if not db:
        logger.warning("Firestore client (db) is not initialized.")
        return None
        
    try:
        doc_ref = db.collection(COLLECTION_NAME).document(email)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        return None
    except Exception as e:
        logger.error(f"Error fetching user access for {email}: {e}")
        return None

def set_user_access(email: str, allowed_features: List[str], expiration_date: str, is_admin: bool = False, image_quota: int = 0, video_quota: int = 0, audio_quota: int = 0):
    """Set access controls for a specific user email. Preserves usage."""
    email = email.lower().strip()
    if not db:
        logger.warning("Firestore client (db) is not initialized.")
        return
        
    try:
        doc_ref = db.collection(COLLECTION_NAME).document(email)
        data = {
            "email": email,
            "allowed_features": allowed_features,
            "expiration_date": expiration_date,
            "is_admin": is_admin,
            "image_quota": image_quota,
            "video_quota": video_quota,
            "audio_quota": audio_quota,
        }
        doc_ref.set(data, merge=True)
        logger.info(f"Successfully set access control for {email}")
    except Exception as e:
        logger.error(f"Error setting user access for {email}: {e}")
        raise e

def list_all_users_access() -> List[UserAccess]:
    """Retrieve all users' access controls."""
    if not db:
        logger.warning("Firestore client (db) is not initialized.")
        return []
        
    try:
        docs = db.collection(COLLECTION_NAME).stream()
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        logger.error(f"Error listing all users access: {e}")
        return []

def delete_user_access(email: str):
    """Delete access controls for a specific user email."""
    if not db:
        logger.warning("Firestore client (db) is not initialized.")
        return
        
    try:
        doc_ref = db.collection(COLLECTION_NAME).document(email)
        doc_ref.delete()
        logger.info(f"Successfully deleted access control for {email}")
    except Exception as e:
        logger.error(f"Error deleting user access for {email}: {e}")
        raise e

def increment_user_usage(email: str, feature: str, amount: int = 1):
    """Increment usage for a specific feature by a given amount atomically."""
    email = email.lower().strip()
    if not db:
        logger.warning("Firestore client (db) is not initialized.")
        return
        
    try:
        doc_ref = db.collection(COLLECTION_NAME).document(email)
        field_name = f"{feature}_usage"
        # Atomically increment
        doc_ref.set({
            field_name: firestore.Increment(amount)
        }, merge=True)
        logger.info(f"Successfully incremented {feature} usage by {amount} for {email}")
    except Exception as e:
        logger.error(f"Error incrementing user usage for {email}: {e}")
        # Note: If document doesn't exist, this fails. Which is fine because they shouldn't be generating anyway.

def decrement_user_usage(email: str, feature: str, amount: int = 1):
    """Decrement usage for a specific feature by a given amount atomically (refund)."""
    email = email.lower().strip()
    if not db:
        logger.warning("Firestore client (db) is not initialized.")
        return
        
    try:
        doc_ref = db.collection(COLLECTION_NAME).document(email)
        field_name = f"{feature}_usage"
        # Atomically decrement
        doc_ref.set({
            field_name: firestore.Increment(-amount)
        }, merge=True)
        logger.info(f"Successfully decremented (refunded) {feature} usage by {amount} for {email}")
    except Exception as e:
        logger.error(f"Error decrementing user usage for {email}: {e}")
