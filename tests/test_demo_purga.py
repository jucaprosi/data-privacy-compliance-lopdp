# -*- coding: utf-8 -*-
# ¤demo ¤seguridad-tenant
"""DEMO-05: Cloud Run Job de purga nocturna de las demos vencidas.

Corren contra PostgreSQL real (`TEST_DATABASE_URL`: el PG16 del arnés o evydentia-pruebas, nunca producción;
el conftest corta si apunta a producción). Solo valores simulados y correos `.invalid`.

Mutación documentada: si `comprobar_cero_filas` deja de comprobar (se salta o se sustituye por un `pass`),
falla `test_la_comprobacion_de_cero_filas_detecta_restos`, y `test_sin_la_comprobacion_los_restos_pasan_en_silencio`
documenta cómo se vería esa purga defectuosa. Si la guardia acepta otro marcador que no sea 'demo'
(por ejemplo 'pruebas'), falla `test_el_marcador_pruebas_u_otro_se_rechaza`.
"""
from __future__ import annotations

import os
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import DDL, String, cast, column, create_engine, func, literal_column, select, table, text
from sqlalchemy.engine import make_url

from features.demo.demo_service import PLANTILLA_TENANT_ID
from jobs.purga_demo import purga as modulo_purga
from jobs.purga_demo.almacen import AlmacenS3
from jobs.purga_demo.guardias import PurgaRechazada, exigir_demo
from jobs.purga_demo.purga import ErrorPurga, comprobar_cero_filas, purgar, purgar_tenant, tenants_vencidos

AHORA = datetime(2026, 11, 9, 3, 0, tzinfo=timezone.utc)
HUELLA = "huella-prod-simulada"
PROYECTO_DEMO = "proyecto-demo-simulado"
ENTORNO_DEMO = {"APP_ENV": "demo", "HUELLA_PROYECTO_PRODUCCION": HUELLA}


def _url() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL no configurada")
    return url.replace("postgresql://", "postgresql+psycopg://", 1)


class AlmacenEnMemoria:
    """Objetos por clave; registra el orden de las llamadas y, opcionalmente, qué ve la base al borrar."""

    def __init__(self, claves=(), al_borrar=None):
        self.claves = set(claves)
        self.al_borrar = al_borrar
        self.llamadas: list[str] = []

    def listar(self, prefijo):
        return sorted(c for c in self.claves if c.startswith(prefijo))

    def borrar(self, claves):
        self.llamadas.append("borrar")
        if self.al_borrar:
            self.al_borrar()
        self.claves -= set(claves)


