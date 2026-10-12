"""Áreas de la organización y alcance por área (sala ADPA: Organización).

'responsable_area' puede acotarse a un área; el alcance incluye sus subáreas.
Una asignación sin area_id es transversal al tenant.
"""
from typing import Optional
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from features.organizacion.domain.models import AreaCreate, AreaUpdate, RbacError
from features.organizacion.domain.roles import Role
from features.organizacion.services.contexto_tenant import fijar_tenant
from features.organizacion.services.usuarios_engine import has_active_role


async def get_area(session: AsyncSession, tenant_id: str, area_id: str) -> Optional[dict]:
    row = (await session.execute(
        text("SELECT * FROM areas WHERE id=:id AND tenant_id=:t AND deleted_at IS NULL"),
        {"id": area_id, "t": tenant_id},
    )).mappings().first()
    return dict(row) if row else None


async def list_areas(session: AsyncSession, tenant_id: str) -> list[dict]:
    await fijar_tenant(session, tenant_id)
    rows = (await session.execute(
        text("SELECT * FROM areas WHERE tenant_id=:t AND deleted_at IS NULL ORDER BY nombre"),
        {"t": tenant_id},
    )).mappings().all()
    return [dict(r) for r in rows]


async def create_area(session: AsyncSession, tenant_id: str, payload: AreaCreate) -> dict:
    await fijar_tenant(session, tenant_id)
    if payload.parent_area_id and not await get_area(session, tenant_id, payload.parent_area_id):
        raise RbacError(404, "Área padre no encontrada en el tenant")

    area_id = str(uuid4())
    row = (await session.execute(
        text(
            "INSERT INTO areas (id, tenant_id, nombre, codigo, parent_area_id) "
            "VALUES (:id, :t, :n, :c, :p) RETURNING *"
        ),
        {"id": area_id, "t": tenant_id, "n": payload.nombre, "c": payload.codigo, "p": payload.parent_area_id},
    )).mappings().first()
    return dict(row)


async def update_area(session: AsyncSession, tenant_id: str, area_id: str, payload: AreaUpdate) -> dict:
    await fijar_tenant(session, tenant_id)
    if not await get_area(session, tenant_id, area_id):
        raise RbacError(404, "Área no encontrada")

    changes = payload.model_dump(exclude_unset=True)
    if changes.get("responsable_user_id"):
        if not await has_active_role(session, tenant_id, changes["responsable_user_id"], Role.responsable_area.value):
            raise RbacError(409, "El usuario no tiene rol 'responsable_area' activo en el tenant")
    if not changes:
        return await get_area(session, tenant_id, area_id)

    # Sentencia estática: cada columna editable tiene su bandera; una columna ausente
    # de `changes` conserva su valor y una presente (incluso nula) lo reemplaza.
    row = (await session.execute(
        text(
            "UPDATE areas SET "
            "nombre = CASE WHEN :set_nombre THEN :nombre ELSE nombre END, "
            "codigo = CASE WHEN :set_codigo THEN :codigo ELSE codigo END, "
            "responsable_user_id = CASE WHEN :set_resp THEN :resp ELSE responsable_user_id END, "
            "updated_at = now() "
            "WHERE id=:id AND tenant_id=:t RETURNING *"
        ),
        {
            "set_nombre": "nombre" in changes, "nombre": changes.get("nombre"),
            "set_codigo": "codigo" in changes, "codigo": changes.get("codigo"),
            "set_resp": "responsable_user_id" in changes, "resp": changes.get("responsable_user_id"),
            "id": area_id, "t": tenant_id,
        },
    )).mappings().first()
    return dict(row)


async def allowed_area_ids(session: AsyncSession, tenant_id: str, user_id: str) -> Optional[set[str]]:
    """Áreas (con subáreas) donde el usuario actúa como responsable_area.

    None = alcance transversal (alguna asignación sin area_id).
    """
    rows = (await session.execute(
        text(
            "SELECT area_id FROM user_tenant_roles "
            "WHERE user_id=:u AND tenant_id=:t AND role='responsable_area' "
            "AND (valid_to IS NULL OR valid_to > now())"
        ),
        {"u": user_id, "t": tenant_id},
    )).all()
    roots = [r[0] for r in rows]
    if any(r is None for r in roots):
        return None
    if not roots:
        return set()

    result = await session.execute(
        text("""
            WITH RECURSIVE scope AS (
                SELECT id FROM areas WHERE tenant_id = :t AND id = ANY(:roots)
                UNION
                SELECT a.id FROM areas a JOIN scope s ON a.parent_area_id = s.id
                WHERE a.tenant_id = :t
            )
            SELECT id FROM scope
        """),
        {"t": tenant_id, "roots": roots},
    )
    return {r[0] for r in result.all()}
