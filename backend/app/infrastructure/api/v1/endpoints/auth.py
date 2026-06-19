from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.infrastructure.api.dependencies import get_current_user, get_auth_use_case
from app.domain.entities.user import UserCreate, UserOut
from app.domain.entities.auth import Token, LoginRequest
from app.infrastructure.database.models.user import User
from app.application.use_cases.auth_use_cases import AuthUseCase

router = APIRouter()

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate, 
    auth_use_case: AuthUseCase = Depends(get_auth_use_case)
):
    return await auth_use_case.register_user(user_in=user_in)

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    auth_use_case: AuthUseCase = Depends(get_auth_use_case)
):
    # Form data uses 'username' and 'password'
    login_in = LoginRequest(username=form_data.username, password=form_data.password)
    return await auth_use_case.authenticate_user(login_in=login_in)

@router.get("/me", response_model=UserOut)
async def read_current_user(current_user: User = Depends(get_current_user)):
    return UserOut.model_validate(current_user)
