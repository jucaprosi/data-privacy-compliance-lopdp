"""Aislamiento RLS real con el rol de aplicación lopdp_app (sin BYPASSRLS).

Se conecta con el rol dueño de TEST_DATABASE_URL y hace SET LOCAL ROLE
lopdp_app (membresía concedida por la migración 20261008_app_role_rls), de
modo que las políticas se evalúan como las vería la app en producción.
"""
import pytest
from sqlalchemy import text

from app_core.services import rbac_service

pytestmark = pytest.mark.asyncio


async def _as_app_role(session, tenant_id: str | None) -> None:
    exists = (await session.execute(
        text("SELECT 1 FROM pg_roles WHERE rolname = 'lopdp_app'")
    )).first()
    if not exists:
        pytest.skip("Rol lopdp_app no existe: falta aplicar 20261008_app_role_rls")
    await session.execute(text("SET LOCAL ROLE lopdp_app"))
    if tenant_id is not None:
        await session.execute(
            text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": tenant_id}
        )


async def _count_utr(session, tenant_id: str) -> int:
    return (await session.execute(
        text("SELECT count(*) FROM user_tenant_roles WHERE tenant_id = :t"), {"t": tenant_id}
    )).scalar_one()


async def test_rol_app_sin_bypassrls(db_session):
    row = (await db_session.execute(
        text("SELECT rolbypassrls, rolsuper FROM pg_roles WHERE rolname = 'lopdp_app'")
    )).first()
    if row is None:
        pytest.skip("Rol lopdp_app no existe")
    assert row == (False, False)


async def test_tenant_ajeno_ve_cero_filas(db_session, seed_tenants):
    ta, tb = seed_tenants["tenant_a"], seed_tenants["tenant_b"]
    await db_session.commit()

    await _as_app_role(db_session, tb)
    assert await _count_utr(db_session, ta) == 0
    total = (await db_session.execute(text("SELECT count(*) FROM user_tenant_roles"))).scalar_one()
    assert total == await _count_utr(db_session, tb)
    await db_session.rollback()

    await _as_app_role(db_session, "tenant-inexistente")
    assert (await db_session.execute(text("SELECT count(*) FROM user_tenant_roles"))).scalar_one() == 0
    await db_session.rollback()


async def test_sin_tenant_fijado_no_ve_filas(db_session, seed_tenants):
    await db_session.commit()
    await _as_app_role(db_session, None)
    assert (await db_session.execute(text("SELECT count(*) FROM user_tenant_roles"))).scalar_one() == 0
    await db_session.rollback()


async def test_tenant_propio_ve_sus_filas_y_has_active_role(db_session, seed_tenants):
    ta, ua = seed_tenants["tenant_a"], seed_tenants["user_a"]
    await db_session.commit()

    await _as_app_role(db_session, ta)
    assert await _count_utr(db_session, ta) == 1
    await db_session.rollback()

    # get_context -> has_active_role debe fijar el tenant por sí mismo.
    await _as_app_role(db_session, None)
    assert await rbac_service.has_active_role(db_session, ta, ua, "implementador")
    await db_session.rollback()
