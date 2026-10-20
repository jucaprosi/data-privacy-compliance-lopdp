"""Asignación y revocación de roles por tenant (sala ADPA: Organización).

Reglas: SoD del DPO (ver sod_engine); no se puede revocar el último
'admin_organizacion' activo del tenant.
"""
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from features.organizacion.domain.models import RbacError, RoleGrant, SoDViolation
from features.organizacion.domain.roles import Role
from features.organizacion.services.areas_engine import get_area
from features.organizacion.services.contexto_tenant import fijar_tenant
from features.organizacion.services.regla_tamano_engine import (
    traducir_error_trigger,
    verificar_excepcion_coordinador_responsable,
)
from features.organizacion.services.sod_engine import check_dpo_sod


async def list_role_assignments(session: AsyncSession, tenant_id: str, include_revoked: bool = False) -> list[dict]:
    await fijar_tenant(session, tenant_id)
    if include_revoked:
        consulta = text("SELECT * FROM user_tenant_roles WHERE tenant_id=:t ORDER BY granted_at")
    else:
        consulta = text(
            "SELECT * FROM user_tenant_roles WHERE tenant_id=:t "
            "AND (valid_to IS NULL OR valid_to > now()) ORDER BY granted_at"
        )
    rows = (await session.execute(consulta, {"t": tenant_id})).mappings().all()
    return [dict(r) for r in rows]


async def grant_role(session: AsyncSession, tenant_id: str, granted_by: str, payload: RoleGrant) -> dict:
    await fijar_tenant(session, tenant_id, granted_by)

    user = (await session.execute(
        text("SELECT id FROM users WHERE id=:id AND deleted_at IS NULL"),
        {"id": payload.user_id},
    )).first()
    if not user:
        raise RbacError(404, "Usuario no encontrado")
    if payload.area_id and not await get_area(session, tenant_id, payload.area_id):
        raise RbacError(404, "Área no encontrada en el tenant")
    if payload.valid_to and payload.valid_to <= datetime.now(timezone.utc):
        raise RbacError(422, "valid_to debe ser una fecha futura")

    current = (await session.execute(
        text(
            "SELECT id, role, area_id, valid_to FROM user_tenant_roles "
            "WHERE user_id=:u AND tenant_id=:t"
        ),
        {"u": payload.user_id, "t": tenant_id},
    )).mappings().all()
    now = datetime.now(timezone.utc)
    active = [r for r in current if r["valid_to"] is None or r["valid_to"] > now]

    if any(r["role"] == payload.role.value and r["area_id"] == payload.area_id for r in active):
        raise RbacError(409, "El usuario ya tiene esa asignación activa")

    motivo = check_dpo_sod(payload.role, (Role(r["role"]) for r in active))
    if motivo:
        raise SoDViolation(motivo)
    await verificar_excepcion_coordinador_responsable(session, tenant_id, payload.user_id, payload.role.value)

    previous = next(
        (r for r in current if r["role"] == payload.role.value and r["area_id"] == payload.area_id),
        None,
    )
    try:
        if previous:
            # La restricción única (user, tenant, area, role) impide duplicar: se reactiva.
            row = (await session.execute(
                text("""
                    UPDATE user_tenant_roles
                    SET valid_to = :vt, revoked_by = NULL, granted_by = :gb,
                        granted_at = now(), valid_from = now()
                    WHERE id = :id RETURNING *
                """),
                {"vt": payload.valid_to, "gb": granted_by, "id": previous["id"]},
            )).mappings().first()
        else:
            row = (await session.execute(
                text("""
                    INSERT INTO user_tenant_roles
                        (id, user_id, tenant_id, area_id, role, granted_by, valid_from, valid_to)
                    VALUES (:id, :u, :t, :a, :r, :gb, now(), :vt)
                    RETURNING *
                """),
                {
                    "id": str(uuid4()), "u": payload.user_id, "t": tenant_id,
                    "a": payload.area_id, "r": payload.role.value,
                    "gb": granted_by, "vt": payload.valid_to,
                },
            )).mappings().first()
    except IntegrityError as exc:
        traducido = traducir_error_trigger(exc)
        if traducido is not None:
            raise traducido from exc
        # Carrera con otra asignación concurrente; el trigger de BD tiene la última palabra.
        raise SoDViolation(f"Asignación rechazada por la BD: {exc.orig}") from exc
    return dict(row)


async def revoke_role(session: AsyncSession, tenant_id: str, revoked_by: str, assignment_id: str) -> dict:
    await fijar_tenant(session, tenant_id, revoked_by)

    row = (await session.execute(
        text(
            "SELECT * FROM user_tenant_roles "
            "WHERE id=:id AND tenant_id=:t AND (valid_to IS NULL OR valid_to > now())"
        ),
        {"id": assignment_id, "t": tenant_id},
    )).mappings().first()
    if not row:
        raise RbacError(404, "Asignación activa no encontrada")

    if row["role"] == Role.admin_organizacion.value:
        admins = (await session.execute(
            text(
                "SELECT count(*) FROM user_tenant_roles "
                "WHERE tenant_id=:t AND role='admin_organizacion' "
                "AND (valid_to IS NULL OR valid_to > now())"
            ),
            {"t": tenant_id},
        )).scalar_one()
        if admins <= 1:
            raise RbacError(409, "No se puede revocar el último admin_organizacion del tenant")

    updated = (await session.execute(
        text("""
            UPDATE user_tenant_roles SET valid_to = now(), revoked_by = :rb
            WHERE id = :id RETURNING *
        """),
        {"rb": revoked_by, "id": assignment_id},
    )).mappings().first()
    return dict(updated)
