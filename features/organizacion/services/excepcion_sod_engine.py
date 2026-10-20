"""Motor de gestión de excepciones de separación de funciones (SoD) (ORG-02).

Invariante: INV_LOPDP_COORDINADOR_RESPONSABLE_EXCEPCION.
Permite la combinación coordinador + responsable_area únicamente mediante una excepción SoD explícita,
aprobada, vigente y con control compensatorio.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.errores import ErrorNegocio
from app_core.audit import registrar_evento
from app_core.errors import SOD_VIOLATION, TENANT_SIZE_NOT_CONFIGURED
from features.organizacion.domain.models import RbacError
from features.organizacion.domain.roles import Role
from features.organizacion.domain.tamanos import TamanoOrganizacion
from features.organizacion.services.contexto_tenant import fijar_tenant
from features.organizacion.services.regla_tamano_engine import evaluar_tamano


class ControlCompensatorioTipo(str, Enum):
    observaciones_periodicas_delegado = "observaciones_periodicas_delegado"
    verificacion_tercero_externo = "verificacion_tercero_externo"
    aprobacion_decisiones_alta_direccion = "aprobacion_decisiones_alta_direccion"


class EstadoExcepcionSoD(str, Enum):
    pendiente = "pendiente"
    activa = "activa"
    vencida = "vencida"
    revocada = "revocada"


class OrigenExcepcionSoD(str, Enum):
    solicitud = "solicitud"
    migracion = "migracion"


class ExcepcionSoDCreate(BaseModel):
    user_id: str = Field(min_length=1)
    rol_existente: str = Field(min_length=1)
    rol_solicitado: str = Field(min_length=1)
    motivo: str = Field(min_length=5)
    control_compensatorio_tipo: ControlCompensatorioTipo
    control_compensatorio_detalle: str = Field(min_length=5)
    valid_from: Optional[datetime] = None
    valid_to: datetime


class ExcepcionSoDAprobar(BaseModel):
    resolucion_referencia: Optional[str] = None


class ExcepcionSoDRevocar(BaseModel):
    motivo: str = Field(min_length=3)


class ExcepcionSoDObservacionDpo(BaseModel):
    observaciones: str = Field(min_length=3)


def _formatear_excepcion(row: dict[str, Any]) -> dict[str, Any]:
    item = dict(row)
    now = datetime.now(timezone.utc)
    # Comprobación de vencimiento dinámico en lectura si no está revocada
    if item["estado"] == "activa" and item["valid_to"] and item["valid_to"] <= now:
        item["estado"] = "vencida"
    return item


async def solicitar_excepcion_sod(
    session: AsyncSession,
    tenant_id: str,
    requested_by: str,
    payload: ExcepcionSoDCreate,
) -> dict[str, Any]:
    """Solicita una excepción SoD para la combinación coordinador + responsable_area."""
    await fijar_tenant(session, tenant_id, requested_by)

    # 1. Validar que la organización tenga tamaño configurado (falla cerrado)
    tamano = (await session.execute(
        text("SELECT tamano FROM tenants WHERE id = :t"), {"t": tenant_id}
    )).scalar_one_or_none()
    evaluar_tamano(tamano)

    # 2. Validar combinación de roles permitida
    roles_validos = (
        (payload.rol_existente == Role.coordinador.value and payload.rol_solicitado == Role.responsable_area.value) or
        (payload.rol_existente == Role.responsable_area.value and payload.rol_solicitado == Role.coordinador.value)
    )
    if not roles_validos:
        raise RbacError(400, "La excepción SoD solo aplica para el par coordinador y responsable_area")

    # 3. Validar fechas
    now = datetime.now(timezone.utc)
    valid_from = payload.valid_from or (now - timedelta(minutes=5))
    if payload.valid_to <= valid_from:
        raise RbacError(400, "valid_to debe ser posterior a valid_from")

    # 4. Validar existencia del usuario beneficiario
    user = (await session.execute(
        text("SELECT id FROM users WHERE id = :u AND deleted_at IS NULL"), {"u": payload.user_id}
    )).first()
    if not user:
        raise RbacError(404, "Usuario beneficiario no encontrado")

    # 5. Comprobar que no exista ya una excepción activa o pendiente para ese usuario
    existente = (await session.execute(
        text(
            "SELECT id FROM sod_exceptions "
            "WHERE tenant_id = :t AND user_id = :u AND estado IN ('activa', 'pendiente') "
            "AND valid_to > now()"
        ),
        {"t": tenant_id, "u": payload.user_id},
    )).first()
    if existente:
        raise RbacError(409, "Ya existe una solicitud o excepción SoD vigente para este usuario")

    exc_id = str(uuid4())
    row = (await session.execute(
        text("""
            INSERT INTO sod_exceptions (
                id, tenant_id, user_id, rol_existente, rol_solicitado,
                motivo, control_compensatorio_tipo, control_compensatorio_detalle,
                origen, estado, requested_by, requested_at, valid_from, valid_to
            ) VALUES (
                :id, :t, :u, :re, :rs, :m, :cct, :ccd, 'solicitud', 'pendiente', :rb, :now, :vf, :vt
            ) RETURNING *
        """),
        {
            "id": exc_id,
            "t": tenant_id,
            "u": payload.user_id,
            "re": payload.rol_existente,
            "rs": payload.rol_solicitado,
            "m": payload.motivo,
            "cct": payload.control_compensatorio_tipo.value,
            "ccd": payload.control_compensatorio_detalle,
            "rb": requested_by,
            "now": now,
            "vf": valid_from,
            "vt": payload.valid_to,
        },
    )).mappings().first()

    await registrar_evento(
        session=session,
        tenant_id=tenant_id,
        entity_type="sod_exception",
        entity_id=exc_id,
        action="sod_exception_requested",
        user_id=requested_by,
        payload={
            "user_id": payload.user_id,
            "rol_existente": payload.rol_existente,
            "rol_solicitado": payload.rol_solicitado,
            "control_compensatorio_tipo": payload.control_compensatorio_tipo.value,
            "valid_to": payload.valid_to.isoformat(),
        },
    )

    return _formatear_excepcion(dict(row))


async def listar_excepciones_sod(
    session: AsyncSession,
    tenant_id: str,
    estado: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Lista las excepciones SoD del tenant."""
    await fijar_tenant(session, tenant_id)
    query = "SELECT * FROM sod_exceptions WHERE tenant_id = :t"
    params: dict[str, Any] = {"t": tenant_id}
    if estado:
        query += " AND estado = :st"
        params["st"] = estado
    query += " ORDER BY requested_at DESC"

    rows = (await session.execute(text(query), params)).mappings().all()
    return [_formatear_excepcion(dict(r)) for r in rows]


