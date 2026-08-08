import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

DEFAULT_DEV_SECRET_KEY = "a74e0cd1eceda53ff0b1cd99e67a7e0269cce9eca7a27be3de248d58be9ff54d"
ALLOWED_ENVIRONMENTS = {"development", "test", "production"}

# Admin que se crea solo al levantar el proyecto, cuando la base todavia no tiene
# ninguno. Estan aca y no solo en el .env para que un clon recien hecho arranque con
# un administrador utilizable: el roster siembra tutores y estudiantes, y sin esto no
# quedaba nadie que pudiera entrar al panel.
#
# Son credenciales publicas: viven en el repositorio. Solo se aplican fuera de
# produccion, y validate_admin_password_for_environment impide que lleguen alli.
DEFAULT_ADMIN_EMAIL = "admin@unsaac.edu.pe"
DEFAULT_ADMIN_PASSWORD = "admin123"
DEFAULT_ADMIN_NAME = "Administrador"

KNOWN_INSECURE_ADMIN_PASSWORDS = {
    DEFAULT_ADMIN_PASSWORD,
    "admin",
    "admin1234",
    "administrador",
    "changeme",
    "change_me",
    "password",
    "123456",
    "12345678",
    "contrasena",
    "secret",
}
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




def resolve_admin_bootstrap(app_env: str) -> tuple[str, str, str] | None:
    """Credenciales del admin inicial, o None si no corresponde crearlo.

    Fuera de produccion cae a los valores por defecto del repositorio, para que
    ``docker compose up`` deje el panel accesible sin editar el .env a mano.

    En produccion no hay valores por defecto: si el .env no los declara, devuelve
    None y el admin se crea a mano con ``python -m app.create_superuser``.
    """
    env_clean = validate_environment_name(app_env)
    en_produccion = env_clean == "production"

    email = (os.getenv("ADMIN_EMAIL") or "").strip()
    name = (os.getenv("ADMIN_NAME") or "").strip()

    # La contraseña no se recorta: los espacios al borde pueden ser parte de ella.
    # Pero una que es solo espacios equivale a no haberla declarado.
    password = os.getenv("ADMIN_PASSWORD") or ""
    if not password.strip():
        password = ""

    if not en_produccion:
        email = email or DEFAULT_ADMIN_EMAIL
        password = password or DEFAULT_ADMIN_PASSWORD
        name = name or DEFAULT_ADMIN_NAME

    if not email or not password:
        return None

    validate_admin_password_for_environment(env_clean, password)
    return email, password, name or DEFAULT_ADMIN_NAME


def validate_admin_password_for_environment(app_env: str, admin_password: str | None) -> None:
    """Impide que la contraseña de desarrollo del admin llegue a produccion.

    'admin123' esta escrita en el repositorio, asi que en produccion equivale a no
    tener contraseña. Se comprueba igual que SECRET_KEY y DB_PASSWORD: fallando al
    arrancar, no cuando alguien entra con ella.
    """
    if validate_environment_name(app_env) != "production":
        return

    if admin_password is None or not str(admin_password).strip():
        # Sin credenciales no se crea ningun admin automatico: es seguro.
        return

    pwd = str(admin_password).strip()

    if pwd.lower() in KNOWN_INSECURE_ADMIN_PASSWORDS:
        raise ValueError(
            "ADMIN_PASSWORD usa una contraseña conocida o de desarrollo, que está "
            "publicada en el repositorio. Elija otra para producción."
        )

    if len(pwd) < 12:
        raise ValueError(
            "ADMIN_PASSWORD debe tener al menos 12 caracteres en producción."
        )


def validate_password_reset_notifier(app_env: str) -> None:
    """En produccion tiene que haber un notificador real, y todavia no hay ninguno.

    El unico adaptador implementado escribe el codigo de recuperacion en el log del
    backend: es lo que permite probar el flujo sin servidor de correo, y es entregar
    las cuentas a cualquiera que lea los logs. Se comprueba al arrancar, igual que
    SECRET_KEY y CORS, para que el problema aparezca al desplegar y no la primera vez
    que alguien olvida su contraseña.

    Cuando exista un adaptador SMTP, esta funcion pasa a verificar que este
    configurado en vez de rechazar produccion de plano.
    """
    if validate_environment_name(app_env) == "production":
        raise ValueError(
            "No hay un notificador de recuperación de contraseña apto para producción: "
            "el único implementado escribe los códigos en el log del backend. "
            "Implemente un adaptador de correo real antes de desplegar."
        )


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
    # Falla al arrancar si el unico notificador disponible filtraria los codigos.
    validate_password_reset_notifier(current_env)
    # Falla al arrancar si el admin de produccion usa la contraseña del repositorio.
    validate_admin_password_for_environment(current_env, os.getenv("ADMIN_PASSWORD"))
