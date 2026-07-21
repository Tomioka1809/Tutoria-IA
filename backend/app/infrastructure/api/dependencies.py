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

from sqlalchemy.orm import selectinload

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
    
    # Query user from database with profiles
    result = await db.execute(
        select(User)
        .options(
            selectinload(User.student_profile),
            selectinload(User.tutor_profile),
            selectinload(User.admin_profile)
        )
        .where(User.id == int(user_id))
    )
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
from app.application.use_cases.session_service import SessionUseCase
from app.infrastructure.database.repositories.user_repository import UserRepository
from app.infrastructure.database.repositories.tutor_assignment_repository import TutorAssignmentRepository
from app.infrastructure.database.repositories.calendar_repository import CalendarRepository
from app.infrastructure.database.repositories.session_repository import SessionRepository
from app.infrastructure.security.security_adapter import PasswordHasher, TokenService, DevelopmentPasswordResetNotifier

def get_auth_use_case(db: AsyncSession = Depends(get_db)) -> AuthUseCase:
    user_repo = UserRepository(db)
    password_hasher = PasswordHasher()
    token_service = TokenService()
    notifier = DevelopmentPasswordResetNotifier()
    return AuthUseCase(user_repo, password_hasher, token_service, notifier)

def get_session_use_case(db: AsyncSession = Depends(get_db)) -> SessionUseCase:
    session_repo = SessionRepository(db)
    tutor_assignment_repo = TutorAssignmentRepository(db)
    return SessionUseCase(session_repo=session_repo, tutor_assignment_repo=tutor_assignment_repo)

def get_chat_use_case(db: AsyncSession = Depends(get_db)) -> ChatUseCase:
    chat_repo = ChatRepository(db)
    corpus_repo = CorpusRepository(db)
    tutor_assignment_repo = TutorAssignmentRepository(db)
    calendar_repo = CalendarRepository(db)
    llm = GeminiAdapter(api_key=settings.GEMINI_API_KEY)
    return ChatUseCase(
        chat_repo=chat_repo,
        corpus_repo=corpus_repo,
        llm=llm,
        tutor_assignment_repo=tutor_assignment_repo,
        calendar_repo=calendar_repo
    )