async def obtener_excepcion_sod(
    session: AsyncSession,
    tenant_id: str,
    exception_id: str,
) -> dict[str, Any]:
    """Obtiene una excepción SoD por id."""
    await fijar_tenant(session, tenant_id)
    row = (await session.execute(
        text("SELECT * FROM sod_exceptions WHERE id = :id AND tenant_id = :t"),
        {"id": exception_id, "t": tenant_id},
    )).mappings().first()
    if not row:
        raise RbacError(404, "Excepción SoD no encontrada")
    return _formatear_excepcion(dict(row))


async def aprobar_excepcion_sod(
    session: AsyncSession,
    tenant_id: str,
    approver_id: str,
    approver_role: str,
    exception_id: str,
    payload: ExcepcionSoDAprobar,
) -> dict[str, Any]:
    """Aprueba una excepción SoD.

    Reglas:
    - El DPO NUNCA aprueba (Art. 18.3 Reglamento DPD).
    - El beneficiario NO puede aprobar su propia excepción.
    - Si el único admin_organizacion activo es el propio beneficiario, se exige resolucion_referencia.
    - Requiere que la organización tenga tamaño configurado.
    """
    await fijar_tenant(session, tenant_id, approver_id)

    # 1. DPO no puede aprobar
    if approver_role == Role.dpo.value:
        raise RbacError(403, "El DPO no puede aprobar excepciones SoD (Art. 18.3 Reglamento del Delegado)")

    # 2. Verificar existencia y estado
    row = (await session.execute(
        text("SELECT * FROM sod_exceptions WHERE id = :id AND tenant_id = :t"),
        {"id": exception_id, "t": tenant_id},
    )).mappings().first()
    if not row:
        raise RbacError(404, "Excepción SoD no encontrada")
    if row["estado"] != "pendiente":
        raise RbacError(400, f"No se puede aprobar una excepción en estado '{row['estado']}'")

    # 3. Validar tamaño de la organización
    tamano = (await session.execute(
        text("SELECT tamano FROM tenants WHERE id = :t"), {"t": tenant_id}
    )).scalar_one_or_none()
    evaluar_tamano(tamano)

    # 4. Validar que el aprobador no sea el beneficiario
    beneficiario_id = row["user_id"]
    if approver_id == beneficiario_id:
        # Verificar si hay otros administradores activos en el tenant
        otros_admins = (await session.execute(
            text(
                "SELECT count(*) FROM user_tenant_roles "
                "WHERE tenant_id = :t AND role = 'admin_organizacion' AND user_id <> :u "
                "AND (valid_to IS NULL OR valid_to > now())"
            ),
            {"t": tenant_id, "u": beneficiario_id},
        )).scalar_one()

        if otros_admins > 0:
            raise RbacError(403, "El beneficiario no puede aprobar su propia excepción habiendo otros administradores")

        # Es el único admin: exige resolución del representante legal
        if not payload.resolucion_referencia or not payload.resolucion_referencia.strip():
            raise RbacError(
                400,
                "Cuando el único administrador es el beneficiario, se exige la referencia de la resolución del representante legal",
            )

    now = datetime.now(timezone.utc)
    updated = (await session.execute(
        text("""
            UPDATE sod_exceptions
            SET estado = 'activa',
                approved_by = :ab,
                approved_at = :now,
                resolucion_referencia = :ref,
                updated_at = :now
            WHERE id = :id AND tenant_id = :t
            RETURNING *
        """),
        {
            "id": exception_id,
            "t": tenant_id,
            "ab": approver_id,
            "now": now,
            "ref": payload.resolucion_referencia,
        },
    )).mappings().first()

    await registrar_evento(
        session=session,
        tenant_id=tenant_id,
        entity_type="sod_exception",
        entity_id=exception_id,
        action="sod_exception_approved",
        user_id=approver_id,
        payload={
            "approved_by": approver_id,
            "resolucion_referencia": payload.resolucion_referencia,
        },
    )

    return _formatear_excepcion(dict(updated))


