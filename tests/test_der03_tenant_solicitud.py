"""DER-03 · La solicitud ARCO queda en su organización: tenant recibido, sin uuid4 ni commit propio.

`¤seguridad-tenant` `¤rbac-tenant`

Contra la PostgreSQL de pruebas migrada (TEST_DATABASE_URL), con RLS y el rol lopdp_app.
"""
import importlib.util
import uuid
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from features.derechos_arco import derechos_arco_service as compuerta

pytestmark = pytest.mark.asyncio

RAIZ = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "der03_migracion", RAIZ / "alembic/versions/20261108_derechos_tenant_texto.py"
)
migracion = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(migracion)

DATOS = {"tipo_solicitud": "RECTIFICACION", "cedula_solicitante": "1700000001", "nombre_solicitante": "Titular Simulado"}


async def _tenant(session) -> str:
    tid = f"t-der03-{uuid.uuid4().hex[:10]}"
    await session.execute(
        text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) VALUES (:t, :t, :t, :ruc)"),
        {"t": tid, "ruc": f"RUC{uuid.uuid4().hex[:12]}"},
    )
    return tid


async def _como_app(session, tenant: str) -> None:
    if not (await session.execute(text("SELECT 1 FROM pg_roles WHERE rolname = 'lopdp_app'"))).first():
        pytest.skip("Rol lopdp_app no existe")
    await session.execute(text("SET LOCAL ROLE lopdp_app"))
    await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": tenant})


async def test_01_queda_con_el_tenant_recibido_y_se_lee_en_ese_tenant(db_session):
    propio = await _tenant(db_session)
    await _como_app(db_session, propio)
    creada = await compuerta.crear_solicitud_arco(db_session, DATOS, tenant_id=propio)
    assert creada.tenant_id == propio and creada.id is not None
    visibles = await compuerta.listar_solicitudes_arco(db_session)
    assert [s.id for s in visibles] == [creada.id]
    assert visibles[0].tenant_id == propio
    await db_session.rollback()


async def test_01b_sin_tenant_explicito_usa_el_de_la_sesion(db_session):
    propio = await _tenant(db_session)
    await _como_app(db_session, propio)
    creada = await compuerta.crear_solicitud_arco(db_session, DATOS)
    assert creada.tenant_id == propio
    await db_session.rollback()


async def test_01c_sin_tenant_alguno_no_crea(db_session):
    await db_session.execute(text("SELECT set_config('app.current_tenant_id', '', true)"))
    with pytest.raises(compuerta.TenantNoDisponible):
        await compuerta.crear_solicitud_arco(db_session, DATOS)
    await db_session.rollback()


async def test_02_desde_otro_tenant_no_se_ve(db_session):
    propio, ajeno = await _tenant(db_session), await _tenant(db_session)
    await _como_app(db_session, propio)
    creada = await compuerta.crear_solicitud_arco(db_session, DATOS, tenant_id=propio)
    await db_session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": ajeno})
    assert await compuerta.listar_solicitudes_arco(db_session) == []
    # Tampoco se puede escribir en otra organización (WITH CHECK).
    with pytest.raises(DBAPIError):
        await compuerta.crear_solicitud_arco(db_session, DATOS, tenant_id=propio)
    assert creada.tenant_id == propio
    await db_session.rollback()


async def test_03_no_hace_commit_el_rollback_de_quien_llama_la_deja_sin_fila(db_session):
    propio = await _tenant(db_session)
    await _como_app(db_session, propio)
    creada = await compuerta.crear_solicitud_arco(db_session, DATOS, tenant_id=propio)
    ident = creada.id
    await db_session.rollback()
    fila = (await db_session.execute(
        text("SELECT 1 FROM derechos_arco_solicitudes WHERE id = :i"), {"i": ident}
    )).first()
    assert fila is None


async def test_04_migracion_aborta_con_huerfanos_y_no_toca_la_tabla(db_session):
    """Con un huérfano sembrado, la comprobación previa falla con el número y la tabla sigue igual.

    Se usa una tabla temporal con el esquema anterior (tenant_id uuid), que en esta sesión tapa a la real.
    """
    await db_session.execute(text(
        "CREATE TEMP TABLE derechos_arco_solicitudes (id uuid PRIMARY KEY, tenant_id uuid NOT NULL) ON COMMIT DROP"
    ))
    huerfano = uuid.uuid4()
    await db_session.execute(text("INSERT INTO pg_temp.derechos_arco_solicitudes VALUES (:i, :t)"),
                             {"i": uuid.uuid4(), "t": huerfano})
    await db_session.execute(text("SAVEPOINT antes"))
    with pytest.raises(DBAPIError) as error:
        await db_session.execute(text(migracion.SQL_HUERFANOS))
    assert "1 solicitud(es) ARCO" in str(error.value) and "no borra ni reasigna" in str(error.value)
    await db_session.execute(text("ROLLBACK TO SAVEPOINT antes"))
    filas = (await db_session.execute(text("SELECT tenant_id FROM pg_temp.derechos_arco_solicitudes"))).scalars().all()
    assert filas == [huerfano]
    columnas = (await db_session.execute(text(
        "SELECT column_name FROM information_schema.columns WHERE table_name = 'derechos_arco_solicitudes' "
        "AND table_schema LIKE 'pg_temp%'"
    ))).scalars().all()
    assert sorted(columnas) == ["id", "tenant_id"]
    await db_session.rollback()


async def test_05_migracion_es_compatible_expand_contract():
    import sys
    sys.path.insert(0, str(RAIZ / "scripts"))
    import verificar_migracion_compatible as vmc

    codigo = (RAIZ / "alembic/versions/20261108_derechos_tenant_texto.py").read_text(encoding="utf-8")
    assert vmc.verificar(codigo) == []
    assert "NOT VALID" in codigo and "VALIDATE CONSTRAINT" in codigo


# DER-04 retiró test_06a y test_06b: probaban la ventana de reversión de DER-03 (el disparador que llenaba
# tenant_id uuid y la guardia del downgrade), y la contracción de DER-04 (20261109_der04_contraccion)
# retira esa columna y ese disparador. Su sustituto es tests/test_der04_contraccion.py.
