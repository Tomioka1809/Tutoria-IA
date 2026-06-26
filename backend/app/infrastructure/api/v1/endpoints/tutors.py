from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List

from app.infrastructure.api.dependencies import get_db, get_current_user
from app.domain.entities.tutor_assignment import TutorAssignmentOut
from app.domain.entities.service_type import ServiceTypeOut
from app.domain.entities.user import UserOut
from app.infrastructure.database.models.user import User
from app.infrastructure.database.models.tutor_assignment import TutorAssignment
from app.infrastructure.database.models.service_type import ServiceType

router = APIRouter()

@router.get("/assigned", response_model=List[TutorAssignmentOut])
async def get_assigned_tutors(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    if current_user.role != "estudiante":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only students can query assigned tutors.",
        )
    result = await db.execute(
        select(TutorAssignment)
        .where(TutorAssignment.student_id == current_user.id)
        .options(
            selectinload(TutorAssignment.student).selectinload(User.student_profile),
            selectinload(TutorAssignment.student).selectinload(User.tutor_profile),
            selectinload(TutorAssignment.student).selectinload(User.admin_profile),
            selectinload(TutorAssignment.tutor).selectinload(User.tutor_profile),
            selectinload(TutorAssignment.tutor).selectinload(User.student_profile),
            selectinload(TutorAssignment.tutor).selectinload(User.admin_profile),
            selectinload(TutorAssignment.service_type),
        )
    )
    return list(result.scalars().all())

@router.get("/students", response_model=List[UserOut])
async def get_assigned_students(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    if current_user.role != "tutor":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only tutors can query assigned students.",
        )
    result = await db.execute(
        select(TutorAssignment)
        .where(TutorAssignment.tutor_id == current_user.id)
        .options(
            selectinload(TutorAssignment.student).selectinload(User.student_profile),
            selectinload(TutorAssignment.student).selectinload(User.tutor_profile),
            selectinload(TutorAssignment.student).selectinload(User.admin_profile),
            selectinload(TutorAssignment.tutor).selectinload(User.tutor_profile),
            selectinload(TutorAssignment.tutor).selectinload(User.student_profile),
            selectinload(TutorAssignment.tutor).selectinload(User.admin_profile),
        )
    )
    assignments = result.scalars().all()
    # Extract unique student user profiles
    students = []
    seen_ids = set()
    for assign in assignments:
        if assign.student.id not in seen_ids:
            students.append(assign.student)
            seen_ids.add(assign.student.id)
    return students

@router.get("/service-types", response_model=List[ServiceTypeOut])
async def get_service_types(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(ServiceType))
    return list(result.scalars().all())
