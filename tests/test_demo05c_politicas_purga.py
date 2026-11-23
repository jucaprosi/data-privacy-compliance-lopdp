# -*- coding: utf-8 -*-
# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤demo ¤seguridad ¤arbitro
"""DEMO-05c: purga de la demo con políticas explícitas por rol `purga_demo`, sin BYPASSRLS.

Corren contra PostgreSQL 16 real (`TEST_DATABASE_URL`, el del arnés local o el servicio del CI) con todas
las migraciones (`alembic upgrade heads`). Todo ocurre en UNA transacción que se revierte (R11):
`CREATE ROLE purga_demo` es global en el servidor, y en PostgreSQL es transaccional, así que el rol, el
marcador `demo`, `politicas_purga.sql` y los datos desaparecen al terminar. Solo valores simulados y
correos `.invalid`.

Mutaciones (governance/especificaciones/DEMO-05c.md §5), aplicadas una a una al código o al SQL, con la
suite corrida y el archivo restaurado; el resultado de cada una está en el cuerpo del PR:
- m1 `__main__.py`: `ejecutar` sin cortar cuando `faltan_politicas` devuelve algo (`if faltan:` -> `if False:`)
  -> falla `test_guardia_nombra_la_tabla_sin_politicas`; también falla si `_SQL_TABLAS` vuelve a
  `information_schema`, que no le enseña a `purga_demo` una tabla sin permisos.
- m2 `purga.py`: `_SQL_VENCIDOS` sin `AND t.id <> :plantilla` -> falla `test_purga_solo_los_vencidos`.
- m3 `purga.py`: `_SQL_VENCIDOS` sin la condición `NOT EXISTS (... 'activa')` -> falla `test_purga_solo_los_vencidos`.
- m4 `purga.py`: `DIAS_DE_RETENCION = 0` -> falla `test_caducidad_a_90_dias`.
- m5 `politicas_purga.sql`: `GRANT SELECT, DELETE ON public.demo_sesiones` entera -> falla `test_permisos_por_columnas`.
- m6 `politicas_purga.sql`: `GRANT SELECT (id, email), DELETE ON public.users` -> falla `test_permisos_por_columnas`.
- m7 `politicas_purga.sql`: `es_persona_ficticia` que devuelve siempre true -> falla
  `test_se_conserva_un_usuario_real_correo_sin_invalid_con_rol_en_demo_vencida` (DEMO-05b).
- m8 `politicas_purga.sql`: `GRANT EXECUTE ... TO purga_demo, PUBLIC` -> la guardia falla y con ella
  `test_guardia_vigila_la_funcion_y_el_correo`, `test_funcion_persona_ficticia` y las que esperan la guardia vacía.
- m9 `usuarios.py`: sin `AND ds.tenant_id IS NOT NULL` -> falla
  `test_se_borra_el_usuario_invalid_cuyos_roles_eran_solo_de_demos_vencidas` (DEMO-05b).
- Sin el filtro por `tenant_id` del código (`_de_tenant` sin condición) -> falla
  `test_tabla_sin_rls_respeta_plantilla_y_activas`.
"""
from __future__ import annotations

import os
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

from features.demo.demo_service import PLANTILLA_TENANT_ID
from jobs.purga_demo import purga as modulo_purga
from jobs.purga_demo.__main__ import ejecutar
from jobs.purga_demo.guardias import faltan_politicas, tablas_sin_rls

RAIZ = Path(__file__).resolve().parent.parent
SQL_POLITICAS = (RAIZ / "jobs" / "purga_demo" / "politicas_purga.sql").read_text(encoding="utf-8")
AHORA = datetime.now(timezone.utc)
CINCO_SIN_RLS = {"tenants", "demo_sesiones", "users", "invitaciones_organizacion", "auditoria_plataforma"}


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


def preparar_rol_y_marcador(con, marcador: str | None = "demo") -> None:
    """Rol `purga_demo` y marcador dentro de la transacción del llamador, que se revierte (R11)."""
    if not con.execute(text("SELECT 1 FROM pg_roles WHERE rolname = 'purga_demo'")).first():
        con.execute(text("CREATE ROLE purga_demo NOLOGIN"))
    if not con.execute(text("SELECT rolsuper FROM pg_roles WHERE rolname = current_user")).scalar_one():
        con.execute(text("GRANT purga_demo TO CURRENT_USER"))
    con.execute(text("CREATE TABLE IF NOT EXISTS public.entorno_marcador (valor text NOT NULL)"))
    poner_marcador(con, marcador)


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