class Mundo:
    """Datos ficticios: una demo vencida, una activa y la plantilla, con una fila en cada tabla."""

    def __init__(self, motor):
        s = uuid.uuid4().hex[:8]
        self.motor = motor
        self.s = s
        self.vencido, self.activo = f"zz-demo-vencido-{s}", f"zz-demo-activo-{s}"
        self.email = f"vendedor-{s}@vendedores.invalid"
        self.sub_v, self.sub_a = f"sub-v-{s}", f"sub-a-{s}"
        self.persona = f"zz-persona-{s}"
        self.sesion_v, self.sesion_a = f"zz-ses-v-{s}", f"zz-ses-a-{s}"
        self.plantilla_creada = False

    def sembrar(self, con):
        con.execute(text("CREATE TABLE zz_a_padre (id text PRIMARY KEY, tenant_id text NOT NULL)"))
        con.execute(text("CREATE TABLE zz_b_hija (id text PRIMARY KEY, tenant_id text NOT NULL, "
                         "padre_id text NOT NULL REFERENCES zz_a_padre(id))"))
        for tid in (PLANTILLA_TENANT_ID, self.vencido, self.activo):
            creada = con.execute(text(
                "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, es_demo) "
                "VALUES (:i, 'Cooperativa Demo', 'Cooperativa Demo', :ruc, TRUE) "
                "ON CONFLICT (id) DO NOTHING RETURNING id"),
                {"i": tid, "ruc": f"{uuid.uuid4().int % 10**13:013d}"}).first()
            if tid == PLANTILLA_TENANT_ID:
                self.plantilla_creada = creada is not None
            con.execute(text("INSERT INTO zz_a_padre VALUES (:p, :t)"), {"p": f"p-{tid}", "t": tid})
            con.execute(text("INSERT INTO zz_b_hija VALUES (:h, :t, :p)"), {"h": f"h-{tid}", "t": tid, "p": f"p-{tid}"})
            con.execute(text(
                "INSERT INTO audit_events (id, tenant_id, entity_type, entity_id, action, payload) "
                "VALUES (:i, :t, 'demo', 'x', 'crear', CAST(:p AS json))"),
                {"i": f"zz-aud-{tid}", "t": tid, "p": '{"nota": "dato ficticio"}'})
        con.execute(text("INSERT INTO users (id, email, nombre) VALUES (:i, :e, 'Persona Demo')"),
                    {"i": self.persona, "e": f"persona-{self.s}@cooperativa-demo.invalid"})
        con.execute(text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) "
                         "VALUES (:i, :u, :t, 'coordinador')"),
                    {"i": f"zz-utr-{self.s}", "u": self.persona, "t": self.vencido})
        # El correo del vendedor aparece también en la auditoría del tenant vencido (debe desaparecer).
        con.execute(text("INSERT INTO audit_events (id, tenant_id, entity_type, entity_id, action, payload) "
                         "VALUES (:i, :t, 'demo', 'y', 'ver_como', CAST(:p AS json))"),
                    {"i": f"zz-aud-v-{self.s}", "t": self.vencido, "p": f'{{"vendedor": "{self.email}"}}'})
        self.sesion(con, self.sesion_v, self.sub_v, self.vencido, "vencida", dias_desde_fin=1)
        self.sesion(con, self.sesion_a, self.sub_a, self.activo, "activa")

    def sesion(self, con, id_, sub, tenant, estado, dias_desde_fin=None, persona=True):
        fin = None if estado == "activa" else AHORA - timedelta(days=dias_desde_fin)
        con.execute(text(
            "INSERT INTO demo_sesiones (id, vendedor_sub, vendedor_email, tenant_id, persona_usuario_id, estado, "
            "iniciada_en, ultima_actividad, terminada_en, motivo_fin) VALUES "
            "(:i, :s, :e, :t, :p, :est, :ini, :ini, :fin, :m)"),
            {"i": id_, "s": sub, "e": self.email, "t": tenant, "p": self.persona if persona else None, "est": estado,
             "ini": AHORA - timedelta(days=200), "fin": fin, "m": None if fin is None else "terminar"})

    def limpiar(self, con):
        con.execute(text("DROP TABLE IF EXISTS zz_b_hija, zz_a_padre"))
        con.execute(text("DELETE FROM demo_sesiones WHERE id LIKE :p"), {"p": f"zz-ses-%{self.s}"})
        con.execute(text("DELETE FROM audit_events WHERE id LIKE 'zz-aud-%'  AND (id LIKE :a OR tenant_id IN (:v, :c))"),
                    {"a": f"%{self.s}", "v": self.vencido, "c": self.activo})
        con.execute(text("DELETE FROM audit_events WHERE id = :i"), {"i": f"zz-aud-{PLANTILLA_TENANT_ID}"})
        con.execute(text("DELETE FROM user_tenant_roles WHERE user_id = :u"), {"u": self.persona})
        con.execute(text("DELETE FROM users WHERE id = :u"), {"u": self.persona})
        for tid in (self.vencido, self.activo):
            con.execute(text("DELETE FROM tenants WHERE id = :i"), {"i": tid})
        if self.plantilla_creada:
            con.execute(text("DELETE FROM tenants WHERE id = :i"), {"i": PLANTILLA_TENANT_ID})


@pytest.fixture
def motor():
    motor = create_engine(_url())
    with motor.begin() as con:  # marcador de entorno que exige la guardia (SEC-20); solo si falta
        creado = con.execute(text("SELECT to_regclass('public.entorno_marcador')")).scalar() is None
        if creado:
            con.execute(text("CREATE TABLE public.entorno_marcador (valor text NOT NULL)"))
        if not con.execute(text("SELECT count(*) FROM public.entorno_marcador")).scalar():
            con.execute(text("INSERT INTO public.entorno_marcador VALUES ('pruebas')"))
    yield motor
    if creado:
        with motor.begin() as con:
            con.execute(text("DROP TABLE public.entorno_marcador"))
    motor.dispose()


