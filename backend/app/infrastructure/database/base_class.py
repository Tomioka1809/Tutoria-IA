from typing import Any
from sqlalchemy.orm import as_declarative, declared_attr

@as_declarative()
class Base:
    id: Any
    __name__: str

    # Generate __tablename__ automatically from class name
    @declared_attr
    def __tablename__(cls) -> str:
        # Convert CamelCase to snake_case or just return lowercase
        name = cls.__name__
        # A simple pluralization/lowercase mapping or manual is usually preferred,
        # but let's just make it lowercase. We'll specify __tablename__ manually on models
        # for maximum clarity and safety.
        return name.lower()
