from datetime import datetime
from typing import Optional

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.application.ports.repository_ports import PasswordResetTokenRepositoryPort
from app.infrastructure.database.models.password_reset_token import PasswordResetToken


class PasswordResetTokenRepository(PasswordResetTokenRepositoryPort):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def replace_for_email(
        self, email: str, code_hash: str, expires_at: datetime
    ) -> PasswordResetToken:
        await self.db.execute(
            update(PasswordResetToken)
            .where(
                PasswordResetToken.email == email,
                PasswordResetToken.is_active.is_(True),
            )
            .values(is_active=False)
        )

        token = PasswordResetToken(
            email=email,
            code_hash=code_hash,
            expires_at=expires_at,
            attempts=0,
            is_active=True,
        )
        self.db.add(token)
        await self.db.commit()
        await self.db.refresh(token)
        return token

    async def get_active(self, email: str) -> Optional[PasswordResetToken]:
        result = await self.db.execute(
            select(PasswordResetToken)
            .where(
                PasswordResetToken.email == email,
                PasswordResetToken.is_active.is_(True),
            )
            .order_by(PasswordResetToken.id.desc())
            .limit(1)
        )
        return result.scalars().first()

    async def register_failed_attempt(self, token_id: int) -> int:
        # El incremento se calcula en la base y no en Python: dos peticiones
        # simultaneas leyendo el mismo valor podrian escribir el mismo total y
        # regalar intentos extra.
        result = await self.db.execute(
            update(PasswordResetToken)
            .where(PasswordResetToken.id == token_id)
            .values(attempts=PasswordResetToken.attempts + 1)
            .returning(PasswordResetToken.attempts)
        )
        attempts = result.scalar_one()
        await self.db.commit()
        return attempts

    async def invalidate(self, token_id: int) -> None:
        await self.db.execute(
            update(PasswordResetToken)
            .where(PasswordResetToken.id == token_id)
            .values(is_active=False)
        )
        await self.db.commit()
