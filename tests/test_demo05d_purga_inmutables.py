# -*- coding: utf-8 -*-
# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤demo ¤seguridad ¤arbitro
"""DEMO-05d: purga de la demo frente a los triggers de inmutabilidad de biblioteca y consultas al DPO.

Corren contra PostgreSQL 16 real (`TEST_DATABASE_URL`, el del arnés local o el servicio del CI) con todas
las migraciones (`alembic upgrade heads`) y `politicas_purga.sql`. Todo ocurre en UNA transacción que se
revierte, como en DEMO-05c: el rol `purga_demo`, el marcador, la función y los datos desaparecen al terminar.
Solo valores simulados y correos `.invalid`.

Mutaciones (governance/especificaciones/DEMO-05d.md §5), aplicadas una a una, con la suite corrida y el
archivo restaurado; el resultado de cada una está en el cuerpo del PR:
- m1 `politicas_purga.sql`: sin la comprobación del marcador -> falla `test_sin_marcador_demo_falla_cerrada`.
- m2 `politicas_purga.sql`: sin la exclusión de la plantilla -> falla `test_plantilla_y_no_demo_fallan`.
- m3 `politicas_purga.sql`: el DELETE de `biblioteca_eventos_documento` en un bloque que traga el error y sale
  antes del ENABLE (rehabilitar fuera de la transacción) -> falla
  `test_fallo_a_mitad_deja_los_triggers_encendidos`.
- m4 `politicas_purga.sql`: sin `REVOKE ALL ON FUNCTION purga_demo_borrar_inmutables ... FROM PUBLIC` -> falla
  `test_permisos_de_la_funcion`.
- m5 `guardias.py`: `falta_funcion_inmutables` sin comparar con `TRIGGERS_INMUTABLES` -> falla
  `test_guardia_nombra_el_trigger_nuevo`.
- m6 `politicas_purga.sql`: sin la condición de la sesión `activa` -> falla `test_demo_con_sesion_activa_falla`.
- m7 (adicional, R5) `politicas_purga.sql`: sin `set_config('app.current_tenant_id', ...)` -> falla
  `test_dueno_sin_bypassrls_borra_con_force_rls`: un dueño sin BYPASSRLS no ve las filas y no borra nada.
"""
from __future__ import annotations

import hashlib
import os
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy import String, cast, column, create_engine, func, select, table, text
from sqlalchemy.exc import DBAPIError

from features.demo.demo_service import PLANTILLA_TENANT_ID
from jobs.purga_demo import purga as modulo_purga
from jobs.purga_demo.__main__ import ejecutar
from jobs.purga_demo.guardias import TRIGGERS_INMUTABLES, falta_funcion_inmutables, faltan_politicas

RAIZ = Path(__file__).resolve().parent.parent
SQL_POLITICAS = (RAIZ / "jobs" / "purga_demo" / "politicas_purga.sql").read_text(encoding="utf-8")
AHORA = datetime.now(timezone.utc)
FUNCION = "public.purga_demo_borrar_inmutables"
FIRMA = "public.purga_demo_borrar_inmutables(character varying)"
#: SQL literal por rol (sin interpolar identificadores: tests/test_sin_sql_interpolado.py).
_SQL_CREAR_ROL = {
    "purga_demo": "CREATE ROLE purga_demo NOLOGIN",
    "lopdp_app": "CREATE ROLE lopdp_app NOLOGIN",
    "zz_d_dueno": "CREATE ROLE zz_d_dueno NOLOGIN",
}
#: Las cinco tablas y las tres que lee R1 pasan a un dueño sin BYPASSRLS (como en Cloud SQL).
_SQL_TRASPASAR_DUENO = (
    "DO $$ DECLARE t text; BEGIN "
    "FOREACH t IN ARRAY ARRAY['biblioteca_documentos_historial', 'biblioteca_descargas', "
    "'biblioteca_eventos_documento', 'dpo_consultas_mensajes', 'dpo_consultas', 'tenants', 'demo_sesiones', "
    "'entorno_marcador'] LOOP EXECUTE format('ALTER TABLE public.%I OWNER TO zz_d_dueno', t); END LOOP; END $$"
)
#: Las cinco tablas de §1 y el resto de tablas de la demo que la prueba siembra.
INMUTABLES = modulo_purga.TABLAS_INMUTABLES
SEMBRADAS = (*INMUTABLES, "biblioteca_documentos", "audit_events")


