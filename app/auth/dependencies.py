"""
app/auth/dependencies.py  [NEW]

FastAPI dependency that extracts and validates the current user from
the Authorization header.  Import `get_current_user` and use it as
a route dependency to protect any endpoint.

Usage:
    @router.get("/me")
    async def me(current_user: User = Depends(get_current_user)):
        return current_user
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.auth.jwt_handler import decode_token
from app.core.database import get_db
from app.models.user import User

# Reads the Bearer token from the Authorization header
bearer_scheme = HTTPBearer(auto_error=True)

_CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Validate the Bearer JWT and return the corresponding User row.
    Raises 401 if the token is invalid or the user no longer exists.
    """
    token = credentials.credentials

    try:
        payload = decode_token(token)
        user_id: str | None = payload.get("sub")
        token_type: str | None = payload.get("type")

        if user_id is None or token_type != "access":
            raise _CREDENTIALS_EXCEPTION

    except JWTError:
        raise _CREDENTIALS_EXCEPTION

    # Fetch user from DB
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if user is None:
        raise _CREDENTIALS_EXCEPTION

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Alias — explicitly documents 'active user required'."""
    return current_user
