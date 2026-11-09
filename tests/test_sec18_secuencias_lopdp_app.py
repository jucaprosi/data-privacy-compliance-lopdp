# ¤arbitro
# ¤¤qa-engineer
"""Árbitro SEC-18: lopdp_app inserta en columnas identity sin permiso sobre sus secuencias. ¤seguridad

PostgreSQL no comprueba permisos de secuencia al generar un valor identity en un INSERT; solo los
comprueba en nextval/currval/setval explícitos. Por mínimo privilegio, lopdp_app no recibe USAGE sobre
secuencias: el INSERT pasa en las tres tablas identity donde inserta y el nextval explícito falla.

Corre contra PostgreSQL 16 local (TEST_DATABASE_URL) con la base migrada. Datos sintéticos, correos
.invalid y rollback.

Mutaciones documentadas (2026-11-07, contenedor pgvector/pgvector:pg16):
1. Con `GRANT USAGE, SELECT ON SEQUENCE <secuencia> TO lopdp_app`, nextval deja de fallar y
   test_nextval_explicito_denegado falla.
2. Con `REVOKE INSERT ON <tabla> FROM lopdp_app`, test_insert_identity_pasa_en_las_tres_tablas falla
   con «permission denied for table».
"""
import os
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import create_async_engine

TABLAS_IDENTITY = {"biblioteca_importaciones", "biblioteca_verificaciones", "dpo_inscripciones"}
HASH = "a" * 64

# Secuencias de las tablas del esquema public en las que lopdp_app tiene INSERT.
SECUENCIAS = text("""
    SELECT DISTINCT t.relname, format('%I.%I', ns.nspname, s.relname)
    FROM information_schema.role_table_grants g
    JOIN pg_class t ON t.relname = g.table_name
    JOIN pg_namespace tn ON tn.oid = t.relnamespace AND tn.nspname = g.table_schema
    JOIN pg_depend d ON d.refobjid = t.oid AND d.classid = 'pg_class'::regclass
                    AND d.refclassid = 'pg_class'::regclass AND d.deptype IN ('a', 'i')
    JOIN pg_class s ON s.oid = d.objid AND s.relkind = 'S'
    JOIN pg_namespace ns ON ns.oid = s.relnamespace
    WHERE g.grantee = 'lopdp_app' AND g.privilege_type = 'INSERT' AND g.table_schema = 'public'
""")


@pytest_asyncio.fixture
async def conexion():
    url = os.environ.get("TEST_DATABASE_URL", "")
    if not url:
        pytest.skip("TEST_DATABASE_URL no configurada")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    engine = create_async_engine(url, hide_parameters=True)
    async with engine.connect() as con:
        transaccion = await con.begin()
        try:
            yield con
        finally:
            await transaccion.rollback()
    await engine.dispose()


async def _sembrar(con) -> dict:
    """Como el rol que migra: usuario editor, organización, acción y evidencia sintéticas."""
    m = {"u": "sec18-" + uuid4().hex, "t": str(uuid4()), "c": "SEC18-" + uuid4().hex[:8].upper(),
         "accion": str(uuid4()), "ev": str(uuid4())}
    hoja, ola = str(uuid4()), str(uuid4())
    await con.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), m)
    await con.execute(text("SELECT set_config('app.current_user_id', :u, true)"), m)
    await con.execute(text("INSERT INTO users(id,email,nombre) VALUES (:u, :e, 'SEC-18')"), {**m, "e": m["u"] + "@prueba.invalid"})
    await con.execute(text("WITH o AS (INSERT INTO users(id,email,nombre) SELECT 'otorgante-'||g, 'otorgante-'||g||'@correo.invalid', 'Otorgante sintético' FROM md5(random()::text) g RETURNING id) "
                           "INSERT INTO biblioteca_capacidades(usuario_id,capacidad,concedida_por,motivo) "
                           "SELECT :u,'editor',o.id,'Fixture sintética SEC-18' FROM o"), m)
    await con.execute(text("INSERT INTO biblioteca_catalogo(codigo) VALUES (:c)"), m)
    await con.execute(text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
                           "VALUES (:t, 'Org sintética', 'Org sintética S.A.', :ruc)"),
                      {**m, "ruc": str(uuid4().int)[:13]})
    await con.execute(text("INSERT INTO roadmaps(id, tenant_id, variables_json) VALUES (:h, :t, '{}')"),
                      {**m, "h": hoja})
    await con.execute(text("INSERT INTO roadmap_waves(id, roadmap_id, tenant_id, name) VALUES (:w, :h, :t, 'Ola')"),
                      {**m, "w": ola, "h": hoja})
    await con.execute(text("INSERT INTO roadmap_tasks(id, wave_id, tenant_id, control_ref, dimension, title, priority) "
                           "VALUES (:accion, :w, :t, 'P7', 'D01', 'Capacitar al personal', 'alta')"), {**m, "w": ola})
    await con.execute(text("INSERT INTO biblioteca_evidencias(id,tenant_id,accion_id,titulo,version,sha256,"
                           "clasificacion,permisos,fecha,creado_por) "
                           "VALUES (:ev,:t,:accion,'Evidencia','1',:h,'interna',ARRAY['dpo'],now(),:u)"),
                      {**m, "h": HASH})
    return m


# ¤seguridad
@pytest.mark.asyncio
async def test_las_tablas_identity_de_lopdp_app_son_las_esperadas(conexion):
    tablas = {fila[0] for fila in (await conexion.execute(SECUENCIAS)).all()}
    assert tablas == TABLAS_IDENTITY


# ¤seguridad
@pytest.mark.asyncio
async def test_insert_identity_pasa_en_las_tres_tablas(conexion):
    m = await _sembrar(conexion)
    await conexion.execute(text("SET LOCAL ROLE lopdp_app"))
    ids = [
        (await conexion.execute(text(
            "INSERT INTO biblioteca_importaciones(clave,codigo,apertura,ejecutada_por) "
            "VALUES ('sec18',:c,'sin_archivo',:u) RETURNING id"), m)).scalar_one(),
        (await conexion.execute(text(
            "INSERT INTO biblioteca_verificaciones(id,tenant_id,accion_id,evidencia_id,criterio,evidencia_legible,"
            "resultado,revisor,fecha) VALUES (:id,:t,:accion,:ev,'criterio largo',false,'no_conforme',:u,now()) "
            "RETURNING secuencia"), {**m, "id": str(uuid4())})).scalar_one(),
        (await conexion.execute(text(
            "INSERT INTO dpo_inscripciones(id,tenant_id,inscrito,registrado_por) "
            "VALUES (:id,:t,false,:u) RETURNING orden"), {**m, "id": str(uuid4())})).scalar_one(),
    ]
    assert all(isinstance(i, int) and i > 0 for i in ids)


# ¤seguridad
@pytest.mark.asyncio
async def test_nextval_explicito_denegado(conexion):
    secuencias = [fila[1] for fila in (await conexion.execute(SECUENCIAS)).all()]
    assert len(secuencias) == len(TABLAS_IDENTITY)
    await conexion.execute(text("SET LOCAL ROLE lopdp_app"))
    for secuencia in secuencias:
        with pytest.raises(DBAPIError, match="permission denied for sequence"):
            async with conexion.begin_nested():
                await conexion.execute(text("SELECT nextval(CAST(:s AS regclass))"), {"s": secuencia})
