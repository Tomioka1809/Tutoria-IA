import secrets
from datetime import datetime, timedelta, timezone
from app.application.ports.repository_ports import (
    UserRepositoryPort,
    PasswordResetTokenRepositoryPort,
)
from app.application.ports.security_port import (
    PasswordHasherPort,
    TokenServicePort,
    PasswordResetNotifierPort,
)
from app.domain.entities.user import UserCreate, UserOut, UserSelfUpdate
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

# Vida util del codigo de recuperacion.
RESET_CODE_TTL_MINUTES = 15

# Intentos fallidos antes de anular el codigo. Son seis digitos: sin un tope, un
# atacante recorre el espacio completo dentro de la ventana de validez.
MAX_RESET_ATTEMPTS = 5

# Respuesta unica del pedido de recuperacion. No distingue si el correo existe:
# responder distinto convertia el endpoint en un verificador de cuentas.
RESET_REQUEST_ACK = "Si el correo corresponde a una cuenta, se envió un código de recuperación."


class AuthUseCase:
    def __init__(
        self,
        user_repo: UserRepositoryPort,
        password_hasher: PasswordHasherPort,
        token_service: TokenServicePort,
        notifier: PasswordResetNotifierPort,
        reset_token_repo: PasswordResetTokenRepositoryPort,
    ):
        self.user_repo = user_repo
        self.password_hasher = password_hasher
        self.token_service = token_service
        self.notifier = notifier
        self.reset_token_repo = reset_token_repo

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

    async def update_profile(self, user_id: int, user_in: UserSelfUpdate) -> UserOut:
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
        """Emite un codigo de recuperacion. No revela si el correo esta registrado.

        Antes lanzaba UserNotFoundError, que el manejador traducia a 404 mientras
        que un correo existente devolvia 200: el endpoint era publico, asi que
        cualquiera podia averiguar que cuentas existen probando correos.
        """
        email_key = email.lower()
        user = await self.user_repo.get_by_email(email)

        # El codigo se genera y se hashea siempre, exista el usuario o no. El hash
        # domina el tiempo de respuesta, asi que hacerlo solo en una de las ramas
        # dejaria abierta por reloj la misma pregunta que se acaba de cerrar.
        code = str(secrets.randbelow(900000) + 100000)
        code_hash = self.password_hasher.get_password_hash(code)

        if not user:
            return

        # Con zona horaria: la columna es timestamptz y PostgreSQL devuelve datetimes
        # con tzinfo, que no se pueden comparar contra uno naive.
        expires = datetime.now(timezone.utc) + timedelta(minutes=RESET_CODE_TTL_MINUTES)
        await self.reset_token_repo.replace_for_email(email_key, code_hash, expires)

        self.notifier.send_reset_code(
            email=email,
            code=code,
            expires_at=expires,
        )

    async def reset_password_with_token(self, email: str, token: str, new_password: str) -> bool:
        email_key = email.lower()
        record = await self.reset_token_repo.get_active(email_key)

        # Mismo mensaje para "nunca se pidio" y "ya no sirve": diferenciarlos vuelve
        # a decir si la cuenta existe.
        if not record:
            raise InvalidTokenError(
                "El código de recuperación no es válido o ya expiró. Solicita uno nuevo."
            )

        if datetime.now(timezone.utc) > record.expires_at:
            await self.reset_token_repo.invalidate(record.id)
            raise InvalidTokenError(
                "El código de recuperación ha expirado. Por favor, solicita uno nuevo."
            )

        if not self.password_hasher.verify_password(token, record.code_hash):
            attempts = await self.reset_token_repo.register_failed_attempt(record.id)
            if attempts >= MAX_RESET_ATTEMPTS:
                await self.reset_token_repo.invalidate(record.id)
                raise InvalidTokenError(
                    "Demasiados intentos fallidos. El código fue anulado; solicita uno nuevo."
                )
            raise InvalidTokenError("El código de recuperación ingresado es incorrecto.")

        # A partir de aca el codigo es correcto. Un fallo posterior no lo consume:
        # obligar a pedir uno nuevo por escribir una contraseña corta seria hostil.
        if len(new_password) < 6:
            raise PasswordValidationError("La contraseña debe tener al menos 6 caracteres.")

        user = await self.user_repo.get_by_email(email)
        if not user:
            raise UserNotFoundError("Usuario no encontrado.")

        new_hashed = self.password_hasher.get_password_hash(new_password)
        success = await self.user_repo.update_password(user.id, new_hashed)
        if not success:
            raise PasswordUpdateError("No se pudo actualizar la contraseña.")

        # El codigo se anula recien despues de que la contraseña quedo escrita.
        await self.reset_token_repo.invalidate(record.id)
        return True