@pytest.fixture
def mundo(motor):
    m = Mundo(motor)
    with motor.begin() as con:
        m.sembrar(con)
    yield m
    with motor.begin() as con:
        m.limpiar(con)


def _citar(motor, nombre):
    return motor.dialect.identifier_preparer.quote(nombre)


def _filas(motor, sql, **p):
    with motor.connect() as con:
        return con.execute(text(sql), p).scalar_one()


def _por_tenant(motor, tenant):
    sql = "SELECT count(*) FROM {} WHERE tenant_id = :t"
    return {t: _filas(motor, sql.format(t), t=tenant)
            for t in ("zz_a_padre", "zz_b_hija", "audit_events", "user_tenant_roles")}


# --- Purga -------------------------------------------------------------------------------------------


def test_no_queda_ninguna_fila_del_tenant_vencido_y_el_resto_queda_intacto(motor, mundo):
    almacen = AlmacenEnMemoria({f"{mundo.vencido}/t1/a.pdf", f"{mundo.activo}/t1/b.pdf",
                                f"{PLANTILLA_TENANT_ID}/t1/c.pdf"})
    plantilla_antes = _por_tenant(motor, PLANTILLA_TENANT_ID)
    activo_antes = _por_tenant(motor, mundo.activo)

    informe = purgar(motor, almacen, AHORA)

    assert mundo.vencido in informe.tenants and mundo.activo not in informe.tenants
    assert _por_tenant(motor, mundo.vencido) == dict.fromkeys(
        ("zz_a_padre", "zz_b_hija", "audit_events", "user_tenant_roles"), 0)
    with motor.connect() as con:  # recorre TODAS las tablas con tenant_id
        for (tabla,) in con.execute(text(modulo_purga._SQL_TABLAS)).all():
            n = con.execute(select(func.count()).select_from(table(tabla)).where(
                literal_column("tenant_id::text") == mundo.vencido)).scalar_one()
            assert n == 0, tabla
    assert _filas(motor, "SELECT count(*) FROM tenants WHERE id = :t", t=mundo.vencido) == 0
    assert _por_tenant(motor, PLANTILLA_TENANT_ID) == plantilla_antes
    assert _por_tenant(motor, mundo.activo) == activo_antes
    assert _filas(motor, "SELECT count(*) FROM tenants WHERE id = :t", t=PLANTILLA_TENANT_ID) == 1
    assert almacen.claves == {f"{mundo.activo}/t1/b.pdf", f"{PLANTILLA_TENANT_ID}/t1/c.pdf"}


def test_la_plantilla_nunca_es_vencida_ni_se_purga(motor, mundo):
    with motor.begin() as con:  # aun con una sesión «vencida» apuntando a la plantilla
        mundo.sesion(con, f"zz-ses-p-{mundo.s}", f"sub-p-{mundo.s}", PLANTILLA_TENANT_ID, "vencida", dias_desde_fin=1)
    with motor.connect() as con:
        assert PLANTILLA_TENANT_ID not in tenants_vencidos(con)
    with pytest.raises(ErrorPurga):
        purgar_tenant(motor, AlmacenEnMemoria(), PLANTILLA_TENANT_ID)


def test_una_demo_con_sesion_activa_no_se_purga(motor, mundo):
    with motor.begin() as con:  # el mismo tenant con una sesión activa y otra vencida
        mundo.sesion(con, f"zz-ses-x-{mundo.s}", f"sub-x-{mundo.s}", mundo.vencido, "activa")
    with motor.connect() as con:
        assert mundo.vencido not in tenants_vencidos(con)


