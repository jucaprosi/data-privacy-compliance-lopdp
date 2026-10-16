# ¤roadmap
"""Motor de edición de detalles de tareas en la Hoja de Ruta (sala ADPA: Hoja de Ruta).

Permite al implementador actualizar campos operativos de una tarea:
- titulo (title en BD)
- fecha_inicio (start_date en BD)
- fecha_fin (end_date en BD)
- responsable_id (owner en BD)
- kpi
- entregable (deliverable en BD)

Valida que fecha_fin >= fecha_inicio y registra auditoría 'task_edited'.
"""
from __future__ import annotations

from datetime import date
from typing import Any, Optional
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.errores import ErrorNegocio
from app_core.errors import CodigoErrorNegocio
from features.roadmap.services.auditoria_engine import registrar_auditoria
from features.roadmap.services.contexto_tenant import set_session_context

ERROR_FECHAS_INVALIDAS = CodigoErrorNegocio(
    codigo="INVALID_DATE_RANGE",
    status_code=422,
    mensaje_defecto="La fecha de fin no puede ser anterior a la fecha de inicio.",
)


class TaskDetailsUpdate(BaseModel):
    """Modelo de entrada para la edición de campos de una tarea."""
    titulo: Optional[str] = Field(default=None, min_length=1)
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    responsable_id: Optional[str] = None
    kpi: Optional[str] = None
    entregable: Optional[str] = None


async def edit_task_details(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    task_id: str,
    payload: TaskDetailsUpdate,
) -> Optional[dict[str, Any]]:
    """Actualiza campos editables de una tarea de la hoja de ruta y registra auditoría.

    Raises:
        ErrorNegocio: Si fecha_fin < fecha_inicio (status 422).
    Returns:
        dict con la tarea actualizada si existe en el tenant, None si no se encuentra (404).
    """
    await set_session_context(session, tenant_id, user_id)

    # 1. Obtener la tarea actual para verificar pertenencia al tenant y fechas actuales
    result_actual = await session.execute(
        text("SELECT * FROM roadmap_tasks WHERE id = :id AND tenant_id = :tid"),
        {"id": task_id, "tid": tenant_id},
    )
    actual = result_actual.mappings().first()
    if not actual:
        return None

    # 2. Validar coherencia de fechas entre valores entrantes y existentes
    nueva_inicio = payload.fecha_inicio if payload.fecha_inicio is not None else actual["start_date"]
    nueva_fin = payload.fecha_fin if payload.fecha_fin is not None else actual["end_date"]

    if nueva_inicio is not None and nueva_fin is not None:
        if nueva_fin < nueva_inicio:
            raise ErrorNegocio(
                ERROR_FECHAS_INVALIDAS,
                detail="fecha_fin anterior a fecha_inicio",
                status_code=422,
            )

    # 3. Construir actualización con parámetros enlazados (cero SQL interpolado)
    updates: list[str] = []
    params: dict[str, Any] = {"id": task_id, "tid": tenant_id}
    cambios_audit: dict[str, Any] = {}

    if payload.titulo is not None:
        updates.append("title = :title")
        params["title"] = payload.titulo
        cambios_audit["title"] = {"old": actual["title"], "new": payload.titulo}

    if payload.fecha_inicio is not None:
        updates.append("start_date = :start_date")
        params["start_date"] = payload.fecha_inicio
        cambios_audit["start_date"] = {
            "old": str(actual["start_date"]) if actual["start_date"] else None,
            "new": str(payload.fecha_inicio),
        }

    if payload.fecha_fin is not None:
        updates.append("end_date = :end_date")
        params["end_date"] = payload.fecha_fin
        cambios_audit["end_date"] = {
            "old": str(actual["end_date"]) if actual["end_date"] else None,
            "new": str(payload.fecha_fin),
        }

    if payload.responsable_id is not None:
        updates.append("owner = :owner")
        params["owner"] = payload.responsable_id
        cambios_audit["owner"] = {"old": actual["owner"], "new": payload.responsable_id}

    if payload.kpi is not None:
        updates.append("kpi = :kpi")
        params["kpi"] = payload.kpi
        cambios_audit["kpi"] = {"old": actual["kpi"], "new": payload.kpi}

    if payload.entregable is not None:
        updates.append("deliverable = :deliverable")
        params["deliverable"] = payload.entregable
        cambios_audit["deliverable"] = {"old": actual["deliverable"], "new": payload.entregable}

    if not updates:
        return dict(actual)

    sql_update = f"""
        UPDATE roadmap_tasks
        SET {', '.join(updates)}
        WHERE id = :id AND tenant_id = :tid
        RETURNING *
    """

    res = await session.execute(text(sql_update), params)
    actualizado = res.mappings().first()
    if not actualizado:
        return None

    # 4. Registrar auditoría inmutable
    await registrar_auditoria(
        session=session,
        tenant_id=tenant_id,
        user_id=user_id,
        task_id=task_id,
        action="task_edited",
        payload=cambios_audit,
    )

    return dict(actualizado)
