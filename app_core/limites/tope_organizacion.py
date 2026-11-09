# ¤seguridad-tenant ¤copiloto-ia
"""Tope total de generaciones de IA por organización (SEC-13a).

`consumir_generacion` incrementa `usadas` de forma atómica solo si cabe (`UPDATE … WHERE usadas < tope
RETURNING`). Sin fila o con `tope` nulo no hay tope. `fijar_tope` (SEC-13b) es el alta idempotente: crea la
fila o actualiza su tope sin tocar `usadas`. Ambas requieren el contexto RLS del tenant en la sesión.
"""
from __future__ import annotations

from sqlalchemy import text

from app_core.errors import IA_TOPE_ORGANIZACION, ErrorNegocio

_CONSUMIR = text(
    "UPDATE ia_tope_organizacion SET usadas = usadas + 1 "
    "WHERE tenant_id = :t AND tope IS NOT NULL AND usadas < tope RETURNING usadas"
)
_ESTADO = text("SELECT tope FROM ia_tope_organizacion WHERE tenant_id = :t")
_FIJAR = text(
    "INSERT INTO ia_tope_organizacion (tenant_id, tope) VALUES (:t, :tope) "
    "ON CONFLICT (tenant_id) DO UPDATE SET tope = EXCLUDED.tope"
)


async def consumir_generacion(session, tenant_id: str) -> None:
    """Cuenta una generación de IA del tenant; lanza `IA_TOPE_ORGANIZACION` si ya llegó al tope."""
    if (await session.execute(_CONSUMIR, {"t": tenant_id})).first() is not None:
        return
    fila = (await session.execute(_ESTADO, {"t": tenant_id})).first()
    if fila is not None and fila[0] is not None:
        raise ErrorNegocio(IA_TOPE_ORGANIZACION)


async def fijar_tope(session, tenant_id: str, tope: int | None) -> None:
    """Crea o actualiza el tope de IA del tenant (idempotente). No hace commit."""
    await session.execute(_FIJAR, {"t": tenant_id, "tope": tope})
