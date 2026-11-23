# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤engine ¤evidencias ¤rbac-tenant
"""Motor de cálculo de cobertura de formación (FOR-01)."""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.pasillo import organizacion as pasillo_organizacion


async def _fijar_rls(session: AsyncSession, tenant_id: str, user_id: str) -> None:
    await session.execute(
        text("SELECT set_config('app.current_tenant_id', :t, true)"),
        {"t": tenant_id},
    )
    await session.execute(
        text("SELECT set_config('app.current_user_id', :u, true)"),
        {"u": user_id},
    )


async def calcular_cobertura(
    session: AsyncSession, tenant_id: str, user_id: str
) -> dict[str, Any]:
    """R3: Calcula personas formadas, obligadas y porcentaje de cobertura."""
    await _fijar_rls(session, tenant_id, user_id)

    # 1. Obtener personas activas del inventario (obligadas)
    personas_activas = await pasillo_organizacion.listar_personas_activas_inventario(session, tenant_id)
    ids_activas = {str(p["id"]) for p in personas_activas}
    obligadas = len(ids_activas)

    # 2. Obtener personas que han aprobado al menos una acción
    rows_formadas = (
        await session.execute(
            text(
                """
                SELECT DISTINCT p.persona_id
                FROM formacion_participaciones p
                JOIN formacion_acciones a ON a.id = p.accion_id AND a.tenant_id = p.tenant_id
                WHERE p.tenant_id = :t
                  AND p.terminado_en IS NOT NULL
                  AND p.nota >= a.nota_minima
                """
            ),
            {"t": tenant_id},
        )
    ).scalars().all()

    # Contar únicamente personas activas
    formadas_set = {str(pid) for pid in rows_formadas if str(pid) in ids_activas}
    formadas = len(formadas_set)

    cobertura = round(formadas / obligadas, 2) if obligadas > 0 else 0.0

    return {
        "formadas": formadas,
        "obligadas": obligadas,
        "cobertura": cobertura,
    }
