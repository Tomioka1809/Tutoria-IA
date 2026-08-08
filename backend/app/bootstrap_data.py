"""Inicializacion idempotente de datos, pensada para el arranque en Docker.

Cada bloque se salta si la tabla correspondiente ya tiene registros. Esto es
deliberado: `seed_users` y `seed` borran datos antes de insertar, asi que
ejecutarlos sin condicion en cada arranque destruiria la informacion existente.
Aca solo se siembra lo que falta.
"""
import asyncio
import os

from sqlalchemy import func, select

import app.infrastructure.database.base  # noqa: F401  registra todos los modelos
from app.infrastructure.config.config import DEFAULT_ADMIN_PASSWORD, resolve_admin_bootstrap
from app.infrastructure.database.models.corpus_chunk import CorpusChunk
from app.infrastructure.database.models.profiles import AdminProfile
from app.infrastructure.database.models.user import User
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.security.security import get_password_hash


async def _count(db, model, *conditions) -> int:
    stmt = select(func.count()).select_from(model)
    if conditions:
        stmt = stmt.where(*conditions)
    return (await db.execute(stmt)).scalar_one()


async def ensure_admin() -> None:
    """Crea el admin inicial si la base todavia no tiene ninguno.

    Fuera de produccion no hace falta configurar nada: cae a las credenciales por
    defecto del repositorio. Antes dependia de que el .env declarara ADMIN_EMAIL y
    ADMIN_PASSWORD, y como .env.example los trae vacios, un clon recien levantado
    quedaba con el roster de tutores y estudiantes pero sin nadie que pudiera entrar
    al panel de administracion.
    """
    async with SessionLocal() as db:
        if await _count(db, User, User.role == "admin"):
            print("[bootstrap] Ya existe al menos un admin, no se crea otro.")
            return

        app_env = os.getenv("APP_ENV", "development")
        # La validacion vive aca ademas de en validate_runtime_security porque el
        # entrypoint siembra antes de arrancar la app: sin esto, produccion podria
        # crear el admin debil y recien despues fallar al levantar uvicorn.
        credenciales = resolve_admin_bootstrap(app_env)

        if credenciales is None:
            print(
                "[bootstrap] No hay admin y no se declararon ADMIN_EMAIL/ADMIN_PASSWORD. "
                "Crealo a mano con: python -m app.create_superuser"
            )
            return

        email, password, full_name = credenciales

        admin = User(
            email=email,
            password_hash=get_password_hash(password),
            role="admin",
            is_active=True,
        )
        admin.admin_profile = AdminProfile(
            full_name=full_name,
            administrative_position="Superadmin",
        )
        db.add(admin)
        await db.commit()
        print(f"[bootstrap] Admin '{email}' creado.")

        if password == DEFAULT_ADMIN_PASSWORD:
            print(
                "[bootstrap] ATENCION: se uso la contraseña por defecto del repositorio. "
                "Cambiala antes de exponer este backend fuera de tu maquina."
            )


async def ensure_users() -> None:
    """Carga el roster de tutores y estudiantes solo si no hay ninguno cargado."""
    async with SessionLocal() as db:
        existing = await _count(db, User, User.role.in_(["tutor", "estudiante"]))

    if existing:
        print(f"[bootstrap] Ya hay {existing} tutores/estudiantes, se omite el roster.")
        return

    from app.infrastructure.database.seed_users import seed_users

    print("[bootstrap] Base sin tutores ni estudiantes, cargando roster...")
    await seed_users()


async def ensure_corpus() -> None:
    """Pone el indice del RAG al dia desde el corpus estructurado.

    Usa la ingesta incremental y no el seed antiguo: aquel leia el corpus
    heredado -la parafrasis sin articulado- y borraba corpus_chunks entero antes
    de reescribirlo, de modo que un arranque limpio habria pisado el corpus
    extraido de los PDF oficiales.

    Ya no hace falta el guardado de "solo si esta vacio": la ingesta compara
    hashes y unicamente embebe lo que falta, asi que reejecutarla es barato.
    """
    async with SessionLocal() as db:
        existing = await _count(db, CorpusChunk)

    if not os.getenv("GEMINI_API_KEY"):
        print(f"[bootstrap] Falta GEMINI_API_KEY, se omite la ingesta ({existing} chunks).")
        return

    if os.getenv("AUTO_SEED_CORPUS", "1") != "1":
        print(f"[bootstrap] AUTO_SEED_CORPUS=0, se omite la ingesta ({existing} chunks).")
        return

    from scripts.ingest_corpus import ingestar

    print(f"[bootstrap] Actualizando el indice del RAG ({existing} chunks ya indexados)...")
    try:
        await ingestar()
    except Exception as exc:
        # La cuota de Gemini puede agotarse a mitad de camino. La ingesta es
        # reanudable, asi que el arranque continua en vez de fallar: lo indexado
        # queda intacto y la proxima corrida sigue donde quedo.
        print(f"[bootstrap] Ingesta interrumpida ({type(exc).__name__}). Reanudable.")


async def bootstrap() -> None:
    await ensure_admin()
    await ensure_users()
    await ensure_corpus()
    print("[bootstrap] Datos iniciales verificados.")


if __name__ == "__main__":
    asyncio.run(bootstrap())
