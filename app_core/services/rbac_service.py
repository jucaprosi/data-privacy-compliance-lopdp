"""Servicio RBAC por tenant: usuarios, áreas, asignación de roles y SoD.

Reglas de negocio:
- SoD del DPO (Art. 48 LOPDP): 'dpo' es incompatible con 'implementador' y
  'encargado' activos en el mismo tenant. Se valida aquí y, como respaldo,
  en el trigger trg_utr_dpo_sod de la BD.
- Cuatro ojos: quien sube una evidencia no puede validarla.
- 'responsable_area' puede acotarse a un área; el alcance incluye sus subáreas.
  Una asignación sin area_id es transversal al tenant.
- No se puede revocar el último 'admin_organizacion' activo del tenant.
"""
from datetime import datetime, timezone
from typing import Iterable, Optional
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.schemas.rbac_schema import (
    AREA_SCOPED_ROLES,
    DPO_INCOMPATIBLE_ROLES,
    AreaCreate,
    AreaUpdate,
    RoleGrant,
    UserCreate,
)
from app_core.schemas.roadmap_schema import Role

ACTIVE_ROLE_SQL = "(valid_to IS NULL OR valid_to > now())"


class RbacError(Exception):
    """Error de negocio RBAC. `code` se traduce a HTTP en el router."""

    def __init__(self, code: int, detail: str):
        super().__init__(detail)
        self.code = code
        self.detail = detail


class SoDViolation(RbacError):
    def __init__(self, detail: str):
        super().__init__(409, detail)


# ============================================================================
# Reglas puras
# ============================================================================

def check_dpo_sod(new_role: Role, active_roles: Iterable[Role]) -> Optional[str]:
    """Devuelve el motivo de violación de SoD del DPO, o None si es compatible."""
    active = set(active_roles)
    if new_role == Role.dpo and active & DPO_INCOMPATIBLE_ROLES:
        conflicto = sorted(r.value for r in active & DPO_INCOMPATIBLE_ROLES)
        return f"El DPO no puede tener roles operativos en el mismo tenant (tiene: {', '.join(conflicto)})"
    if new_role in DPO_INCOMPATIBLE_ROLES and Role.dpo in active:
        return f"El usuario es DPO en este tenant y no puede recibir el rol '{new_role.value}'"
    return None


def check_four_eyes(uploaded_by: Optional[str], validator_id: str) -> Optional[str]:
    """Devuelve el motivo si el validador es quien subió la evidencia."""
    if uploaded_by and uploaded_by == validator_id:
        return "Quien sube una evidencia no puede validarla"
    return None


# ============================================================================
# Persistencia
# ============================================================================

async def _set_tenant(session: AsyncSession, tenant_id: str, user_id: str | None = None) -> None:
    await session.execute(
        text("SELECT set_config('app.current_tenant_id', :tid, true)"),
        {"tid": tenant_id},
    )
    if user_id:
        await session.execute(
            text("SELECT set_config('app.current_user_id', :uid, true)"),
            {"uid": user_id},
        )


async def has_active_role(session: AsyncSession, tenant_id: str, user_id: str, role: str) -> bool:
    # Fija el tenant antes de leer: con el rol de app la política RLS oculta
    # todas las filas si app.current_tenant_id no está definido.
    await _set_tenant(session, tenant_id, user_id)
    result = await session.execute(
        text(
            "SELECT 1 FROM user_tenant_roles "
            f"WHERE user_id=:u AND tenant_id=:t AND role=:r AND {ACTIVE_ROLE_SQL}"
        ),
        {"u": user_id, "t": tenant_id, "r": role},
    )
    return result.fetchone() is not None


async def list_my_roles(session: AsyncSession, tenant_id: str, user_id: str) -> list[dict]:
    await _set_tenant(session, tenant_id, user_id)
    rows = (await session.execute(
        text(
            "SELECT r.id, r.role, r.area_id, a.nombre AS area_nombre, r.valid_from, r.valid_to "
            "FROM user_tenant_roles r LEFT JOIN areas a ON a.id = r.area_id "
            f"WHERE r.user_id=:u AND r.tenant_id=:t AND {ACTIVE_ROLE_SQL.replace('valid_to', 'r.valid_to')} "
            "ORDER BY r.role"
        ),
        {"u": user_id, "t": tenant_id},
    )).mappings().all()
    return [dict(r) for r in rows]


# ---------------------------- Usuarios --------------------------------------

async def create_or_get_user(session: AsyncSession, payload: UserCreate) -> dict:
    """Crea el usuario o devuelve el existente con ese email (los usuarios son globales)."""
    email = payload.email.strip().lower()
    row = (await session.execute(
        text("SELECT id, email FROM users WHERE lower(email) = :e AND deleted_at IS NULL"),
        {"e": email},
    )).mappings().first()
    if row:
        return {"id": row["id"], "email": row["email"], "creado": False}

    user_id = str(uuid4())
    await session.execute(
        text("INSERT INTO users (id, email, nombre) VALUES (:id, :e, :n)"),
        {"id": user_id, "e": email, "n": payload.nombre.strip()},
    )
    return {"id": user_id, "email": email, "creado": True}


async def list_tenant_users(session: AsyncSession, tenant_id: str) -> list[dict]:
    """Usuarios con al menos una asignación activa en el tenant, con sus roles."""
    await _set_tenant(session, tenant_id)
    rows = (await session.execute(
        text(
            "SELECT u.id, u.email, u.nombre, u.activo, r.id AS assignment_id, r.role, r.area_id "
            "FROM user_tenant_roles r JOIN users u ON u.id = r.user_id "
            f"WHERE r.tenant_id=:t AND {ACTIVE_ROLE_SQL.replace('valid_to', 'r.valid_to')} "
            "ORDER BY u.nombre, r.role"
        ),
        {"t": tenant_id},
    )).mappings().all()

    users: dict[str, dict] = {}
    for r in rows:
        u = users.setdefault(r["id"], {
            "id": r["id"], "email": r["email"], "nombre": r["nombre"],
            "activo": r["activo"], "roles": [],
        })
        u["roles"].append({"assignment_id": r["assignment_id"], "role": r["role"], "area_id": r["area_id"]})
    return list(users.values())


