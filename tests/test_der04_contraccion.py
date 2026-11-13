"""DER-04 · Contracción de DER-03: se retiran tenant_id uuid y el disparador de las solicitudes ARCO.

`¤arbitro` `¤seguridad-tenant`

Contra la PostgreSQL 16 local del arnés (TEST_DATABASE_URL); nunca producción ni Cloud SQL. Las pruebas que
ejecutan la migración lo hacen sobre una réplica de la tabla en un esquema temporal (search_path), para no
contraer la base que comparten las demás pruebas. Datos simulados.

Mutaciones documentadas (cada una deja en rojo la prueba indicada):
- M1: quitar `CONTRACCION = True` de la migración → test_06.
- M2: mover op.execute(SQL_GUARDIA) después de los DROP en upgrade() → test_01 (la columna y el disparador desaparecen).
- M3: incluir la cédula o el nombre en el RAISE de la guardia → test_02.
- M4: quitar el conteo de políticas desconocidas de la guardia o usar DROP COLUMN … CASCADE → test_03b
  (la política desconocida desaparece en vez de abortar).
- M5: no retirar la política vieja de 001 por nombre → test_03a (el DROP COLUMN falla por dependencia).
- M6: quitar `raise` de downgrade() → test_05.
- M7: añadir `trg_derechos_arco_tenant_texto` o `text("... WHERE tenant_id = :t")` sobre la tabla en features/ → test_07.
"""
import ast
import importlib.util
import os
import re
import subprocess
import uuid
from pathlib import Path

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

RAIZ = Path(__file__).resolve().parents[1]
RUTA = RAIZ / "alembic/versions/20261109_derechos_contraccion_tenant.py"
_spec = importlib.util.spec_from_file_location("der04_migracion", RUTA)
migracion = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(migracion)

CEDULA, NOMBRE = "1799999990", "Titular Simulado Cuatro"


def _motor():
    url = os.environ.get("TEST_DATABASE_URL", "")
    if not url:
        pytest.skip("TEST_DATABASE_URL no definida (PostgreSQL 16 local del arnés)")
    url = url.replace("postgresql+asyncpg://", "postgresql://").replace("postgresql://", "postgresql+psycopg://", 1)
    return create_engine(url)


@pytest.fixture
def replica():
    """Esquema temporal con la tabla en el estado que deja DER-03."""
    motor = _motor()
    esquema = f"der04_{uuid.uuid4().hex[:10]}"
    with motor.begin() as c:
        c.execute(text(f"CREATE SCHEMA {esquema}"))
        c.execute(text(f"SET LOCAL search_path = {esquema}"))
        c.execute(text("CREATE TABLE tenants (id VARCHAR PRIMARY KEY)"))
        c.execute(text("INSERT INTO tenants VALUES ('t-a'), ('t-b')"))
        c.execute(text(
            "CREATE TABLE derechos_arco_solicitudes (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), "
            "tenant_id UUID NULL, tenant_id_texto VARCHAR NULL, cedula_solicitante VARCHAR(20) NOT NULL, "
            "nombre_solicitante VARCHAR(200) NOT NULL)"
        ))
        c.execute(text("CREATE INDEX ix_derechos_arco_solicitudes_tenant_id ON derechos_arco_solicitudes(tenant_id)"))
        c.execute(text("CREATE INDEX ix_derechos_arco_solicitudes_tenant_id_texto ON derechos_arco_solicitudes(tenant_id_texto)"))
        c.execute(text(
            "ALTER TABLE derechos_arco_solicitudes ADD CONSTRAINT fk_derechos_arco_solicitudes_tenant "
            "FOREIGN KEY (tenant_id_texto) REFERENCES tenants(id) NOT VALID"
        ))
        c.execute(text(
            "CREATE FUNCTION derechos_arco_tenant_texto() RETURNS trigger AS $$ BEGIN "
            "IF NEW.tenant_id_texto IS NULL AND NEW.tenant_id IS NOT NULL THEN NEW.tenant_id_texto := NEW.tenant_id::text; END IF; "
            "RETURN NEW; END $$ LANGUAGE plpgsql"
        ))
        c.execute(text(
            "CREATE TRIGGER trg_derechos_arco_tenant_texto BEFORE INSERT OR UPDATE ON derechos_arco_solicitudes "
            "FOR EACH ROW EXECUTE FUNCTION derechos_arco_tenant_texto()"
        ))
        c.execute(text(
            "CREATE POLICY tenant_isolation_derechos_arco_solicitudes ON derechos_arco_solicitudes "
            "USING (tenant_id_texto = current_setting('app.current_tenant_id', true)) "
            "WITH CHECK (tenant_id_texto = current_setting('app.current_tenant_id', true))"
        ))
        c.execute(text("ALTER TABLE derechos_arco_solicitudes ENABLE ROW LEVEL SECURITY"))
        c.execute(text("ALTER TABLE derechos_arco_solicitudes FORCE ROW LEVEL SECURITY"))
    try:
        yield motor, esquema
    finally:
        with motor.begin() as c:
            c.execute(text(f"DROP SCHEMA {esquema} CASCADE"))
        motor.dispose()


