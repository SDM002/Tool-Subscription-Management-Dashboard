"""
app/services/auth_service.py  [NEW]

Business logic for user registration and login.
Routes delegate to this service — keeps routes thin.
"""

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt_handler import create_access_token, create_refresh_token
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.services.auth import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)


class AuthService:

    async def register(
        self, db: AsyncSession, payload: UserRegisterRequest
    ) -> TokenResponse:
        # Check email uniqueness
        result = await db.execute(select(User).where(User.email == payload.email))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists",
            )

        user = User(
            email=payload.email,
            full_name=payload.full_name,
            hashed_password=hash_password(payload.password),
        )
        db.add(user)
        await db.flush()   # get user.id before commit

        return self._build_token_response(user)

    async def login(
        self, db: AsyncSession, payload: UserLoginRequest
    ) -> TokenResponse:
        result = await db.execute(select(User).where(User.email == payload.email))
        user = result.scalar_one_or_none()

        if not user or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive",
            )

        return self._build_token_response(user)

    def _build_token_response(self, user: User) -> TokenResponse:
        access_token = create_access_token(
            subject=user.id, extra_claims={"email": user.email}
        )
        refresh_token = create_refresh_token(subject=user.id)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserResponse.model_validate(user),
        )


auth_service = AuthService()
