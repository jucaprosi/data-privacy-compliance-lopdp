# ¤rbac-tenant
# ¤seguridad
# ¤arbitro
"""ORG-01: Pruebas de la matriz única de incompatibilidades y DPO sin roles operativos.

Verifica:
1. Matriz en Python (features.organizacion.organizacion_service.INCOMPATIBILIDADES_ROLES y DPO_INCOMPATIBLE_ROLES):
   - Estructura y exhaustividad: pares bien formados con motivo y base legal específica.
   - DPO incompatible con todos los demás roles en la plataforma: coordinador, implementador, responsable_area, admin_organizacion.
   - Simetría lógica en las reglas de SoD del servicio (check_dpo_sod).
2. Consistencia entre Python y la Base de Datos:
   - Los roles incompatibles con DPO extraídos de fn_utr_dpo_sod en Postgres (vía pg_get_functiondef)
     coinciden exactamente con DPO_INCOMPATIBLE_ROLES en Python.
3. Validación contra el trigger de Base de Datos (fn_utr_dpo_sod):
   - Si un usuario ya tiene 'dpo', se rechaza asignar 'coordinador', 'implementador', 'responsable_area' o 'admin_organizacion'.
   - Si un usuario ya tiene cualquiera de esos 4 roles, se rechaza asignar 'dpo'.
   - Roles históricos expirados (valid_to <= now()) no bloquean la asignación.
4. Validación a través de la compuerta / servicio (grant_role):
   - Falla con RbacError / SoDViolation al intentar asignar roles incompatibles en ambos sentidos.
"""
from __future__ import annotations

import os
import re
import uuid
from datetime import datetime, timezone, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import create_async_engine

from features.organizacion.organizacion_service import (
    DPO_INCOMPATIBLE_ROLES,
    INCOMPATIBILIDADES_ROLES,
    RbacError,
    Role,
    RoleGrant,
    check_dpo_sod,
    grant_role,
)

ROLES_OPERATIVOS_DPO = {
    Role.coordinador,
    Role.implementador,
    Role.responsable_area,
    Role.admin_organizacion,
}


def _async_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL no configurada")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


@pytest_asyncio.fixture
async def conn():
    engine = create_async_engine(_async_url(), pool_pre_ping=True)
    async with engine.connect() as connection:
        trans = await connection.begin()
        yield connection
        await trans.rollback()
    await engine.dispose()


# ============================================================================
# 1. PRUEBAS PURAS DE LA MATRIZ (PYTHON)
# ============================================================================

def test_matriz_estructura_y_base_legal():
    """Cada entrada de la matriz tiene rol_a, rol_b, motivo claro y cita legal del Reglamento del Delegado."""
    assert len(INCOMPATIBILIDADES_ROLES) == 4
    for rol_a, rol_b, motivo, base_legal in INCOMPATIBILIDADES_ROLES:
        assert isinstance(rol_a, Role)
        assert isinstance(rol_b, Role)
        assert rol_a != rol_b
        assert len(motivo.strip()) > 15
        assert "Reglamento del Delegado" in base_legal
        # No debe citar el Art. 48 de la LOPDP para la independencia
        assert "Art. 48 LOPDP" not in base_legal


def test_dpo_incompatible_con_todos_los_demas_roles():
    """El DPO no puede tener ningún otro rol en la plataforma."""
    assert DPO_INCOMPATIBLE_ROLES == ROLES_OPERATIVOS_DPO
    todos_los_roles = set(Role)
    assert DPO_INCOMPATIBLE_ROLES == todos_los_roles - {Role.dpo}


@pytest.mark.parametrize("rol", list(ROLES_OPERATIVOS_DPO))
def test_check_dpo_sod_simetria_ambos_sentidos(rol):
    """check_dpo_sod rechaza la combinación en ambos sentidos."""
    # Sentido 1: nuevo DPO, ya tiene rol
    motivo_1 = check_dpo_sod(Role.dpo, [rol])
    assert motivo_1 is not None
    assert "El DPO no puede tener roles operativos" in motivo_1

    # Sentido 2: nuevo rol, ya es DPO
    motivo_2 = check_dpo_sod(rol, [Role.dpo])
    assert motivo_2 is not None
    assert "no puede recibir el rol" in motivo_2


