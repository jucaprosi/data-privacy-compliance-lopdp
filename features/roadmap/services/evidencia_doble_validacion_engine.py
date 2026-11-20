"""Primera validación de la evidencia por el Coordinador (RM-25a, sala ADPA: Hoja de Ruta). ¤roadmap

Quien subió la evidencia no puede validarla primero (cuatro ojos); solo cuenta una por evidencia. Desde RM-25b
la validación final (PATCH existente) la exige, y una evidencia `approved` con `requiere_revalidacion` (aprobada
antes de RM-25b con una sola validación) la admite de nuevo para revalidarse por los dos pasos (R4b).
"""
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.errors import CodigoErrorNegocio, ErrorNegocio
from features.roadmap.domain.errores import VALIDADOR_REPETIDO
from app_core.pasillo import organizacion as pasillo_organizacion
from features.roadmap.services.auditoria_engine import registrar_auditoria
from features.roadmap.services.contexto_tenant import set_session_context

ROL_PRIMERA_VALIDACION = "coordinador"

RM_PRIMERA_VALIDACION_YA_REGISTRADA = CodigoErrorNegocio(
    codigo="RM_PRIMERA_VALIDACION_YA_REGISTRADA",
    status_code=409,
    mensaje_defecto="Esta evidencia ya tiene su primera validación.",
    action_required=None,
)
RM_EVIDENCIA_NO_PENDIENTE = CodigoErrorNegocio(
    codigo="RM_EVIDENCIA_NO_PENDIENTE",
    status_code=409,
    mensaje_defecto="La evidencia ya fue resuelta: no admite primera validación.",
    action_required=None,
)


async def registrar_primera_validacion(
    session: AsyncSession, tenant_id: str, user_id: str, rol: str, task_id: str, evidence_id: str
) -> Optional[dict]:
    """Registra quién, cuándo y con qué rol hizo la primera validación. None si la evidencia no existe."""
    await set_session_context(session, tenant_id, user_id)
    actual = (await session.execute(
        text(
            "SELECT uploaded_by, validation_status, primera_validacion_por, requiere_revalidacion, validated_by "
            "FROM task_evidence "
            "WHERE id = :id AND task_id = :task AND tenant_id = :tid"
        ),
        {"id": evidence_id, "task": task_id, "tid": tenant_id},
    )).first()
    if not actual:
        return None
    motivo = pasillo_organizacion.verificar_cuatro_ojos(actual[0], user_id)
    if motivo:
        raise pasillo_organizacion.violacion_sod(motivo)
    if actual[2] is not None:
        raise ErrorNegocio(RM_PRIMERA_VALIDACION_YA_REGISTRADA)
    por_revalidar = actual[1] == "approved" and bool(actual[3])
    if actual[1] != "pending" and not por_revalidar:
        raise ErrorNegocio(RM_EVIDENCIA_NO_PENDIENTE)
    if por_revalidar and actual[4] == user_id:
        # Sigue `approved` hasta la validación final: quien la aprobó entonces no puede ser ahora el primer validador.
        raise ErrorNegocio(VALIDADOR_REPETIDO)
    fila = (await session.execute(
        text(
            "UPDATE task_evidence SET primera_validacion_por = :uid, primera_validacion_en = now(), "
            "primera_validacion_rol = :rol WHERE id = :id AND tenant_id = :tid RETURNING *"
        ),
        {"uid": user_id, "rol": rol, "id": evidence_id, "tid": tenant_id},
    )).mappings().first()
    await registrar_auditoria(
        session, tenant_id, user_id, task_id, "evidence_first_validated", {"evidence_id": evidence_id}
    )
    return dict(fila)
