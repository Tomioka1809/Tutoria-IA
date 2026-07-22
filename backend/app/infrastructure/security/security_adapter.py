import logging
from datetime import datetime
from app.application.ports.security_port import PasswordHasherPort, TokenServicePort, PasswordResetNotifierPort
from app.infrastructure.security.security import (
    verify_password as _verify_password,
    get_password_hash as _get_password_hash,
    create_access_token as _create_access_token,
)

logger = logging.getLogger(__name__)

class PasswordHasher(PasswordHasherPort):
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return _verify_password(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return _get_password_hash(password)

class TokenService(TokenServicePort):
    def create_access_token(self, subject: str) -> str:
        return _create_access_token(subject)

class DevelopmentPasswordResetNotifier(PasswordResetNotifierPort):
    """
    Adaptador temporal de desarrollo para notificación de códigos de recuperación de contraseña.
    En producción debe ser reemplazado por un adaptador con servicio SMTP/Email real.
    """
    def send_reset_code(
        self,
        email: str,
        code: str,
        expires_at: datetime,
    ) -> None:
        logger.info(
            "🔑 CÓDIGO DE RECUPERACIÓN DE CONTRASEÑA para %s: %s | Expira en: %s",
            email,
            code,
            expires_at.strftime("%Y-%m-%d %H:%M:%S")
        )
