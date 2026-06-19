from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.application.ports.repository_ports import UserRepositoryPort
from app.domain.entities.user import UserCreate
from app.infrastructure.database.models.user import User

class UserRepository(UserRepositoryPort):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalars().first()

    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalars().first()

    async def create(self, user_in: UserCreate, hashed_password: str) -> User:
        db_user = User(
            full_name=user_in.full_name,
            email=user_in.email,
            password_hash=hashed_password,
            student_code=user_in.student_code,
            role=user_in.role,
            school=user_in.school,
        )
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        return db_user
