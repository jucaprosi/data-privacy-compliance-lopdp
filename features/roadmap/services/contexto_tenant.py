"""Contexto de sesión por tenant para RLS (sala ADPA: Hoja de Ruta)."""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def set_session_context(session: AsyncSession, tenant_id: str, user_id: str | None = None) -> None:
    """Inyecta tenant_id y user_id en la sesión para RLS."""
    await session.execute(
        text("SELECT set_config('app.current_tenant_id', :tid, true)"),
        {"tid": tenant_id},
    )
    if user_id:
        await session.execute(
            text("SELECT set_config('app.current_user_id', :uid, true)"),
            {"uid": user_id},
        )
