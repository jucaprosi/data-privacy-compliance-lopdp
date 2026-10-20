"""Pruebas de esquema, RLS y permisos de derechos_arco_solicitudes (SEC-09).

Verifica contra la base de datos real:
1. Columnas y tipos en PostgreSQL concuerdan con el modelo SolicitudARCO.
2. ENABLE y FORCE ROW LEVEL SECURITY activos en pg_class.
3. Existencia y definición de la política RLS tenant_isolation_derechos_arco_solicitudes.
4. Permisos para lopdp_app: SELECT, INSERT, UPDATE permitidos; DELETE denegado.
5. Aislamiento RLS efectivo:
   - Con tenant_id fijado, ve sus propias solicitudes y no las de otro tenant.
   - Sin tenant_id fijado, ve 0 solicitudes.
"""
from datetime import datetime, timezone, timedelta
import uuid
import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from features.derechos_arco.domain.models import SolicitudARCO, TipoSolicitud, EstadoSolicitud

pytestmark = pytest.mark.asyncio


async def _as_app_role(session, tenant_id: str | uuid.UUID | None) -> None:
    exists = (await session.execute(
        text("SELECT 1 FROM pg_roles WHERE rolname = 'lopdp_app'")
    )).first()
    if not exists:
        pytest.skip("Rol lopdp_app no existe")
    await session.execute(text("SET LOCAL ROLE lopdp_app"))
    if tenant_id is not None:
        await session.execute(
            text("SELECT set_config('app.current_tenant_id', :t, true)"),
            {"t": str(tenant_id)},
        )
    else:
        await session.execute(
            text("SELECT set_config('app.current_tenant_id', '', true)")
        )


async def test_esquema_columnas_y_tipos_coinciden_con_modelo(db_session):
    """Verifica que las columnas físicas en PostgreSQL coincidan con SolicitudARCO."""
    query = text("""
        SELECT column_name, data_type, udt_name, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'derechos_arco_solicitudes'
    """)
    res = await db_session.execute(query)
    columnas_db = {row.column_name: row for row in res.fetchall()}

    columnas_modelo = SolicitudARCO.__table__.columns
    for col in columnas_modelo:
        assert col.name in columnas_db, f"Columna {col.name} falta en la base de datos"
        db_col = columnas_db[col.name]
        if not col.nullable:
            assert db_col.is_nullable == "NO", f"Columna {col.name} debería ser NOT NULL"

    # Tipos específicos
    assert columnas_db["id"].udt_name == "uuid"
    assert columnas_db["tenant_id"].udt_name == "uuid"
    assert columnas_db["tipo_solicitud"].udt_name == "tiposolicitud"
    assert columnas_db["estado"].udt_name == "estadosolicitud"
    assert columnas_db["cedula_solicitante"].udt_name == "varchar"
    assert columnas_db["nombre_solicitante"].udt_name == "varchar"
    assert columnas_db["fecha_recepcion"].udt_name in ("timestamptz", "timestamp with time zone")
    assert columnas_db["fecha_vencimiento"].udt_name in ("timestamptz", "timestamp with time zone")
    assert columnas_db["evidencia_respuesta_hash"].udt_name == "varchar"


async def test_rls_activado_y_forzado(db_session):
    """Verifica relrowsecurity=true y relforcerowsecurity=true en pg_class."""
    query = text("""
        SELECT relrowsecurity, relforcerowsecurity
        FROM pg_class
        WHERE relname = 'derechos_arco_solicitudes'
          AND relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
    """)
    res = await db_session.execute(query)
    row = res.first()
    assert row is not None, "No se encontró la tabla en pg_class"
    relrowsecurity, relforcerowsecurity = row
    assert relrowsecurity is True, "ROW LEVEL SECURITY no está activado"
    assert relforcerowsecurity is True, "ROW LEVEL SECURITY no está forzado (FORCE)"


async def test_politica_rls_existente(db_session):
    """Verifica existencia de la política de aislamiento en pg_policies."""
    query = text("""
        SELECT policyname, permissive, cmd
        FROM pg_policies
        WHERE tablename = 'derechos_arco_solicitudes'
          AND policyname = 'tenant_isolation_derechos_arco_solicitudes'
    """)
    res = await db_session.execute(query)
    row = res.first()
    assert row is not None, "Falta la política tenant_isolation_derechos_arco_solicitudes"
    assert row.permissive == "PERMISSIVE"
    assert row.cmd == "ALL"