def denegado(con, sql: str) -> bool:
    """Verdadero si la sentencia falla con «permission denied»; un savepoint deja viva la transacción."""
    try:
        with con.begin_nested():
            con.execute(text(sql))
    except DBAPIError as error:
        return "permission denied" in str(error.orig).lower()
    return False


class Mundo:
    """Un tenant demo vencido, la plantilla, una demo con sesión activa y un tenant no demo."""

    def __init__(self, con) -> None:
        self.con = con
        self.s = uuid.uuid4().hex[:8]
        self.vencido = f"zz-c-vencido-{self.s}"
        self.activo = f"zz-c-activo-{self.s}"
        self.no_demo = f"zz-c-real-{self.s}"
        self.persona = f"zz-c-persona-{self.s}"
        self.real = f"zz-c-real-usr-{self.s}"

    def tenant(self, tid: str, es_demo: bool) -> None:
        self.con.execute(text(
            "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, es_demo) "
            "VALUES (:i, :n, :n, :r, :d) ON CONFLICT (id) DO NOTHING"),
            {"i": tid, "n": f"Tenant {tid}", "r": f"{uuid.uuid4().int % 10**13:013d}", "d": es_demo})

    def sesion(self, sid: str, tid: str | None, estado: str, dias_fin: int = 1, persona: str | None = None) -> None:
        fin = None if estado == "activa" else AHORA - timedelta(days=dias_fin)
        self.con.execute(text(
            "INSERT INTO demo_sesiones (id, vendedor_sub, vendedor_email, tenant_id, persona_usuario_id, estado, "
            "iniciada_en, ultima_actividad, terminada_en, motivo_fin) "
            "VALUES (:i, :sub, :e, :t, :p, :est, :ini, :ini, :fin, :m)"),
            {"i": sid, "sub": f"sub-{self.s}", "e": f"vendedor-{self.s}@vendedores.invalid", "t": tid, "p": persona,
             "est": estado, "ini": AHORA - timedelta(days=200), "fin": fin, "m": None if fin is None else "terminar"})

    def auditoria(self, tid: str) -> None:
        self.con.execute(text(
            "INSERT INTO audit_events (id, tenant_id, entity_type, entity_id, action, payload) "
            "VALUES (:i, :t, 'demo', 'x', 'crear', CAST('{}' AS json))"), {"i": f"zz-c-aud-{tid}", "t": tid})

    def invitacion(self, tid: str) -> None:
        self.con.execute(text(
            "INSERT INTO invitaciones_organizacion (id, tenant_id, email, codigo_hash, expira_en, created_by) "
            "VALUES (:i, :t, :e, :h, :exp, 'zz-c-sistema')"),
            {"i": f"zz-c-inv-{tid}", "t": tid, "e": f"invitada-{self.s}@cooperativa-demo.invalid", "h": f"hash-{tid}",
             "exp": AHORA + timedelta(days=7)})

    def sembrar(self) -> None:
        self.tenant(PLANTILLA_TENANT_ID, True)
        self.tenant(self.vencido, True)
        self.tenant(self.activo, True)
        self.tenant(self.no_demo, False)
        # La plantilla y el no demo tienen una sesión «vencida»: solo los filtros del código los protegen.
        self.sesion(f"zz-c-ses-v-{self.s}", self.vencido, "vencida")
        self.sesion(f"zz-c-ses-p-{self.s}", PLANTILLA_TENANT_ID, "vencida")
        self.sesion(f"zz-c-ses-n-{self.s}", self.no_demo, "vencida")
        self.sesion(f"zz-c-ses-a1-{self.s}", self.activo, "vencida")
        self.sesion(f"zz-c-ses-a2-{self.s}", self.activo, "activa")
        for tid in (PLANTILLA_TENANT_ID, self.vencido, self.activo, self.no_demo):
            self.auditoria(tid)
            self.invitacion(tid)
        self.con.execute(text("INSERT INTO users (id, email, nombre) VALUES (:i, :e, 'Persona Demo'), "
                              "(:r, :re, 'Persona Real')"),
                         {"i": self.persona, "e": f"persona-{self.s}@cooperativa-demo.invalid",
                          "r": self.real, "re": f"consultor-{self.s}@empresa-real.com"})

    def cuenta(self, sql: str, **p) -> int:
        return self.con.execute(text(sql), p).scalar_one()

    def existe_tenant(self, tid: str) -> bool:
        return self.cuenta("SELECT count(*) FROM tenants WHERE id = :t", t=tid) == 1