def test_los_objetos_se_borran_antes_que_las_filas(motor, mundo):
    vistas = []
    almacen = AlmacenEnMemoria(
        {f"{mundo.vencido}/t1/a.pdf"},
        al_borrar=lambda: vistas.append(_por_tenant(motor, mundo.vencido)["audit_events"]))
    purgar(motor, almacen, AHORA)
    assert vistas == [2], "al borrar los objetos las filas debían existir todavía"
    assert almacen.llamadas == ["borrar"]


def test_si_quedan_objetos_no_se_tocan_las_filas(motor, mundo):
    class Terco(AlmacenEnMemoria):
        def borrar(self, claves):
            self.llamadas.append("borrar")

    with pytest.raises(ErrorPurga):
        purgar_tenant(motor, Terco({f"{mundo.vencido}/t1/a.pdf"}), mundo.vencido)
    assert _por_tenant(motor, mundo.vencido)["audit_events"] == 2


def test_la_fila_de_sesion_sigue_el_dia_89_y_ya_no_esta_el_dia_91(motor, mundo):
    with motor.begin() as con:
        mundo.sesion(con, f"zz-ses-89-{mundo.s}", f"sub-89-{mundo.s}", None, "vencida", dias_desde_fin=89, persona=False)
        mundo.sesion(con, f"zz-ses-91-{mundo.s}", f"sub-91-{mundo.s}", None, "vencida", dias_desde_fin=91, persona=False)
    informe = purgar(motor, AlmacenEnMemoria(), AHORA)
    assert informe.sesiones_caducadas >= 1
    ids = lambda: {f[0] for f in motor.connect().execute(text(  # noqa: E731
        "SELECT id FROM demo_sesiones WHERE id LIKE :p"), {"p": f"%{mundo.s}"})}
    assert f"zz-ses-89-{mundo.s}" in ids() and f"zz-ses-91-{mundo.s}" not in ids()


def test_la_fila_de_demo_sesiones_queda_sin_tenant_ni_persona(motor, mundo):
    purgar(motor, AlmacenEnMemoria(), AHORA)
    with motor.connect() as con:
        fila = con.execute(text("SELECT tenant_id, persona_usuario_id, vendedor_sub, vendedor_email, iniciada_en, "
                                "terminada_en, motivo_fin FROM demo_sesiones WHERE id = :i"),
                           {"i": mundo.sesion_v}).one()
    assert fila.tenant_id is None and fila.persona_usuario_id is None
    assert (fila.vendedor_sub, fila.vendedor_email) == (mundo.sub_v, mundo.email)
    assert fila.iniciada_en and fila.terminada_en and fila.motivo_fin == "terminar"


def test_no_queda_otro_dato_del_vendedor_fuera_de_su_fila(motor, mundo):
    purgar(motor, AlmacenEnMemoria(), AHORA)
    with motor.connect() as con:
        columnas = con.execute(text(
            "SELECT c.table_name, c.column_name, c.data_type FROM information_schema.columns c "
            "JOIN information_schema.tables t USING (table_schema, table_name) "
            "WHERE c.table_schema = 'public' AND t.table_type = 'BASE TABLE' AND c.table_name <> 'demo_sesiones' "
            "AND c.data_type IN ('character varying', 'text', 'json', 'jsonb')")).all()
        for tabla, columna, _tipo in columnas:
            n = con.execute(select(func.count()).select_from(table(tabla)).where(
                cast(column(columna), String).like(f"%{mundo.email}%"))).scalar_one()
            assert n == 0, f"{tabla}.{columna} conserva el correo del vendedor"
    assert _filas(motor, "SELECT count(*) FROM demo_sesiones WHERE vendedor_email = :e", e=mundo.email) >= 1


# --- Comprobación de 0 filas ---------------------------------------------------------------------------


def _con_resto_silencioso(con, mundo):
    """Una regla hace que DELETE no borre nada en zz_a_padre: la purga «cree» haber terminado."""
    con.execute(text("CREATE RULE zz_sin_borrado AS ON DELETE TO zz_a_padre DO INSTEAD NOTHING"))


