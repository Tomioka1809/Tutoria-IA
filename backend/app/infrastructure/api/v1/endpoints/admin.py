from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

from app.infrastructure.api.dependencies import get_db, get_current_active_admin
from app.domain.entities.user import UserOut, UserCreate
from app.infrastructure.database.models.user import User
from app.infrastructure.database.models.tutor_assignment import TutorAssignment
from app.infrastructure.database.models.session import Session
from app.infrastructure.database.models.corpus_chunk import CorpusChunk
from app.infrastructure.database.models.motivational_quote import MotivationalQuote
from app.infrastructure.security.security import get_password_hash
from app.infrastructure.database.repositories.user_repository import UserRepository
from app.infrastructure.adapters.gemini_adapter import GeminiAdapter
from app.infrastructure.config.config import settings

router = APIRouter()

class AdminStats(BaseModel):
    total_students: int
    active_tutors: int
    pending_tutors: int
    completed_sessions: int
    total_capacity: int
    assigned_students: int

class UserStatusUpdate(BaseModel):
    is_active: bool

class CapacityUpdate(BaseModel):
    max_capacity: int

class TutorAssignmentCreate(BaseModel):
    student_id: int
    tutor_id: int
    academic_period: str = "2026-I"
    service_type_id: int = 1

class BulkTransferCreate(BaseModel):
    from_tutor_id: int
    to_tutor_id: int
    academic_period: str = "2026-I"

class CorpusChunkCreate(BaseModel):
    source: str
    text_content: str

class CorpusChunkOut(BaseModel):
    id: int
    source: str
    text_content: str
    model_config = ConfigDict(from_attributes=True)

class QuoteCreate(BaseModel):
    text: str

class QuoteOut(BaseModel):
    id: int
    text: str
    model_config = ConfigDict(from_attributes=True)

class AdminUserOut(UserOut):
    current_load: int = 0
    model_config = ConfigDict(from_attributes=True)

@router.get("/stats", response_model=AdminStats)
async def get_admin_stats(db: AsyncSession = Depends(get_db), _: User = Depends(get_current_active_admin)):
    students_res = await db.execute(select(func.count(User.id)).where(User.role == "estudiante"))
    total_students = students_res.scalar() or 0
    
    active_tutors_res = await db.execute(
        select(User).options(selectinload(User.tutor_profile))
        .where(User.role == "tutor", User.is_active == True)
    )
    active_tutors_list = active_tutors_res.scalars().all()
    active_tutors = len(active_tutors_list)
    total_capacity = sum([(t.tutor_profile.max_capacity if t.tutor_profile else 15) for t in active_tutors_list])
    
    pending_tutors_res = await db.execute(select(func.count(User.id)).where(User.role == "tutor", User.is_active == False))
    pending_tutors = pending_tutors_res.scalar() or 0
    
    sessions_res = await db.execute(select(func.count(Session.id)).where(Session.status == "completada"))
    completed_sessions = sessions_res.scalar() or 0
    
    assigned_res = await db.execute(select(func.count(TutorAssignment.id)).where(TutorAssignment.academic_period == "2026-I"))
    assigned_students = assigned_res.scalar() or 0

    return AdminStats(
        total_students=total_students,
        active_tutors=active_tutors,
        pending_tutors=pending_tutors,
        completed_sessions=completed_sessions,
        total_capacity=total_capacity,
        assigned_students=assigned_students
    )

@router.get("/users", response_model=List[AdminUserOut])
async def get_all_users(db: AsyncSession = Depends(get_db), _: User = Depends(get_current_active_admin)):
    result = await db.execute(
        select(User).options(selectinload(User.student_profile), selectinload(User.tutor_profile), selectinload(User.admin_profile))
        .where(User.role.in_(["estudiante", "tutor", "admin"]))
        .order_by(User.id.desc())
    )
    users = list(result.scalars().all())
    
    for u in users:
        if u.role == "tutor":
            load_res = await db.execute(select(func.count(TutorAssignment.id)).where(TutorAssignment.tutor_id == u.id))
            setattr(u, 'current_load', load_res.scalar() or 0)
        else:
            setattr(u, 'current_load', 0)
            
    return users

@router.post("/users", response_model=AdminUserOut, status_code=status.HTTP_201_CREATED)
async def create_staff(user_in: UserCreate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_active_admin)):
    user_repo = UserRepository(db)
    existing_user = await user_repo.get_by_email(email=user_in.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="El email ya está registrado.")
    
    hashed_pwd = get_password_hash(user_in.password)
    new_user = await user_repo.create(user_in=user_in, hashed_password=hashed_pwd, is_active=True)
    
    result = await db.execute(
        select(User).options(selectinload(User.student_profile), selectinload(User.tutor_profile), selectinload(User.admin_profile)).where(User.id == new_user.id)
    )
    final_user = result.scalars().first()
    setattr(final_user, 'current_load', 0)
    return final_user

