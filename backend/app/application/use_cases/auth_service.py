from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from datetime import timedelta

from app.infrastructure.database.models.user import User
from app.infrastructure.database.models.streak import Streak
from app.domain.entities.user import UserCreate
from app.domain.entities.auth import LoginRequest, Token
from app.core import security
from app.core.config import settings

async def register_user(db: AsyncSession, user_in: UserCreate) -> User:
    # Check if user already exists
    result = await db.execute(select(User).where(User.email == user_in.email))
    user = result.scalars().first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists in the system.",
        )
    
    # Hash password
    hashed_password = security.get_password_hash(user_in.password)
    
    # Create user
    db_user = User(
        full_name=user_in.full_name,
        email=user_in.email,
        password_hash=hashed_password,
        student_code=user_in.student_code,
        role=user_in.role,
        school=user_in.school,
    )
    db.add(db_user)
    await db.flush() # Flush to populate ID
    
    # If the user is a student, initialize their streak record
    if db_user.role == "estudiante":
        db_streak = Streak(student_id=db_user.id, current_streak=0, max_streak=0)
        db.add(db_streak)
    
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def authenticate_user(db: AsyncSession, login_in: LoginRequest) -> Token:
    result = await db.execute(select(User).where(User.email == login_in.username))
    user = result.scalars().first()
    if not user or not security.verify_password(login_in.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )
    
    # Generate token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = security.create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    return Token(access_token=token, token_type="bearer")
