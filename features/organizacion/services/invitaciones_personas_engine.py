"""Personas clave del alta (paso 6 de ORG-16): invitaciones de personas, por organización. ¤rbac-tenant

Guarda solo nombre, cargo, área, correo y rol propuesto (D-6): ningún campo de identificación. La tabla
`invitaciones_personas` tiene RLS FORCE; no se usa `invitaciones_organizacion`, que es del operador.
Repetir la persona (mismo correo) actualiza la fila (R3). El rol `dpo` pasa por `check_dpo_sod`.
"""
from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.errores import ErrorNegocio
from app_core.errors import DPO_INDEPENDENCE_VIOLATED
from features.organizacion.domain.models import RbacError
from features.organizacion.domain.roles import Role
from features.organizacion.services.areas_engine import get_area
from features.organizacion.services.contexto_tenant import fijar_tenant
from features.organizacion.services.sod_engine import check_dpo_sod

_SQL_ROLES_ACTIVOS_POR_CORREO = """
SELECT r.role
FROM users u
JOIN user_tenant_roles r ON r.user_id = u.id
WHERE lower(u.email) = :email AND u.deleted_at IS NULL AND r.tenant_id = :t
  AND (r.valid_to IS NULL OR r.valid_to > now())
"""

_SQL_UPSERT = """
INSERT INTO invitaciones_personas
    (id, tenant_id, nombre, cargo, area_id, email, rol_propuesto, created_by)
VALUES (:id, :t, :nombre, :cargo, :area_id, :email, :rol, :creador)
ON CONFLICT (tenant_id, lower(email)) DO UPDATE
SET nombre = EXCLUDED.nombre,
    cargo = EXCLUDED.cargo,
    area_id = EXCLUDED.area_id,
    rol_propuesto = EXCLUDED.rol_propuesto,
    estado = 'pendiente',
    updated_at = now()
"""


async def _verificar_dpo(session: AsyncSession, tenant_id: str, email: str, otros_roles_lote: set[Role]) -> None:
    filas = (await session.execute(
        text(_SQL_ROLES_ACTIVOS_POR_CORREO), {"email": email, "t": tenant_id},
    )).scalars().all()
    activos = {Role(r) for r in filas} | otros_roles_lote
    motivo = check_dpo_sod(Role.dpo, activos)
    if motivo:
        raise ErrorNegocio(DPO_INDEPENDENCE_VIOLATED, motivo)


async def registrar_personas_clave(
    session: AsyncSession, tenant_id: str, user_id: str, personas: list[dict[str, Any]],
) -> int:
    """Guarda las personas del paso 6 (alta o actualización por correo). Devuelve cuántas guardó."""
    await fijar_tenant(session, tenant_id, user_id)
    roles_por_correo: dict[str, set[Role]] = {}
    for p in personas:
        roles_por_correo.setdefault(p["email"].strip().lower(), set()).add(Role(p["rol"]))

    for p in personas:
        email = p["email"].strip().lower()
        if p.get("area_id") and not await get_area(session, tenant_id, p["area_id"]):
            raise RbacError(404, "Área no encontrada en la organización")
        if p["rol"] == Role.dpo.value:
            otros = roles_por_correo[email] - {Role.dpo}
            await _verificar_dpo(session, tenant_id, email, otros)
        await session.execute(text(_SQL_UPSERT), {
            "id": str(uuid4()), "t": tenant_id, "nombre": p["nombre"].strip(), "cargo": p["cargo"].strip(),
            "area_id": p.get("area_id"), "email": email, "rol": p["rol"], "creador": user_id,
        })
    return len(personas)


async def contar_personas_clave(session: AsyncSession, tenant_id: str) -> int:
    await fijar_tenant(session, tenant_id)
    return (await session.execute(
        text("SELECT count(*) FROM invitaciones_personas WHERE tenant_id = :t AND estado <> 'revocada'"),
        {"t": tenant_id},
    )).scalar_one()
