# ¤seguridad-tenant ¤arbitro
# ¤¤qa-engineer
"""SEC-20 · La huella de producción también cubre Cloud SQL.

- `apunta_a_produccion(url)` es pura: reconoce la instancia de producción en la URL o en una variable del
  conector, sin abrir conexiones.
- `base_es_produccion(conexion)`: marcador invertido `public.entorno_marcador`; sin él, con un valor raro,
  con otro dueño, con `evydentia_prod` o con un error, la base cuenta como producción.

Solo nombres de instancia simulados y la PostgreSQL local o del CI (TEST_DATABASE_URL). Nunca Cloud SQL.

Mutaciones documentadas (ficha SEC-20):
- M1: quitar `nombra_instancia_de_produccion` de `apunta_a_produccion` hace fallar la prueba 1.
- M2: devolver «no producción» cuando el catálogo no halla `public.entorno_marcador` hace fallar la 2.
- M3: no capturar el error de la consulta hace fallar la 3.
- M4: consultar `entorno_marcador` sin esquema hace fallar la 7.
- M5: quitar la señal de `evydentia_prod` hace fallar la 8.
- M6: no decodificar la URL hace fallar la 1 en sus formas codificadas.
"""
import os
import socket
import threading
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from app_core import huellas_produccion as huellas
from app_core.huellas_produccion import (
    HUELLA_HOST_PRODUCCION, INSTANCIA_CLOUD_SQL_PRODUCCION, VARIABLES_DEL_CONECTOR, apunta_a_produccion,
    base_es_produccion,
)

INSTANCIA = INSTANCIA_CLOUD_SQL_PRODUCCION
OTRA_INSTANCIA = "evydentia-pruebas:us-central1:evydentia-pruebas"


# ----------------------------------------------------------------------------- 1. URL, sin conexiones

@pytest.fixture
def sin_red(monkeypatch):
    def prohibido(*_a, **_k):
        raise AssertionError("apunta_a_produccion abrió una conexión")
    monkeypatch.setattr(socket.socket, "connect", prohibido)
    monkeypatch.setattr(socket, "create_connection", prohibido)
    for nombre in VARIABLES_DEL_CONECTOR:
        monkeypatch.delenv(nombre, raising=False)


@pytest.mark.parametrize("url", [
    f"postgresql+psycopg://lopdp_app:clave-ficticia@/evydentia?host=/cloudsql/{INSTANCIA}",
    f"postgresql://lopdp_app@/evydentia?unix_sock=/cloudsql/{INSTANCIA}/.s.PGSQL.5432",
    "postgresql://lopdp_app@/evydentia?host=%2Fcloudsql%2F" + INSTANCIA.replace(":", "%3A"),
    "postgresql://lopdp_app@/evydentia?host=%252Fcloudsql%252F" + INSTANCIA.replace(":", "%253A"),
    f"postgresql://lopdp_app@/evydentia?host=/cloudsql/{INSTANCIA.upper()}",
    f"postgresql://lopdp_app@/evydentia?options=-c%20x%3D1&host=/CloudSQL/{INSTANCIA.title()}",
])
def test_1_url_con_la_instancia_de_produccion(sin_red, url):
    assert apunta_a_produccion(url)


@pytest.mark.parametrize("variable", VARIABLES_DEL_CONECTOR)
@pytest.mark.parametrize("valor", [INSTANCIA, INSTANCIA.upper(), INSTANCIA.replace(":", "%3A")])
def test_1_cada_variable_del_conector(sin_red, variable, valor):
    assert apunta_a_produccion("postgresql://lopdp_app@127.0.0.1:5432/lopdp", {variable: valor})


def test_1_control_otra_instancia_y_local_no_son_produccion(sin_red):
    assert not apunta_a_produccion(f"postgresql://lopdp_app@/db?host=/cloudsql/{OTRA_INSTANCIA}", {})
    assert not apunta_a_produccion("postgresql://lopdp_app@127.0.0.1:5432/lopdp", {})
    assert not apunta_a_produccion("postgresql://lopdp_app@127.0.0.1:5432/lopdp",
                                   {"CLOUD_SQL_INSTANCE": OTRA_INSTANCIA})
    assert apunta_a_produccion(f"postgresql://u@{HUELLA_HOST_PRODUCCION}.neon.invalid/db", {})


def test_1_la_variable_del_despliegue_esta_en_la_lista():
    from pathlib import Path
    flujo = (Path(__file__).resolve().parent.parent / ".github" / "workflows" / "deploy-gcp.yml").read_text(encoding="utf-8")
    nombrada = [n for n in VARIABLES_DEL_CONECTOR if f"{n}: {INSTANCIA}" in flujo]
    assert nombrada, "deploy-gcp.yml nombra la instancia con una variable fuera de la lista cerrada"


# ----------------------------------------------------------------------------- base real

def _url() -> str:
    url = os.environ.get("TEST_DATABASE_URL", "")
    if not url:
        pytest.skip("SEC-20 sin acreditar: falta TEST_DATABASE_URL (PostgreSQL 16 local o del CI)")
    if apunta_a_produccion(url):
        pytest.fail("TEST_DATABASE_URL apunta a producción; no se abrió conexión", pytrace=False)
    return make_url(url).set(drivername="postgresql+psycopg").render_as_string(hide_password=False)


@pytest.fixture
def conexion():
    motor = create_engine(_url(), connect_args={"connect_timeout": 5})
    with motor.connect() as con:
        transaccion = con.begin()
        try:
            con.execute(text("DROP TABLE IF EXISTS public.entorno_marcador"))
            yield con
        finally:
            transaccion.rollback()
    motor.dispose()


