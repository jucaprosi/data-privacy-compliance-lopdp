# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤adpa
# ¤¤developer-architect
"""Capacidades globales explícitas. No infiere permisos de roles empresariales."""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app_core.errors import ErrorNegocio
from features.biblioteca.domain.editorial import Capacidad


# ¤adpa
async def capacidades(session: AsyncSession, actor: str) -> list[str]:
    # Reemplaza cualquier contexto recibido por cabecera con la identidad ya verificada.
    await session.execute(text("SELECT set_config('app.current_user_id', :actor, true)"), {"actor": actor})
    filas = await session.execute(text(
        "SELECT capacidad FROM biblioteca_capacidades c JOIN users u ON u.id=c.usuario_id "
        "WHERE c.usuario_id=:actor AND c.revocada_en IS NULL AND u.activo AND u.deleted_at IS NULL"
    ), {"actor": actor})
    permisos = list(filas.scalars())
    # R1 (BIB-411): una capacidad solo cuenta si su titular es operador activo; la baja no toca filas (R4).
    if permisos and not await _operador_activo(session, actor):
        return []
    return permisos


# ¤adpa
async def _operador_activo(session: AsyncSession, usuario_id: str) -> bool:
    from app_core.pasillo import plataforma as pasillo_plataforma

    return bool(await pasillo_plataforma.operador_activo(session, usuario_id))


# ¤adpa
async def autorizar(session: AsyncSession, actor: str, requerida: Capacidad | None = None) -> list[str]:
    permisos = await capacidades(session, actor)
    if not permisos or (requerida is not None and requerida.value not in permisos):
        raise ErrorNegocio("BIB_SIN_CAPACIDAD")
    return permisos
