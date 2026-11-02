# ¤roadmap ¤hallazgos ¤rbac-tenant
"""Recordatorios de vencimiento de tareas por correo (RM-23, R2 a R4).

Contrato: governance/especificaciones/RM-23.md §3. Un correo por usuario y día con todas sus tareas. Solo se
anota lo que el proveedor confirmó: lo no enviado se reintenta en la siguiente ejecución. ADPA §3 prohíbe que
esta sala importe `notificaciones`: el envío llega como función desde la capa de API.
"""
from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from features.organizacion import organizacion_service
from features.roadmap.services.cierre_hallazgos_engine import cerrar_por_tareas, reabrir_por_tareas
from features.roadmap.services.contexto_tenant import set_session_context

ZONA_GUAYAQUIL = timezone(timedelta(hours=-5), "America/Guayaquil")
DIAS_AVISO = 7


@dataclass(frozen=True)
class Responsable:
    user_id: str
    email: str
    nombre: str


@dataclass(frozen=True)
class Aviso:
    tarea_id: str
    titulo: str
    control_ref: str
    prioridad: str
    fecha_fin: str
    tipo: str


EnviarAvisos = Callable[[Responsable, list[Aviso]], Awaitable[bool]]


@dataclass(frozen=True)
class ResultadoRecordatorios:
    correos: int
    hallazgos_cerrados: int


def hoy_guayaquil() -> date:
    return datetime.now(ZONA_GUAYAQUIL).date()


def tipo_recordatorio(fin: date, hoy: date) -> str | None:
    """Tipo de aviso que toca hoy para una tarea sin completar que vence en `fin` (R2)."""
    if fin < hoy:
        return "vencida"
    if fin == hoy:
        return "hoy"
    if fin - hoy == timedelta(days=DIAS_AVISO):
        return "7dias"
    return None


async def _tareas_por_avisar(session: AsyncSession, tenant_id: str, hoy: date) -> list[dict]:
    """Tareas sin completar con aviso pendiente hoy. El responsable sale de la última asignación (RM-08)."""
    filas = (
        await session.execute(
            text(
                "SELECT t.id, t.title, t.control_ref, t.priority, t.end_date, "
                "(SELECT a.payload ->> 'responsable_id' FROM task_audit_log a WHERE a.task_id = t.id "
                "AND a.tenant_id = t.tenant_id AND a.action = 'task_assigned' "
                "ORDER BY a.timestamp DESC LIMIT 1) AS responsable_id "
                "FROM roadmap_tasks t WHERE t.tenant_id = :t AND t.status <> 'completada' "
                "AND t.end_date IS NOT NULL AND t.end_date <= :limite ORDER BY t.end_date, t.id"
            ),
            {"t": tenant_id, "limite": hoy + timedelta(days=DIAS_AVISO)},
        )
    ).mappings().all()
    enviados = {
        (f["tarea_id"], f["tipo"])
        for f in (
            await session.execute(
                text(
                    "SELECT tarea_id, tipo FROM recordatorios_enviados "
                    "WHERE tenant_id = :t AND (dia = :hoy OR tipo = 'vencida')"
                ),
                {"t": tenant_id, "hoy": hoy},
            )
        ).mappings().all()
    }
    pendientes = []
    for fila in filas:
        tipo = tipo_recordatorio(fila["end_date"], hoy)
        if tipo and fila["responsable_id"] and (fila["id"], tipo) not in enviados:
            pendientes.append({**fila, "tipo": tipo})
    return pendientes


async def _enviar(session: AsyncSession, tenant_id: str, enviar: EnviarAvisos, hoy: date) -> int:
    pendientes = await _tareas_por_avisar(session, tenant_id, hoy)
    if not pendientes:
        return 0
    usuarios = {
        u["id"]: u for u in await organizacion_service.list_tenant_users(session, tenant_id) if u["activo"]
    }
    por_usuario: dict[str, list[dict]] = {}
    for tarea in pendientes:
        if tarea["responsable_id"] in usuarios:
            por_usuario.setdefault(tarea["responsable_id"], []).append(tarea)

    correos = 0
    for usuario_id, tareas in por_usuario.items():
        usuario = usuarios[usuario_id]
        avisos = [
            Aviso(t["id"], t["title"], t["control_ref"] or "", t["priority"] or "", t["end_date"].isoformat(), t["tipo"])
            for t in tareas
        ]
        if not await enviar(Responsable(usuario_id, usuario["email"], usuario["nombre"]), avisos):
            continue
        correos += 1
        for tarea in tareas:
            await session.execute(
                text(
                    "INSERT INTO recordatorios_enviados (tenant_id, tarea_id, tipo, dia) "
                    "VALUES (:t, :tarea, :tipo, :dia) ON CONFLICT DO NOTHING"
                ),
                {"t": tenant_id, "tarea": tarea["id"], "tipo": tarea["tipo"], "dia": hoy},
            )
    return correos


async def ejecutar_recordatorios(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    enviar: EnviarAvisos,
) -> ResultadoRecordatorios:
    """Corrida diaria de una organización: reabre y cierra hallazgos, y envía los avisos que tocan hoy."""
    await set_session_context(session, tenant_id, user_id)
    # Dos corridas a la vez verían los mismos pendientes: el candado dura hasta el commit (R4).
    await session.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:clave, 0))"),
        {"clave": f"recordatorios:{tenant_id}"},
    )
    await reabrir_por_tareas(session, tenant_id, user_id)
    cerrados = await cerrar_por_tareas(session, tenant_id, user_id)
    correos = await _enviar(session, tenant_id, enviar, hoy_guayaquil())
    return ResultadoRecordatorios(correos=correos, hallazgos_cerrados=cerrados)
