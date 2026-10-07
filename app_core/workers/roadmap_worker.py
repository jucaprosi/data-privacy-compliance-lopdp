"""Worker de generación de roadmaps con IA.

- Consume jobs de la cola Redis (roadmap_jobs).
- Llama a DeepSeek con prompts.
- Valida respuesta con RoadmapDocument.
- Persiste olas y tareas.
- Actualiza el estado del job.

Ejecución manual:
    python -m app_core.workers.roadmap_worker
"""
import asyncio
import json
import logging
import time
from uuid import uuid4

from sqlalchemy import text

from app_core.ai.deepseek_client import call_llm
from app_core.ai.roadmap_prompts import SYSTEM_PROMPT, build_roadmap_prompt
from app_core.db.session import async_session_factory
from app_core.queue.redis_client import pop_job, set_job_status
from app_core.schemas.roadmap_schema import RoadmapDocument

logger = logging.getLogger(__name__)
POLL_INTERVAL = 2


async def _set_session_context(session, tenant_id: str, user_id: str) -> None:
    await session.execute(
        text("SET LOCAL app.current_tenant_id = :tid"), {"tid": tenant_id}
    )
    await session.execute(
        text("SET LOCAL app.current_user_id = :uid"), {"uid": user_id}
    )


async def process_job(job_id: str) -> None:
    """Procesa un job: llama al LLM, valida, persiste."""
    from app_core.queue.redis_client import get_job_status

    job_data = get_job_status(job_id)
    if not job_data or "payload" not in job_data:
        logger.error(f"Job {job_id}: sin payload")
        set_job_status(job_id, "failed", {"error": "sin_payload"})
        return

    payload = job_data["payload"]
    roadmap_id = payload["roadmap_id"]
    tenant_id = payload["tenant_id"]
    user_id = payload["user_id"]
    variables = payload["variables"]
    assessment = payload.get("assessment", {})

    set_job_status(job_id, "running")

    # Construir prompt
    prompt = build_roadmap_prompt(assessment, variables)

    # Llamar al LLM (1 intento + 1 reintento correctivo)
    doc: RoadmapDocument | None = None
    for intento in range(2):
        try:
            raw = call_llm(SYSTEM_PROMPT, prompt, json_mode=True)
            data = json.loads(raw)
            data["roadmap_id"] = roadmap_id
            data["tenant_id"] = tenant_id
            doc = RoadmapDocument.model_validate(data)
            break
        except Exception as e:
            logger.warning(f"Job {job_id}: intento {intento+1} falló: {e}")
            if intento == 1:
                set_job_status(job_id, "failed", {"error": str(e)[:500]})
                return
            prompt = (
                prompt
                + "\n\nCORRECCIÓN: La respuesta anterior no cumplió el esquema. "
                + "Verifica que cada tarea tenga control_ref P1-P73 y dimension D01-D10."
            )

    if doc is None:
        set_job_status(job_id, "failed", {"error": "sin_documento"})
        return

    # Persistir
    async with async_session_factory() as session:
        await _set_session_context(session, tenant_id, user_id)
        try:
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
            set_job_status(
                job_id,
                "completed",
                {"roadmap_id": roadmap_id, "waves": len(doc.olas)},
            )
            logger.info(f"Job {job_id}: roadmap {roadmap_id} generado")
        except Exception as e:
            await session.rollback()
            logger.exception(f"Job {job_id}: error persistiendo")
            set_job_status(job_id, "failed", {"error": str(e)[:500]})


def run_worker() -> None:
    """Loop principal. Polling adaptativo sobre la cola Redis."""
    logger.info("Worker de roadmaps iniciado")
    while True:
        try:
            job_id = pop_job()
            if not job_id:
                time.sleep(POLL_INTERVAL)
                continue
            asyncio.run(process_job(job_id))
        except KeyboardInterrupt:
            logger.info("Worker detenido por usuario")
            break
        except Exception:
            logger.exception("Error en loop principal")
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_worker()
