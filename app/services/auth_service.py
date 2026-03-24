"""app/services/auth_service.py — register and login business logic."""
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt_handler import create_access_token
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.auth import TokenResponse, UserLoginRequest, UserRegisterRequest, UserResponse


class AuthService:

    async def register(self, db: AsyncSession, payload: UserRegisterRequest) -> TokenResponse:
        result = await db.execute(select(User).where(User.email == payload.email))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Email already registered")

        user = User(
            email=payload.email,
            full_name=payload.full_name,
            hashed_password=hash_password(payload.password),
        )
        db.add(user)
        await db.flush()
        return self._tokens(user)

    async def login(self, db: AsyncSession, payload: UserLoginRequest) -> TokenResponse:
        result = await db.execute(select(User).where(User.email == payload.email))
        user = result.scalar_one_or_none()
        if not user or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account inactive")
        return self._tokens(user)

    def _tokens(self, user: User) -> TokenResponse:
        token = create_access_token(subject=user.id, extra_claims={"email": user.email})
        return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


auth_service = AuthService()
