from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm

from app.core.dependencies import get_db, get_current_user
from app.schemas.user import UserCreate, UserOut
from app.schemas.auth import Token, LoginRequest
from app.models.user import User
from app.services import auth_service

router = APIRouter()

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    return await auth_service.register_user(db=db, user_in=user_in)

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    # Form data uses 'username' and 'password'
    login_in = LoginRequest(username=form_data.username, password=form_data.password)
    return await auth_service.authenticate_user(db=db, login_in=login_in)

@router.get("/me", response_model=UserOut)
async def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user
