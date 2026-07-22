from abc import ABC, abstractmethod

class TransactionPort(ABC):
    @abstractmethod
    async def commit(self) -> None:
        pass

    @abstractmethod
    async def rollback(self) -> None:
        pass
