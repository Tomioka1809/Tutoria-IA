from typing import Optional
import random
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from app.application.ports.repository_ports import UserRepositoryPort
from app.domain.entities.user import UserCreate, UserOut, UserUpdate
from app.domain.entities.auth import LoginRequest, Token
from app.infrastructure.security.security import create_access_token, get_password_hash, verify_password

# In-memory store for reset tokens (key: email, value: {"token": str, "expires": datetime})
reset_tokens_cache = {}

class AuthUseCase:
    def __init__(self, user_repo: UserRepositoryPort):
        self.user_repo = user_repo

    async def register_user(self, user_in: UserCreate, is_active: bool = True) -> UserOut:
        existing_user = await self.user_repo.get_by_email(user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Este correo ya está registrado",
            )
        hashed_password = get_password_hash(user_in.password)
        db_user = await self.user_repo.create(user_in, hashed_password, is_active=is_active)
        return UserOut.model_validate(db_user)

    async def authenticate_user(self, login_in: LoginRequest) -> Token:
        user = await self.user_repo.get_by_email(login_in.username)
        if not user or not verify_password(login_in.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Correo o contraseña incorrectos",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tu cuenta de tutor aún no ha sido activada por un administrador.",
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

    async def generate_reset_token(self, email: str) -> None:
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No existe ninguna cuenta registrada con este correo.",
            )
            
        # Generate a random 6-digit code
        token = f"{random.randint(100000, 999999)}"
        expires = datetime.now() + timedelta(minutes=15)
        
        # Save in memory cache
        reset_tokens_cache[email.lower()] = {
            "token": token,
            "expires": expires
        }
        
        print("\n" + "="*50)
        print(f"🔑 CÓDIGO DE RECUPERACIÓN DE CONTRASEÑA para {email}: {token}")
        print(f"⏰ Expira en: {expires.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*50 + "\n")
        
    async def reset_password_with_token(self, email: str, token: str, new_password: str) -> bool:
        email_key = email.lower()
        if email_key not in reset_tokens_cache:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se ha solicitado la recuperación de contraseña para este correo.",
            )
            
        cached_data = reset_tokens_cache[email_key]
        if cached_data["token"] != token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El código de recuperación ingresado es incorrecto.",
            )
            
        if datetime.now() > cached_data["expires"]:
            # Delete expired token
            del reset_tokens_cache[email_key]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El código de recuperación ha expirado. Por favor, solicita uno nuevo.",
            )
            
        if len(new_password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La contraseña debe tener al menos 6 caracteres.",
            )
            
        # Clean cached token
        del reset_tokens_cache[email_key]
        
        # Find user
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado.",
            )
            
        # Hash new password
        new_hashed = get_password_hash(new_password)
        return await self.user_repo.update_password(user.id, new_hashed)
