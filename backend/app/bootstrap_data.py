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
    """Crea el admin inicial desde variables de entorno si todavia no hay ninguno."""
    async with SessionLocal() as db:
        if await _count(db, User, User.role == "admin"):
            print("[bootstrap] Ya existe al menos un admin, no se crea otro.")
            return

        email = os.getenv("ADMIN_EMAIL")
        password = os.getenv("ADMIN_PASSWORD")
        if not email or not password:
            print(
                "[bootstrap] No hay admin y faltan ADMIN_EMAIL/ADMIN_PASSWORD. "
                "Crealo a mano con: python -m app.create_superuser"
            )
            return

        admin = User(
            email=email,
            password_hash=get_password_hash(password),
            role="admin",
            is_active=True,
        )
        admin.admin_profile = AdminProfile(
            full_name=os.getenv("ADMIN_NAME", "Administrador"),
            administrative_position="Superadmin",
        )
        db.add(admin)
        await db.commit()
        print(f"[bootstrap] Admin '{email}' creado.")


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
    """Genera el corpus del RAG solo si esta vacio (consume cuota de Gemini)."""
    async with SessionLocal() as db:
        existing = await _count(db, CorpusChunk)

    if existing:
        print(f"[bootstrap] Corpus ya tiene {existing} chunks, se omite el seeding.")
        return

    if not os.getenv("GEMINI_API_KEY"):
        print("[bootstrap] Corpus vacio pero falta GEMINI_API_KEY, se omite el seeding.")
        return

    if os.getenv("AUTO_SEED_CORPUS", "1") != "1":
        print("[bootstrap] AUTO_SEED_CORPUS=0, se omite el seeding del corpus.")
        return

    from app.infrastructure.database.seed import seed_database

    print("[bootstrap] Corpus vacio, generando embeddings (puede tardar varios minutos)...")
    await seed_database()


async def bootstrap() -> None:
    await ensure_admin()
    await ensure_users()
    await ensure_corpus()
    print("[bootstrap] Datos iniciales verificados.")


if __name__ == "__main__":
    asyncio.run(bootstrap())
