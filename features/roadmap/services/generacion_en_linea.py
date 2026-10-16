# ¤roadmap ¤adpa
"""Motor de generación en línea de la hoja de ruta (sala ADPA: Hoja de Ruta).

Decisión D-1:
En el plan gratuito de Vercel (maxDuration: 300 s), la generación se ejecuta
directamente dentro de la solicitud HTTP en un hilo independiente (asyncio.to_thread)
para no bloquear el bucle de eventos, sin necesidad de worker asíncrono en cola.

Si ocurre un fallo en la generación o en la persistencia:
- El registro de la hoja de ruta en BD se marca como status = 'failed' con el motivo
  almacenado en summary.
- El job en Redis se marca con status = 'failed' y detalle del error.
- El cliente recibe respuesta con status = 'failed' y puede reintentar.
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Callable, Optional
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from features.roadmap.domain.models import GenerateRoadmapRequest, RoadmapDocument
from features.roadmap.services.contexto_tenant import set_session_context
from features.roadmap.services.generacion_engine import generate_roadmap_document

logger = logging.getLogger(__name__)


async def generate_roadmap_inline(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    request: GenerateRoadmapRequest,
    *,
    llm_caller: Optional[Callable[[str, str], str]] = None,
) -> dict[str, Any]:
    """Ejecuta la generación de hoja de ruta en línea y persiste olas y tareas.

    Retorna un diccionario con `{job_id, status, roadmap_id}`.
    """
    await set_session_context(session, tenant_id, user_id)

    roadmap_id = str(uuid4())
    job_id = str(uuid4())

    # 1. Crear registro inicial en estado draft
    await session.execute(
        text("""
            INSERT INTO roadmaps (id, tenant_id, status, variables_json, summary)
            VALUES (:id, :tenant_id, 'draft', CAST(:vars AS JSON), :summary)
        """),
        {
            "id": roadmap_id,
            "tenant_id": tenant_id,
            "vars": request.variables.model_dump_json(),
            "summary": "Roadmap en generación en línea",
        },
    )
    await session.commit()

    # Actualizar estado de job inicial en Redis si redis_client está disponible
    try:
        from app_core.queue.redis_client import set_job_status
        set_job_status(
            job_id,
            "running",
            {
                "roadmap_id": roadmap_id,
                "tenant_id": tenant_id,
                "user_id": user_id,
            },
        )
    except Exception as exc:
        logger.warning("No se pudo registrar estado inicial del job en Redis: %s", exc)

    # 2. Generar documento con IA en un hilo aparte (asyncio.to_thread)
    doc: Optional[RoadmapDocument] = None
    generation_error: Optional[Exception] = None

    try:
        doc = await asyncio.to_thread(
            generate_roadmap_document,
            assessment=request.assessment,
            variables=request.variables.model_dump(),
            roadmap_id=roadmap_id,
            tenant_id=tenant_id,
            llm_caller=llm_caller,
        )
    except Exception as exc:
        logger.exception("Fallo durante la llamada de generación de roadmap con IA: %s", exc)
        generation_error = exc

    # 3. Si falló la generación, marcar roadmap como failed y notificar
    if doc is None or generation_error is not None:
        err_msg = str(generation_error)[:500] if generation_error else "Error desconocido en generación"
        try:
            await set_session_context(session, tenant_id, user_id)
            await session.execute(
                text("""
                    UPDATE roadmaps
                    SET status = 'failed',
                        summary = :error_summary,
                        updated_at = now()
                    WHERE id = :rid AND tenant_id = :tid
                """),
                {
                    "error_summary": f"Fallo de generación: {err_msg}",
                    "rid": roadmap_id,
                    "tid": tenant_id,
                },
            )
            await session.commit()
        except Exception as db_exc:
            await session.rollback()
            logger.exception("Error al marcar roadmap como failed en BD: %s", db_exc)

        try:
            from app_core.queue.redis_client import set_job_status
            set_job_status(job_id, "failed", {"error": err_msg, "roadmap_id": roadmap_id})
        except Exception:
            pass

        return {
            "job_id": job_id,
            "status": "failed",
            "roadmap_id": roadmap_id,
        }

    # 4. Persistir olas y tareas estructuradas
    try:
        await set_session_context(session, tenant_id, user_id)
        await session.execute(
            text("""
                UPDATE roadmaps
                SET status = 'generated',
                    summary = :summary,
                    score_objetivo = :score,
                    updated_at = now()
                WHERE id = :rid AND tenant_id = :tid
            """),
            {
                "summary": doc.resumen_ejecutivo,
                "score": doc.kpis_globales.score_objetivo,
                "rid": roadmap_id,
                "tid": tenant_id,
            },
        )

        for sort_order, wave in enumerate(doc.olas, start=1):
            wave_id = str(uuid4())
            await session.execute(
                text("""
                    INSERT INTO roadmap_waves
                        (id, roadmap_id, tenant_id, name, start_date, end_date, objective, sort_order)
                    VALUES
                        (:id, :rid, :tid, :name, :start, :end, :obj, :so)
                """),
                {
                    "id": wave_id,
                    "rid": roadmap_id,
                    "tid": tenant_id,
                    "name": wave.nombre,
                    "start": None,
                    "end": None,
                    "obj": wave.objetivo,
                    "so": sort_order,
                },
            )

            for task in wave.tareas:
                task_id = str(uuid4())
                await session.execute(
                    text("""
                        INSERT INTO roadmap_tasks
                            (id, wave_id, tenant_id, control_ref, dimension, title,
                             description, owner, priority, effort_hours,
                             start_date, end_date, status, kpi, deliverable, evidence_required)
                        VALUES
                            (:id, :wid, :tid, :ctrl, :dim, :title,
                             :desc, :owner, :prio, :effort,
                             :start, :end, 'pendiente', :kpi, :deliv, CAST(:ev AS JSON))
                    """),
                    {
                        "id": task_id,
                        "wid": wave_id,
                        "tid": tenant_id,
                        "ctrl": task.control_ref,
                        "dim": task.dimension,
                        "title": task.titulo,
                        "desc": task.descripcion,
                        "owner": task.responsable,
                        "prio": task.prioridad.value,
                        "effort": task.esfuerzo_estimado_horas,
                        "start": task.fecha_inicio,
                        "end": task.fecha_fin,
                        "kpi": task.kpi,
                        "deliv": task.entregable,
                        "ev": json.dumps(task.evidencia_requerida, ensure_ascii=False),
                    },
                )

        await session.commit()

        try:
            from app_core.queue.redis_client import set_job_status
            set_job_status(
                job_id,
                "completed",
                {"roadmap_id": roadmap_id, "waves": len(doc.olas)},
            )
        except Exception:
            pass

        return {
            "job_id": job_id,
            "status": "completed",
            "roadmap_id": roadmap_id,
        }

    except Exception as exc:
        await session.rollback()
        logger.exception("Error al persistir olas y tareas del roadmap: %s", exc)
        err_msg = str(exc)[:500]

        try:
            await set_session_context(session, tenant_id, user_id)
            await session.execute(
                text("""
                    UPDATE roadmaps
                    SET status = 'failed',
                        summary = :error_summary,
                        updated_at = now()
                    WHERE id = :rid AND tenant_id = :tid
                """),
                {
                    "error_summary": f"Fallo al persistir: {err_msg}",
                    "rid": roadmap_id,
                    "tid": tenant_id,
                },
            )
            await session.commit()
        except Exception:
            await session.rollback()

        try:
            from app_core.queue.redis_client import set_job_status
            set_job_status(job_id, "failed", {"error": err_msg, "roadmap_id": roadmap_id})
        except Exception:
            pass

        return {
            "job_id": job_id,
            "status": "failed",
            "roadmap_id": roadmap_id,
        }
