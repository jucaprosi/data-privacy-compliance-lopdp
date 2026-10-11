"""Consulta de la hoja de ruta y sus KPIs (sala ADPA: Hoja de Ruta)."""
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from features.roadmap.services.contexto_tenant import set_session_context


async def get_roadmap(
    session: AsyncSession,
    tenant_id: str,
    roadmap_id: str,
) -> Optional[dict]:
    """Devuelve roadmap con waves, tasks y evidence."""
    await set_session_context(session, tenant_id)

    rm = (await session.execute(
        text("SELECT * FROM roadmaps WHERE id = :id AND tenant_id = :tid"),
        {"id": roadmap_id, "tid": tenant_id},
    )).mappings().first()
    if not rm:
        return None

    waves = (await session.execute(
        text("SELECT * FROM roadmap_waves WHERE roadmap_id = :rid ORDER BY sort_order"),
        {"rid": roadmap_id},
    )).mappings().all()

    result = {"roadmap": dict(rm), "waves": []}
    for w in waves:
        tasks = (await session.execute(
            text("SELECT * FROM roadmap_tasks WHERE wave_id = :wid ORDER BY start_date"),
            {"wid": w["id"]},
        )).mappings().all()
        wave = dict(w)
        wave["tasks"] = [dict(t) for t in tasks]
        result["waves"].append(wave)
    return result


async def get_kpis(
    session: AsyncSession,
    tenant_id: str,
    roadmap_id: str,
) -> dict:
    """KPIs agregados por roadmap."""
    await set_session_context(session, tenant_id)

    row = (await session.execute(
        text("""
            SELECT
                COUNT(*) FILTER (WHERE t.status = 'completada') AS completadas,
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE t.priority = 'critica') AS criticas,
                COUNT(*) FILTER (WHERE t.priority = 'alta') AS altas
            FROM roadmap_tasks t
            JOIN roadmap_waves w ON t.wave_id = w.id
            WHERE w.roadmap_id = :rid AND t.tenant_id = :tid
        """),
        {"rid": roadmap_id, "tid": tenant_id},
    )).mappings().first()

    total = row["total"] or 0
    completadas = row["completadas"] or 0
    return {
        "total_tareas": total,
        "completadas": completadas,
        "criticas": row["criticas"] or 0,
        "altas": row["altas"] or 0,
        "progreso_porcentaje": round(completadas * 100 / total, 1) if total else 0.0,
    }
