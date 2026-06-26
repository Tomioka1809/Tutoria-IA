from typing import Optional
from fastapi import HTTPException, status
from app.application.ports.repository_ports import UserRepositoryPort
from app.domain.entities.user import UserCreate, UserOut, UserUpdate
from app.domain.entities.auth import LoginRequest, Token
from app.infrastructure.security.security import create_access_token, get_password_hash, verify_password

class AuthUseCase:
    def __init__(self, user_repo: UserRepositoryPort):
        self.user_repo = user_repo

    async def register_user(self, user_in: UserCreate, is_active: bool = True) -> UserOut:
        existing_user = await self.user_repo.get_by_email(user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        hashed_password = get_password_hash(user_in.password)
        db_user = await self.user_repo.create(user_in, hashed_password, is_active=is_active)
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

    async def update_profile(self, user_id: int, user_in: UserUpdate) -> UserOut:
        updated_user = await self.user_repo.update(user_id, user_in)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return UserOut.model_validate(updated_user)

    async def change_password(self, user_id: int, password_in) -> bool:
        user = await self.user_repo.get_by_id(user_id)
        if not user or not verify_password(password_in.current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect current password",
            )
        new_hashed = get_password_hash(password_in.new_password)
        return await self.user_repo.update_password(user_id, new_hashed)
