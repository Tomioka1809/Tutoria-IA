import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

DEFAULT_DEV_SECRET_KEY = "a74e0cd1eceda53ff0b1cd99e67a7e0269cce9eca7a27be3de248d58be9ff54d"
ALLOWED_ENVIRONMENTS = {"development", "test", "production"}
KNOWN_INSECURE_PLACEHOLDERS = {
    "changeme",
    "change_me",
    "secret",
    "your_secret_key",
    "tu_clave_secreta_super_segura_aqui",
}


def validate_environment_name(app_env: str) -> str:
    if app_env is None or not str(app_env).strip():
        return "development"
    env_clean = str(app_env).strip().lower()
    if env_clean not in ALLOWED_ENVIRONMENTS:
        raise ValueError("Entorno no válido. APP_ENV debe ser uno de: development, test, production")
    return env_clean


def validate_secret_key_for_environment(app_env: str, secret_key: str) -> None:
    env_clean = validate_environment_name(app_env)
    if env_clean in ("development", "test"):
        return

    if not secret_key or not str(secret_key).strip():
        raise ValueError("SECRET_KEY no está configurada para el entorno de producción.")

    key_clean = str(secret_key).strip()
    key_lower = key_clean.lower()

    if key_clean == DEFAULT_DEV_SECRET_KEY:
        raise ValueError("SECRET_KEY utiliza la clave predeterminada de desarrollo en producción.")

    if key_lower in KNOWN_INSECURE_PLACEHOLDERS or any(ph in key_lower for ph in KNOWN_INSECURE_PLACEHOLDERS) or key_lower.startswith("your_secret") or key_lower.startswith("tu_clave_secreta"):
        raise ValueError("SECRET_KEY utiliza un placeholder inseguro en producción.")

    if len(key_clean) < 32:
        raise ValueError("SECRET_KEY debe tener al menos 32 caracteres en producción.")


def parse_cors_origins(raw_origins: str | None) -> list[str]:
    """Convierte 'https://a.pe, https://b.pe/' en ['https://a.pe', 'https://b.pe']."""
    if raw_origins is None:
        return []
    origins = []
    for candidate in str(raw_origins).split(","):
        origin = candidate.strip().rstrip("/")
        if origin and origin not in origins:
            origins.append(origin)
    return origins


def resolve_cors_origins(app_env: str, raw_origins: str | None) -> list[str]:
    """Origenes permitidos por entorno.

    En produccion la lista es obligatoria y explicita: el comodin habilita a cualquier
    sitio a emitir peticiones contra la API. En desarrollo se mantiene abierto porque
    Expo sirve la app web desde puertos e IP de LAN variables.
    """
    env_clean = validate_environment_name(app_env)
    origins = parse_cors_origins(raw_origins)

    if env_clean == "production":
        if not origins:
            raise ValueError(
                "CORS_ALLOWED_ORIGINS debe declarar al menos un origen en producción."
            )
        if "*" in origins:
            raise ValueError(
                "CORS_ALLOWED_ORIGINS no puede usar '*' en producción; declare los orígenes explícitamente."
            )
        return origins

    return origins or ["*"]




class Settings:
    PROJECT_NAME: str = "TutorIA API"
    API_V1_STR: str = "/api/v1"

    APP_ENV: str = validate_environment_name(os.getenv("APP_ENV", "development"))

    # JWT Settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", DEFAULT_DEV_SECRET_KEY)
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

    # Gemini API Key for Chatbot
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # Origenes permitidos para CORS, separados por coma. Obligatorio en produccion.
    CORS_ALLOWED_ORIGINS: str = os.getenv("CORS_ALLOWED_ORIGINS", "")


settings = Settings()


def get_cors_origins() -> list[str]:
    return resolve_cors_origins(
        os.getenv("APP_ENV", settings.APP_ENV),
        os.getenv("CORS_ALLOWED_ORIGINS", settings.CORS_ALLOWED_ORIGINS),
    )


def validate_runtime_security() -> None:
    current_env = validate_environment_name(os.getenv("APP_ENV", settings.APP_ENV))
    current_key = os.getenv("SECRET_KEY", settings.SECRET_KEY)
    validate_secret_key_for_environment(current_env, current_key)
    # Falla al arrancar si produccion no declara origenes, en lugar de servir con comodin.
    resolve_cors_origins(
        current_env, os.getenv("CORS_ALLOWED_ORIGINS", settings.CORS_ALLOWED_ORIGINS)
    )
