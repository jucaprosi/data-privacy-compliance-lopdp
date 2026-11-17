# ¤¤backend-developer
# ¤api-integraciones ¤boveda-cloud
"""Techos de uso y consumo de integraciones por organización (API-02).

Consulta los techos del paquete de la organización en Bóveda Cloud (BOV-01)
a través de `app_core.pasillo.boveda_cloud.techos_integracion`.
"""
from typing import Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.errores import ErrorNegocio
from app_core.pasillo import boveda_cloud


async def obtener_techos_integracion(session: AsyncSession, tenant_id: str) -> dict[str, Any]:
    """Devuelve los techos de claves y webhooks con sus contadores de uso activo."""
    # 1. Obtener límites de paquete vía pasillo boveda_cloud
    techos_paquete = await boveda_cloud.techos_integracion(session, tenant_id)
    max_claves = techos_paquete.get("claves")
    max_webhooks = techos_paquete.get("webhooks")

    # 2. Contar claves de integración activas (ni revocadas ni rotadas)
    res_claves = await session.execute(
        text(
            """
            SELECT COUNT(*) FROM claves_integracion
            WHERE tenant_id = :tenant_id
              AND revocada_en IS NULL
              AND rotada_en IS NULL
            """
        ),
        {"tenant_id": tenant_id},
    )
    claves_activas = int(res_claves.scalar() or 0)

    # 3. Webhooks activos: 0 hasta API-02b
    webhooks_activos = 0

    # === API-02b ===
    # --- INICIO API-02b ---
    # Sección sembrada para suscripciones y conteo de webhooks activos en API-02b
    # --- FIN API-02b ---
    # === fin API-02b ===

    return {
        "claves": {
            "maximo": max_claves,
            "activas": claves_activas,
        },
        "webhooks": {
            "maximo": max_webhooks,
            "activos": webhooks_activos,
        },
    }


async def verificar_techo_claves(session: AsyncSession, tenant_id: str) -> None:
    """Valida si el tenant puede crear una nueva clave activa; 409 TECHO_CLAVES_ALCANZADO si excede."""
    techos = await obtener_techos_integracion(session, tenant_id)
    maximo = techos["claves"]["maximo"]
    activas = techos["claves"]["activas"]

    if maximo is not None and activas >= maximo:
        raise ErrorNegocio(
            "TECHO_CLAVES_ALCANZADO",
            detail=f"Se ha alcanzado el límite de claves de integración permitidas por el paquete ({maximo}).",
            status_code=409,
        )
