import logging
import os
from datetime import datetime
from app.application.ports.security_port import PasswordHasherPort, TokenServicePort, PasswordResetNotifierPort
from app.infrastructure.config.config import settings, validate_environment_name
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
    """Notificador de desarrollo: escribe el código en el log del backend.

    Es lo que permite probar la recuperación sin un servidor de correo, y por eso
    mismo no puede existir en producción: cualquiera con acceso a los logs se
    apropia de las cuentas. Antes se instanciaba sin mirar el entorno; ahora se
    niega a construirse en producción, y ``validate_runtime_security`` hace fallar
    el arranque para que el error salte al desplegar y no en el primer reset.
    """

    def __init__(self, app_env: str | None = None):
        env = validate_environment_name(
            app_env if app_env is not None else os.getenv("APP_ENV", settings.APP_ENV)
        )
        if env == "production":
            raise ValueError(
                "DevelopmentPasswordResetNotifier registra los códigos de recuperación "
                "en el log y no puede usarse en producción. Configure un notificador "
                "real (SMTP) antes de desplegar."
            )
        self.app_env = env

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