@router.patch("/users/{user_id}/status", response_model=AdminUserOut)
async def update_user_status(user_id: int, status_update: UserStatusUpdate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_active_admin)):
    result = await db.execute(
        select(User).options(selectinload(User.student_profile), selectinload(User.tutor_profile), selectinload(User.admin_profile)).where(User.id == user_id)
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.is_active = status_update.is_active
    await db.commit()
    
    load = 0
    if user.role == "tutor":
        load_res = await db.execute(select(func.count(TutorAssignment.id)).where(TutorAssignment.tutor_id == user.id))
        load = load_res.scalar() or 0
    setattr(user, 'current_load', load)
    return user

@router.patch("/users/{user_id}/capacity", response_model=AdminUserOut)
async def update_user_capacity(user_id: int, cap_update: CapacityUpdate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_active_admin)):
    result = await db.execute(
        select(User).options(selectinload(User.student_profile), selectinload(User.tutor_profile), selectinload(User.admin_profile)).where(User.id == user_id)
    )
    user = result.scalars().first()
    if not user or user.role != "tutor" or not user.tutor_profile:
        raise HTTPException(status_code=404, detail="Tutor no encontrado o sin perfil")
        
    user.tutor_profile.max_capacity = cap_update.max_capacity
    await db.commit()
    
    load_res = await db.execute(select(func.count(TutorAssignment.id)).where(TutorAssignment.tutor_id == user.id))
    setattr(user, 'current_load', load_res.scalar() or 0)
    return user

@router.get("/users/{user_id}/students", response_model=List[UserOut])
async def get_tutor_students(
    user_id: int, db: AsyncSession = Depends(get_db), current_admin: User = Depends(get_current_active_admin)
):
    # Verify user exists and is a tutor
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user or user.role != "tutor":
        raise HTTPException(status_code=404, detail="Tutor not found")
        
    assignments_res = await db.execute(
        select(TutorAssignment)
        .where(TutorAssignment.tutor_id == user_id)
        .options(selectinload(TutorAssignment.student).selectinload(User.student_profile))
    )
    assignments = assignments_res.scalars().all()
    
    students = []
    seen_ids = set()
    for assign in assignments:
        if assign.student.id not in seen_ids:
            students.append(assign.student)
            seen_ids.add(assign.student.id)
    return students

@router.post("/assignments", status_code=status.HTTP_201_CREATED)
async def create_assignment(assignment_in: TutorAssignmentCreate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_active_admin)):
    existing_res = await db.execute(
        select(TutorAssignment).where(TutorAssignment.student_id == assignment_in.student_id, TutorAssignment.academic_period == assignment_in.academic_period)
    )
    existing_assign = existing_res.scalars().first()
    if existing_assign:
        existing_assign.tutor_id = assignment_in.tutor_id
    else:
        new_assignment = TutorAssignment(
            student_id=assignment_in.student_id,
            tutor_id=assignment_in.tutor_id,
            service_type_id=assignment_in.service_type_id,
            academic_period=assignment_in.academic_period
        )
        db.add(new_assignment)
    await db.commit()
    return {"message": "Assignment created/updated successfully"}

@router.post("/assignments/bulk-transfer")
async def bulk_transfer(transfer_in: BulkTransferCreate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_active_admin)):
    res = await db.execute(
        select(TutorAssignment).where(TutorAssignment.tutor_id == transfer_in.from_tutor_id, TutorAssignment.academic_period == transfer_in.academic_period)
    )
    assignments = res.scalars().all()
    
    target_res = await db.execute(
        select(User).options(selectinload(User.tutor_profile)).where(User.id == transfer_in.to_tutor_id)
    )
    target_tutor = target_res.scalars().first()
    max_cap = target_tutor.tutor_profile.max_capacity if (target_tutor and target_tutor.tutor_profile) else 15
    
    current_target_load_res = await db.execute(
        select(func.count(TutorAssignment.id)).where(TutorAssignment.tutor_id == transfer_in.to_tutor_id, TutorAssignment.academic_period == transfer_in.academic_period)
    )
    target_count = current_target_load_res.scalar() or 0
    
    if target_count + len(assignments) > max_cap:
        raise HTTPException(status_code=400, detail=f"El tutor de destino superaría su límite de {max_cap} alumnos.")
        
    for assign in assignments:
        assign.tutor_id = transfer_in.to_tutor_id
    
    await db.commit()
    return {"message": f"Trasferidos {len(assignments)} alumnos exitosamente."}

