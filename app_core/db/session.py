"""Async session factory para FastAPI.

La infraestructura queda aislada de las migraciones y no abre ninguna
conexión hasta que una dependencia solicite una sesión. PostgreSQL usa
psycopg3 en modo asíncrono mediante SQLAlchemy 2.0.
"""

import os
from contextvars import ContextVar
from typing import AsyncGenerator

from fastapi import Depends, Header
from sqlalchemy import text
from sqlalchemy.exc import ArgumentError
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app_core.security import get_current_tenant


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


# Propaga el tenant actual de forma segura en código asíncrono (lo fija get_tenant_session).
current_tenant_id: ContextVar[str] = ContextVar(
    "current_tenant_id", default="00000000-0000-0000-0000-000000000000"
)


async def fijar_contexto_rls(
    session: AsyncSession,
    tenant_id: str | None = None,
    user_id: str | None = None,
) -> None:
    """Fija tenant y usuario en la transacción para que las políticas RLS los evalúen.

    Única vía para escribir app.current_tenant_id / app.current_user_id: set_config con
    parámetros enlazados (is_local = true equivale a SET LOCAL), nunca texto interpolado.
    """
    if tenant_id:
        await session.execute(
            text("SELECT set_config('app.current_tenant_id', :tid, true)"),
            {"tid": tenant_id},
        )
    if user_id:
        await session.execute(
            text("SELECT set_config('app.current_user_id', :uid, true)"),
            {"uid": user_id},
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
        await fijar_contexto_rls(session, x_tenant_id, x_user_id)
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_tenant_session(
    tenant_id: str = Depends(get_current_tenant),
) -> AsyncGenerator[AsyncSession, None]:
    """Sesión cuyo tenant sale de la identidad autenticada (Authorization), no de cabeceras.

    Es la sesión de los endpoints que resuelven el tenant con get_current_tenant: sin
    credencial válida responde 401 antes de abrir la sesión.
    """
    current_tenant_id.set(tenant_id)
    async with async_session_factory() as session:
        await fijar_contexto_rls(session, tenant_id)
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
