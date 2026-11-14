# ¤adpa
"""Capacidades de la sala Hoja de Ruta para otras salas."""
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession


async def registrar_hallazgo_de_control_vencido(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    origen_ref: str,
    titulo: str,
    control_ref: Optional[str],
) -> tuple[str, bool]:
    from features.roadmap import roadmap_service

    return await roadmap_service.registrar_hallazgo(
        session,
        tenant_id,
        user_id,
        origen=roadmap_service.OrigenHallazgo.control_periodico.value,
        origen_ref=origen_ref,
        severidad=roadmap_service.SeveridadHallazgo.alta.value,
        titulo=titulo[:roadmap_service.TITULO_MAX],
        control_ref=control_ref,
    )


async def cerrar_hallazgo(session: AsyncSession, tenant_id: str, user_id: str, hallazgo_id: str) -> None:
    from features.roadmap import roadmap_service

    await roadmap_service.cerrar_hallazgo(session, tenant_id, user_id, hallazgo_id)


# === RAT-05 ===
async def registrar_hallazgo_rat(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    origen_ref: str,
    severidad: str,
    titulo: str,
    control_ref: Optional[str],
    dimension: Optional[str],
) -> tuple[str, bool]:
    from features.roadmap import roadmap_service

    return await roadmap_service.registrar_hallazgo(
        session,
        tenant_id,
        user_id,
        origen=roadmap_service.OrigenHallazgo.rat.value,
        origen_ref=origen_ref,
        severidad=severidad,
        titulo=titulo[:roadmap_service.TITULO_MAX],
        control_ref=control_ref,
        dimension=dimension,
    )


async def listar_hallazgos_rat(session: AsyncSession, tenant_id: str, user_id: str) -> list:
    from features.roadmap import roadmap_service

    return await roadmap_service.listar_hallazgos(
        session, tenant_id, user_id, origen=roadmap_service.OrigenHallazgo.rat.value
    )


async def reabrir_hallazgo(session: AsyncSession, tenant_id: str, user_id: str, hallazgo_id: str) -> None:
    from features.roadmap import roadmap_service

    await roadmap_service.reabrir_hallazgo(session, tenant_id, user_id, hallazgo_id)
# === fin RAT-05 ===


# === ADPA-06 ===
# ¤adpa Sección reservada del andamiaje ADPA-06 en este pasillo.
# === fin ADPA-06 ===


# === DEMO-03c ===
# ¤demo Copia y siembra de la sala para la demo «Cooperativa Demo»; la lógica vive en el motor de la sala.
async def clonar_desde_plantilla(session: AsyncSession, origen: str, destino: str, mapa_ids: dict) -> dict:
    from features.roadmap import roadmap_service

    return await roadmap_service.clonar_desde_plantilla(session, origen, destino, mapa_ids)


async def sembrar_en_plantilla(session: AsyncSession, plantilla_id: str, datos: dict) -> None:
    from features.roadmap import roadmap_service

    await roadmap_service.sembrar_en_plantilla(session, plantilla_id, datos)
# === fin DEMO-03c ===


# === ORG-15 ===
# ¤cartera
async def contar_hallazgos_abiertos(session: AsyncSession, tenant_id: str, user_id: str) -> int:
    """Hallazgos en estado `abierto` de la organización (fija su contexto RLS)."""
    from features.roadmap import roadmap_service

    abiertos = await roadmap_service.listar_hallazgos(
        session, tenant_id, user_id, estado=roadmap_service.EstadoHallazgo.abierto.value
    )
    return len(abiertos)


async def contar_tareas_vencidas(session: AsyncSession, tenant_id: str, user_id: str) -> int:
    """Tareas sin completar con fecha de fin anterior a hoy en la zona de negocio (fija su contexto RLS)."""
    from features.roadmap import roadmap_service

    return await roadmap_service.contar_tareas_vencidas(session, tenant_id, user_id)
# === fin ORG-15 ===

# === DIAG-12 ===
# ¤roadmap ¤diagnostico-estados Lectura de las tareas cerradas con evidencia validada, para los estados del diagnóstico.
async def tareas_cerradas_con_evidencia_validada(session: AsyncSession, tenant_id: str, user_id: str) -> list[dict]:
    """Tareas cerradas con evidencia aprobada por el DPO; la consulta vive en la sala Hoja de Ruta."""
    from features.roadmap import roadmap_service

    return await roadmap_service.tareas_cerradas_con_evidencia_validada(session, tenant_id, user_id)
# === fin DIAG-12 ===

# === DIAG-07 ===
# Sección reservada para DIAG-07.
# === fin DIAG-07 ===


# === CAPA-04 ===
# Sección reservada para CAPA-04.
# === fin CAPA-04 ===

# === MTGE-03 ===
async def registrar_hallazgo_eipd(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    origen_ref: str,
    titulo: str,
) -> tuple[str, bool]:
    """R2 de MTGE-03: cada punto por corregir de una EIPD es un hallazgo de origen 'eipd' y severidad alta."""
    from features.roadmap import roadmap_service

    return await roadmap_service.registrar_hallazgo(
        session,
        tenant_id,
        user_id,
        origen=roadmap_service.OrigenHallazgo.eipd.value,
        origen_ref=origen_ref,
        severidad=roadmap_service.SeveridadHallazgo.alta.value,
        titulo=titulo[:roadmap_service.TITULO_MAX],
        control_ref=None,
    )
# === fin MTGE-03 ===

# === TER-01 ===
# ¤hallazgos Hallazgos de origen `tercero` (contrato y garantía); cerrar y reabrir usan las funciones de arriba.
async def registrar_hallazgo_tercero(
    session: AsyncSession, tenant_id: str, user_id: str, origen_ref: str, severidad: str, titulo: str
) -> tuple[str, bool]:
    from features.roadmap import roadmap_service

    return await roadmap_service.registrar_hallazgo(
        session,
        tenant_id,
        user_id,
        origen=roadmap_service.OrigenHallazgo.tercero.value,
        origen_ref=origen_ref,
        severidad=severidad,
        titulo=titulo[:roadmap_service.TITULO_MAX],
    )


async def listar_hallazgos_tercero(session: AsyncSession, tenant_id: str, user_id: str) -> list:
    from features.roadmap import roadmap_service

    return await roadmap_service.listar_hallazgos(
        session, tenant_id, user_id, origen=roadmap_service.OrigenHallazgo.tercero.value
    )
# === fin TER-01 ===
