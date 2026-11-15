# ¤adpa
"""Capacidades de la sala biblioteca para otras salas (pasillo central, ADPA §3).

Cada función importa la compuerta en su cuerpo; aquí no hay lógica de negocio.
Cada tarea escribe solo dentro de su sección reservada.
"""

# === ADPA-06 ===
# Andamiaje del pasillo de esta sala: secciones reservadas abajo.
# === fin ADPA-06 ===

# === FIRMA-02 ===
# ¤firma-electronica Solo reexporta: la lógica vive en la compuerta biblioteca_service.
async def obtener_documento_para_firma(session, tenant_id: str, documento_id: str) -> dict:
    from features.biblioteca import biblioteca_service

    return await biblioteca_service.obtener_documento_para_firma(session, tenant_id, documento_id)


async def hay_documento_aprobado_con_huella(session, tenant_id: str, sha256: str) -> bool:
    from features.biblioteca import biblioteca_service

    return await biblioteca_service.hay_documento_aprobado_con_huella(session, tenant_id, sha256)


async def controles_del_documento(session, tenant_id: str, documento_id: str) -> list[str]:
    from features.biblioteca import biblioteca_service

    return await biblioteca_service.controles_del_documento(session, tenant_id, documento_id)
# === fin FIRMA-02 ===

# === BIB-401 ===
# === fin BIB-401 ===

# === DEMO-03d ===
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


async def clonar_desde_plantilla(
    session: AsyncSession, origen: str, destino: str, mapa_ids: dict[str, str]
) -> dict[str, str]:
    """Copia los documentos de la plantilla al tenant destino (DEMO-02 la llama en su orden)."""
    from features.biblioteca import biblioteca_service

    return await biblioteca_service.clonar_desde_plantilla(session, origen, destino, mapa_ids)


async def sembrar_en_plantilla(session: AsyncSession, plantilla_id: str, datos: Any = None) -> None:
    """Siembra el bloque `biblioteca` de la plantilla (DEMO-03)."""
    from features.biblioteca import biblioteca_service

    await biblioteca_service.sembrar_en_plantilla(session, plantilla_id, datos)
# === fin DEMO-03d ===

# === ORG-15 ===
# === fin ORG-15 ===

# === ORG-17 ===
# === fin ORG-17 ===

# === ORG-18 ===
# === fin ORG-18 ===

# === ORG-20 ===
# === fin ORG-20 ===

# === RAT-07 ===
# === fin RAT-07 ===
