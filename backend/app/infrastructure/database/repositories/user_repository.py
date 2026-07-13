from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.application.ports.repository_ports import UserRepositoryPort
from app.domain.entities.user import UserCreate, UserUpdate
from app.infrastructure.database.models.user import User
from app.infrastructure.database.models.profiles import StudentProfile, TutorProfile, AdminProfile

class UserRepository(UserRepositoryPort):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(
            select(User)
            .options(
                selectinload(User.student_profile),
                selectinload(User.tutor_profile),
                selectinload(User.admin_profile)
            )
            .where(User.email == email)
        )
        return result.scalars().first()

    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self.db.execute(
            select(User)
            .options(
                selectinload(User.student_profile),
                selectinload(User.tutor_profile),
                selectinload(User.admin_profile)
            )
            .where(User.id == user_id)
        )
        return result.scalars().first()

    async def create(self, user_in: UserCreate, hashed_password: str, is_active: bool = True) -> User:
        try:
            db_user = User(
                email=user_in.email,
                password_hash=hashed_password,
                role=user_in.role,
                is_active=is_active,
            )
            
            if user_in.role == "estudiante":
                db_user.student_profile = StudentProfile(
                    full_name=user_in.full_name,
                    student_code=user_in.student_code or "",
                    current_semester=user_in.current_semester,
                    phone_number=user_in.phone_number,
                    academic_status=user_in.academic_status
                )
            elif user_in.role == "tutor":
                db_user.tutor_profile = TutorProfile(
                    full_name=user_in.full_name,
                    tutor_code=user_in.tutor_code or "",
                    phone_number=user_in.phone_number,
                    max_capacity=user_in.max_capacity,
                    expertise_areas=user_in.expertise_areas,
                    office_location=user_in.office_location
                )
            elif user_in.role == "admin":
                db_user.admin_profile = AdminProfile(
                    full_name=user_in.full_name,
                    administrative_position=user_in.administrative_position
                )

            self.db.add(db_user)
            await self.db.commit()
            await self.db.refresh(db_user)
            
            # Reload with relationships
            result = await self.db.execute(
                select(User)
                .options(
                    selectinload(User.student_profile),
                    selectinload(User.tutor_profile),
                    selectinload(User.admin_profile)
                )
                .where(User.id == db_user.id)
            )
            return result.scalars().first()
        except Exception as e:
            await self.db.rollback()
            raise e

    async def update(self, user_id: int, user_in: UserUpdate) -> Optional[User]:
        user = await self.get_by_id(user_id)
        if not user:
            return None
            
        update_data = user_in.model_dump(exclude_unset=True)
        
        # Update User Base
        if 'email' in update_data: user.email = update_data['email']
        if 'role' in update_data: user.role = update_data['role']
        if 'is_active' in update_data: user.is_active = update_data['is_active']
        
        # Update specific profiles
        if user.role == "estudiante" and user.student_profile:
            if 'full_name' in update_data: user.student_profile.full_name = update_data['full_name']
            if 'student_code' in update_data: user.student_profile.student_code = update_data['student_code']
            if 'phone_number' in update_data: user.student_profile.phone_number = update_data['phone_number']
            if 'current_semester' in update_data: user.student_profile.current_semester = update_data['current_semester']
            if 'academic_status' in update_data: user.student_profile.academic_status = update_data['academic_status']
        elif user.role == "tutor" and user.tutor_profile:
            if 'full_name' in update_data: user.tutor_profile.full_name = update_data['full_name']
            if 'tutor_code' in update_data: user.tutor_profile.tutor_code = update_data['tutor_code']
            if 'phone_number' in update_data: user.tutor_profile.phone_number = update_data['phone_number']
            if 'expertise_areas' in update_data: user.tutor_profile.expertise_areas = update_data['expertise_areas']
            if 'office_location' in update_data: user.tutor_profile.office_location = update_data['office_location']

        await self.db.commit()
        return await self.get_by_id(user_id)

    async def update_password(self, user_id: int, new_password_hash: str) -> bool:
        user = await self.get_by_id(user_id)
        if not user:
            return False
        user.password_hash = new_password_hash
        await self.db.commit()
        return True
