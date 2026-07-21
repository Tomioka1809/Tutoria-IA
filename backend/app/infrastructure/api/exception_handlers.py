from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from app.domain.exceptions import (
    DomainException,
    UserAlreadyExistsError,
    InvalidCredentialsError,
    AccountInactiveError,
    UserNotFoundError,
    PasswordMismatchError,
    InvalidTokenError,
    NotAuthorizedError,
    ResourceNotFoundError,
    PasswordValidationError,
    PasswordUpdateError,
)

def setup_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(UserAlreadyExistsError)
    async def user_already_exists_handler(request: Request, exc: UserAlreadyExistsError):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": str(exc) or "Este correo ya está registrado"},
        )

    @app.exception_handler(InvalidCredentialsError)
    async def invalid_credentials_handler(request: Request, exc: InvalidCredentialsError):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": str(exc) or "Correo o contraseña incorrectos"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(AccountInactiveError)
    async def account_inactive_handler(request: Request, exc: AccountInactiveError):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": str(exc) or "Tu cuenta de tutor aún no ha sido activada por un administrador."},
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(UserNotFoundError)
    async def user_not_found_handler(request: Request, exc: UserNotFoundError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exc) or "User not found"},
        )

    @app.exception_handler(ResourceNotFoundError)
    async def resource_not_found_handler(request: Request, exc: ResourceNotFoundError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exc) or "Resource not found"},
        )

    @app.exception_handler(PasswordMismatchError)
    async def password_mismatch_handler(request: Request, exc: PasswordMismatchError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc) or "Incorrect current password"},
        )

    @app.exception_handler(PasswordValidationError)
    async def password_validation_handler(request: Request, exc: PasswordValidationError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc) or "La contraseña no cumple los requisitos de validación."},
        )

    @app.exception_handler(PasswordUpdateError)
    async def password_update_handler(request: Request, exc: PasswordUpdateError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc) or "No se pudo actualizar la contraseña."},
        )

    @app.exception_handler(InvalidTokenError)
    async def invalid_token_handler(request: Request, exc: InvalidTokenError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc) or "El código de recuperación ingresado es incorrecto."},
        )

    @app.exception_handler(NotAuthorizedError)
    async def not_authorized_handler(request: Request, exc: NotAuthorizedError):
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": str(exc) or "Not authorized"},
        )

    @app.exception_handler(DomainException)
    async def generic_domain_exception_handler(request: Request, exc: DomainException):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc) or "Bad Request"},
        )