def _sql(motor, esquema, sql, **p):
    with motor.begin() as c:
        c.execute(text(f"SET LOCAL search_path = {esquema}"))
        c.execute(text("SET LOCAL row_security = off"))
        return c.execute(text(sql), p).fetchall() if sql.lstrip().upper().startswith("SELECT") else c.execute(text(sql), p)


def _insertar(motor, esquema, tenant):
    _sql(motor, esquema,
         "INSERT INTO derechos_arco_solicitudes (tenant_id_texto, cedula_solicitante, nombre_solicitante) VALUES (:t, :c, :n)",
         t=tenant, c=CEDULA, n=NOMBRE)


def _migrar(motor, esquema):
    with motor.begin() as c:
        c.execute(text(f"SET LOCAL search_path = {esquema}"))
        with Operations.context(MigrationContext.configure(c)):
            migracion.upgrade()


def _estado(motor, esquema):
    columnas = {r[0]: r[1] for r in _sql(motor, esquema,
        "SELECT column_name, is_nullable FROM information_schema.columns "
        "WHERE table_schema = :e AND table_name = 'derechos_arco_solicitudes'", e=esquema)}
    disparadores = {r[0] for r in _sql(motor, esquema,
        "SELECT tgname FROM pg_trigger WHERE NOT tgisinternal AND tgrelid = 'derechos_arco_solicitudes'::regclass")}
    politicas = {r[0] for r in _sql(motor, esquema,
        "SELECT policyname FROM pg_policies WHERE schemaname = :e AND tablename = 'derechos_arco_solicitudes'", e=esquema)}
    indices = {r[0] for r in _sql(motor, esquema,
        "SELECT indexname FROM pg_indexes WHERE schemaname = :e AND tablename = 'derechos_arco_solicitudes'", e=esquema)}
    fk = _sql(motor, esquema,
        "SELECT convalidated FROM pg_constraint WHERE conname = 'fk_derechos_arco_solicitudes_tenant' "
        "AND conrelid = 'derechos_arco_solicitudes'::regclass")
    return columnas, disparadores, politicas, indices, fk


def _abortar(motor, esquema) -> str:
    with pytest.raises(DBAPIError) as err:
        _migrar(motor, esquema)
    return str(err.value.orig)


def test_01_con_tenant_nulo_aborta_y_no_cambia_nada(replica):
    motor, esquema = replica
    _insertar(motor, esquema, "t-a")
    _insertar(motor, esquema, None)
    antes = _estado(motor, esquema)
    assert "1 solicitud(es)" in _abortar(motor, esquema)
    assert _estado(motor, esquema) == antes
    assert "tenant_id" in antes[0] and "trg_derechos_arco_tenant_texto" in antes[1]


def test_01b_tenant_sin_fila_en_tenants_tambien_aborta(replica):
    motor, esquema = replica
    with motor.begin() as c:
        c.execute(text(f"SET LOCAL search_path = {esquema}"))
        c.execute(text("ALTER TABLE derechos_arco_solicitudes DROP CONSTRAINT fk_derechos_arco_solicitudes_tenant"))
    _insertar(motor, esquema, "t-inexistente")
    assert "1 solicitud(es)" in _abortar(motor, esquema)
    assert "tenant_id" in _estado(motor, esquema)[0]


def test_02_el_aborto_no_contiene_datos_de_la_fila(replica):
    motor, esquema = replica
    _insertar(motor, esquema, None)
    mensaje = _abortar(motor, esquema)
    assert CEDULA not in mensaje and NOMBRE not in mensaje and "Titular" not in mensaje


def test_03_sin_huerfanos_retira_columna_y_disparador(replica):
    motor, esquema = replica
    _insertar(motor, esquema, "t-a")
    _sql(motor, esquema, "ALTER TABLE derechos_arco_solicitudes VALIDATE CONSTRAINT fk_derechos_arco_solicitudes_tenant")
    _migrar(motor, esquema)
    columnas, disparadores, politicas, indices, fk = _estado(motor, esquema)
    assert "tenant_id" not in columnas and columnas["tenant_id_texto"] == "NO"
    assert disparadores == set()
    assert not _sql(motor, esquema, "SELECT 1 FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace "
                    "WHERE p.proname = 'derechos_arco_tenant_texto' AND n.nspname = :e", e=esquema)
    assert "ix_derechos_arco_solicitudes_tenant_id" not in indices
    assert "ix_derechos_arco_solicitudes_tenant_id_texto" in indices
    assert fk == [(True,)]
    assert politicas == {"tenant_isolation_derechos_arco_solicitudes"}
    assert _sql(motor, esquema, "SELECT count(*) FROM derechos_arco_solicitudes") == [(1,)]


