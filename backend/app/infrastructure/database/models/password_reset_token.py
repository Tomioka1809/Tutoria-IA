from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base_class import Base


class PasswordResetToken(Base):
    """Codigo de recuperacion de contraseña, con su contador de intentos.

    Vive en la base y no en memoria del proceso porque antes era un diccionario a
    nivel de modulo: se perdia en cada reinicio y no se compartia entre workers, asi
    que con mas de uno el reset fallaba segun a que proceso cayera la peticion. El
    contador de intentos necesita ese mismo almacenamiento compartido para servir de
    algo: un limite que se reinicia solo no es un limite.

    Se guarda el hash del codigo, no el codigo. Son seis digitos, es decir un secreto
    de baja entropia: si la base se filtra, un hash rapido se revierte por fuerza
    bruta al instante, por eso se usa el mismo hasher que las contraseñas.
    """

    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    code_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # Un token deja de servir por consumo, por expiracion o por agotar los intentos.
    # Se marca en vez de borrarse para que el evento quede auditable.
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