@pytest.fixture
def con():
    """Conexión con rol, marcador `demo` y `politicas_purga.sql` aplicados en una transacción revertida."""
    motor = create_engine(_url())
    conexion = motor.connect()
    transaccion = conexion.begin()
    try:
        conexion.execute(text("SET LOCAL lock_timeout = '10s'"))
        preparar_rol_y_marcador(conexion)
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


# --- Guardias -------------------------------------------------------------------------------------------


def test_guardia_nombra_la_tabla_sin_politicas(con, mundo, capsys):
    assert faltan_politicas(con) == []
    con.execute(text("CREATE TABLE public.zz_c_nueva (id text PRIMARY KEY, "
                     "tenant_id character varying REFERENCES tenants(id))"))
    con.execute(text("ALTER TABLE public.zz_c_nueva ENABLE ROW LEVEL SECURITY"))
    con.execute(text("INSERT INTO public.zz_c_nueva VALUES ('fila', :t)"), {"t": mundo.vencido})
    assert faltan_politicas(con) == ["zz_c_nueva"]

    almacen = AlmacenVacio()
    with como_purga(con):
        assert "zz_c_nueva" in faltan_politicas(con), "la guardia ve la tabla aunque el rol no tenga permisos"
        assert ejecutar(con, almacen, AHORA) == 1
    assert "faltan políticas de purga en: zz_c_nueva; ejecuta politicas_purga.sql" in capsys.readouterr().err
    assert almacen.llamadas == [], "el Job sale antes de tocar el almacén"
    assert mundo.existe_tenant(mundo.vencido), "ni una fila se borra si falta una política"

    ejecutar_sql(con)  # tras volver a ejecutar el SQL, la tabla nueva queda cubierta
    assert faltan_politicas(con) == []


def test_guardia_lista_aparte_las_tablas_sin_rls(con):
    assert set(tablas_sin_rls(con)) == CINCO_SIN_RLS
    assert faltan_politicas(con) == [], "las tablas sin RLS con sus permisos no hacen fallar la guardia"
    con.execute(text("REVOKE DELETE ON public.invitaciones_organizacion FROM purga_demo"))
    assert faltan_politicas(con) == ["invitaciones_organizacion"]
    con.execute(text("REVOKE ALL ON public.demo_sesiones FROM purga_demo"))
    assert "demo_sesiones" in faltan_politicas(con)


# --- Purga como purga_demo ------------------------------------------------------------------------------


def test_purga_solo_los_vencidos(con, mundo):
    with como_purga(con):
        assert mundo.vencido in modulo_purga.tenants_vencidos(con)
        assert ejecutar(con, AlmacenVacio(), AHORA) == 0
    assert not mundo.existe_tenant(mundo.vencido)
    assert mundo.existe_tenant(PLANTILLA_TENANT_ID), "la plantilla nunca se purga"
    assert mundo.existe_tenant(mundo.activo), "una demo con sesión activa no se purga"
    assert mundo.existe_tenant(mundo.no_demo), "un tenant no demo no se purga"
    assert mundo.cuenta("SELECT count(*) FROM audit_events WHERE tenant_id = :t", t=mundo.vencido) == 0
    for tid in (PLANTILLA_TENANT_ID, mundo.activo, mundo.no_demo):
        assert mundo.cuenta("SELECT count(*) FROM audit_events WHERE tenant_id = :t", t=tid) == 1, tid


def test_tabla_sin_rls_respeta_plantilla_y_activas(con, mundo):
    sql = "SELECT count(*) FROM invitaciones_organizacion WHERE tenant_id = :t"
    with como_purga(con):
        modulo_purga.purgar_tenant(con, AlmacenVacio(), mundo.vencido)
    assert mundo.cuenta(sql, t=mundo.vencido) == 0
    for tid in (PLANTILLA_TENANT_ID, mundo.activo, mundo.no_demo):
        assert mundo.cuenta(sql, t=tid) == 1, f"la tabla sin RLS perdió filas de {tid}"


