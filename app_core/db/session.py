"""Async session factory para FastAPI.

La infraestructura queda aislada de las migraciones y no abre ninguna
conexión hasta que una dependencia solicite una sesión. PostgreSQL usa
psycopg3 en modo asíncrono mediante SQLAlchemy 2.0.
"""

import os
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL no definida")

# Normalizar a dialecto async. El dialecto psycopg3 selecciona su conexión
# asíncrona cuando se usa desde create_async_engine.
_async_url = DATABASE_URL
if _async_url.startswith("postgresql://"):
    _async_url = _async_url.replace(
        "postgresql://", "postgresql+psycopg://", 1
    )

engine = create_async_engine(_async_url, pool_pre_ping=True, future=True)
async_session_factory = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_session(
    x_user_id: str | None = None,
    x_tenant_id: str | None = None,
) -> AsyncGenerator[AsyncSession, None]:
    """Dependency FastAPI que inyecta el contexto RLS de usuario y tenant."""

    async with async_session_factory() as session:
        if x_tenant_id:
            await session.execute(
                text("SET LOCAL app.current_tenant_id = :tid"),
                {"tid": x_tenant_id},
            )
        if x_user_id:
            await session.execute(
                text("SET LOCAL app.current_user_id = :uid"),
                {"uid": x_user_id},
            )
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
