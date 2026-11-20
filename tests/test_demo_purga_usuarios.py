# -*- coding: utf-8 -*-
# ¤demo ¤seguridad-tenant
"""DEMO-05b: Purga de personas ficticias de users huérfanas tras purgar demos vencidas.

Corren contra PostgreSQL 16 real del arnés (`TEST_DATABASE_URL`).
Solo valores simulados y correos `.invalid`.

Mutaciones documentadas y verificadas contra PostgreSQL 16 local:
1. `_SQL_PURGAR_USUARIOS`: Si se quita la comprobación de «ningún rol restante»
   (`NOT EXISTS (SELECT 1 FROM user_tenant_roles utr WHERE utr.user_id = users.id)`):
   falla la preservación de usuarios compartidos con la plantilla o demos activas;
   `test_mutacion_sin_comprobacion_roles_restantes_detectada` documenta el fallo.
2. `_SQL_PURGAR_USUARIOS`: Si se quita la comprobación de correo `.invalid`
   (`AND email LIKE '%.invalid'`):
   falla la preservación de usuarios reales (sin `.invalid`);
   `test_mutacion_sin_filtro_invalid_detectada` documenta el fallo.
3. `_SQL_PURGAR_USUARIOS`: Si se quita el filtro de candidatos del paso 1
   (`WHERE id IN :candidatos`):
   falla la preservación de usuarios `.invalid` sin ningún rol (huérfanos ajenos a la demo);
   `test_mutacion_sin_filtro_candidatos_detectada` documenta el fallo.
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

from features.demo.demo_service import PLANTILLA_TENANT_ID
from jobs.purga_demo import usuarios as modulo_usuarios
from jobs.purga_demo.purga import purgar_tenant

AHORA = datetime(2026, 11, 16, 3, 0, tzinfo=timezone.utc)


def _url() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL no configurada")
    return url.replace("postgresql://", "postgresql+psycopg://", 1)


class AlmacenVacio:
    """Almacén ficticio para pruebas de base de datos de usuarios."""

    def listar(self, prefijo: str) -> list[str]:
        return []

    def borrar(self, claves: list[str]) -> None:
        pass


@pytest.fixture
def motor():
    engine = create_engine(_url())
    with engine.begin() as con:
        creado = con.execute(text("SELECT to_regclass('public.entorno_marcador')")).scalar() is None
        if creado:
            con.execute(text("CREATE TABLE public.entorno_marcador (valor text NOT NULL)"))
        if not con.execute(text("SELECT count(*) FROM public.entorno_marcador")).scalar():
            con.execute(text("INSERT INTO public.entorno_marcador VALUES ('pruebas')"))
    yield engine
    if creado:
        with engine.begin() as con:
            con.execute(text("DROP TABLE public.entorno_marcador"))
    engine.dispose()


@pytest.fixture
def ambiente(motor):
    """Contexto de prueba con sufijo único y limpieza al desmontar."""
    s = uuid.uuid4().hex[:8]
    creados_usuarios = []
    creados_tenants = []
    creadas_sesiones = []
    plantilla_creada = False

    class Ambiente:
        sufijo = s

        def insertar_tenant(self, con, tid: str, es_demo: bool = True):
            creada = con.execute(
                text(
                    "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, es_demo) "
                    "VALUES (:i, :n, :n, :ruc, :demo) ON CONFLICT (id) DO NOTHING RETURNING id"
                ),
                {
                    "i": tid,
                    "n": f"Tenant {tid}",
                    "ruc": f"{uuid.uuid4().int % 10**13:013d}",
                    "demo": es_demo,
                },
            ).first()
            if tid == PLANTILLA_TENANT_ID and creada is not None:
                nonlocal plantilla_creada
                plantilla_creada = True
            creados_tenants.append(tid)

        def insertar_usuario(self, con, uid: str, email: str, nombre: str = "Persona Prueba"):
            con.execute(
                text("INSERT INTO users (id, email, nombre) VALUES (:i, :e, :n)"),
                {"i": uid, "e": email, "n": nombre},
            )
            creados_usuarios.append(uid)

        def insertar_rol(self, con, rid: str, uid: str, tid: str, role: str = "coordinador"):
            con.execute(
                text(
                    "INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) "
                    "VALUES (:i, :u, :t, :r)"
                ),
                {"i": rid, "u": uid, "t": tid, "r": role},
            )

        def insertar_sesion(
            self,
            con,
            sid: str,
            tid: str,
            persona_id: str | None,
            estado: str = "vencida",
            dias_fin: int = 1,
        ):
            fin = None if estado == "activa" else AHORA - timedelta(days=dias_fin)
            con.execute(
                text(
                    "INSERT INTO demo_sesiones (id, vendedor_sub, vendedor_email, tenant_id, "
                    "persona_usuario_id, estado, iniciada_en, ultima_actividad, terminada_en, motivo_fin) "
                    "VALUES (:i, :s, :e, :t, :p, :est, :ini, :ini, :fin, :m)"
                ),
                {
                    "i": sid,
                    "s": f"sub-{s}",
                    "e": f"vendedor-{s}@vendedores.invalid",
                    "t": tid,
                    "p": persona_id,
                    "est": estado,
                    "ini": AHORA - timedelta(days=10),
                    "fin": fin,
                    "m": None if fin is None else "terminar",
                },
            )
            creadas_sesiones.append(sid)

        def usuario_existe(self, uid: str) -> bool:
            with motor.connect() as c:
                return (
                    c.execute(
                        text("SELECT count(*) FROM users WHERE id = :u"), {"u": uid}
                    ).scalar_one()
                    > 0
                )

        def roles_de_usuario(self, uid: str) -> list[tuple[str, str]]:
            with motor.connect() as c:
                return [
                    (r[0], r[1])
                    for r in c.execute(
                        text("SELECT tenant_id, role FROM user_tenant_roles WHERE user_id = :u"),
                        {"u": uid},
                    ).all()
                ]

    amb = Ambiente()
    yield amb

    with motor.begin() as con:
        if creadas_sesiones:
            for sid in creadas_sesiones:
                con.execute(text("DELETE FROM demo_sesiones WHERE id = :i"), {"i": sid})
        if creados_usuarios:
            for uid in creados_usuarios:
                con.execute(text("DELETE FROM user_tenant_roles WHERE user_id = :u"), {"u": uid})
                con.execute(text("DELETE FROM users WHERE id = :u"), {"u": uid})
        if creados_tenants:
            for tid in creados_tenants:
                if tid != PLANTILLA_TENANT_ID:
                    con.execute(text("DELETE FROM tenants WHERE id = :i"), {"i": tid})
        if plantilla_creada:
            con.execute(text("DELETE FROM tenants WHERE id = :i"), {"i": PLANTILLA_TENANT_ID})


# --- Árbitros de DEMO-05b -----------------------------------------------------------------------------


def test_se_borra_el_usuario_invalid_cuyos_roles_eran_solo_de_demos_vencidas(motor, ambiente):
    """Árbitro 1: Se borra el usuario .invalid cuyos roles eran solo de demos vencidas."""
    s = ambiente.sufijo
    tid = f"zz-demo-vencida-{s}"
    uid = f"zz-usr-vencido-{s}"
    with motor.begin() as con:
        ambiente.insertar_tenant(con, tid, es_demo=True)
        ambiente.insertar_usuario(con, uid, f"persona-{s}@cooperativa-demo.invalid")
        ambiente.insertar_rol(con, f"zz-utr-{s}", uid, tid, "coordinador")
        ambiente.insertar_sesion(con, f"zz-ses-{s}", tid, persona_id=uid, estado="vencida")

    assert ambiente.usuario_existe(uid)
    purgar_tenant(motor, AlmacenVacio(), tid)
    assert not ambiente.usuario_existe(uid), "el usuario .invalid debía ser purgado de users"


def test_se_conserva_un_usuario_real_correo_sin_invalid_con_rol_en_demo_vencida(motor, ambiente):
    """Árbitro 2: Se conserva un usuario real (correo sin .invalid) con un rol en una demo vencida."""
    s = ambiente.sufijo
    tid = f"zz-demo-vencida-{s}"
    uid = f"zz-usr-real-{s}"
    with motor.begin() as con:
        ambiente.insertar_tenant(con, tid, es_demo=True)
        ambiente.insertar_usuario(con, uid, f"consultor-{s}@empresa-real.com")
        ambiente.insertar_rol(con, f"zz-utr-{s}", uid, tid, "auditor")
        ambiente.insertar_sesion(con, f"zz-ses-{s}", tid, persona_id=uid, estado="vencida")

    assert ambiente.usuario_existe(uid)
    purgar_tenant(motor, AlmacenVacio(), tid)
    assert ambiente.usuario_existe(uid), "el usuario real no debe ser purgado de users"
    assert ambiente.roles_de_usuario(uid) == [], "los roles en la demo vencida sí se purgan"


def test_se_conserva_un_usuario_con_un_rol_en_la_plantilla(motor, ambiente):
    """Árbitro 3: Se conserva un usuario con un rol en la plantilla."""
    s = ambiente.sufijo
    tid = f"zz-demo-vencida-{s}"
    uid = f"zz-usr-plantilla-{s}"
    with motor.begin() as con:
        ambiente.insertar_tenant(con, PLANTILLA_TENANT_ID, es_demo=True)
        ambiente.insertar_tenant(con, tid, es_demo=True)
        ambiente.insertar_usuario(con, uid, f"plantilla-{s}@cooperativa-demo.invalid")
        # ORG-13: dpo e implementador pueden pertenecer a múltiples organizaciones
        ambiente.insertar_rol(con, f"zz-utr-p-{s}", uid, PLANTILLA_TENANT_ID, "dpo")
        ambiente.insertar_rol(con, f"zz-utr-v-{s}", uid, tid, "dpo")
        ambiente.insertar_sesion(con, f"zz-ses-{s}", tid, persona_id=uid, estado="vencida")

    assert ambiente.usuario_existe(uid)
    purgar_tenant(motor, AlmacenVacio(), tid)
    assert ambiente.usuario_existe(uid), "el usuario con rol en la plantilla debe conservarse"
    assert ambiente.roles_de_usuario(uid) == [(PLANTILLA_TENANT_ID, "dpo")]


def test_se_conserva_un_invalid_con_un_rol_en_una_demo_activa(motor, ambiente):
    """Árbitro 4: Se conserva un .invalid con un rol en una demo activa."""
    s = ambiente.sufijo
    tid_v = f"zz-demo-vencida-{s}"
    tid_a = f"zz-demo-activa-{s}"
    uid = f"zz-usr-activo-{s}"
    with motor.begin() as con:
        ambiente.insertar_tenant(con, tid_v, es_demo=True)
        ambiente.insertar_tenant(con, tid_a, es_demo=True)
        ambiente.insertar_usuario(con, uid, f"activo-{s}@cooperativa-demo.invalid")
        ambiente.insertar_rol(con, f"zz-utr-v-{s}", uid, tid_v, "dpo")
        ambiente.insertar_rol(con, f"zz-utr-a-{s}", uid, tid_a, "dpo")
        ambiente.insertar_sesion(con, f"zz-ses-v-{s}", tid_v, persona_id=uid, estado="vencida")
        ambiente.insertar_sesion(con, f"zz-ses-a-{s}", tid_a, persona_id=uid, estado="activa")

    assert ambiente.usuario_existe(uid)
    purgar_tenant(motor, AlmacenVacio(), tid_v)
    assert ambiente.usuario_existe(uid), "el usuario con rol en demo activa debe conservarse"
    assert ambiente.roles_de_usuario(uid) == [(tid_a, "dpo")]


def test_se_conserva_un_invalid_sin_ningun_rol(motor, ambiente):
    """Árbitro 5: Se conserva un .invalid sin ningún rol (no estaba en candidatos del paso 1)."""
    s = ambiente.sufijo
    tid = f"zz-demo-vencida-{s}"
    uid_demo = f"zz-usr-demo-{s}"
    uid_huerfano = f"zz-usr-huerfano-{s}"
    with motor.begin() as con:
        ambiente.insertar_tenant(con, tid, es_demo=True)
        ambiente.insertar_usuario(con, uid_demo, f"persona-{s}@cooperativa-demo.invalid")
        ambiente.insertar_rol(con, f"zz-utr-{s}", uid_demo, tid, "coordinador")
        ambiente.insertar_sesion(con, f"zz-ses-{s}", tid, persona_id=uid_demo, estado="vencida")
        # Usuario .invalid sin ningún rol ni relación con la demo
        ambiente.insertar_usuario(con, uid_huerfano, f"huerfano-{s}@otro.invalid")

    assert ambiente.usuario_existe(uid_demo)
    assert ambiente.usuario_existe(uid_huerfano)

    purgar_tenant(motor, AlmacenVacio(), tid)

    assert not ambiente.usuario_existe(uid_demo), "el usuario de la demo sí se purga"
    assert ambiente.usuario_existe(uid_huerfano), "el .invalid sin roles no se debe tocar"


def test_se_conserva_invalid_si_otra_sesion_de_demo_lo_apunta(motor, ambiente):
    """Guarda adicional: si otra sesión aún apunta al usuario, no se borra."""
    s = ambiente.sufijo
    tid_v = f"zz-demo-vencida-{s}"
    tid_otra = f"zz-demo-otra-{s}"
    uid = f"zz-usr-sesion-{s}"
    with motor.begin() as con:
        ambiente.insertar_tenant(con, tid_v, es_demo=True)
        ambiente.insertar_tenant(con, tid_otra, es_demo=True)
        ambiente.insertar_usuario(con, uid, f"persona-{s}@cooperativa-demo.invalid")
        ambiente.insertar_rol(con, f"zz-utr-{s}", uid, tid_v, "coordinador")
        ambiente.insertar_sesion(con, f"zz-ses-v-{s}", tid_v, persona_id=uid, estado="vencida")
        # Otra sesión en tid_otra apunta a este usuario
        ambiente.insertar_sesion(con, f"zz-ses-o-{s}", tid_otra, persona_id=uid, estado="activa")

    purgar_tenant(motor, AlmacenVacio(), tid_v)
    assert ambiente.usuario_existe(uid), "mientras demo_sesiones lo apunte, no se borra"


def test_usuario_con_roles_en_dos_demos_vencidas_se_borra_al_purgar_la_segunda(motor, ambiente):
    """Un usuario .invalid que solo pertenecía a demos vencidas se borra cuando cae la última."""
    s = ambiente.sufijo
    tid1 = f"zz-demo-v1-{s}"
    tid2 = f"zz-demo-v2-{s}"
    uid = f"zz-usr-multidemo-{s}"
    with motor.begin() as con:
        ambiente.insertar_tenant(con, tid1, es_demo=True)
        ambiente.insertar_tenant(con, tid2, es_demo=True)
        ambiente.insertar_usuario(con, uid, f"multidemo-{s}@cooperativa-demo.invalid")
        # ORG-13: dpo puede pertenecer a múltiples organizaciones
        ambiente.insertar_rol(con, f"zz-utr-1-{s}", uid, tid1, "dpo")
        ambiente.insertar_rol(con, f"zz-utr-2-{s}", uid, tid2, "dpo")
        ambiente.insertar_sesion(con, f"zz-ses-1-{s}", tid1, persona_id=uid, estado="vencida")
        ambiente.insertar_sesion(con, f"zz-ses-2-{s}", tid2, persona_id=uid, estado="vencida")

    # Tras purgar la primera demo, aún tiene rol en la segunda: NO se borra
    purgar_tenant(motor, AlmacenVacio(), tid1)
    assert ambiente.usuario_existe(uid), "aún tiene rol en la segunda demo vencida"
    assert ambiente.roles_de_usuario(uid) == [(tid2, "dpo")]

    # Tras purgar la segunda demo, ya no le queda ningún rol: SE BORRA
    purgar_tenant(motor, AlmacenVacio(), tid2)
    assert not ambiente.usuario_existe(uid), "sin roles restantes en ninguna demo, se purga"


# --- Mutaciones documentadas --------------------------------------------------------------------------


def test_mutacion_sin_comprobacion_roles_restantes_detectada(motor, ambiente, monkeypatch):
    """Mutación común: quitar la comprobación de «ningún rol restante».

    Al quitar NOT EXISTS (SELECT 1 FROM user_tenant_roles...), el usuario con rol en la plantilla
    habría sido borrado erróneamente de users. Esta prueba comprueba la sensibilidad frente a esa mutación.
    """
    s = ambiente.sufijo
    tid = f"zz-demo-vencida-{s}"
    uid = f"zz-usr-plantilla-mut-{s}"
    with motor.begin() as con:
        ambiente.insertar_tenant(con, PLANTILLA_TENANT_ID, es_demo=True)
        ambiente.insertar_tenant(con, tid, es_demo=True)
        ambiente.insertar_usuario(con, uid, f"plantilla-{s}@cooperativa-demo.invalid")
        ambiente.insertar_rol(con, f"zz-utr-p-{s}", uid, PLANTILLA_TENANT_ID, "dpo")
        ambiente.insertar_rol(con, f"zz-utr-v-{s}", uid, tid, "dpo")
        ambiente.insertar_sesion(con, f"zz-ses-{s}", tid, persona_id=uid, estado="vencida")

    # 1. Con código real: el usuario se conserva
    # Primero verificamos la lectura de candidatos
    with motor.connect() as con:
        cands = modulo_usuarios.leer_candidatos_usuarios(con, tid)
    assert uid in cands

    # 1. Con el código real: purgar no toca al usuario y no viola FKs
    with motor.begin() as con:
        con.execute(text("DELETE FROM user_tenant_roles WHERE tenant_id = :t"), {"t": tid})
        con.execute(text("UPDATE demo_sesiones SET persona_usuario_id = NULL WHERE tenant_id = :t"), {"t": tid})
        borrados_real = modulo_usuarios.purgar_usuarios_ficticios(con, cands)
    assert borrados_real == 0, "el código real protege al usuario con roles restantes"
    assert ambiente.usuario_existe(uid), "el usuario sigue en users"

    # 2. Mutamos la consulta SQL quitando la comprobación de roles restantes
    sql_mutada = (
        "DELETE FROM users "
        "WHERE id IN :candidatos "
        "AND email LIKE '%.invalid' "
        "AND NOT EXISTS (SELECT 1 FROM demo_sesiones ds WHERE ds.persona_usuario_id = users.id)"
    )
    monkeypatch.setattr(modulo_usuarios, "_SQL_PURGAR_USUARIOS", sql_mutada)

    # Con la mutación: intentaría borrar al usuario aunque tenga rol en la plantilla,
    # violando la clave foránea user_tenant_roles_user_id_fkey
    with pytest.raises(IntegrityError):
        with motor.begin() as con:
            modulo_usuarios.purgar_usuarios_ficticios(con, cands)


def test_mutacion_sin_filtro_invalid_detectada(motor, ambiente, monkeypatch):
    """Mutación: quitar la comprobación de correo .invalid.

    Al quitar `AND email LIKE '%.invalid'`, el usuario real con rol en demo vencida
    habría sido borrado de users.
    """
    s = ambiente.sufijo
    tid = f"zz-demo-vencida-{s}"
    uid = f"zz-usr-real-mut-{s}"
    with motor.begin() as con:
        ambiente.insertar_tenant(con, tid, es_demo=True)
        ambiente.insertar_usuario(con, uid, f"real-{s}@empresa-real.com")
        ambiente.insertar_rol(con, f"zz-utr-{s}", uid, tid, "coordinador")
        ambiente.insertar_sesion(con, f"zz-ses-{s}", tid, persona_id=uid, estado="vencida")

    with motor.connect() as con:
        cands = modulo_usuarios.leer_candidatos_usuarios(con, tid)
    assert uid in cands

    sql_mutada = (
        "DELETE FROM users "
        "WHERE id IN :candidatos "
        "AND NOT EXISTS (SELECT 1 FROM user_tenant_roles utr WHERE utr.user_id = users.id) "
        "AND NOT EXISTS (SELECT 1 FROM demo_sesiones ds WHERE ds.persona_usuario_id = users.id)"
    )
    monkeypatch.setattr(modulo_usuarios, "_SQL_PURGAR_USUARIOS", sql_mutada)

    with motor.begin() as con:
        con.execute(text("DELETE FROM user_tenant_roles WHERE tenant_id = :t"), {"t": tid})
        con.execute(text("UPDATE demo_sesiones SET persona_usuario_id = NULL WHERE tenant_id = :t"), {"t": tid})
        borrados = modulo_usuarios.purgar_usuarios_ficticios(con, cands)

    assert borrados == 1, "la mutación borró al usuario real (demuestra que la guardia .invalid es crítica)"


def test_mutacion_sin_filtro_candidatos_detectada(motor, ambiente, monkeypatch):
    """Mutación: no filtrar por los candidatos leídos en el paso 1.

    Si se borra cualquier usuario .invalid sin roles en vez de solo los candidatos del tenant,
    un .invalid huérfano ajeno a la demo sería borrado indebidamente.
    """
    s = ambiente.sufijo
    uid_ajeno = f"zz-usr-ajeno-mut-{s}"
    with motor.begin() as con:
        ambiente.insertar_usuario(con, uid_ajeno, f"ajeno-{s}@otro.invalid")

    # El usuario ajeno no está en ningún tenant, por lo que candidatos está vacío
    candidatos_demo = [f"zz-otro-{s}"]

    # Con el código real, candidatos_demo no incluye a uid_ajeno, por lo que no se borra
    with motor.begin() as con:
        borrados = modulo_usuarios.purgar_usuarios_ficticios(con, candidatos_demo)
    assert borrados == 0
    assert ambiente.usuario_existe(uid_ajeno)

    # Si se mutara para borrar todo .invalid sin roles ignorando candidatos:
    sql_mutada = (
        "DELETE FROM users "
        "WHERE email LIKE '%.invalid' "
        "AND NOT EXISTS (SELECT 1 FROM user_tenant_roles utr WHERE utr.user_id = users.id) "
        "AND NOT EXISTS (SELECT 1 FROM demo_sesiones ds WHERE ds.persona_usuario_id = users.id)"
    )
    with motor.begin() as con:
        borrados_mut = con.execute(text(sql_mutada)).rowcount
    assert borrados_mut >= 1, "la mutación borró al huérfano ajeno (demuestra que el paso 1 es crítico)"


# --- DEMO-05c: casos añadidos; las pruebas de DEMO-05b de arriba no cambian ------------------------------

_SQL_POLITICAS = (Path(__file__).resolve().parent.parent / "jobs" / "purga_demo" / "politicas_purga.sql").read_text(
    encoding="utf-8")


def _definicion_persona_ficticia() -> str:
    """El `CREATE OR REPLACE FUNCTION` de politicas_purga.sql, sin los GRANT al rol (que es global)."""
    return _SQL_POLITICAS.split("-- [es_persona_ficticia]", 1)[1].split("-- [/es_persona_ficticia]", 1)[0]


def _ejecutar_sql(con, sql: str) -> None:
    with con.connection.dbapi_connection.cursor() as cursor:
        cursor.execute(sql)


@pytest.fixture(autouse=True)
def persona_ficticia_instalada():
    """DEMO-05c: `usuarios.py` pregunta a `es_persona_ficticia`, que exige el marcador `demo`.

    Las pruebas de DEMO-05b confirman sus transacciones, así que esta base de pruebas recibe la función (sin
    permisos para el rol, que es global) y el marcador `demo`, y se le quitan al terminar si no estaban.
    Si la base ya tiene otro marcador, no se cambia: las pruebas se saltan.
    """
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        yield
        return
    engine = create_engine(url.replace("postgresql://", "postgresql+psycopg://", 1))
    with engine.begin() as con:
        marcador_creado = con.execute(text("SELECT to_regclass('public.entorno_marcador')")).scalar() is None
        if marcador_creado:
            con.execute(text("CREATE TABLE public.entorno_marcador (valor text NOT NULL)"))
            con.execute(text("INSERT INTO public.entorno_marcador VALUES ('demo')"))
        valores = [v for (v,) in con.execute(text("SELECT valor FROM public.entorno_marcador"))]
        funcion_creada = con.execute(text(
            "SELECT to_regprocedure('public.es_persona_ficticia(character varying)')")).scalar() is None
        if valores == ["demo"] and funcion_creada:
            _ejecutar_sql(con, _definicion_persona_ficticia())
            con.execute(text("REVOKE ALL ON FUNCTION public.es_persona_ficticia(character varying) FROM PUBLIC"))
    try:
        if valores != ["demo"]:
            pytest.skip("la base de pruebas tiene un marcador distinto de 'demo'; no se cambia")
        yield
    finally:
        with engine.begin() as con:
            if funcion_creada and valores == ["demo"]:
                con.execute(text("DROP FUNCTION IF EXISTS public.es_persona_ficticia(character varying)"))
            if marcador_creado:
                con.execute(text("DROP TABLE IF EXISTS public.entorno_marcador"))
        engine.dispose()


def test_persona_ficticia_se_borra_sin_update():
    """DEMO-05c §5: la persona ficticia de una demo vencida se borra como `purga_demo`, sin UPDATE.

    Su sesión sigue nombrándola con `tenant_id` nulo hasta que el borrado de la persona la vacía por
    `ON DELETE SET NULL`. Todo en una transacción revertida: el rol `purga_demo` es global (R11).
    Mutación m9: sin `AND ds.tenant_id IS NOT NULL` en `usuarios.py`, la sesión ya sin organización protege a
    la persona y falla `test_se_borra_el_usuario_invalid_cuyos_roles_eran_solo_de_demos_vencidas`.
    """
    engine = create_engine(_url())
    con = engine.connect()
    transaccion = con.begin()
    try:
        s = uuid.uuid4().hex[:8]
        tid, uid, sid = f"zz-c5-demo-{s}", f"zz-c5-persona-{s}", f"zz-c5-ses-{s}"
        if not con.execute(text("SELECT 1 FROM pg_roles WHERE rolname = 'purga_demo'")).first():
            con.execute(text("CREATE ROLE purga_demo NOLOGIN"))
        con.execute(text("DELETE FROM public.entorno_marcador"))
        con.execute(text("INSERT INTO public.entorno_marcador VALUES ('demo')"))
        _ejecutar_sql(con, _SQL_POLITICAS)
        con.execute(text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, es_demo) "
                         "VALUES (:i, 'Demo', 'Demo', :r, true)"), {"i": tid, "r": f"{uuid.uuid4().int % 10**13:013d}"})
        con.execute(text("INSERT INTO users (id, email, nombre) VALUES (:i, :e, 'Persona Demo')"),
                    {"i": uid, "e": f"persona-{s}@cooperativa-demo.invalid"})
        con.execute(text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) "
                         "VALUES (:i, :u, :t, 'coordinador')"), {"i": f"zz-c5-utr-{s}", "u": uid, "t": tid})
        con.execute(text(
            "INSERT INTO demo_sesiones (id, vendedor_sub, vendedor_email, tenant_id, persona_usuario_id, estado, "
            "iniciada_en, ultima_actividad, terminada_en, motivo_fin) "
            "VALUES (:i, :sub, :e, :t, :p, 'vencida', :ini, :ini, :fin, 'terminar')"),
            {"i": sid, "sub": f"sub-{s}", "e": f"vendedor-{s}@vendedores.invalid", "t": tid, "p": uid,
             "ini": AHORA - timedelta(days=10), "fin": AHORA - timedelta(days=1)})

        con.execute(text("SET ROLE purga_demo"))
        assert not con.execute(text("SELECT has_table_privilege('purga_demo', 'demo_sesiones', 'UPDATE')")).scalar()
        purgar_tenant(con, AlmacenVacio(), tid)
        con.execute(text("RESET ROLE"))

        assert con.execute(text("SELECT count(*) FROM users WHERE id = :u"), {"u": uid}).scalar_one() == 0
        assert con.execute(text("SELECT tenant_id, persona_usuario_id FROM demo_sesiones WHERE id = :i"),
                           {"i": sid}).one() == (None, None)
    finally:
        transaccion.rollback()
        con.close()
        engine.dispose()
