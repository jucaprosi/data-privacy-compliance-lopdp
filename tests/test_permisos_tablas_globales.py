# ¤seguridad
# ¤rbac-tenant
# ¤arbitro
"""Pruebas de permisos mínimos y ausencia de BYPASSRLS en tablas globales (SEC-10, PRD §5.3.1).

Doctrina:
- Los privilegios de 'lopdp_app' sobre 'tenants' y 'users' son estrictamente los
  mínimos que usa el código de la aplicación (SELECT, INSERT, UPDATE).
- 'lopdp_app' bajo ninguna circunstancia debe tener concedido DELETE sobre 'tenants' ni 'users'.
- El rol con el que conecta la aplicación (cuando DATABASE_URL esté definida con rol de aplicación)
  no debe tener el atributo BYPASSRLS.
- Aislamiento: sin SQL interpolado (tests/test_sin_sql_interpolado.py).
"""
from __future__ import annotations

import os
import urllib.parse
from typing import Optional

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def conn(db_engine):
    """Conexión transaccional directa a la base de pruebas."""
    async with db_engine.connect() as c:
        tx = await c.begin()
        try:
            yield c
        finally:
            await tx.rollback()


async def test_privilegios_minimos_lopdp_app_en_tenants(conn):
    """Verifica que lopdp_app tenga SELECT, INSERT, UPDATE en tenants y NUNCA DELETE."""
    # Consultar privilegios concedidos en information_schema sin f-strings
    query = text(
        "SELECT privilege_type "
        "FROM information_schema.table_privileges "
        "WHERE grantee = :grantee AND table_name = :tname "
        "ORDER BY privilege_type"
    )
    res = await conn.execute(query, {"grantee": "lopdp_app", "tname": "tenants"})
    privilegios = {r[0] for r in res.fetchall()}

    assert "DELETE" not in privilegios, "lopdp_app no debe tener permiso DELETE en 'tenants'"
    assert "SELECT" in privilegios, "lopdp_app requiere permiso SELECT en 'tenants'"
    assert "INSERT" in privilegios, "lopdp_app requiere permiso INSERT en 'tenants'"
    assert "UPDATE" in privilegios, "lopdp_app requiere permiso UPDATE en 'tenants'"


async def test_privilegios_minimos_lopdp_app_en_users(conn):
    """Verifica que lopdp_app tenga SELECT, INSERT, UPDATE en users y NUNCA DELETE."""
    query = text(
        "SELECT privilege_type "
        "FROM information_schema.table_privileges "
        "WHERE grantee = :grantee AND table_name = :tname "
        "ORDER BY privilege_type"
    )
    res = await conn.execute(query, {"grantee": "lopdp_app", "tname": "users"})
    privilegios = {r[0] for r in res.fetchall()}

    assert "DELETE" not in privilegios, "lopdp_app no debe tener permiso DELETE en 'users'"
    assert "SELECT" in privilegios, "lopdp_app requiere permiso SELECT en 'users'"
    assert "INSERT" in privilegios, "lopdp_app requiere permiso INSERT en 'users'"
    assert "UPDATE" in privilegios, "lopdp_app requiere permiso UPDATE en 'users'"


async def test_rol_lopdp_app_no_tiene_bypassrls(conn):
    """Verifica que el rol de aplicación 'lopdp_app' tenga rolbypassrls = False."""
    query = text("SELECT rolbypassrls, rolsuper FROM pg_roles WHERE rolname = :rol")
    res = await conn.execute(query, {"rol": "lopdp_app"})
    fila = res.first()
    assert fila is not None, "El rol 'lopdp_app' debe existir en la base de datos"
    assert fila[0] is False, "El rol 'lopdp_app' no debe tener atributo BYPASSRLS"
    assert fila[1] is False, "El rol 'lopdp_app' no debe ser superusuario"


async def test_rol_conexion_aplicacion_no_tiene_bypassrls_si_es_lopdp_app(conn):
    """Comprueba el atributo BYPASSRLS del rol configurado para la aplicación."""
    # Inspeccionar el rol de la aplicación en DATABASE_URL
    app_url = os.environ.get("DATABASE_URL")
    if not app_url:
        pytest.skip("DATABASE_URL no configurada")

    # Extraer usuario de la URL de forma segura
    parsed = urllib.parse.urlsplit(app_url)
    username = parsed.username

    if not username:
        pytest.skip("No se pudo inferir el usuario de DATABASE_URL")

    # Si la URL usa lopdp_app, verificar en pg_roles que no tenga BYPASSRLS
    if username == "lopdp_app":
        query = text("SELECT rolbypassrls FROM pg_roles WHERE rolname = :rol")
        res = await conn.execute(query, {"rol": username})
        fila = res.first()
        assert fila is not None, "El rol de la aplicación debe existir"
        assert fila[0] is False, "El rol de la aplicación no debe tener BYPASSRLS"


async def test_intento_delete_como_lopdp_app_falla_por_permisos(conn):
    """Intento explícito de ejecutar DELETE sobre users o tenants con SET LOCAL ROLE lopdp_app debe ser denegado."""
    sp = await conn.begin_nested()
    try:
        await conn.execute(text("SET LOCAL ROLE lopdp_app"))
        with pytest.raises(Exception) as exc:
            await conn.execute(text("DELETE FROM users WHERE id = :u"), {"u": "usuario-inexistente"})
        assert "permission denied" in str(exc.value).lower() or "permiso denegado" in str(exc.value).lower()
    finally:
        await sp.rollback()