def test_la_comprobacion_de_cero_filas_detecta_restos(motor, mundo):
    # Mutación: si comprobar_cero_filas se salta, esta prueba falla (la purga terminaría «bien» con restos).
    # La regla deja intactos padre y, por su FK, también la hija: el borrado por pasadas lo detecta antes
    # o la comprobación después; en ambos casos el job sale con error.
    with motor.begin() as con:
        con.execute(text("ALTER TABLE zz_b_hija DROP CONSTRAINT zz_b_hija_padre_id_fkey"))
        _con_resto_silencioso(con, mundo)
    with pytest.raises(ErrorPurga, match="quedan filas"):
        purgar(motor, AlmacenEnMemoria(), AHORA)
    assert _por_tenant(motor, mundo.vencido)["audit_events"] == 2, "la transacción debía revertirse"
    assert _filas(motor, "SELECT count(*) FROM tenants WHERE id = :t", t=mundo.vencido) == 1


def test_sin_la_comprobacion_los_restos_pasan_en_silencio(motor, mundo, monkeypatch):
    with motor.begin() as con:
        con.execute(text("ALTER TABLE zz_b_hija DROP CONSTRAINT zz_b_hija_padre_id_fkey"))
        _con_resto_silencioso(con, mundo)
    monkeypatch.setattr(modulo_purga, "comprobar_cero_filas", lambda *a, **k: None)  # la mutación
    purgar(motor, AlmacenEnMemoria(), AHORA)  # no lanza
    assert _por_tenant(motor, mundo.vencido)["zz_a_padre"] == 1  # y queda un resto sin avisar


def test_comprobar_cero_filas_rechaza_un_tenant_con_filas(motor, mundo):
    with motor.connect() as con:
        with pytest.raises(ErrorPurga):
            comprobar_cero_filas(con, mundo.vencido, ["zz_a_padre", "audit_events"])


# --- Guardias -------------------------------------------------------------------------------------------


def _mundo_ok(url):
    exigir_demo(url, ENTORNO_DEMO, proyecto=lambda: PROYECTO_DEMO)


@contextmanager
def _base_con_marcador(motor, valor):
    """Base desechable con `public.entorno_marcador` = valor; se salta si el rol no puede crear bases."""
    nombre = f"zz_purga_{uuid.uuid4().hex[:8]}"
    admin = motor.execution_options(isolation_level="AUTOCOMMIT")
    try:
        with admin.connect() as con:
            con.execute(DDL("CREATE DATABASE " + _citar(admin, nombre)))
    except Exception:
        pytest.skip("el rol de pruebas no puede crear bases desechables")
    url = make_url(_url()).set(database=nombre)
    try:
        propio = create_engine(url)
        with propio.begin() as con:
            con.execute(text("CREATE TABLE public.entorno_marcador (valor text NOT NULL)"))
            con.execute(text("INSERT INTO public.entorno_marcador VALUES (:v)"), {"v": valor})
        propio.dispose()
        yield url.render_as_string(hide_password=False)
    finally:
        with admin.connect() as con:
            con.execute(DDL("DROP DATABASE IF EXISTS " + _citar(admin, nombre) + " WITH (FORCE)"))


def test_con_proyecto_demo_y_marcador_demo_la_guardia_deja_pasar(motor):
    with _base_con_marcador(motor, "demo") as url:
        _mundo_ok(url)


def test_el_marcador_pruebas_u_otro_se_rechaza(motor):
    # Mutación: si la guardia vuelve a aceptar 'pruebas' (como base_es_produccion), esta prueba falla.
    for valor in ("pruebas", "produccion", ""):
        with _base_con_marcador(motor, valor) as url:
            with pytest.raises(PurgaRechazada, match="marcador"):
                _mundo_ok(url)


def test_el_job_se_niega_con_la_huella_de_produccion():
    url = "postgresql+psycopg://u:p@127.0.0.1:5432/demo"
    siempre_ok = lambda _u: False  # noqa: E731
    with pytest.raises(PurgaRechazada, match="proyecto de Google Cloud de producción"):
        exigir_demo(url, ENTORNO_DEMO, proyecto=lambda: HUELLA.upper(), comprobar_base=siempre_ok)
    with pytest.raises(PurgaRechazada, match="base es la de producción"):
        exigir_demo(f"postgresql+psycopg://u:p@{HUELLA}.example/db", ENTORNO_DEMO,
                    proyecto=lambda: PROYECTO_DEMO, comprobar_base=siempre_ok)
    with pytest.raises(PurgaRechazada, match="base es la de producción"):
        exigir_demo("postgresql+psycopg://u:p@h/db?host=/cloudsql/evydentia:us-central1:evydentia-production",
                    ENTORNO_DEMO, proyecto=lambda: PROYECTO_DEMO, comprobar_base=siempre_ok)