# ---------------------------- Áreas -----------------------------------------

async def _get_area(session: AsyncSession, tenant_id: str, area_id: str) -> Optional[dict]:
    row = (await session.execute(
        text("SELECT * FROM areas WHERE id=:id AND tenant_id=:t AND deleted_at IS NULL"),
        {"id": area_id, "t": tenant_id},
    )).mappings().first()
    return dict(row) if row else None


async def list_areas(session: AsyncSession, tenant_id: str) -> list[dict]:
    await _set_tenant(session, tenant_id)
    rows = (await session.execute(
        text("SELECT * FROM areas WHERE tenant_id=:t AND deleted_at IS NULL ORDER BY nombre"),
        {"t": tenant_id},
    )).mappings().all()
    return [dict(r) for r in rows]


async def create_area(session: AsyncSession, tenant_id: str, payload: AreaCreate) -> dict:
    await _set_tenant(session, tenant_id)
    if payload.parent_area_id and not await _get_area(session, tenant_id, payload.parent_area_id):
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
    await _set_tenant(session, tenant_id)
    if not await _get_area(session, tenant_id, area_id):
        raise RbacError(404, "Área no encontrada")

    changes = payload.model_dump(exclude_unset=True)
    if "responsable_user_id" in changes and changes["responsable_user_id"]:
        uid = changes["responsable_user_id"]
        if not await has_active_role(session, tenant_id, uid, Role.responsable_area.value):
            raise RbacError(409, "El usuario no tiene rol 'responsable_area' activo en el tenant")
    if not changes:
        return await _get_area(session, tenant_id, area_id)

    sets = ", ".join(f"{col} = :{col}" for col in changes)
    row = (await session.execute(
        text(f"UPDATE areas SET {sets}, updated_at = now() WHERE id=:id AND tenant_id=:t RETURNING *"),
        {**changes, "id": area_id, "t": tenant_id},
    )).mappings().first()
    return dict(row)


async def allowed_area_ids(session: AsyncSession, tenant_id: str, user_id: str) -> Optional[set[str]]:
    """Áreas (con subáreas) donde el usuario actúa como responsable_area.

    None = alcance transversal (alguna asignación sin area_id).
    """
    rows = (await session.execute(
        text(
            "SELECT area_id FROM user_tenant_roles "
            f"WHERE user_id=:u AND tenant_id=:t AND role='responsable_area' AND {ACTIVE_ROLE_SQL}"
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


async def ensure_task_in_area_scope(session: AsyncSession, tenant_id: str, user_id: str, task_id: str) -> None:
    """Exige que la tarea pertenezca a un área del responsable_area. Transversal = sin restricción."""
    scope = await allowed_area_ids(session, tenant_id, user_id)
    if scope is None:
        return
    row = (await session.execute(
        text("SELECT area_id FROM roadmap_tasks WHERE id=:id AND tenant_id=:t"),
        {"id": task_id, "t": tenant_id},
    )).first()
    if not row:
        raise RbacError(404, "Tarea no encontrada")
    if row[0] is None or row[0] not in scope:
        raise RbacError(403, "La tarea no pertenece a un área a su cargo")


# ---------------------------- Roles -----------------------------------------

async def list_role_assignments(session: AsyncSession, tenant_id: str, include_revoked: bool = False) -> list[dict]:
    await _set_tenant(session, tenant_id)
    where = "" if include_revoked else f"AND {ACTIVE_ROLE_SQL}"
    rows = (await session.execute(
        text(f"SELECT * FROM user_tenant_roles WHERE tenant_id=:t {where} ORDER BY granted_at"),
        {"t": tenant_id},
    )).mappings().all()
    return [dict(r) for r in rows]


async def grant_role(session: AsyncSession, tenant_id: str, granted_by: str, payload: RoleGrant) -> dict:
    await _set_tenant(session, tenant_id, granted_by)

    user = (await session.execute(
        text("SELECT id FROM users WHERE id=:id AND deleted_at IS NULL"),
        {"id": payload.user_id},
    )).first()
    if not user:
        raise RbacError(404, "Usuario no encontrado")
    if payload.area_id and not await _get_area(session, tenant_id, payload.area_id):
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
        # Carrera con otra asignación concurrente; el trigger de BD tiene la última palabra.
        raise SoDViolation(f"Asignación rechazada por la BD: {exc.orig}") from exc
    return dict(row)


async def revoke_role(session: AsyncSession, tenant_id: str, revoked_by: str, assignment_id: str) -> dict:
    await _set_tenant(session, tenant_id, revoked_by)

    row = (await session.execute(
        text(
            "SELECT * FROM user_tenant_roles "
            f"WHERE id=:id AND tenant_id=:t AND {ACTIVE_ROLE_SQL}"
        ),
        {"id": assignment_id, "t": tenant_id},
    )).mappings().first()
    if not row:
        raise RbacError(404, "Asignación activa no encontrada")

    if row["role"] == Role.admin_organizacion.value:
        admins = (await session.execute(
            text(
                "SELECT count(*) FROM user_tenant_roles "
                f"WHERE tenant_id=:t AND role='admin_organizacion' AND {ACTIVE_ROLE_SQL}"
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