def _url() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL no configurada")
    return url.replace("postgresql://", "postgresql+psycopg://", 1)


class AlmacenVacio:
    def __init__(self) -> None:
        self.llamadas: list[str] = []

    def listar(self, prefijo: str) -> list[str]:
        self.llamadas.append(f"listar {prefijo}")
        return []

    def borrar(self, claves: list[str]) -> None:
        self.llamadas.append("borrar")


def ejecutar_sql(con, sql: str = SQL_POLITICAS) -> None:
    """El SQL tiene `%` y `$$`: va por el cursor del driver, sin parámetros, dentro de la misma transacción."""
    with con.connection.dbapi_connection.cursor() as cursor:
        cursor.execute(sql)


def asegurar_rol(con, rol: str) -> None:
    if not con.execute(text("SELECT 1 FROM pg_roles WHERE rolname = :r"), {"r": rol}).first():
        con.execute(text(_SQL_CREAR_ROL[rol]))


def poner_marcador(con, marcador: str | None) -> None:
    con.execute(text("DELETE FROM public.entorno_marcador"))
    if marcador is not None:
        con.execute(text("INSERT INTO public.entorno_marcador VALUES (:v)"), {"v": marcador})


@contextmanager
def como_purga(con):
    con.execute(text("SET ROLE purga_demo"))
    try:
        yield con
    finally:
        con.execute(text("RESET ROLE"))


def triggers_encendidos(con) -> dict[str, str]:
    """`tgenabled` de los cinco triggers de la lista cerrada."""
    filas = con.execute(text(
        "SELECT t.tgname, t.tgenabled FROM pg_trigger t WHERE t.tgname = ANY (:n) AND NOT t.tgisinternal"),
        {"n": [trigger for _, trigger in TRIGGERS_INMUTABLES]}).all()
    return {f.tgname: f.tgenabled for f in filas}


def llamar(con, tenant: str):
    """Llama a la función como `purga_demo` en un savepoint; devuelve el número o el SQLSTATE del error.

    `SET ROLE` es transaccional: si la llamada falla, el rollback del savepoint devuelve el rol de la prueba
    (un `RESET ROLE` en la transacción abortada taparía el error con 25P02)."""
    try:
        with con.begin_nested():
            con.execute(text("SET ROLE purga_demo"))
            resultado = con.execute(text(f"SELECT {FUNCION}(:t)"), {"t": tenant}).scalar_one()
            con.execute(text("RESET ROLE"))
            return resultado
    except DBAPIError as error:
        return getattr(error.orig, "sqlstate", None) or "error"


