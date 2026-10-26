# ¤seguridad-tenant
# ¤rbac-tenant
"""Árbitro del criterio 11 del MVP (QA-04): RLS en todas las tablas con datos de organización.

El inventario sale del catálogo de PostgreSQL, sin lista fija de tablas:

- Regla de inventario: toda tabla de ``public`` con columna ``tenant_id`` tiene RLS habilitado
  y forzado, salvo las de ``EXENCIONES``, cada una con su motivo. Una tabla nueva con
  ``tenant_id`` y sin RLS hace fallar la prueba; una exención que ya no hace falta, también.
- Regla de comportamiento: con el rol de la aplicación (``lopdp_app``), sin tenant fijado no se
  ve ninguna fila, y con un tenant fijado no se ve ninguna fila de otro. Para que no se cumpla
  en vacío, se siembran filas de dos organizaciones en las tablas de ``SIEMBRAS``.
- ``lopdp_app`` no tiene ``BYPASSRLS`` ni es superusuario.

Todo ocurre en una transacción que se revierte al terminar.
"""
from __future__ import annotations

import os
import uuid

import pytest
from sqlalchemy import String, cast, column, create_engine, func, select, table, text

EXENCIONES = {
    "invitaciones_organizacion": "Sala plataforma (ORG-09): el operador la consulta para todas las organizaciones y nunca fija tenant.",
    "auditoria_plataforma": "Sala plataforma (ORG-09): bitácora del operador, transversal a las organizaciones; nunca fija tenant.",
}

# Tablas en las que la prueba siembra una fila por organización (inserción mínima, sin FK
# a otras tablas de datos). El resto se evalúa sobre las filas que ya tenga la base.
SIEMBRAS = {
    "areas": "INSERT INTO areas (id, tenant_id, nombre, codigo) VALUES (:id, :t, 'Área QA-04', :id)",
    "tareas_mitigacion": (
        "INSERT INTO tareas_mitigacion (id, tenant_id, id_diagnostico, descripcion, impacto_riesgo) "
        "VALUES (:id, :t, 'qa-04', 'Tarea QA-04', 'ALTO')"
    ),
    "registro_auditoria": (
        "INSERT INTO registro_auditoria (id, tenant_id, id_diagnostico, snapshot_hash) "
        "VALUES (:id, :t, 'qa-04', 'hash-qa-04')"
    ),
}


@pytest.fixture
def conn():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL no configurada")
    engine = create_engine(url.replace("postgresql://", "postgresql+psycopg://", 1))
    with engine.connect() as c:
        tx = c.begin()
        try:
            yield c
        finally:
            tx.rollback()
    engine.dispose()


def _contar(tabla: str, distinto_de: str | None = None, igual_a: str | None = None):
    """count(*) de una tabla del catálogo, con el identificador entrecomillado por SQLAlchemy."""
    t = table(tabla, column("tenant_id"))
    tenant = cast(t.c.tenant_id, String)  # algunas tablas lo tienen como uuid, como las políticas: ::text
    consulta = select(func.count()).select_from(t)
    if distinto_de is not None:
        consulta = consulta.where(tenant != distinto_de)
    if igual_a is not None:
        consulta = consulta.where(tenant == igual_a)
    return consulta


def _tablas_con_tenant(conn) -> set[str]:
    return set(conn.execute(text(
        "SELECT c.table_name FROM information_schema.columns c "
        "JOIN information_schema.tables t ON t.table_schema = c.table_schema AND t.table_name = c.table_name "
        "WHERE c.table_schema = 'public' AND c.column_name = 'tenant_id' AND t.table_type = 'BASE TABLE'"
    )).scalars())


def _tablas_con_rls_forzado(conn) -> set[str]:
    return set(conn.execute(text(
        "SELECT relname FROM pg_class WHERE relkind = 'r' AND relnamespace = 'public'::regnamespace "
        "AND relrowsecurity AND relforcerowsecurity"
    )).scalars())


def test_toda_tabla_con_tenant_tiene_rls_forzado_salvo_exenciones(conn):
    sin_rls = sorted(_tablas_con_tenant(conn) - _tablas_con_rls_forzado(conn) - EXENCIONES.keys())
    assert not sin_rls, f"Tablas con tenant_id y sin RLS forzado (añada RLS o una exención con motivo): {sin_rls}"


def test_las_exenciones_siguen_haciendo_falta(conn):
    con_tenant = _tablas_con_tenant(conn)
    forzadas = _tablas_con_rls_forzado(conn)
    for tabla, motivo in EXENCIONES.items():
        assert motivo.strip(), tabla
        assert tabla in con_tenant, f"{tabla} ya no existe o no tiene tenant_id: retire la exención"
        assert tabla not in forzadas, f"{tabla} ya tiene RLS forzado: retire la exención"


def test_rol_de_la_aplicacion_sin_bypassrls(conn):
    fila = conn.execute(text("SELECT rolbypassrls, rolsuper FROM pg_roles WHERE rolname = 'lopdp_app'")).first()
    assert fila is not None, "No existe el rol lopdp_app"
    assert fila.rolbypassrls is False and fila.rolsuper is False


def test_con_el_rol_de_la_aplicacion_no_se_ve_otra_organizacion(conn):
    tenants = [f"t-qa04-{uuid.uuid4().hex[:8]}" for _ in range(2)]
    for t in tenants:
        conn.execute(
            text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) VALUES (:t, :t, :t, :ruc)"),
            {"t": t, "ruc": f"RUC{uuid.uuid4().hex[:12]}"},
        )
        for sql in SIEMBRAS.values():
            conn.execute(text(sql), {"id": f"qa04-{uuid.uuid4().hex[:12]}", "t": t})

    forzadas = sorted(_tablas_con_rls_forzado(conn) & _tablas_con_tenant(conn))
    assert set(SIEMBRAS) <= set(forzadas), f"Tablas sembradas sin RLS forzado: {sorted(set(SIEMBRAS) - set(forzadas))}"

    conn.execute(text("SET LOCAL ROLE lopdp_app"))
    conn.execute(text("SELECT set_config('app.current_tenant_id', '', true)"))
    visibles_sin_tenant = {tabla: conn.execute(_contar(tabla)).scalar() for tabla in forzadas}
    assert all(n == 0 for n in visibles_sin_tenant.values()), f"Filas visibles sin tenant: {visibles_sin_tenant}"

    propio, ajeno = tenants
    conn.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": propio})
    ajenas = {tabla: conn.execute(_contar(tabla, distinto_de=propio)).scalar() for tabla in forzadas}
    assert all(n == 0 for n in ajenas.values()), f"Filas de otra organización visibles: {ajenas}"
    for tabla in SIEMBRAS:
        propias = conn.execute(_contar(tabla, igual_a=propio)).scalar()
        assert propias == 1, f"{tabla}: el tenant propio debe ver su fila sembrada (vio {propias})"
