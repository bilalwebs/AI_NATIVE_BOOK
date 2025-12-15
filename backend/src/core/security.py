import secrets
from passlib.context import CryptContext


# For hashing passwords (if needed for user accounts in the future)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate a hash for a plain password."""
    return pwd_context.hash(password)


def generate_api_key() -> str:
    """Generate a secure API key."""
    return secrets.token_urlsafe(32)


def verify_api_key(provided_key: str, expected_key: str) -> bool:
    """Verify an API key. This is a simple comparison but could be enhanced with database lookup."""
    # For now, just do a simple comparison
    # In a production environment, you might want to hash the keys or check against a database
    return secrets.compare_digest(provided_key, expected_key)