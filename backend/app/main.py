import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.infrastructure.api.v1.api import api_router
from app.infrastructure.config.config import settings, validate_runtime_security, get_cors_origins
from app.infrastructure.database.session import validate_database_security
from app.infrastructure.api.exception_handlers import setup_exception_handlers


def configure_logging(app_env: str) -> None:
    """Hace visibles los logs de la aplicacion bajo uvicorn.

    Uvicorn configura sus propios loggers y deja el root sin handlers, asi que el
    arbol 'app.*' quedaba en WARNING por defecto: todo logger.info del codigo se
    descartaba en silencio. Eso volvia inservible al notificador de recuperacion de
    contraseña, cuya unica funcion es escribir el codigo en la consola del backend.

    En produccion se mantiene en WARNING: ahi los INFO son ruido, y ademas es donde
    no debe existir un notificador que escriba codigos.
    """
    nivel = logging.WARNING if app_env == "production" else logging.INFO
    app_logger = logging.getLogger("app")
    app_logger.setLevel(nivel)

    if not app_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(levelname)s:     %(name)s - %(message)s"))
        app_logger.addHandler(handler)


@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_runtime_security()
    validate_database_security(settings.APP_ENV)
    configure_logging(settings.APP_ENV)
    yield


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)
setup_exception_handlers(app)

# CORS por entorno: comodin solo fuera de produccion (Expo sirve desde IP/puertos de LAN
# variables); en produccion la lista es explicita y obligatoria.
cors_origins = get_cors_origins()

# "*" junto a allow_credentials=True es invalido por especificacion y habilita peticiones
# autenticadas desde cualquier origen. La autenticacion viaja en el header Authorization,
# no en cookies, por lo que el modo credentials solo se activa con origenes explicitos.
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials="*" not in cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {"status": "ok", "message": "TutorIA backend corriendo con Arquitectura Hexagonal"}