@router.post("/sorteo")
async def execute_sorteo(period: str = "2026-I", db: AsyncSession = Depends(get_db), _: User = Depends(get_current_active_admin)):
    subq = select(TutorAssignment.student_id).where(TutorAssignment.academic_period == period)
    students_res = await db.execute(select(User).where(User.role == "estudiante", User.is_active == True, User.id.not_in(subq)))
    unassigned_students = students_res.scalars().all()
    
    tutors_res = await db.execute(
        select(User).options(selectinload(User.tutor_profile)).where(User.role == "tutor", User.is_active == True)
    )
    tutors = tutors_res.scalars().all()
    
    if not tutors:
        raise HTTPException(status_code=400, detail="No hay tutores activos para realizar el sorteo.")
        
    assigned_count = 0
    tutor_index = 0
    
    for student in unassigned_students:
        attempts = 0
        assigned = False
        while attempts < len(tutors):
            current_tutor = tutors[tutor_index]
            max_cap = current_tutor.tutor_profile.max_capacity if current_tutor.tutor_profile else 15
            
            load_res = await db.execute(
                select(func.count(TutorAssignment.id))
                .where(TutorAssignment.tutor_id == current_tutor.id, TutorAssignment.academic_period == period)
            )
            load = load_res.scalar() or 0
            
            if load < max_cap:
                new_assign = TutorAssignment(
                    student_id=student.id,
                    tutor_id=current_tutor.id,
                    service_type_id=1,
                    academic_period=period
                )
                db.add(new_assign)
                assigned_count += 1
                assigned = True
                tutor_index = (tutor_index + 1) % len(tutors)
                break
            else:
                tutor_index = (tutor_index + 1) % len(tutors)
                attempts += 1
        
        if not assigned:
            break 

    await db.commit()
    return {"message": f"Sorteo finalizado. {assigned_count} estudiantes asignados."}

@router.get("/corpus", response_model=List[CorpusChunkOut])
async def get_corpus(db: AsyncSession = Depends(get_db), _: User = Depends(get_current_active_admin)):
    result = await db.execute(select(CorpusChunk).order_by(CorpusChunk.id.desc()))
    return list(result.scalars().all())

@router.post("/corpus", response_model=CorpusChunkOut)
async def create_corpus(chunk_in: CorpusChunkCreate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_active_admin)):
    adapter = GeminiAdapter(api_key=settings.GEMINI_API_KEY)
    embedding = await adapter.compute_embedding(chunk_in.text_content)
    
    new_chunk = CorpusChunk(
        source=chunk_in.source,
        text_content=chunk_in.text_content,
        embedding=embedding
    )
    db.add(new_chunk)
    await db.commit()
    await db.refresh(new_chunk)
    return new_chunk

@router.delete("/corpus/{chunk_id}")
async def delete_corpus(chunk_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_active_admin)):
    res = await db.execute(select(CorpusChunk).where(CorpusChunk.id == chunk_id))
    chunk = res.scalars().first()
    if chunk:
        await db.delete(chunk)
        await db.commit()
    return {"message": "Deleted successfully"}

@router.put("/corpus/{chunk_id}", response_model=CorpusChunkOut)
async def update_corpus(chunk_id: int, chunk_in: CorpusChunkCreate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_active_admin)):
    res = await db.execute(select(CorpusChunk).where(CorpusChunk.id == chunk_id))
    chunk = res.scalars().first()
    if not chunk:
        raise HTTPException(status_code=404, detail="Not found")
    
    adapter = GeminiAdapter(api_key=settings.GEMINI_API_KEY)
    embedding = await adapter.compute_embedding(chunk_in.text_content)
    
    chunk.source = chunk_in.source
    chunk.text_content = chunk_in.text_content
    chunk.embedding = embedding
    
    await db.commit()
    await db.refresh(chunk)
    return chunk

@router.get("/quotes", response_model=List[QuoteOut])
async def get_quotes(db: AsyncSession = Depends(get_db), _: User = Depends(get_current_active_admin)):
    result = await db.execute(select(MotivationalQuote).order_by(MotivationalQuote.id.desc()))
    return list(result.scalars().all())

@router.post("/quotes", response_model=QuoteOut)
async def create_quote(quote_in: QuoteCreate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_active_admin)):
    new_quote = MotivationalQuote(text=quote_in.text)
    db.add(new_quote)
    await db.commit()
    await db.refresh(new_quote)
    return new_quote

@router.put("/quotes/{quote_id}", response_model=QuoteOut)
async def update_quote(quote_id: int, quote_in: QuoteCreate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_active_admin)):
    res = await db.execute(select(MotivationalQuote).where(MotivationalQuote.id == quote_id))
    quote = res.scalars().first()
    if not quote:
        raise HTTPException(status_code=404, detail="Not found")
        
    quote.text = quote_in.text
    await db.commit()
    await db.refresh(quote)
    return quote

@router.delete("/quotes/{quote_id}")
async def delete_quote(quote_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_active_admin)):
    res = await db.execute(select(MotivationalQuote).where(MotivationalQuote.id == quote_id))
    quote = res.scalars().first()
    if quote:
        await db.delete(quote)
        await db.commit()
    return {"message": "Deleted successfully"}
