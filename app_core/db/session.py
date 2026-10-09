"""Async session factory para FastAPI.

La infraestructura queda aislada de las migraciones y no abre ninguna
conexión hasta que una dependencia solicite una sesión. PostgreSQL usa
psycopg3 en modo asíncrono mediante SQLAlchemy 2.0.
"""

import os
from typing import AsyncGenerator

from fastapi import Header
from sqlalchemy import text
from sqlalchemy.exc import ArgumentError
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def _clean_url(raw: str) -> str:
    """Quita restos habituales de copiar/pegar la URL en paneles de secretos:
    BOM, espacios, comillas y un prefijo 'DATABASE_URL='."""
    url = raw.strip().lstrip("﻿").strip()
    if url.startswith("DATABASE_URL="):
        url = url[len("DATABASE_URL="):]
    return url.strip().strip("'\"").strip()


def _describe_url(raw: str) -> str:
    """Descripción del valor sin revelar credenciales, para diagnosticar."""
    scheme = raw.split("://", 1)[0][:30] if "://" in raw else "(sin '://')"
    bom = raw.startswith("﻿")
    comillas = raw[:1] in ("'", '"')
    espacios = raw != raw.strip()
    prefijo = raw.lstrip("﻿").startswith("DATABASE_URL=")
    return (
        f"len={len(raw)}, esquema={scheme!r}, bom={bom}, comillas={comillas}, "
        f"espacios={espacios}, prefijo_nombre={prefijo}"
    )


DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL no definida")

# Normalizar a dialecto async. El dialecto psycopg3 selecciona su conexión
# asíncrona cuando se usa desde create_async_engine.
_async_url = _clean_url(DATABASE_URL)
if _async_url.startswith("postgresql://"):
    _async_url = _async_url.replace(
        "postgresql://", "postgresql+psycopg://", 1
    )

try:
    engine = create_async_engine(_async_url, pool_pre_ping=True, future=True)
except ArgumentError as exc:
    raise RuntimeError(f"DATABASE_URL no es una URL válida ({_describe_url(DATABASE_URL)})") from exc
async_session_factory = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_session(
    x_user_id: str | None = Header(None, alias="X-User-ID"),
    x_tenant_id: str | None = Header(None, alias="X-Tenant-ID"),
) -> AsyncGenerator[AsyncSession, None]:
    """Dependency FastAPI que inyecta el contexto RLS de usuario y tenant.

    Lee las cabeceras X-User-ID / X-Tenant-ID; sin Header() FastAPI los
    tomaría de la query string y el contexto nunca se fijaría.
    """

    async with async_session_factory() as session:
        if x_tenant_id:
            await session.execute(
                text("SELECT set_config('app.current_tenant_id', :tid, true)"),
                {"tid": x_tenant_id},
            )
        if x_user_id:
            await session.execute(
                text("SELECT set_config('app.current_user_id', :uid, true)"),
                {"uid": x_user_id},
            )
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
