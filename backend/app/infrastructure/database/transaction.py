from sqlalchemy.ext.asyncio import AsyncSession
from app.application.ports.transaction_port import TransactionPort

class SqlAlchemyTransaction(TransactionPort):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def commit(self) -> None:
        await self.db.commit()

    async def rollback(self) -> None:
        await self.db.rollback()