def _marcador(con, *valores):
    con.execute(text("CREATE TABLE public.entorno_marcador(valor text)"))
    for valor in valores:
        con.execute(text("INSERT INTO public.entorno_marcador(valor) VALUES (:v)"), {"v": valor})


def _sigue_usable(con):
    assert con.execute(text("SELECT 1")).scalar() == 1


def test_2_sin_marcador_es_produccion(conexion):
    assert base_es_produccion(conexion)
    _sigue_usable(conexion)


def test_3_si_la_consulta_falla_es_produccion_y_la_transaccion_sigue(conexion, monkeypatch):
    _marcador(conexion, "pruebas")
    monkeypatch.setattr(huellas, "_SQL_MARCADOR_FILAS", "SELECT valor FROM public.tabla_que_no_existe")
    assert base_es_produccion(conexion)
    _sigue_usable(conexion)
    assert conexion.execute(text("SELECT count(*) FROM public.entorno_marcador")).scalar() == 1


def test_3_tiempo_agotado_es_produccion_y_no_cambia_el_ajuste_del_llamador():
    """Base propia con el marcador confirmado y bloqueado por otra sesión: la consulta agota los 2 s."""
    administracion = create_engine(_url(), isolation_level="AUTOCOMMIT")
    nombre = "sec20_" + uuid4().hex[:10]
    with administracion.connect() as con:
        con.execute(text("SELECT 1"))
        con.exec_driver_sql(f'CREATE DATABASE "{nombre}"')  # nombre generado aquí, sin datos externos
    base = make_url(_url()).set(database=nombre).render_as_string(hide_password=False)
    motor = create_engine(base)
    try:
        with motor.begin() as con:
            _marcador(con, "pruebas")
        listo, soltar = threading.Event(), threading.Event()

        def bloquear():
            with motor.connect() as otra, otra.begin():
                otra.execute(text("LOCK TABLE public.entorno_marcador IN ACCESS EXCLUSIVE MODE"))
                listo.set()
                soltar.wait(10)
        hilo = threading.Thread(target=bloquear)
        hilo.start()
        try:
            assert listo.wait(10)
            with motor.connect() as con, con.begin():
                antes = con.execute(text("SHOW statement_timeout")).scalar()
                assert base_es_produccion(con)
                _sigue_usable(con)
                assert con.execute(text("SHOW statement_timeout")).scalar() == antes
        finally:
            soltar.set()
            hilo.join(15)
        with motor.connect() as con:
            assert not base_es_produccion(con), "control: sin bloqueo, el marcador es válido"
    finally:
        motor.dispose()
        with administracion.connect() as con:
            con.exec_driver_sql(f'DROP DATABASE IF EXISTS "{nombre}" WITH (FORCE)')
        administracion.dispose()


def test_4_marcador_valido_no_es_produccion(conexion):
    _marcador(conexion, "pruebas")
    assert not base_es_produccion(conexion)
    conexion.execute(text("UPDATE public.entorno_marcador SET valor='demo'"))
    assert not base_es_produccion(conexion)


@pytest.mark.parametrize("valor", ["produccion", "PRUEBAS", " pruebas", ""])
def test_5_marcador_con_otro_valor_es_produccion(conexion, valor):
    _marcador(conexion, valor)
    assert base_es_produccion(conexion)


def test_7_una_tabla_temporal_no_sombrea_el_marcador(conexion):
    conexion.execute(text("CREATE TEMP TABLE entorno_marcador(valor text)"))
    conexion.execute(text("INSERT INTO pg_temp.entorno_marcador VALUES ('pruebas')"))
    assert base_es_produccion(conexion), "solo la temporal: no hay marcador en public"
    _marcador(conexion, "otro")
    assert base_es_produccion(conexion), "la temporal 'pruebas' no debe tapar el marcador real 'otro'"


def test_8_con_el_nombre_de_la_base_de_produccion_es_produccion(conexion):
    _marcador(conexion, "pruebas")
    assert not base_es_produccion(conexion)
    assert base_es_produccion(conexion, nombre_base="evydentia_prod")
    assert base_es_produccion(conexion, nombre_base="EVYDENTIA_PROD")


@pytest.mark.parametrize("valores", [(), ("pruebas", "pruebas"), ("pruebas", "demo"), (None,)])
def test_9_cero_dos_filas_o_null_es_produccion(conexion, valores):
    _marcador(conexion, *valores)
    assert base_es_produccion(conexion)


def test_10_marcador_de_un_rol_que_no_es_el_dueno_es_produccion(conexion):
    rol = "sec20_" + uuid4().hex[:10]
    conexion.execute(text("SELECT set_config('sec20.rol', :r, true)"), {"r": rol})
    conexion.execute(text("""
        DO $$ BEGIN
            EXECUTE format('CREATE ROLE %I NOLOGIN NOSUPERUSER NOBYPASSRLS', current_setting('sec20.rol'));
            EXECUTE format('GRANT CREATE, USAGE ON SCHEMA public TO %I', current_setting('sec20.rol'));
        END $$"""))
    conexion.execute(text("SELECT set_config('role', :r, true)"), {"r": rol})
    _marcador(conexion, "pruebas")
    conexion.execute(text("RESET ROLE"))
    assert base_es_produccion(conexion)


def test_10_vista_con_el_mismo_nombre_es_produccion(conexion):
    conexion.execute(text("CREATE VIEW public.entorno_marcador AS SELECT 'pruebas'::text AS valor"))
    assert base_es_produccion(conexion)


def test_11_lopdp_app_no_puede_crear_en_public(conexion):
    assert conexion.execute(text("SELECT has_schema_privilege('lopdp_app', 'public', 'CREATE')")).scalar() is False
