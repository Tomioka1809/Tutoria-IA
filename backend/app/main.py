from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.infrastructure.api.v1.api import api_router
from app.infrastructure.config.config import settings, validate_runtime_security
from app.infrastructure.database.session import validate_database_security
from app.infrastructure.api.exception_handlers import setup_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_runtime_security()
    validate_database_security(settings.APP_ENV)
    yield


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)
setup_exception_handlers(app)

# Enable CORS for React Native / Expo development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {"status": "ok", "message": "TutorIA backend corriendo con Arquitectura Hexagonal"}
