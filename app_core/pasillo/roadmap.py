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
# Sección reservada para ORG-15 (cartera por pertenencia).
# === fin ORG-15 ===

# === DIAG-12 ===
# ¤roadmap ¤diagnostico-estados Lectura de las tareas cerradas con evidencia validada, para los estados del diagnóstico.
async def tareas_cerradas_con_evidencia_validada(session: AsyncSession, tenant_id: str, user_id: str) -> list[dict]:
    """Tareas `completada` con al menos una evidencia aprobada por el DPO o el auditor, distinto de quien la subió.

    El rol es el vigente en la organización, no el que tenía al validar. `task_evidence` no guarda la primera
    validación del coordinador, así que hoy no se comprueba (queda como ficha aparte de roadmap).

    Cuatro ojos (INV_LOPDP_FOUR_EYES_CLOSURE): una tarea sin evidencia aprobada, o cuya evidencia aprobó
    quien la subió, no cuenta. Devuelve `tarea_id`, `control_ref` ("P12") y `cerrada_en`, por tarea.
    """
    from sqlalchemy import text

    from app_core.db.session import fijar_contexto_rls

    await fijar_contexto_rls(session, tenant_id, user_id)
    filas = await session.execute(
        text(
            "SELECT t.id AS tarea_id, t.control_ref AS control_ref, t.completed_at AS cerrada_en "
            "FROM roadmap_tasks t "
            "WHERE t.tenant_id = :t AND t.status = 'completada' AND EXISTS ("
            "  SELECT 1 FROM task_evidence e WHERE e.task_id = t.id AND e.tenant_id = :t "
            "  AND e.validation_status = 'approved' AND e.validated_by IS NOT NULL "
            "  AND e.uploaded_by IS NOT NULL AND e.validated_by <> e.uploaded_by "
            "  AND EXISTS (SELECT 1 FROM user_tenant_roles r WHERE r.user_id = e.validated_by "
            "  AND r.tenant_id = :t AND r.role IN ('dpo', 'auditor'))) "
            "ORDER BY t.control_ref, t.id"
        ),
        {"t": tenant_id},
    )
    return [dict(f) for f in filas.mappings().all()]
# === fin DIAG-12 ===

# === DIAG-07 ===
# Sección reservada para DIAG-07.
# === fin DIAG-07 ===