def test_roles_entre_si_sin_dpo_no_violan_sod_dpo():
    """Roles no-DPO no violan la regla SoD DPO entre sí."""
    for r1 in ROLES_OPERATIVOS_DPO:
        for r2 in ROLES_OPERATIVOS_DPO:
            assert check_dpo_sod(r1, [r2]) is None


# ============================================================================
# 2. COMPARACIÓN DETERMINISTA PYTHON VS BASE DE DATOS (pg_get_functiondef)
# ============================================================================

@pytest.mark.asyncio
async def test_coincidencia_exacta_trigger_sql_y_tabla_python(conn):
    """La lista de roles de fn_utr_dpo_sod en Postgres coincide con DPO_INCOMPATIBLE_ROLES."""
    res = await conn.execute(
        text("SELECT pg_get_functiondef(oid) FROM pg_proc WHERE proname = 'fn_utr_dpo_sod'")
    )
    fdef = res.scalar()
    assert fdef is not None, "La función fn_utr_dpo_sod no existe en la BD"

    # Buscar todas las listas de roles en: role IN ('...')
    matches = re.findall(r"role\s+IN\s*\(([^)]+)\)", fdef, re.IGNORECASE)
    assert len(matches) >= 1, f"No se encontró 'role IN (...)': {fdef}"

    roles_encontrados_en_sql: set[str] = set()
    for m in matches:
        roles = {r.strip().strip("'\"") for r in m.split(",")}
        roles_encontrados_en_sql.update(roles)

    roles_python = {r.value for r in DPO_INCOMPATIBLE_ROLES}
    assert roles_encontrados_en_sql == roles_python, (
        f"Discrepancia entre SQL ({roles_encontrados_en_sql}) y Python ({roles_python})"
    )


# ============================================================================
# 3. PRUEBAS CONTRA EL TRIGGER DE LA BD (user_tenant_roles)
# ============================================================================

async def _crear_tenant_y_usuario(conn, sufijo: str) -> tuple[str, str]:
    tid = f"org01-t-{sufijo}"
    uid = f"org01-u-{sufijo}"
    await conn.execute(
        text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, tamano) "
             "VALUES (:t, :n, :r, :ruc, 'micro')"),
        {"t": tid, "n": tid, "r": tid, "ruc": f"RUC{sufijo[:12]}"},
    )
    await conn.execute(
        text("INSERT INTO users (id, email, nombre) VALUES (:u, :e, :n)"),
        {"u": uid, "e": f"{uid}@test.local", "n": uid},
    )
    return tid, uid


@pytest.mark.asyncio
@pytest.mark.parametrize("rol", [r.value for r in ROLES_OPERATIVOS_DPO])
async def test_trigger_bloquea_asignar_otro_rol_a_un_dpo(conn, rol):
    """Si el usuario ya tiene 'dpo', el trigger fn_utr_dpo_sod rechaza asignarle cualquier otro rol."""
    sufijo = uuid.uuid4().hex[:10]
    tid, uid = await _crear_tenant_y_usuario(conn, sufijo)

    await conn.execute(
        text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:id, :u, :t, 'dpo')"),
        {"id": f"r1-{sufijo}", "u": uid, "t": tid},
    )

    sp = await conn.begin_nested()
    with pytest.raises(IntegrityError) as exc:
        await conn.execute(
            text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:id, :u, :t, :r)"),
            {"id": f"r2-{sufijo}", "u": uid, "t": tid, "r": rol},
        )
    assert "SoD DPO" in str(exc.value.orig)
    await sp.rollback()


