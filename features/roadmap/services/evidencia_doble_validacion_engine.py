"""Primera validación de la evidencia por el Coordinador (RM-25a, sala ADPA: Hoja de Ruta). ¤roadmap

Expandir, sin exigir: la primera validación se registra, pero la validación final (PATCH existente) todavía no
la exige. Quien subió la evidencia no puede validarla primero (cuatro ojos); solo cuenta una por evidencia.
"""
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.errors import CodigoErrorNegocio, ErrorNegocio
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
            "SELECT uploaded_by, validation_status, primera_validacion_por FROM task_evidence "
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
    if actual[1] != "pending":
        raise ErrorNegocio(RM_EVIDENCIA_NO_PENDIENTE)
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
