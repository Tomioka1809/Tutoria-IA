import secrets
from datetime import datetime, timedelta
from app.application.ports.repository_ports import UserRepositoryPort
from app.application.ports.security_port import (
    PasswordHasherPort,
    TokenServicePort,
    PasswordResetNotifierPort,
)
from app.domain.entities.user import UserCreate, UserOut, UserUpdate
from app.domain.entities.auth import LoginRequest, Token
from app.domain.exceptions import (
    UserAlreadyExistsError,
    InvalidCredentialsError,
    AccountInactiveError,
    UserNotFoundError,
    PasswordMismatchError,
    InvalidTokenError,
    PasswordValidationError,
    PasswordUpdateError,
)

# In-memory store for reset tokens (key: email, value: {"token": str, "expires": datetime})
reset_tokens_cache = {}


class AuthUseCase:
    def __init__(
        self,
        user_repo: UserRepositoryPort,
        password_hasher: PasswordHasherPort,
        token_service: TokenServicePort,
        notifier: PasswordResetNotifierPort,
    ):
        self.user_repo = user_repo
        self.password_hasher = password_hasher
        self.token_service = token_service
        self.notifier = notifier

    async def register_user(self, user_in: UserCreate, is_active: bool = True) -> UserOut:
        existing_user = await self.user_repo.get_by_email(user_in.email)
        if existing_user:
            raise UserAlreadyExistsError("Este correo ya está registrado")
        hashed_password = self.password_hasher.get_password_hash(user_in.password)
        db_user = await self.user_repo.create(user_in, hashed_password, is_active=is_active)
        return UserOut.model_validate(db_user)

    async def authenticate_user(self, login_in: LoginRequest) -> Token:
        user = await self.user_repo.get_by_email(login_in.username)
        if not user or not self.password_hasher.verify_password(login_in.password, user.password_hash):
            raise InvalidCredentialsError("Correo o contraseña incorrectos")

        if not user.is_active:
            raise AccountInactiveError("Tu cuenta de tutor aún no ha sido activada por un administrador.")

        access_token = self.token_service.create_access_token(subject=str(user.id))
        return Token(access_token=access_token, token_type="bearer")

    async def update_profile(self, user_id: int, user_in: UserUpdate) -> UserOut:
        updated_user = await self.user_repo.update(user_id, user_in)
        if not updated_user:
            raise UserNotFoundError("User not found")
        return UserOut.model_validate(updated_user)

    async def change_password(self, user_id: int, password_in) -> bool:
        user = await self.user_repo.get_by_id(user_id)
        if not user or not self.password_hasher.verify_password(password_in.current_password, user.password_hash):
            raise PasswordMismatchError("Incorrect current password")

        if len(password_in.new_password) < 6:
            raise PasswordValidationError("La contraseña debe tener al menos 6 caracteres.")

        new_hashed = self.password_hasher.get_password_hash(password_in.new_password)
        success = await self.user_repo.update_password(user_id, new_hashed)
        if not success:
            raise PasswordUpdateError("No se pudo actualizar la contraseña.")
        return True

    async def generate_reset_token(self, email: str) -> None:
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise UserNotFoundError("No existe ninguna cuenta registrada con este correo.")

        # Generate a secure random 6-digit code
        code = str(secrets.randbelow(900000) + 100000)
        expires = datetime.now() + timedelta(minutes=15)

        # Save in memory cache
        reset_tokens_cache[email.lower()] = {
            "token": code,
            "expires": expires
        }

        # Send via notifier port
        self.notifier.send_reset_code(
            email=email,
            code=code,
            expires_at=expires,
        )

    async def reset_password_with_token(self, email: str, token: str, new_password: str) -> bool:
        email_key = email.lower()
        if email_key not in reset_tokens_cache:
            raise InvalidTokenError("No se ha solicitado la recuperación de contraseña para este correo.")

        cached_data = reset_tokens_cache[email_key]
        if cached_data["token"] != token:
            raise InvalidTokenError("El código de recuperación ingresado es incorrecto.")

        if datetime.now() > cached_data["expires"]:
            # Delete expired token
            del reset_tokens_cache[email_key]
            raise InvalidTokenError("El código de recuperación ha expirado. Por favor, solicita uno nuevo.")

        if len(new_password) < 6:
            raise PasswordValidationError("La contraseña debe tener al menos 6 caracteres.")

        user = await self.user_repo.get_by_email(email)
        if not user:
            raise UserNotFoundError("Usuario no encontrado.")

        new_hashed = self.password_hasher.get_password_hash(new_password)
        success = await self.user_repo.update_password(user.id, new_hashed)
        if not success:
            raise PasswordUpdateError("No se pudo actualizar la contraseña.")

        # Clean cached token ONLY after successful password update
        del reset_tokens_cache[email_key]
        return True