def test_03a_retira_la_politica_vieja_de_001_y_deja_la_vigente(replica):
    motor, esquema = replica
    _sql(motor, esquema, "CREATE POLICY tenant_isolation_policy ON derechos_arco_solicitudes "
                         "USING (tenant_id = current_setting('app.current_tenant_id')::uuid)")
    _migrar(motor, esquema)
    assert _estado(motor, esquema)[2] == {"tenant_isolation_derechos_arco_solicitudes"}


def test_03b_politica_desconocida_sobre_la_columna_vieja_aborta(replica):
    motor, esquema = replica
    _sql(motor, esquema, "CREATE POLICY politica_ajena ON derechos_arco_solicitudes USING (tenant_id IS NOT NULL)")
    assert "1 política(s)" in _abortar(motor, esquema)
    columnas, _, politicas, _, _ = _estado(motor, esquema)
    assert "tenant_id" in columnas and politicas == {"politica_ajena", "tenant_isolation_derechos_arco_solicitudes"}


def test_04_con_lopdp_app_un_tenant_no_ve_las_solicitudes_de_otro(replica):
    motor, esquema = replica
    with motor.connect() as c:
        if not c.execute(text("SELECT 1 FROM pg_roles WHERE rolname = 'lopdp_app'")).first():
            pytest.skip("Rol lopdp_app no existe")
    _migrar(motor, esquema)
    _sql(motor, esquema, f"GRANT USAGE ON SCHEMA {esquema} TO lopdp_app")
    _sql(motor, esquema, "GRANT SELECT, INSERT ON derechos_arco_solicitudes, tenants TO lopdp_app")
    with motor.begin() as c:
        c.execute(text(f"SET LOCAL search_path = {esquema}"))
        c.execute(text("SET LOCAL ROLE lopdp_app"))
        c.execute(text("SELECT set_config('app.current_tenant_id', 't-a', true)"))
        c.execute(text("INSERT INTO derechos_arco_solicitudes (tenant_id_texto, cedula_solicitante, nombre_solicitante) "
                       "VALUES ('t-a', :c, :n)"), {"c": CEDULA, "n": NOMBRE})
        assert c.execute(text("SELECT count(*) FROM derechos_arco_solicitudes")).scalar() == 1
        c.execute(text("SELECT set_config('app.current_tenant_id', 't-b', true)"))
        assert c.execute(text("SELECT count(*) FROM derechos_arco_solicitudes")).scalar() == 0
        with pytest.raises(DBAPIError):
            with c.begin_nested():
                c.execute(text("INSERT INTO derechos_arco_solicitudes (tenant_id_texto, cedula_solicitante, "
                               "nombre_solicitante) VALUES ('t-a', :c, :n)"), {"c": CEDULA, "n": NOMBRE})


def test_05_downgrade_lanza_contraccion_irreversible():
    with pytest.raises(RuntimeError, match="contracción irreversible"):
        migracion.downgrade()


def test_06_verificador_acepta_solo_con_contraccion():
    from scripts import verificar_migracion_compatible as v

    codigo = RUTA.read_text(encoding="utf-8")
    assert v.verificar(codigo) == []
    sin_marca = re.sub(r"^CONTRACCION = True$", "CONTRACCION = False", codigo, flags=re.MULTILINE)
    assert sin_marca != codigo
    assert v.verificar(sin_marca), "sin CONTRACCION el DROP debe ser incompatible"


_CARPETAS = ("features", "api", "app_core", "scripts", "frontend/src")
_VIEJA = re.compile(r"(?<![\w.'])tenant_id(?!_texto)\b")


def _cadenas_sql(ruta: Path) -> list[str]:
    """Literales de cadena del archivo, sin docstrings ni comentarios."""
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    docstrings = {id(n.value) for n in ast.walk(arbol) if isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)}
    return [n.value for n in ast.walk(arbol)
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docstrings]


def test_07_ningun_codigo_nombra_la_columna_vieja_ni_el_disparador():
    nombres = subprocess.run(
        ["git", "grep", "-n", "-E", r"trg_derechos_arco_tenant_texto|derechos_arco_tenant_texto\(", "--", *_CARPETAS],
        cwd=RAIZ, capture_output=True, text=True, encoding="utf-8",
    ).stdout.strip()
    assert nombres == "", nombres
    archivos = subprocess.run(["git", "grep", "-l", "derechos_arco_solicitudes", "--", *_CARPETAS],
                              cwd=RAIZ, capture_output=True, text=True, encoding="utf-8").stdout.split()
    usos = [f"{a}: {s.strip()[:80]}" for a in archivos if a.endswith(".py") for s in _cadenas_sql(RAIZ / a) if _VIEJA.search(s)
            and ("derechos_arco" in s or "SELECT" in s.upper() or "WHERE" in s.upper() or s == "tenant_id")]
    assert usos == [], usos