def test_sin_marcador_demo_no_ve_nada(con, mundo):
    for marcador in ("pruebas", None):
        poner_marcador(con, marcador)
        with como_purga(con):
            for tabla in ("audit_events", "user_tenant_roles"):
                assert mundo.cuenta(f"SELECT count(*) FROM {tabla}") == 0, (marcador, tabla)
            assert mundo.cuenta("SELECT count(*) FROM audit_events WHERE tenant_id = :t", t=mundo.vencido) == 0
            assert con.execute(text("SELECT es_persona_ficticia(:u)"), {"u": mundo.persona}).scalar_one() is False
        assert mundo.cuenta("SELECT count(*) FROM audit_events WHERE tenant_id = :t", t=mundo.vencido) == 1
    poner_marcador(con, "demo")
    with como_purga(con):
        assert mundo.cuenta("SELECT count(*) FROM audit_events WHERE tenant_id = :t", t=mundo.vencido) == 1
        assert con.execute(text("SELECT es_persona_ficticia(:u)"), {"u": mundo.persona}).scalar_one() is True


def test_caducidad_a_90_dias(con, mundo):
    mundo.sesion(f"zz-c-ses-91-{mundo.s}", None, "vencida", dias_fin=91)
    mundo.sesion(f"zz-c-ses-89-{mundo.s}", None, "vencida", dias_fin=89)
    with como_purga(con):
        modulo_purga.caducar_sesiones(con, AHORA)
    ids = {f[0] for f in con.execute(text("SELECT id FROM demo_sesiones WHERE id LIKE :p"),
                                     {"p": f"zz-c-ses-%{mundo.s}"})}
    assert f"zz-c-ses-91-{mundo.s}" not in ids
    assert f"zz-c-ses-89-{mundo.s}" in ids


def test_permisos_por_columnas(con, mundo):
    with como_purga(con):
        con.execute(text("SELECT id, tenant_id, estado, terminada_en, persona_usuario_id FROM demo_sesiones"))
        con.execute(text("SELECT id FROM users"))
        for sql in (
            "SELECT vendedor_email FROM demo_sesiones",
            "SELECT vendedor_sub FROM demo_sesiones",
            "SELECT * FROM demo_sesiones",
            "SELECT email FROM users",
            "SELECT * FROM users",
            "UPDATE demo_sesiones SET persona_usuario_id = NULL WHERE false",
            "UPDATE demo_sesiones SET tenant_id = NULL WHERE false",
            "UPDATE users SET nombre = 'x' WHERE false",
            "UPDATE tenants SET es_demo = true WHERE false",
            "UPDATE audit_events SET action = 'x' WHERE false",
            "INSERT INTO demo_sesiones (id, estado) VALUES ('zz-c-intruso', 'activa')",
            "INSERT INTO users (id, email, nombre) VALUES ('zz-c-intruso', 'x@y.invalid', 'x')",
            "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
            "VALUES ('zz-c-intruso', 'x', 'x', '0')",
        ):
            assert denegado(con, sql), sql


def test_funcion_persona_ficticia(con, mundo):
    fila = con.execute(text(
        "SELECT p.prosecdef, p.proconfig, format_type(p.prorettype, NULL) AS tipo, "
        "has_function_privilege('public', p.oid, 'EXECUTE') AS publica, "
        "has_function_privilege('purga_demo', p.oid, 'EXECUTE') AS purga "
        "FROM pg_proc p WHERE p.proname = 'es_persona_ficticia' AND p.pronamespace = 'public'::regnamespace")).one()
    assert fila.prosecdef is True
    assert any(o.startswith("search_path=") for o in fila.proconfig or [])
    assert fila.tipo == "boolean"
    assert fila.publica is False and fila.purga is True
    with como_purga(con):
        assert con.execute(text("SELECT es_persona_ficticia(:u)"), {"u": mundo.persona}).scalar_one() is True
        assert con.execute(text("SELECT es_persona_ficticia(:u)"), {"u": mundo.real}).scalar_one() is False
        assert con.execute(text("SELECT es_persona_ficticia('zz-c-no-existe')")).scalar_one() is False


def test_guardia_vigila_la_funcion_y_el_correo(con):
    casos = {
        "ALTER FUNCTION public.es_persona_ficticia(character varying) SECURITY INVOKER": "es_persona_ficticia",
        "DROP FUNCTION public.es_persona_ficticia(character varying)": "es_persona_ficticia",
        "GRANT EXECUTE ON FUNCTION public.es_persona_ficticia(character varying) TO PUBLIC": "PUBLIC",
        "GRANT SELECT (email) ON public.users TO purga_demo": "users.email",
        "GRANT SELECT ON public.users TO purga_demo": "users.email",
    }
    for sql, esperado in casos.items():
        punto = con.begin_nested()
        con.execute(text(sql))
        faltan = faltan_politicas(con)
        punto.rollback()
        assert any(esperado in f for f in faltan), (sql, faltan)
    assert faltan_politicas(con) == []


