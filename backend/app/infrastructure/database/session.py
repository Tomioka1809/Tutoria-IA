import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

KNOWN_INSECURE_DB_PASSWORDS = {
    "postgres",
    "password",
    "changeme",
    "change_me",
    "change-me",
    "change me",
    "your_password",
    "your_password_here",
    "db_password",
    "tu_password",
    "tu_contrasena",
    "tu_password_aqui",
}


def _normalize_placeholder(value: str) -> str:
    return str(value).strip().lower().replace("-", "_").replace(" ", "_")


_NORMALIZED_INSECURE_PASSWORDS = {
    _normalize_placeholder(p) for p in KNOWN_INSECURE_DB_PASSWORDS
}


def validate_database_password_for_environment(app_env: str, db_password: str) -> None:
    if app_env is None or not str(app_env).strip():
        env_clean = "development"
    else:
        env_clean = str(app_env).strip().lower()
        if env_clean not in ("development", "test", "production"):
            raise ValueError("Entorno no válido para la verificación de base de datos.")

    if env_clean in ("development", "test"):
        return

    if db_password is None or not str(db_password).strip():
        raise ValueError("DB_PASSWORD no está configurada para el entorno de producción.")

    pwd_norm = _normalize_placeholder(db_password)

    if pwd_norm in _NORMALIZED_INSECURE_PASSWORDS:
        raise ValueError("DB_PASSWORD utiliza una contraseña insegura o de desarrollo en producción.")


def validate_database_security(app_env: str) -> None:
    current_pass = os.getenv("DB_PASSWORD", DB_PASSWORD)
    validate_database_password_for_environment(app_env, current_pass)



# Database URL configuration
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "tutoria_db")

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
)

# Async sessionmaker
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)