class Mundo:
    """Un tenant demo vencido, la plantilla, una demo con sesión activa y un tenant no demo, con filas en las
    cinco tablas inmutables (y en el resto) para cada uno."""

    def __init__(self, con) -> None:
        self.con = con
        self.s = uuid.uuid4().hex[:8]
        self.vencido = f"zz-d-vencido-{self.s}"
        self.activo = f"zz-d-activo-{self.s}"
        self.no_demo = f"zz-d-real-{self.s}"
        self.actor = f"zz-d-actor-{self.s}"
        self.version = str(uuid.uuid4())
        self.todos = (PLANTILLA_TENANT_ID, self.vencido, self.activo, self.no_demo)

    def tenant(self, tid: str, es_demo: bool) -> None:
        self.con.execute(text(
            "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, es_demo) "
            "VALUES (:i, :n, :n, :r, :d) ON CONFLICT (id) DO NOTHING"),
            {"i": tid, "n": f"Tenant {tid}", "r": f"{uuid.uuid4().int % 10**13:013d}", "d": es_demo})

    def sesion(self, tid: str, estado: str) -> None:
        fin = None if estado == "activa" else AHORA - timedelta(days=1)
        self.con.execute(text(
            "INSERT INTO demo_sesiones (id, vendedor_sub, vendedor_email, tenant_id, estado, iniciada_en, "
            "ultima_actividad, terminada_en, motivo_fin) VALUES (:i, :sub, :e, :t, :est, :ini, :ini, :fin, :m)"),
            {"i": f"zz-d-ses-{uuid.uuid4().hex[:12]}", "sub": f"sub-{self.s}",
             "e": f"vendedor-{self.s}@vendedores.invalid", "t": tid, "est": estado,
             "ini": AHORA - timedelta(days=10), "fin": fin, "m": None if fin is None else "terminar"})

    def version_de_biblioteca(self) -> None:
        """Una versión del catálogo para las descargas. Sus triggers exigen el flujo editorial, que no es el
        objeto de esta prueba: se desactivan solo durante la siembra, dentro de la transacción revertida."""
        codigo = f"ZZ-D-{self.s.upper()}"
        self.con.execute(text("INSERT INTO biblioteca_catalogo (codigo) VALUES (:c)"), {"c": codigo})
        self.con.execute(text("ALTER TABLE biblioteca_versiones DISABLE TRIGGER USER"))
        self.con.execute(text(
            "INSERT INTO biblioteca_versiones (id, codigo, version, formato, responsable_id, autores) "
            "VALUES (:i, :c, '1.0', 'MD', :a, CAST(:au AS jsonb))"),
            {"i": self.version, "c": codigo, "a": self.actor, "au": f'["{self.actor}"]'})
        self.con.execute(text("ALTER TABLE biblioteca_versiones ENABLE TRIGGER USER"))

    def biblioteca_y_consultas(self, tid: str) -> None:
        """Una fila en cada una de las cinco tablas inmutables, más el documento y un evento de auditoría."""
        self.con.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": tid})
        contenido = f"Política de prueba de {tid}"
        documento = str(uuid.uuid4())
        sha = hashlib.sha256(contenido.encode("utf-8")).hexdigest()
        self.con.execute(text(
            "INSERT INTO biblioteca_documentos (id, tenant_id, codigo, nombre, origen, contenido_markdown, sha256, "
            "fecha_emision, proxima_revision, creado_por) "
            "VALUES (:i, :t, 'POL-ZZ', 'Política', 'propio', :c, :h, current_date, current_date + 365, :a)"),
            {"i": documento, "t": tid, "c": contenido, "h": sha, "a": self.actor})
        self.con.execute(text(
            "INSERT INTO biblioteca_documentos_historial (id, tenant_id, documento_id, revision, accion, "
            "contenido_markdown, sha256, actor_id) VALUES (:i, :t, :d, 1, 'creado', :c, :h, :a)"),
            {"i": str(uuid.uuid4()), "t": tid, "d": documento, "c": contenido, "h": sha, "a": self.actor})
        self.con.execute(text(
            "INSERT INTO biblioteca_eventos_documento (id, tenant_id, documento_id, tipo, actor_id) "
            "VALUES (:i, :t, :d, 'generacion', :a)"),
            {"i": str(uuid.uuid4()), "t": tid, "d": documento, "a": self.actor})
        self.con.execute(text(
            "INSERT INTO biblioteca_descargas (id, tenant_id, usuario_id, plantilla_id, version) "
            "VALUES (:i, :t, :a, :v, '1.0')"),
            {"i": str(uuid.uuid4()), "t": tid, "a": self.actor, "v": self.version})
        consulta = f"zz-d-cons-{uuid.uuid4().hex[:12]}"
        self.con.execute(text(
            "INSERT INTO dpo_consultas (id, tenant_id, asunto, estado, creado_por, creado_en) "
            "VALUES (:i, :t, 'Consulta de prueba', 'abierta', :a, now())"), {"i": consulta, "t": tid, "a": self.actor})
        self.con.execute(text(
            "INSERT INTO dpo_consultas_mensajes (id, tenant_id, consulta_id, secuencia, autor_id, autor_rol, texto, "
            "creado_en) VALUES (:i, :t, :c, 1, :a, 'dpo', 'Mensaje de prueba', now())"),
            {"i": f"zz-d-msg-{uuid.uuid4().hex[:12]}", "t": tid, "c": consulta, "a": self.actor})
        self.con.execute(text(
            "INSERT INTO audit_events (id, tenant_id, entity_type, entity_id, action, payload) "
            "VALUES (:i, :t, 'demo', 'x', 'crear', CAST('{}' AS json))"), {"i": f"zz-d-aud-{uuid.uuid4().hex}", "t": tid})
        self.con.execute(text("SELECT set_config('app.current_tenant_id', '', true)"))

    def sembrar(self) -> None:
        self.con.execute(text("INSERT INTO users (id, email, nombre) VALUES (:i, :e, 'Actor de prueba')"),
                         {"i": self.actor, "e": f"actor-{self.s}@empresa-real.invalid"})
        self.tenant(PLANTILLA_TENANT_ID, True)
        self.tenant(self.vencido, True)
        self.tenant(self.activo, True)
        self.tenant(self.no_demo, False)
        # La plantilla y el no demo tienen una sesión «vencida»: solo las condiciones de la función los protegen.
        for tid in (self.vencido, PLANTILLA_TENANT_ID, self.no_demo, self.activo):
            self.sesion(tid, "vencida")
        self.sesion(self.activo, "activa")
        self.version_de_biblioteca()
        for tid in self.todos:
            self.biblioteca_y_consultas(tid)

    def filas(self, tabla: str, tid: str) -> int:
        """SQLAlchemy cita el identificador; el tenant va como parámetro enlazado."""
        condicion = cast(column("tenant_id"), String) == tid
        return self.con.execute(select(func.count()).select_from(table(tabla, column("tenant_id"))).where(condicion)
                                ).scalar_one()

    def recuento(self, tid: str) -> dict[str, int]:
        return {tabla: self.filas(tabla, tid) for tabla in SEMBRADAS}

    def existe_tenant(self, tid: str) -> bool:
        return self.con.execute(text("SELECT count(*) FROM tenants WHERE id = :t"), {"t": tid}).scalar_one() == 1


