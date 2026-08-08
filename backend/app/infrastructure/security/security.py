from datetime import datetime, timedelta, timezone
from typing import Any, Union

import bcrypt
from jose import jwt

from app.infrastructure.config.config import settings

# Coste de bcrypt. 12 es el valor con el que estan hasheadas las contraseñas ya
# guardadas; bajarlo debilita las nuevas, subirlo encarece cada login.
BCRYPT_ROUNDS = 12

# bcrypt solo considera los primeros 72 bytes de la clave. Se trunca explicitamente
# porque el stack anterior (passlib sobre el backend os_crypt) lo hacia en silencio:
# rechazar las claves largas ahora dejaria fuera a las cuentas creadas con ellas.
# Sin este truncado, bcrypt levanta ValueError y el login responde 500.
BCRYPT_MAX_BYTES = 72


def _encode(password: str) -> bytes:
    """Pasa la clave a los bytes que bcrypt realmente usa.

    El corte es por bytes, no por caracteres, asi que se recorta sobre el UTF-8 ya
    codificado y se descarta un caracter multibyte partido por la mitad.
    """
    return password.encode("utf-8")[:BCRYPT_MAX_BYTES]


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not plain_password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(_encode(plain_password), hashed_password.encode("utf-8"))
    except (ValueError, TypeError):
        # Hash corrupto o con un formato que bcrypt no reconoce: es un intento de
        # login fallido, no un error del servidor.
        return False


def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    return bcrypt.hashpw(_encode(password), salt).decode("utf-8")


def create_access_token(
    subject: Union[str, Any], expires_delta: timedelta = None
) -> str:
    # datetime.utcnow() esta deprecado desde Python 3.12: devuelve un datetime naive
    # que aparenta ser UTC, y de ahi salen las comparaciones que fallan por zona.
    ahora = datetime.now(timezone.utc)
    if expires_delta:
        expire = ahora + expires_delta
    else:
        expire = ahora + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt
