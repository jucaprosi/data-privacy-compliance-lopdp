"""Contexto de sesión por tenant para RLS (sala ADPA: Organización)."""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def fijar_tenant(session: AsyncSession, tenant_id: str, user_id: str | None = None) -> None:
    """Fija tenant (y usuario) en la transacción: con el rol de app la política RLS oculta
    todas las filas si app.current_tenant_id no está definido."""
    await session.execute(
        text("SELECT set_config('app.current_tenant_id', :tid, true)"),
        {"tid": tenant_id},
    )
    if user_id:
        await session.execute(
            text("SELECT set_config('app.current_user_id', :uid, true)"),
            {"uid": user_id},
        )
