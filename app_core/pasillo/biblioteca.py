# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
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

# === BIB-406 ===
async def proponer_por_resolucion(session, id_resolucion: str, estado: str, estado_anterior: str | None,
                                  actor: str) -> dict:
    """La sala normativa la llama tras revisar una resolución (R1); la IA propone, nunca publica."""
    from features.biblioteca import biblioteca_service

    return await biblioteca_service.proponer_por_resolucion(
        session, id_resolucion, estado, estado_anterior, actor)
# === fin BIB-406 ===

# === RAT-07 ===
# === fin RAT-07 ===

# === BIB-415 ===
# ¤arbitro Lectura mínima para NOTIF-02 (R1, R2): solo leen, por las funciones SECURITY DEFINER de la sala.
_VERSIONES_EN_REVISION = "SELECT id, codigo, titulo, redactada_por, origen_ia, id_resolucion, creada_en FROM biblioteca_versiones_en_revision()"
_REVISORES_TECNICOS = "SELECT usuario_id FROM biblioteca_revisores_tecnicos()"


async def versiones_en_revision(session) -> list[dict]:
    """Una fila por versión `en_revision`: id, código, título, redactada_por, origen_ia, id_resolucion, creada_en."""
    from sqlalchemy import text

    return [dict(f) for f in (await session.execute(text(_VERSIONES_EN_REVISION))).mappings().all()]


async def revisores_tecnicos(session) -> list[str]:
    """Los `usuario_id` con `revisor_tecnico` vigente (sin revocar)."""
    from sqlalchemy import text

    return [f[0] for f in (await session.execute(text(_REVISORES_TECNICOS))).all()]
# === fin BIB-415 ===

# === BIB-411 ===
# === fin BIB-411 ===
