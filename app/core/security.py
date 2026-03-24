"""
app/core/security.py  [NEW]

Password hashing helpers using passlib/bcrypt.
Kept separate from JWT logic so each concern is isolated.
"""

from passlib.context import CryptContext

# bcrypt is the recommended algorithm — auto-upgrades hashes when needed
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Return a bcrypt hash of the plain-text password."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if plain_password matches the stored hash."""
    return pwd_context.verify(plain_password, hashed_password)