async def revocar_excepcion_sod(
    session: AsyncSession,
    tenant_id: str,
    revoked_by: str,
    exception_id: str,
    payload: ExcepcionSoDRevocar,
) -> dict[str, Any]:
    """Revoca una excepción SoD activa o pendiente."""
    await fijar_tenant(session, tenant_id, revoked_by)

    row = (await session.execute(
        text("SELECT * FROM sod_exceptions WHERE id = :id AND tenant_id = :t"),
        {"id": exception_id, "t": tenant_id},
    )).mappings().first()
    if not row:
        raise RbacError(404, "Excepción SoD no encontrada")
    if row["estado"] not in ("activa", "pendiente"):
        raise RbacError(400, f"No se puede revocar una excepción en estado '{row['estado']}'")

    now = datetime.now(timezone.utc)
    updated = (await session.execute(
        text("""
            UPDATE sod_exceptions
            SET estado = 'revocada',
                revoked_by = :rb,
                revoked_at = :now,
                motivo_revocacion = :mot,
                updated_at = :now
            WHERE id = :id AND tenant_id = :t
            RETURNING *
        """),
        {
            "id": exception_id,
            "t": tenant_id,
            "rb": revoked_by,
            "now": now,
            "mot": payload.motivo,
        },
    )).mappings().first()

    await registrar_evento(
        session=session,
        tenant_id=tenant_id,
        entity_type="sod_exception",
        entity_id=exception_id,
        action="sod_exception_revoked",
        user_id=revoked_by,
        payload={"motivo": payload.motivo},
    )

    return _formatear_excepcion(dict(updated))


async def agregar_observacion_dpo(
    session: AsyncSession,
    tenant_id: str,
    dpo_user_id: str,
    exception_id: str,
    payload: ExcepcionSoDObservacionDpo,
) -> dict[str, Any]:
    """Permite al DPO registrar observaciones no vinculantes sobre una excepción SoD."""
    await fijar_tenant(session, tenant_id, dpo_user_id)

    row = (await session.execute(
        text("SELECT * FROM sod_exceptions WHERE id = :id AND tenant_id = :t"),
        {"id": exception_id, "t": tenant_id},
    )).mappings().first()
    if not row:
        raise RbacError(404, "Excepción SoD no encontrada")

    now = datetime.now(timezone.utc)
    updated = (await session.execute(
        text("""
            UPDATE sod_exceptions
            SET observaciones_dpo = :obs,
                observaciones_dpo_by = :uid,
                observaciones_dpo_at = :now,
                updated_at = :now
            WHERE id = :id AND tenant_id = :t
            RETURNING *
        """),
        {
            "id": exception_id,
            "t": tenant_id,
            "obs": payload.observaciones,
            "uid": dpo_user_id,
            "now": now,
        },
    )).mappings().first()

    await registrar_evento(
        session=session,
        tenant_id=tenant_id,
        entity_type="sod_exception",
        entity_id=exception_id,
        action="sod_exception_dpo_observation",
        user_id=dpo_user_id,
        payload={"observaciones": payload.observaciones},
    )

    return _formatear_excepcion(dict(updated))


__all__ = [
    "ControlCompensatorioTipo",
    "EstadoExcepcionSoD",
    "ExcepcionSoDAprobar",
    "ExcepcionSoDCreate",
    "ExcepcionSoDObservacionDpo",
    "ExcepcionSoDRevocar",
    "OrigenExcepcionSoD",
    "agregar_observacion_dpo",
    "aprobar_excepcion_sod",
    "listar_excepciones_sod",
    "obtener_excepcion_sod",
    "revocar_excepcion_sod",
    "solicitar_excepcion_sod",
]