def test_rol_sin_privilegios_especiales(con):
    rol = con.execute(text("SELECT rolsuper, rolbypassrls, rolcreaterole, rolcreatedb FROM pg_roles "
                           "WHERE rolname = 'purga_demo'")).one()
    assert tuple(rol) == (False, False, False, False)
    assert con.execute(text("SELECT count(*) FROM pg_policies WHERE policyname LIKE 'purga_demo_%' "
                            "AND roles <> '{purga_demo}'")).scalar_one() == 0
    assert con.execute(text("SELECT count(*) FROM pg_policies WHERE 'purga_demo' = ANY(roles)")).scalar_one() > 0
    assert con.execute(text("SELECT count(*) FROM pg_policies WHERE 'purga_demo' = ANY(roles) "
                            "AND (qual IS NULL OR qual = 'true' OR qual NOT LIKE '%entorno_marcador%')")
                       ).scalar_one() == 0, "toda política exige el marcador y ninguna es USING (true)"


_SQL_ESTADO = (
    "SELECT 'politica', tablename || '|' || policyname || '|' || cmd || '|' || coalesce(qual, '') "
    "FROM pg_policies WHERE 'purga_demo' = ANY(roles) "
    "UNION ALL SELECT 'tabla', table_name || '|' || privilege_type FROM information_schema.role_table_grants "
    "WHERE grantee = 'purga_demo' "
    "UNION ALL SELECT 'columna', table_name || '|' || column_name || '|' || privilege_type "
    "FROM information_schema.role_column_grants WHERE grantee = 'purga_demo' "
    "UNION ALL SELECT 'funcion', pg_get_functiondef(p.oid) || coalesce(array_to_string(p.proacl, ','), '') "
    "FROM pg_proc p WHERE p.proname = 'es_persona_ficticia' "
    "ORDER BY 1, 2"
)


def test_sql_idempotente(con):
    antes = con.execute(text(_SQL_ESTADO)).all()
    ejecutar_sql(con)
    assert con.execute(text(_SQL_ESTADO)).all() == antes
    assert faltan_politicas(con) == []


def test_guardia_vigila_las_funciones_de_otras_politicas(con):
    """Una política `TO public` de otra sala que llama a una función sin EXECUTE para `purga_demo` haría
    fallar cada DELETE de la purga («permission denied for function»): la guardia la nombra antes."""
    funciones = [f for (f,) in con.execute(text(
        "SELECT DISTINCT p.oid::regprocedure::text FROM pg_policy pol JOIN pg_depend d "
        "ON d.classid = 'pg_policy'::regclass AND d.objid = pol.oid AND d.refclassid = 'pg_proc'::regclass "
        "JOIN pg_proc p ON p.oid = d.refobjid WHERE 0 = ANY (pol.polroles) AND NOT p.prosecdef "
        "AND p.pronamespace = 'public'::regnamespace ORDER BY 1"))]
    if not funciones:
        pytest.skip("el esquema no tiene políticas TO public que llamen a funciones")
    for firma in funciones:
        assert con.execute(text("SELECT has_function_privilege('purga_demo', CAST(:f AS regprocedure), 'EXECUTE')"),
                           {"f": firma}).scalar_one(), firma
    punto = con.begin_nested()
    con.execute(text("SELECT set_config('purga.fn', :f, true)"), {"f": funciones[0]})
    con.execute(text(
        "DO $$ BEGIN EXECUTE 'REVOKE EXECUTE ON FUNCTION ' || current_setting('purga.fn') || ' FROM purga_demo'; END $$"
    ))
    faltan = faltan_politicas(con)
    punto.rollback()
    assert any(funciones[0] in f for f in faltan), faltan


def test_comprobacion_de_solo_lectura_del_propietario(con, mundo, capsys):
    """R10: `--comprobar` da 0 con la guardia vacía y al menos una persona ficticia, y no borra nada."""
    from jobs.purga_demo.__main__ import comprobar

    with como_purga(con):
        assert comprobar(con) == 0
    salida = capsys.readouterr().out
    assert "faltan=0" in salida and "personas_ficticias=" in salida and "@" not in salida
    assert mundo.existe_tenant(mundo.vencido)
    poner_marcador(con, "pruebas")
    with como_purga(con):
        assert comprobar(con) == 1, "sin marcador demo no reconoce a nadie: la comprobación lo dice"