@pytest.mark.asyncio
@pytest.mark.parametrize("rol", [r.value for r in ROLES_OPERATIVOS_DPO])
async def test_trigger_bloquea_asignar_dpo_a_usuario_con_otro_rol(conn, rol):
    """Si el usuario ya tiene cualquier otro rol operativo, el trigger fn_utr_dpo_sod rechaza asignarle 'dpo'."""
    sufijo = uuid.uuid4().hex[:10]
    tid, uid = await _crear_tenant_y_usuario(conn, sufijo)

    await conn.execute(
        text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:id, :u, :t, :r)"),
        {"id": f"r1-{sufijo}", "u": uid, "t": tid, "r": rol},
    )

    sp = await conn.begin_nested()
    with pytest.raises(IntegrityError) as exc:
        await conn.execute(
            text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:id, :u, :t, 'dpo')"),
            {"id": f"r2-{sufijo}", "u": uid, "t": tid},
        )
    assert "SoD DPO" in str(exc.value.orig)
    await sp.rollback()


@pytest.mark.asyncio
async def test_trigger_permite_rol_si_dpo_anterior_expirado(conn):
    """Un rol previo con valid_to en el pasado no genera violación de SoD en el trigger."""
    sufijo = uuid.uuid4().hex[:10]
    tid, uid = await _crear_tenant_y_usuario(conn, sufijo)
    expirado = datetime.now(timezone.utc) - timedelta(days=1)

    # Rol DPO expirado
    await conn.execute(
        text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role, valid_to) VALUES (:id, :u, :t, 'dpo', :vt)"),
        {"id": f"r1-{sufijo}", "u": uid, "t": tid, "vt": expirado},
    )

    # Ahora puede recibir responsable_area sin excepción
    await conn.execute(
        text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:id, :u, :t, 'responsable_area')"),
        {"id": f"r2-{sufijo}", "u": uid, "t": tid},
    )

    res = await conn.execute(
        text("SELECT role FROM user_tenant_roles WHERE user_id = :u AND tenant_id = :t AND (valid_to IS NULL OR valid_to > now())"),
        {"u": uid, "t": tid},
    )
    roles = [r[0] for r in res.fetchall()]
    assert roles == ["responsable_area"]


# ============================================================================
# 4. PRUEBAS DEL SERVICIO (grant_role)
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.parametrize("rol", list(ROLES_OPERATIVOS_DPO))
async def test_servicio_grant_role_falla_por_sod_con_dpo(conn, rol):
    """grant_role eleva RbacError cuando se intenta asignar un rol incompatible con DPO."""
    sufijo = uuid.uuid4().hex[:10]
    tid, uid = await _crear_tenant_y_usuario(conn, sufijo)
    admin_id = f"admin-{sufijo}"
    await conn.execute(
        text("INSERT INTO users (id, email, nombre) VALUES (:u, :e, :n)"),
        {"u": admin_id, "e": f"{admin_id}@test.local", "n": admin_id},
    )

    # Caso 1: Asignar rol a quien ya es DPO
    await grant_role(conn, tenant_id=tid, granted_by=admin_id, payload=RoleGrant(user_id=uid, role=Role.dpo))

    with pytest.raises(RbacError) as exc:
        await grant_role(conn, tenant_id=tid, granted_by=admin_id, payload=RoleGrant(user_id=uid, role=rol))
    assert "DPO" in str(exc.value)

    # Caso 2: Nuevo usuario con 'rol', intentar asignarle DPO
    sufijo2 = uuid.uuid4().hex[:10]
    tid2, uid2 = await _crear_tenant_y_usuario(conn, sufijo2)
    admin_id2 = f"admin-{sufijo2}"
    await conn.execute(
        text("INSERT INTO users (id, email, nombre) VALUES (:u, :e, :n)"),
        {"u": admin_id2, "e": f"{admin_id2}@test.local", "n": admin_id2},
    )
    await grant_role(conn, tenant_id=tid2, granted_by=admin_id2, payload=RoleGrant(user_id=uid2, role=rol))

    with pytest.raises(RbacError) as exc2:
        await grant_role(conn, tenant_id=tid2, granted_by=admin_id2, payload=RoleGrant(user_id=uid2, role=Role.dpo))
    assert "DPO" in str(exc2.value)
