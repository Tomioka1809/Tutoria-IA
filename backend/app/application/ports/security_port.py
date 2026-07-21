from abc import ABC, abstractmethod
from datetime import datetime

class PasswordHasherPort(ABC):
    @abstractmethod
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        pass

    @abstractmethod
    def get_password_hash(self, password: str) -> str:
        pass

class TokenServicePort(ABC):
    @abstractmethod
    def create_access_token(self, subject: str) -> str:
        pass

class PasswordResetNotifierPort(ABC):
    @abstractmethod
    def send_reset_code(
        self,
        email: str,
        code: str,
        expires_at: datetime,
    ) -> None:
        pass