async def test_permisos_lopdp_app_select_insert_update_permitidos(db_session):
    """Verifica que el rol lopdp_app puede hacer SELECT, INSERT y UPDATE."""
    tenant_id = uuid.uuid4()
    solicitud_id = uuid.uuid4()
    vencimiento = datetime.now(timezone.utc) + timedelta(days=15)

    # Entrar como lopdp_app y fijar tenant
    await _as_app_role(db_session, tenant_id)

    # 1. INSERT
    insert_sql = text("""
        INSERT INTO derechos_arco_solicitudes (
            id, tenant_id, tipo_solicitud, estado, cedula_solicitante, nombre_solicitante, fecha_vencimiento
        ) VALUES (
            :id, :tenant_id, 'ACCESO', 'RECIBIDA', '1710000001', 'Juan Perez', :vencimiento
        )
    """)
    await db_session.execute(insert_sql, {
        "id": solicitud_id,
        "tenant_id": tenant_id,
        "vencimiento": vencimiento,
    })

    # 2. SELECT
    select_sql = text("""
        SELECT cedula_solicitante, estado FROM derechos_arco_solicitudes WHERE id = :id
    """)
    row = (await db_session.execute(select_sql, {"id": solicitud_id})).first()
    assert row is not None
    assert row.cedula_solicitante == "1710000001"
    assert row.estado == "RECIBIDA"

    # 3. UPDATE
    update_sql = text("""
        UPDATE derechos_arco_solicitudes
        SET estado = 'EN_ANALISIS'
        WHERE id = :id
    """)
    await db_session.execute(update_sql, {"id": solicitud_id})

    row_upd = (await db_session.execute(select_sql, {"id": solicitud_id})).first()
    assert row_upd.estado == "EN_ANALISIS"

    await db_session.rollback()


async def test_permisos_lopdp_app_delete_denegado(db_session):
    """Verifica que el rol lopdp_app tiene denegado el DELETE (GRANT SELECT, INSERT, UPDATE)."""
    tenant_id = uuid.uuid4()
    solicitud_id = uuid.uuid4()
    vencimiento = datetime.now(timezone.utc) + timedelta(days=15)

    # Como dueño, insertar fila para probar
    insert_sql = text("""
        INSERT INTO derechos_arco_solicitudes (
            id, tenant_id, tipo_solicitud, estado, cedula_solicitante, nombre_solicitante, fecha_vencimiento
        ) VALUES (
            :id, :tenant_id, 'RECTIFICACION', 'RECIBIDA', '1710000002', 'Maria Lopez', :vencimiento
        )
    """)
    await db_session.execute(insert_sql, {
        "id": solicitud_id,
        "tenant_id": tenant_id,
        "vencimiento": vencimiento,
    })

    # Cambiar a rol lopdp_app
    await _as_app_role(db_session, tenant_id)

    delete_sql = text("""
        DELETE FROM derechos_arco_solicitudes WHERE id = :id
    """)
    with pytest.raises(DBAPIError) as exc_info:
        await db_session.execute(delete_sql, {"id": solicitud_id})

    # Código 42501 es insufficient_privilege en Postgres
    orig = getattr(exc_info.value, "orig", None)
    sqlstate = getattr(orig, "sqlstate", None) or getattr(orig, "pgcode", None)
    assert sqlstate == "42501" or "permission denied" in str(exc_info.value).lower()

    await db_session.rollback()


async def test_aislamiento_rls_entre_tenants_y_sin_tenant(db_session):
    """Verifica aislamiento RLS:
    - Tenant A solo ve registros de Tenant A.
    - Tenant B solo ve registros de Tenant B.
    - Sin tenant fijado ve 0 registros.
    """
    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()
    vencimiento = datetime.now(timezone.utc) + timedelta(days=15)

    # Insertar filas como dueño
    insert_sql = text("""
        INSERT INTO derechos_arco_solicitudes (
            id, tenant_id, tipo_solicitud, estado, cedula_solicitante, nombre_solicitante, fecha_vencimiento
        ) VALUES (
            :id, :tenant_id, 'ACCESO', 'RECIBIDA', '1710000003', 'Usuario A', :vencimiento
        )
    """)
    id_a = uuid.uuid4()
    id_b = uuid.uuid4()
    await db_session.execute(insert_sql, {"id": id_a, "tenant_id": tenant_a, "vencimiento": vencimiento})
    await db_session.execute(insert_sql, {"id": id_b, "tenant_id": tenant_b, "vencimiento": vencimiento})

    count_sql = text("SELECT count(*) FROM derechos_arco_solicitudes")

    # 1. Sin tenant fijado -> 0
    await _as_app_role(db_session, None)
    c_none = (await db_session.execute(count_sql)).scalar_one()
    assert c_none == 0

    # 2. Con tenant_a fijado -> ve solo 1 (el suyo)
    await _as_app_role(db_session, tenant_a)
    c_a = (await db_session.execute(count_sql)).scalar_one()
    assert c_a == 1
    row_a = (await db_session.execute(text("SELECT id FROM derechos_arco_solicitudes"))).scalar_one()
    assert row_a == id_a

    # 3. Con tenant_b fijado -> ve solo 1 (el suyo)
    await _as_app_role(db_session, tenant_b)
    c_b = (await db_session.execute(count_sql)).scalar_one()
    assert c_b == 1
    row_b = (await db_session.execute(text("SELECT id FROM derechos_arco_solicitudes"))).scalar_one()
    assert row_b == id_b

    await db_session.rollback()
