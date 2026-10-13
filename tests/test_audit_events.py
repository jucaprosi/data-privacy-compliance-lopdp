"""Pruebas de la tabla audit_events, RLS y registrar_evento.

Comprueba:
- Registro de evento via registrar_evento(...) usando la sesion del tenant.
- Aislamiento RLS con el rol lopdp_app:
  * Insercion propia -> 1 fila visible.
  * Tenant ajeno -> 0 filas visibles.
  * Sin tenant fijado -> 0 filas visibles.
- Append-only bajo el rol de aplicacion lopdp_app:
  * UPDATE denegado (PermissionDenied / insufficient_privilege).
  * DELETE denegado (PermissionDenied / insufficient_privilege).
- Indices e integridad de clave foranea.
"""
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app_core.audit import registrar_evento
from app_core.db.session import fijar_contexto_rls

pytestmark = pytest.mark.asyncio


async def _as_app_role(session, tenant_id: str | None) -> None:
    """Cambia al rol de aplicacion lopdp_app y fija el contexto RLS."""
    exists = (
        await session.execute(
            text("SELECT 1 FROM pg_roles WHERE rolname = 'lopdp_app'")
        )
    ).first()
    if not exists:
        pytest.skip("Rol lopdp_app no existe en la base de datos")
    await session.execute(text("SET LOCAL ROLE lopdp_app"))
    if tenant_id is not None:
        await fijar_contexto_rls(session, tenant_id=tenant_id)


async def test_registrar_evento_propio(db_session, seed_tenants):
    ta = seed_tenants["tenant_a"]
    ua = seed_tenants["user_a"]

    await _as_app_role(db_session, ta)

    event_id = await registrar_evento(
        session=db_session,
        tenant_id=ta,
        entity_type="area_responsable_request",
        entity_id="req-12345",
        action="role_assigned",
        user_id=ua,
        payload={"rol": "responsable_area", "area_id": "area-01"},
    )
    assert event_id is not None

    res = (
        await db_session.execute(
            text(
                "SELECT id, tenant_id, entity_type, entity_id, action, user_id, payload "
                "FROM audit_events WHERE id = :id"
            ),
            {"id": event_id},
        )
    ).first()

    assert res is not None
    assert res.id == event_id
    assert res.tenant_id == ta
    assert res.entity_type == "area_responsable_request"
    assert res.entity_id == "req-12345"
    assert res.action == "role_assigned"
    assert res.user_id == ua
    assert res.payload == {"rol": "responsable_area", "area_id": "area-01"}


async def test_aislamiento_rls_tenant_ajeno_ve_cero(db_session, seed_tenants):
    ta = seed_tenants["tenant_a"]
    tb = seed_tenants["tenant_b"]
    ua = seed_tenants["user_a"]

    # Insertamos evento como tenant A bajo rol lopdp_app
    await _as_app_role(db_session, ta)
    event_id = await registrar_evento(
        session=db_session,
        tenant_id=ta,
        entity_type="configuracion",
        entity_id="cfg-01",
        action="update_tamano",
        user_id=ua,
        payload={"nuevo_tamano": "pequena"},
    )
    await db_session.commit()

    # Como tenant B bajo lopdp_app, debe ver 0 filas de ese evento
    await _as_app_role(db_session, tb)
    res_b = (
        await db_session.execute(
            text("SELECT COUNT(*) FROM audit_events WHERE id = :id"),
            {"id": event_id},
        )
    ).scalar_one()
    assert res_b == 0

    # Total de eventos del tenant A vistos por B debe ser 0
    total_a_visto_por_b = (
        await db_session.execute(
            text("SELECT COUNT(*) FROM audit_events WHERE tenant_id = :t"),
            {"t": ta},
        )
    ).scalar_one()
    assert total_a_visto_por_b == 0

    # Como tenant desconocido / inexistente bajo lopdp_app
    await db_session.rollback()
    await _as_app_role(db_session, f"tenant-inexistente-{uuid4().hex[:8]}")
    res_inexistente = (
        await db_session.execute(
            text("SELECT COUNT(*) FROM audit_events WHERE id = :id"),
            {"id": event_id},
        )
    ).scalar_one()
    assert res_inexistente == 0


async def test_sin_tenant_fijado_no_ve_filas(db_session, seed_tenants):
    ta = seed_tenants["tenant_a"]
    ua = seed_tenants["user_a"]

    await _as_app_role(db_session, ta)
    event_id = await registrar_evento(
        session=db_session,
        tenant_id=ta,
        entity_type="roles",
        entity_id="role-xyz",
        action="role_revoked",
        user_id=ua,
        payload={"razon": "reestructuracion"},
    )
    await db_session.commit()

    # Sin tenant fijado (None) bajo lopdp_app
    await _as_app_role(db_session, None)
    res_sin_tenant = (
        await db_session.execute(
            text("SELECT COUNT(*) FROM audit_events WHERE id = :id"),
            {"id": event_id},
        )
    ).scalar_one()
    assert res_sin_tenant == 0


async def test_append_only_update_denegado_para_lopdp_app(db_session, seed_tenants):
    ta = seed_tenants["tenant_a"]
    ua = seed_tenants["user_a"]

    await _as_app_role(db_session, ta)
    event_id = await registrar_evento(
        session=db_session,
        tenant_id=ta,
        entity_type="seguridad",
        entity_id="sec-01",
        action="mfa_enabled",
        user_id=ua,
        payload={},
    )

    # Intento de UPDATE debe ser denegado por permisos de PostgreSQL
    with pytest.raises(DBAPIError) as exc_info:
        await db_session.execute(
            text("UPDATE audit_events SET action = 'tampered' WHERE id = :id"),
            {"id": event_id},
        )
    assert (
        "permission denied" in str(exc_info.value).lower()
        or "insufficient_privilege" in str(exc_info.value).lower()
    )
    await db_session.rollback()


async def test_append_only_delete_denegado_para_lopdp_app(db_session, seed_tenants):
    ta = seed_tenants["tenant_a"]
    ua = seed_tenants["user_a"]

    await _as_app_role(db_session, ta)
    event_id = await registrar_evento(
        session=db_session,
        tenant_id=ta,
        entity_type="seguridad",
        entity_id="sec-02",
        action="mfa_disabled",
        user_id=ua,
        payload={},
    )

    # Intento de DELETE debe ser denegado por permisos de PostgreSQL
    with pytest.raises(DBAPIError) as exc_info:
        await db_session.execute(
            text("DELETE FROM audit_events WHERE id = :id"),
            {"id": event_id},
        )
    assert (
        "permission denied" in str(exc_info.value).lower()
        or "insufficient_privilege" in str(exc_info.value).lower()
    )
    await db_session.rollback()


async def test_fk_invalida_rechazada(db_session):
    # Tenant inexistente debe fallar por Foreign Key Constraint
    with pytest.raises(DBAPIError) as exc_info:
        await db_session.execute(
            text(
                """
                INSERT INTO audit_events (
                    id, tenant_id, entity_type, entity_id, action, timestamp
                ) VALUES (
                    :id, :tid, :etype, :eid, :act, now()
                )
                """
            ),
            {
                "id": str(uuid4()),
                "tid": "tenant-no-existe-fk",
                "etype": "test",
                "eid": "test",
                "act": "test",
            },
        )
    assert (
        "foreign key" in str(exc_info.value).lower()
        or "violates foreign key constraint" in str(exc_info.value).lower()
    )
    await db_session.rollback()