def test_el_job_se_niega_si_no_es_el_proyecto_de_la_demo():
    url = "postgresql+psycopg://u:p@127.0.0.1:5432/demo"
    ok = lambda _u: False  # noqa: E731
    casos = [
        ({**ENTORNO_DEMO, "APP_ENV": "production"}, lambda: PROYECTO_DEMO, "APP_ENV=demo"),
        ({"APP_ENV": "demo"}, lambda: PROYECTO_DEMO, "HUELLA_PROYECTO_PRODUCCION"),
        (ENTORNO_DEMO, lambda: None, "no se pudo determinar"),
        ({**ENTORNO_DEMO, "PURGA_PROYECTO_DEMO": "otro-proyecto"}, lambda: PROYECTO_DEMO, "no es el de la demo"),
    ]
    for env, proyecto, mensaje in casos:
        with pytest.raises(PurgaRechazada, match=mensaje):
            exigir_demo(url, env, proyecto=proyecto, comprobar_base=ok)
    with pytest.raises(PurgaRechazada, match="marcador"):
        exigir_demo(url, ENTORNO_DEMO, proyecto=lambda: PROYECTO_DEMO, comprobar_base=lambda _u: True)
    with pytest.raises(PurgaRechazada, match="PURGA_DATABASE_URL"):
        exigir_demo("", ENTORNO_DEMO, proyecto=lambda: PROYECTO_DEMO, comprobar_base=ok)


def test_el_punto_de_entrada_sale_con_error_contra_produccion(monkeypatch, capsys):
    from jobs.purga_demo.__main__ import main

    monkeypatch.setenv("APP_ENV", "demo")
    monkeypatch.setenv("HUELLA_PROYECTO_PRODUCCION", HUELLA)
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", HUELLA)
    monkeypatch.setenv("PURGA_DATABASE_URL", "postgresql://u:secreta@127.0.0.1:5432/demo")
    assert main() == 1
    salida = capsys.readouterr().err
    assert "ERROR" in salida and "secreta" not in salida


# --- Almacén S3 ----------------------------------------------------------------------------------------


class ClienteS3Falso:
    def __init__(self, objetos):
        self.objetos = {b: set(k) for b, k in objetos.items()}
        self.borrados = []

    def get_paginator(self, _nombre):
        cliente = self

        class Paginador:
            def paginate(self, Bucket, Prefix):
                claves = sorted(k for k in cliente.objetos[Bucket] if k.startswith(Prefix))
                yield {"Contents": [{"Key": k} for k in claves[:1]]}
                yield {"Contents": [{"Key": k} for k in claves[1:]]} if claves[1:] else {}

        return Paginador()

    def delete_objects(self, Bucket, Delete):
        claves = {o["Key"] for o in Delete["Objects"]}
        self.borrados.append((Bucket, claves))
        self.objetos[Bucket] -= claves


def test_el_almacen_borra_solo_el_prefijo_del_tenant_en_cada_bucket():
    cliente = ClienteS3Falso({"b1": {"t-1/a", "t-1/b", "t-10/a", "t-2/a"}, "b2": {"t-1/c"}})
    almacen = AlmacenS3(["b1", "b2"], cliente=cliente)
    claves = almacen.listar("t-1/")
    assert sorted(claves) == ["b1/t-1/a", "b1/t-1/b", "b2/t-1/c"]
    almacen.borrar(claves)
    assert cliente.objetos == {"b1": {"t-10/a", "t-2/a"}, "b2": set()}
    assert almacen.listar("t-1/") == []


def test_el_almacen_sin_buckets_falla():
    with pytest.raises(ValueError):
        AlmacenS3([])
