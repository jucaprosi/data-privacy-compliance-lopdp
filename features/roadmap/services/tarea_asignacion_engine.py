"""Motor de asignación de tareas a responsables de área (sala ADPA: Hoja de Ruta).
`¤roadmap` `¤rbac-tenant`

Asigna una tarea de roadmap_tasks a un responsable de área, validando:
1. La tarea existe y pertenece al tenant (404 si no).
2. El responsable_id es usuario activo con rol 'responsable_area' en el MISMO tenant (404 si no).
3. El responsable pertenece al MISMO área que la tarea (422 con ErrorNegocio si no).
4. Registra el evento de auditoría 'task_assigned' en task_audit_log (disparador para NOTIF-01).
"""
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.errores import ErrorNegocio
from features.organizacion import organizacion_service
from features.roadmap.services.auditoria_engine import registrar_auditoria
from features.roadmap.services.contexto_tenant import set_session_context


async def assign_task_to_responsable(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    task_id: str,
    responsable_id: str,
) -> dict:
    """Asigna una tarea a un responsable de área validando tenant, rol y área."""
    await set_session_context(session, tenant_id, user_id)

    # 1. Verificar existencia de la tarea en el tenant
    task_row = (
        await session.execute(
            text(
                "SELECT id, tenant_id, area_id, title, owner, status "
                "FROM roadmap_tasks "
                "WHERE id = :id AND tenant_id = :t"
            ),
            {"id": task_id, "t": tenant_id},
        )
    ).mappings().first()

    if not task_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tarea no encontrada",
        )

    task_area_id = task_row["area_id"]

    # 2. Consultar usuarios del tenant a través de la compuerta de Organización
    tenant_users = await organizacion_service.list_tenant_users(session, tenant_id)
    target_user = next((u for u in tenant_users if u["id"] == responsable_id), None)

    if not target_user or not target_user.get("activo", True):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Responsable no encontrado o inactivo en la organización",
        )

    # 3. Validar que tenga el rol responsable_area activo
    roles_responsable = [
        r for r in target_user.get("roles", [])
        if r.get("role") == "responsable_area"
    ]
    if not roles_responsable:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El usuario no es un responsable de área activo en la organización",
        )

    # 4. Validar pertenencia al mismo área que la tarea
    # Se consulta el alcance permitido de áreas del responsable vía compuerta
    scope = await organizacion_service.allowed_area_ids(session, tenant_id, responsable_id)

    # Si la tarea no tiene área asignada o el área no está en el scope del responsable
    # (scope is None significa alcance transversal a todo el tenant)
    if task_area_id is None or (scope is not None and task_area_id not in scope):
        raise ErrorNegocio(
            codigo_o_obj="RESPONSABLE_AREA_MISMATCH",
            detail="El responsable no pertenece al área asignada a la tarea",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            action_required="assign_area_matching_responsable",
        )

    # 5. Actualizar la tarea con el nuevo owner (responsable_id o nombre)
    responsable_nombre = target_user.get("nombre") or responsable_id
    updated_row = (
        await session.execute(
            text(
                """
                UPDATE roadmap_tasks
                SET owner = :owner
                WHERE id = :id AND tenant_id = :t
                RETURNING *
                """
            ),
            {
                "owner": responsable_nombre,
                "id": task_id,
                "t": tenant_id,
            },
        )
    ).mappings().first()

    # 6. Registrar evento de auditoría 'task_assigned' en task_audit_log (disparador NOTIF-01)
    await registrar_auditoria(
        session=session,
        tenant_id=tenant_id,
        user_id=user_id,
        task_id=task_id,
        action="task_assigned",
        payload={
            "responsable_id": responsable_id,
            "responsable_nombre": responsable_nombre,
            "area_id": task_area_id,
        },
    )

    return dict(updated_row)
