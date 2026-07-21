from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app.infrastructure.api.dependencies import get_current_user, get_auth_use_case
from app.domain.entities.user import UserCreate, UserOut, UserUpdate, PasswordChange
from app.domain.entities.auth import Token, LoginRequest, ForgotPasswordRequest, ResetPasswordRequest
from app.infrastructure.database.models.user import User
from app.application.use_cases.auth_use_cases import AuthUseCase

router = APIRouter()

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate, 
    auth_use_case: AuthUseCase = Depends(get_auth_use_case)
):
    if user_in.role == "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No se permite registrar administradores por esta vía.")
        
    is_active = False if user_in.role == "tutor" else True
    return await auth_use_case.register_user(user_in=user_in, is_active=is_active)

@router.post("/register-staff", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register_staff(
    user_in: UserCreate, 
    auth_use_case: AuthUseCase = Depends(get_auth_use_case),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo los administradores pueden crear staff.")
        
    return await auth_use_case.register_user(user_in=user_in, is_active=True)

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

@router.put("/profile", response_model=UserOut)
async def update_profile(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    auth_use_case: AuthUseCase = Depends(get_auth_use_case)
):
    return await auth_use_case.update_profile(current_user.id, user_in)

@router.put("/change-password", response_model=dict)
async def change_password(
    password_in: PasswordChange,
    current_user: User = Depends(get_current_user),
    auth_use_case: AuthUseCase = Depends(get_auth_use_case)
):
    success = await auth_use_case.change_password(current_user.id, password_in)
    if success:
        return {"status": "success", "message": "Password changed successfully"}
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to change password")

@router.post("/forgot-password", response_model=dict)
async def forgot_password(
    request: ForgotPasswordRequest,
    auth_use_case: AuthUseCase = Depends(get_auth_use_case)
):
    await auth_use_case.generate_reset_token(email=request.email)
    return {"status": "success", "message": "Código de recuperación enviado con éxito."}

@router.post("/reset-password", response_model=dict)
async def reset_password(
    request: ResetPasswordRequest,
    auth_use_case: AuthUseCase = Depends(get_auth_use_case)
):
    success = await auth_use_case.reset_password_with_token(
        email=request.email,
        token=request.token,
        new_password=request.new_password
    )
    if success:
        return {"status": "success", "message": "Contraseña restablecida con éxito."}
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo restablecer la contraseña.")
