"""Usuarios y membresía por tenant (sala ADPA: Organización).

Una asignación está activa cuando valid_to es nulo o futuro.
"""
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from features.organizacion.domain.models import UserCreate
from features.organizacion.services.contexto_tenant import fijar_tenant


async def has_active_role(session: AsyncSession, tenant_id: str, user_id: str, role: str) -> bool:
    # Fija el tenant antes de leer: con el rol de app la política RLS oculta
    # todas las filas si app.current_tenant_id no está definido.
    await fijar_tenant(session, tenant_id, user_id)
    result = await session.execute(
        text(
            "SELECT 1 FROM user_tenant_roles "
            "WHERE user_id=:u AND tenant_id=:t AND role=:r "
            "AND (valid_to IS NULL OR valid_to > now())"
        ),
        {"u": user_id, "t": tenant_id, "r": role},
    )
    return result.fetchone() is not None


async def list_my_roles(session: AsyncSession, tenant_id: str, user_id: str) -> list[dict]:
    await fijar_tenant(session, tenant_id, user_id)
    rows = (await session.execute(
        text(
            "SELECT r.id, r.role, r.area_id, a.nombre AS area_nombre, r.valid_from, r.valid_to "
            "FROM user_tenant_roles r LEFT JOIN areas a ON a.id = r.area_id "
            "WHERE r.user_id=:u AND r.tenant_id=:t "
            "AND (r.valid_to IS NULL OR r.valid_to > now()) "
            "ORDER BY r.role"
        ),
        {"u": user_id, "t": tenant_id},
    )).mappings().all()
    return [dict(r) for r in rows]


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
    await fijar_tenant(session, tenant_id)
    rows = (await session.execute(
        text(
            "SELECT u.id, u.email, u.nombre, u.activo, r.id AS assignment_id, r.role, r.area_id "
            "FROM user_tenant_roles r JOIN users u ON u.id = r.user_id "
            "WHERE r.tenant_id=:t AND (r.valid_to IS NULL OR r.valid_to > now()) "
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
