from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.infrastructure.config.config import settings
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.database.models.user import User

from app.infrastructure.database.repositories.chat_repository import ChatRepository
from app.infrastructure.database.repositories.corpus_repository import CorpusRepository
from app.infrastructure.adapters.gemini_adapter import GeminiAdapter
from app.application.use_cases.chat_use_cases import ChatUseCase

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def get_current_user(
    db: AsyncSession = Depends(get_db), token: str = Depends(reusable_oauth2)
) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Query user from database
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

def get_current_active_tutor(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role not in ["tutor", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user does not have enough privileges",
        )
    return current_user

def get_current_active_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user does not have enough privileges",
        )
    return current_user

from app.application.use_cases.auth_use_cases import AuthUseCase
from app.infrastructure.database.repositories.user_repository import UserRepository

def get_auth_use_case(db: AsyncSession = Depends(get_db)) -> AuthUseCase:
    user_repo = UserRepository(db)
    return AuthUseCase(user_repo)

def get_chat_use_case(db: AsyncSession = Depends(get_db)) -> ChatUseCase:
    chat_repo = ChatRepository(db)
    corpus_repo = CorpusRepository(db)
    llm = GeminiAdapter(api_key=settings.GEMINI_API_KEY)
    return ChatUseCase(chat_repo, corpus_repo, llm)