@pytest.fixture
def con():
    """Conexión con rol, marcador `demo` y `politicas_purga.sql` aplicados en una transacción revertida."""
    motor = create_engine(_url())
    conexion = motor.connect()
    transaccion = conexion.begin()
    try:
        conexion.execute(text("SET LOCAL lock_timeout = '10s'"))
        asegurar_rol(conexion, "purga_demo")
        if not conexion.execute(text("SELECT rolsuper FROM pg_roles WHERE rolname = current_user")).scalar_one():
            conexion.execute(text("GRANT purga_demo TO CURRENT_USER"))
        conexion.execute(text("CREATE TABLE IF NOT EXISTS public.entorno_marcador (valor text NOT NULL)"))
        poner_marcador(conexion, "demo")
        ejecutar_sql(conexion)
        yield conexion
    finally:
        transaccion.rollback()
        conexion.close()
        motor.dispose()


@pytest.fixture
def mundo(con):
    m = Mundo(con)
    m.sembrar()
    return m


TODOS_ENCENDIDOS = {trigger: "O" for _, trigger in TRIGGERS_INMUTABLES}


# --- Purga de una demo con biblioteca ------------------------------------------------------------------


def test_demo_con_biblioteca_queda_vacia(con, mundo):
    antes = {tid: mundo.recuento(tid) for tid in mundo.todos}
    assert all(n == 1 for n in antes[mundo.vencido].values()), antes[mundo.vencido]
    assert faltan_politicas(con) == [] and falta_funcion_inmutables(con) == []

    with como_purga(con):
        assert ejecutar(con, AlmacenVacio(), AHORA) == 0

    assert not mundo.existe_tenant(mundo.vencido)
    assert mundo.recuento(mundo.vencido) == {tabla: 0 for tabla in SEMBRADAS}
    for tid in (PLANTILLA_TENANT_ID, mundo.activo, mundo.no_demo):
        assert mundo.existe_tenant(tid), tid
        assert mundo.recuento(tid) == antes[tid], f"perdió filas: {tid}"
    assert triggers_encendidos(con) == TODOS_ENCENDIDOS


def test_la_funcion_devuelve_las_filas_borradas(con, mundo):
    assert llamar(con, mundo.vencido) == len(INMUTABLES), "una fila por tabla inmutable"
    assert all(mundo.filas(t, mundo.vencido) == 0 for t in INMUTABLES)
    assert mundo.filas("biblioteca_documentos", mundo.vencido) == 1, "el resto lo borra la purga después"
    assert triggers_encendidos(con) == TODOS_ENCENDIDOS
    assert con.execute(text("SELECT current_setting('app.current_tenant_id', true)")).scalar_one() in ("", None),         "la función deja el tenant de la sesión como estaba"


# --- R1 · Falla cerrada ---------------------------------------------------------------------------------


def test_sin_marcador_demo_falla_cerrada(con, mundo):
    for marcador in ("pruebas", "produccion", None):
        poner_marcador(con, marcador)
        assert llamar(con, mundo.vencido) == "42501", marcador
        assert triggers_encendidos(con) == TODOS_ENCENDIDOS, marcador
        assert all(mundo.filas(t, mundo.vencido) == 1 for t in INMUTABLES), marcador
    con.execute(text("INSERT INTO public.entorno_marcador VALUES ('demo'), ('demo')"))
    assert llamar(con, mundo.vencido) == "42501", "dos filas de marcador no son «una sola fila demo»"


