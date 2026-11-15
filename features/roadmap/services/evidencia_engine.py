"""Evidencia de tareas: registro, listado y validación con cuatro ojos (sala ADPA: Hoja de Ruta)."""
from typing import Optional
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# --- INICIO ADPA-04 ---
from app_core.pasillo import organizacion as pasillo_organizacion
# --- FIN ADPA-04 ---
from features.roadmap.services.auditoria_engine import registrar_auditoria
from features.roadmap.services.contexto_tenant import set_session_context


from app_core.errors import ErrorNegocio  # noqa: E402
from app_core.storage.gcs import Almacen, AlmacenNoDisponible, FirmaSubida, almacen_por_defecto  # noqa: E402
from app_core.storage.limites import (  # noqa: E402
    clave_pertenece_a_tenant,
    construir_clave_objeto,
    motivo_de_rechazo,
)
from features.roadmap.domain.errores import (  # noqa: E402
    RM_ALMACEN_NO_DISPONIBLE,
    RM_CLAVE_OBJETO_INVALIDA,
)


def almacen_evidencias() -> Almacen:
    """Obtiene el puerto `Almacen` de Cloud Storage; falla cerrado con 503 si no está disponible."""
    try:
        return almacen_por_defecto()
    except AlmacenNoDisponible as exc:
        raise ErrorNegocio(RM_ALMACEN_NO_DISPONIBLE) from exc


def validar_archivo_evidencia(nombre: str, mime_type: str, file_size: int) -> None:
    """Aplica las reglas de tipo MIME, extensión y límite de 25 MB del almacén."""
    rechazo = motivo_de_rechazo(nombre, mime_type, file_size)
    if rechazo:
        codigo, motivo = rechazo
        raise ErrorNegocio(codigo, detail=motivo)


def validar_clave_objeto_tenant(clave_objeto: str, tenant_id: str) -> None:
    """Exige que `clave_objeto` esté confinada al prefijo `<tenant_id>/` sin saltos de ruta."""
    if not clave_pertenece_a_tenant(clave_objeto, tenant_id):
        raise ErrorNegocio(RM_CLAVE_OBJETO_INVALIDA)


def firmar_subida_evidencia(
    almacen: Almacen,
    tenant_id: str,
    task_id: str,
    filename: str,
    mime_type: str,
    file_size: int,
) -> FirmaSubida:
    """Valida el archivo, construye la clave por tenant y firma la URL de subida directa en Cloud Storage."""
    validar_archivo_evidencia(filename, mime_type, file_size)
    clave = construir_clave_objeto(tenant_id, task_id, filename)
    try:
        return almacen.firmar_subida(clave, mime_type)
    except AlmacenNoDisponible as exc:
        raise ErrorNegocio(RM_ALMACEN_NO_DISPONIBLE) from exc


async def register_evidence_upload(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    task_id: str,
    clave_objeto: str,
    mime_type: str,
    file_size: int,
    file_hash: str | None = None,
) -> dict:
    """Registra evidencia tras subida a Cloud Storage."""
    await set_session_context(session, tenant_id, user_id)

    evidence_id = str(uuid4())
    await session.execute(
        text("""
            INSERT INTO task_evidence
                (id, task_id, tenant_id, clave_objeto, mime_type, file_size, file_hash, uploaded_by, validation_status)
            VALUES
                (:id, :task_id, :tid, :clave_objeto, :mime, :size, :hash, :user, 'pending')
        """),
        {
            "id": evidence_id,
            "task_id": task_id,
            "tid": tenant_id,
            "clave_objeto": clave_objeto,
            "mime": mime_type,
            "size": file_size,
            "hash": file_hash,
            "user": user_id,
        },
    )
    await registrar_auditoria(
        session, tenant_id, user_id, task_id, "evidence_uploaded", {"clave_objeto": clave_objeto}
    )
    return {"id": evidence_id, "task_id": task_id, "clave_objeto": clave_objeto}


async def list_evidence(
    session: AsyncSession,
    tenant_id: str,
    task_id: str,
    rol: Optional[str] = None,
    user_id: Optional[str] = None,
) -> list[dict]:
    """Lista evidencia de una tarea.

    El `responsable_area` ve solo la evidencia que subió él (PRD §5.2, Módulo 5); los demás roles,
    toda la del tenant. Sin identidad de usuario falla cerrado: no devuelve nada.
    """
    await set_session_context(session, tenant_id)
    if rol == "responsable_area":
        if not user_id:
            return []
        rows = (await session.execute(
            text(
                "SELECT * FROM task_evidence WHERE task_id = :tid AND tenant_id = :org "
                "AND uploaded_by = :uid ORDER BY uploaded_at DESC"
            ),
            {"tid": task_id, "org": tenant_id, "uid": user_id},
        )).mappings().all()
        return [dict(r) for r in rows]
    rows = (await session.execute(
        text("SELECT * FROM task_evidence WHERE task_id = :tid AND tenant_id = :org ORDER BY uploaded_at DESC"),
        {"tid": task_id, "org": tenant_id},
    )).mappings().all()
    return [dict(r) for r in rows]


async def validate_evidence(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    evidence_id: str,
    validation_status: str,
    notes: str = "",
    rol: Optional[str] = None,  # RM-25a: rol con el que valida (lo guarda `validado_rol`)
) -> Optional[dict]:
    """Cambia el estado de validación de una evidencia.

    Cuatro ojos: quien subió la evidencia no puede validarla (SoDViolation).
    """
    await set_session_context(session, tenant_id, user_id)

    current = (await session.execute(
        text("SELECT uploaded_by FROM task_evidence WHERE id = :id AND tenant_id = :tid"),
        {"id": evidence_id, "tid": tenant_id},
    )).first()
    if not current:
        return None
    motivo = pasillo_organizacion.verificar_cuatro_ojos(current[0], user_id)
    if motivo:
        raise pasillo_organizacion.violacion_sod(motivo)

    result = await session.execute(
        text("""
            UPDATE task_evidence
            SET validation_status = :vs,
                validated_by = :uid,
                validated_at = now(),
                validado_rol = :rol,
                notes = :notes
            WHERE id = :id AND tenant_id = :tid
            RETURNING *
        """),
        {"vs": validation_status, "uid": user_id, "rol": rol, "notes": notes, "id": evidence_id, "tid": tenant_id},
    )
    row = result.mappings().first()
    if not row:
        return None

    task_id = row["task_id"]
    await registrar_auditoria(
        session, tenant_id, user_id, task_id, "evidence_validated",
        {"evidence_id": evidence_id, "status": validation_status},
    )
    return dict(row)
