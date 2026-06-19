from typing import Optional
from fastapi import HTTPException, status
from app.application.ports.repository_ports import UserRepositoryPort
from app.domain.entities.user import UserCreate, UserOut
from app.domain.entities.auth import LoginRequest, Token
from app.infrastructure.security.security import create_access_token, get_password_hash, verify_password

class AuthUseCase:
    def __init__(self, user_repo: UserRepositoryPort):
        self.user_repo = user_repo

    async def register_user(self, user_in: UserCreate) -> UserOut:
        existing_user = await self.user_repo.get_by_email(user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        hashed_password = get_password_hash(user_in.password)
        db_user = await self.user_repo.create(user_in, hashed_password)
        return UserOut.model_validate(db_user)

    async def authenticate_user(self, login_in: LoginRequest) -> Token:
        user = await self.user_repo.get_by_email(login_in.username)
        if not user or not verify_password(login_in.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token = create_access_token(subject=str(user.id))
        return Token(access_token=access_token, token_type="bearer")