def test_plantilla_y_no_demo_fallan(con, mundo):
    for tid in (PLANTILLA_TENANT_ID, mundo.no_demo, f"zz-d-no-existe-{mundo.s}"):
        assert llamar(con, tid) == "42501", tid
        assert triggers_encendidos(con) == TODOS_ENCENDIDOS, tid
    for tid in (PLANTILLA_TENANT_ID, mundo.no_demo):
        assert all(mundo.filas(t, tid) == 1 for t in INMUTABLES), tid


def test_demo_con_sesion_activa_falla(con, mundo):
    assert llamar(con, mundo.activo) == "42501"
    assert triggers_encendidos(con) == TODOS_ENCENDIDOS
    assert all(mundo.filas(t, mundo.activo) == 1 for t in INMUTABLES)


# --- R3 y R5 · Dueño sin BYPASSRLS, sujeto a FORCE RLS ---------------------------------------------------


def test_dueno_sin_bypassrls_borra_con_force_rls(con, mundo):
    """Como en Cloud SQL: el dueño de las tablas y de la función no es superusuario ni tiene BYPASSRLS, así que
    FORCE RLS lo somete a las políticas de la sala; la función fija el tenant y borra solo el suyo."""
    asegurar_rol(con, "zz_d_dueno")
    if not con.execute(text("SELECT rolsuper FROM pg_roles WHERE rolname = current_user")).scalar_one():
        con.execute(text("GRANT zz_d_dueno TO CURRENT_USER"))
    con.execute(text(_SQL_TRASPASAR_DUENO))
    con.execute(text(f"ALTER FUNCTION {FIRMA} OWNER TO zz_d_dueno"))
    dueno = con.execute(text("SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = 'zz_d_dueno'")).one()
    assert tuple(dueno) == (False, False)
    assert con.execute(text("SELECT bool_and(relrowsecurity AND relforcerowsecurity) FROM pg_class "
                            "WHERE oid = ANY (CAST(:t AS regclass[]))"),
                       {"t": [f"public.{t}" for t in INMUTABLES]}).scalar_one() is True

    assert llamar(con, mundo.vencido) == len(INMUTABLES)
    assert all(mundo.filas(t, mundo.vencido) == 0 for t in INMUTABLES)
    for tid in (PLANTILLA_TENANT_ID, mundo.activo, mundo.no_demo):
        assert all(mundo.filas(t, tid) == 1 for t in INMUTABLES), tid
    assert triggers_encendidos(con) == TODOS_ENCENDIDOS


# --- R4 · Triggers en la misma transacción --------------------------------------------------------------


def test_fallo_a_mitad_deja_los_triggers_encendidos(con, mundo):
    """Un trigger de sentencia ajeno a la lista falla en el tercer DELETE, tras borrar las dos primeras."""
    con.execute(text(
        "CREATE FUNCTION public.zz_d_fallo() RETURNS trigger LANGUAGE plpgsql AS "
        "$$ BEGIN RAISE EXCEPTION 'fallo inyectado' USING ERRCODE = 'P0001'; END $$"))
    con.execute(text(
        "CREATE TRIGGER zz_d_fallo_inyectado BEFORE DELETE ON biblioteca_eventos_documento "
        "FOR EACH STATEMENT EXECUTE FUNCTION public.zz_d_fallo()"))

    assert llamar(con, mundo.vencido) == "P0001"
    assert triggers_encendidos(con) == TODOS_ENCENDIDOS
    assert all(mundo.filas(t, mundo.vencido) == 1 for t in INMUTABLES), "el rollback devolvió las filas"


# --- R3 · Permisos mínimos ------------------------------------------------------------------------------


def test_permisos_de_la_funcion(con, mundo):
    asegurar_rol(con, "lopdp_app")
    fila = con.execute(text(
        "SELECT p.prosecdef, p.proconfig, format_type(p.prorettype, NULL) AS tipo, "
        "has_function_privilege('public', p.oid, 'EXECUTE') AS publica, "
        "has_function_privilege('lopdp_app', p.oid, 'EXECUTE') AS app, "
        "has_function_privilege('purga_demo', p.oid, 'EXECUTE') AS purga "
        f"FROM pg_proc p WHERE p.oid = '{FIRMA}'::regprocedure")).one()
    assert fila.prosecdef is True
    assert "search_path=pg_catalog, public" in (fila.proconfig or [])
    assert fila.tipo == "integer"
    assert (fila.publica, fila.app, fila.purga) == (False, False, True), "EXECUTE solo para purga_demo"

    rol = con.execute(text("SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = 'purga_demo'")).one()
    assert tuple(rol) == (False, False)
    assert con.execute(text(
        "SELECT count(*) FROM pg_class WHERE relowner = (SELECT oid FROM pg_roles WHERE rolname = 'purga_demo')"
    )).scalar_one() == 0, "purga_demo sigue sin ser dueño de nada"


