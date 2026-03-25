"""
app/core/security.py

Password hashing helpers.
Uses bcrypt directly (bypassing passlib's version-mismatch bug with bcrypt 4.x).
The passlib library has a compatibility issue with bcrypt>=4.0 where it passes
a string instead of bytes. We use bcrypt directly to avoid this.
"""

import bcrypt


def hash_password(plain_password: str) -> str:
    """Return a bcrypt hash of the plain-text password."""
    # bcrypt expects bytes; encode to utf-8
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if plain_password matches the stored hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False