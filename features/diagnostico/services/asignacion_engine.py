"""Asignación de dominios del assessment a encargados del diagnóstico (DIAG-04). ¤diagnostico-asignacion

Tabla append-only: la asignación vigente de una dimensión es su última fila (R2) y un responsable nulo
la desasigna. El encargado es cualquier persona con un rol vigente en la organización salvo el `dpo` (R1);
esa consulta pasa por el pasillo de la sala Organización. Esta tarea no cambia quién responde (R3).
"""
from typing import Any
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.audit import registrar_evento
from app_core.db.session import fijar_contexto_rls
from app_core.errors import ErrorNegocio
from app_core.pasillo import organizacion as pasillo_organizacion
from features.diagnostico.domain.errores import ENCARGADO_ES_DPO, ENCARGADO_SIN_ROL
from features.diagnostico.services.dimensiones_sgpdp import obtener_catalogo_dimensiones


async def _validar_encargado(session: AsyncSession, tenant_id: str, responsable_user_id: str) -> None:
    usuarios = await pasillo_organizacion.listar_usuarios(session, tenant_id)
    roles = {
        rol["role"] for usuario in usuarios if usuario["id"] == responsable_user_id for rol in usuario["roles"]
    }
    if not roles:
        raise ErrorNegocio(ENCARGADO_SIN_ROL)
    if roles == {"dpo"}:
        raise ErrorNegocio(ENCARGADO_ES_DPO)


async def listar_asignaciones(session: AsyncSession, tenant_id: str, user_id: str) -> list[dict[str, Any]]:
    """Una fila por dimensión, con su asignación vigente (responsable nulo si no tiene)."""
    await fijar_contexto_rls(session, tenant_id, user_id)
    filas = (await session.execute(
        text(
            "SELECT DISTINCT ON (dimension) dimension, responsable_user_id, asignado_en "
            "FROM diagnostico_asignaciones WHERE tenant_id = :tenant_id "
            "ORDER BY dimension, asignado_en DESC, id DESC"
        ),
        {"tenant_id": tenant_id},
    )).mappings().all()
    vigentes = {fila["dimension"]: fila for fila in filas}
    return [
        {
            "dimension": dim.id,
            "nombre_dimension": dim.nombre,
            "responsable_user_id": vigentes[dim.id]["responsable_user_id"] if dim.id in vigentes else None,
            "asignado_en": vigentes[dim.id]["asignado_en"] if dim.id in vigentes else None,
        }
        for dim in obtener_catalogo_dimensiones()
    ]


async def asignar_dominio(
    session: AsyncSession, tenant_id: str, user_id: str, dimension: str, responsable_user_id: str | None
) -> dict[str, Any]:
    """Añade la asignación y devuelve la vigente de la dimensión; deja un evento de auditoría (R4)."""
    if responsable_user_id is not None:
        await _validar_encargado(session, tenant_id, responsable_user_id)
    await fijar_contexto_rls(session, tenant_id, user_id)
    await session.execute(
        text(
            "INSERT INTO diagnostico_asignaciones (id, tenant_id, dimension, responsable_user_id, asignado_por) "
            "VALUES (:id, :tenant_id, :dimension, :responsable, :asignado_por)"
        ),
        {
            "id": str(uuid4()), "tenant_id": tenant_id, "dimension": dimension,
            "responsable": responsable_user_id, "asignado_por": user_id,
        },
    )
    await registrar_evento(
        session, tenant_id, "diagnostico_asignacion", dimension,
        "asignada" if responsable_user_id else "desasignada",
        user_id=user_id, payload={"responsable_user_id": responsable_user_id},
    )
    vigentes = await listar_asignaciones(session, tenant_id, user_id)
    return next(fila for fila in vigentes if fila["dimension"] == dimension)


async def historial_asignaciones(
    session: AsyncSession, tenant_id: str, user_id: str, dimension: str | None
) -> list[dict[str, Any]]:
    """Todas las asignaciones, la más reciente primero; `dimension` filtra por un dominio."""
    await fijar_contexto_rls(session, tenant_id, user_id)
    filas = (await session.execute(
        text(
            "SELECT dimension, responsable_user_id, asignado_por, asignado_en FROM diagnostico_asignaciones "
            "WHERE tenant_id = :tenant_id AND (CAST(:dimension AS VARCHAR) IS NULL OR dimension = :dimension) "
            "ORDER BY asignado_en DESC, id DESC"
        ),
        {"tenant_id": tenant_id, "dimension": dimension},
    )).mappings().all()
    return [dict(fila) for fila in filas]