def test_el_sql_es_idempotente_y_no_abre_la_funcion(con):
    asegurar_rol(con, "lopdp_app")
    con.execute(text(f"GRANT EXECUTE ON FUNCTION {FIRMA} TO lopdp_app"))
    ejecutar_sql(con)
    assert con.execute(text(f"SELECT has_function_privilege('lopdp_app', '{FIRMA}'::regprocedure, 'EXECUTE')")
                       ).scalar_one() is False, "volver a ejecutar el SQL retira un EXECUTE concedido a otro rol"
    assert falta_funcion_inmutables(con) == []


# --- R6 · Guardia del Job -------------------------------------------------------------------------------


def test_guardia_nombra_el_trigger_nuevo(con, mundo, capsys):
    assert falta_funcion_inmutables(con) == []
    con.execute(text(
        "CREATE FUNCTION public.zz_d_inmutable() RETURNS trigger LANGUAGE plpgsql AS "
        "$$ BEGIN RAISE EXCEPTION 'inmutable' USING ERRCODE = '23514'; END $$"))
    con.execute(text(
        "CREATE TRIGGER zz_d_trigger_nuevo BEFORE DELETE ON audit_events "
        "FOR EACH ROW EXECUTE FUNCTION public.zz_d_inmutable()"))

    faltan = falta_funcion_inmutables(con)
    assert any("zz_d_trigger_nuevo" in f and "audit_events" in f for f in faltan), faltan

    almacen = AlmacenVacio()
    with como_purga(con):
        assert ejecutar(con, almacen, AHORA) == 1
    assert "zz_d_trigger_nuevo" in capsys.readouterr().err
    assert almacen.llamadas == [], "el Job sale antes de tocar el almacén"
    assert mundo.existe_tenant(mundo.vencido)
    assert mundo.recuento(mundo.vencido) == {tabla: 1 for tabla in SEMBRADAS}, "ni una fila se borra"


def test_sin_la_funcion_no_hay_borrado_a_medias(con, mundo):
    """Fuera del Job (sin guardia) y sin la función: las inmutables no se tocan, la purga falla (por las claves
    foráneas que las atan al documento o por la comprobación de 0 filas) y la transacción del tenant revierte."""
    con.execute(text(f"DROP FUNCTION {FIRMA}"))
    antes = mundo.recuento(mundo.vencido)
    with como_purga(con):
        with pytest.raises(modulo_purga.ErrorPurga):
            modulo_purga.purgar_tenant(con, AlmacenVacio(), mundo.vencido)
    assert mundo.existe_tenant(mundo.vencido)
    assert mundo.recuento(mundo.vencido) == antes


def test_guardia_vigila_la_funcion(con):
    casos = {
        f"ALTER FUNCTION {FIRMA} SECURITY INVOKER": "SECURITY DEFINER",
        f"ALTER FUNCTION {FIRMA} RESET search_path": "search_path",
        f"GRANT EXECUTE ON FUNCTION {FIRMA} TO PUBLIC": "PUBLIC",
        f"REVOKE EXECUTE ON FUNCTION {FIRMA} FROM purga_demo": "EXECUTE para purga_demo",
        f"DROP FUNCTION {FIRMA}": "purga_demo_borrar_inmutables",
    }
    for sql, esperado in casos.items():
        punto = con.begin_nested()
        con.execute(text(sql))
        faltan = falta_funcion_inmutables(con)
        punto.rollback()
        assert any(esperado in f for f in faltan), (sql, faltan)
    assert falta_funcion_inmutables(con) == []


# --- R2 · Solo en la base de la demo --------------------------------------------------------------------


def test_ninguna_migracion_define_la_funcion():
    migraciones = sorted((RAIZ / "alembic" / "versions").glob("*.py"))
    assert migraciones, "no se encontraron migraciones"
    con_funcion = [m.name for m in migraciones if "purga_demo_borrar_inmutables" in m.read_text(encoding="utf-8")]
    assert con_funcion == []
