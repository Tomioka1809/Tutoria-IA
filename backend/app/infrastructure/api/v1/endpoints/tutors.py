from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Optional

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
    academic_period: Optional[str] = None,
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    if current_user.role != "estudiante":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only students can query assigned tutors.",
        )
        
    query = select(TutorAssignment).where(TutorAssignment.student_id == current_user.id)
    
    if academic_period:
        query = query.where(TutorAssignment.academic_period == academic_period)
    else:
        # Default to latest period in DB
        latest_period_query = select(TutorAssignment.academic_period).order_by(TutorAssignment.academic_period.desc()).limit(1)
        latest_res = await db.execute(latest_period_query)
        latest_period = latest_res.scalar()
        if latest_period:
            query = query.where(TutorAssignment.academic_period == latest_period)

    result = await db.execute(
        query
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

@router.get("/periods", response_model=List[str])
async def get_academic_periods(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(TutorAssignment.academic_period).distinct())
    periods = [p for p in result.scalars().all() if p]
    periods.sort(reverse=True)
    return periods

@router.get("/students", response_model=List[UserOut])
async def get_assigned_students(
    academic_period: Optional[str] = None,
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    if current_user.role != "tutor":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only tutors can query assigned students.",
        )
        
    student_query = (
        select(User)
        .join(TutorAssignment, TutorAssignment.student_id == User.id)
        .where(TutorAssignment.tutor_id == current_user.id)
        .options(
            selectinload(User.student_profile),
            selectinload(User.tutor_profile),
            selectinload(User.admin_profile),
        )
        .distinct()
    )
    
    if academic_period:
        student_query = student_query.where(TutorAssignment.academic_period == academic_period)
    else:
        # Default to latest period in DB
        latest_period_query = select(TutorAssignment.academic_period).order_by(TutorAssignment.academic_period.desc()).limit(1)
        latest_res = await db.execute(latest_period_query)
        latest_period = latest_res.scalar()
        if latest_period:
            student_query = student_query.where(TutorAssignment.academic_period == latest_period)
            
    result = await db.execute(student_query)
    return list(result.scalars().all())

@router.get("/service-types", response_model=List[ServiceTypeOut])
async def get_service_types(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(ServiceType))
    return list(result.scalars().all())
