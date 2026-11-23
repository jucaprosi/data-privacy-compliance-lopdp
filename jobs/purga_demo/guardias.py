# -*- coding: utf-8 -*-
# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤demo ¤seguridad
"""Guardias del job: solo corre en el proyecto y la base de la demo, nunca en producción."""
from __future__ import annotations

import os
from typing import Callable, Mapping, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from app_core.entorno.guardias import proyecto_en_ejecucion
from app_core.huellas_produccion import apunta_a_produccion, base_es_produccion

SEGUNDOS_CONEXION = 5
MARCADOR_DEMO = "demo"


class PurgaRechazada(RuntimeError):
    """El job se niega a correr; el mensaje nombra la causa y nunca incluye la URL de la base."""


def _base_sin_marcador_de_entorno(url: str) -> bool:
    """Abre una conexión síncrona y pregunta `base_es_produccion`. Un fallo cuenta como producción."""
    try:
        destino = make_url(url)
        if not destino.drivername.startswith("postgresql"):
            return True
        motor = create_engine(destino.set(drivername="postgresql+psycopg"),
                              connect_args={"connect_timeout": SEGUNDOS_CONEXION}, pool_pre_ping=False)
        try:
            with motor.connect() as conexion:
                if base_es_produccion(conexion):
                    return True
                # Más estricto que SEC-20: la purga solo corre con el marcador exacto 'demo', no con 'pruebas'.
                valores = [v for (v,) in conexion.execute(text("SELECT valor FROM public.entorno_marcador LIMIT 2"))]
                return valores != [MARCADOR_DEMO]
        finally:
            motor.dispose()
    except Exception:
        return True


def exigir_demo(
    url: Optional[str],
    entorno: Optional[Mapping[str, str]] = None,
    proyecto: Optional[Callable[[], Optional[str]]] = None,
    comprobar_base: Callable[[str], bool] = _base_sin_marcador_de_entorno,
) -> None:
    """Lanza `PurgaRechazada` salvo que `APP_ENV=demo`, el proyecto sea el de la demo y la base no sea producción."""
    env = os.environ if entorno is None else entorno
    if env.get("APP_ENV", "").strip().lower() != "demo":
        raise PurgaRechazada("la purga solo corre con APP_ENV=demo.")
    huella = env.get("HUELLA_PROYECTO_PRODUCCION", "").strip().lower()
    if not huella:
        raise PurgaRechazada("falta HUELLA_PROYECTO_PRODUCCION; no se puede descartar el proyecto de producción.")
    actual = ((proyecto() if proyecto else proyecto_en_ejecucion()) or "").strip().lower()
    if not actual:
        raise PurgaRechazada("no se pudo determinar el proyecto de Google Cloud donde corre el job.")
    if actual == huella:
        raise PurgaRechazada("el job corre en el proyecto de Google Cloud de producción.")
    esperado = env.get("PURGA_PROYECTO_DEMO", "").strip().lower()
    if esperado and actual != esperado:
        raise PurgaRechazada("el proyecto de Google Cloud no es el de la demo.")
    if not url or not url.strip():
        raise PurgaRechazada("falta PURGA_DATABASE_URL.")
    if huella in url.lower() or apunta_a_produccion(url, env):
        raise PurgaRechazada("la base es la de producción.")
    if comprobar_base(url):
        raise PurgaRechazada("la base no tiene el marcador de entorno exacto 'demo'.")


# --- DEMO-05c: políticas del rol de purga, sin BYPASSRLS --------------------------------------------------

ROL_PURGA = "purga_demo"
FUNCION_PERSONA = "es_persona_ficticia"
#: Tablas que la purga toca sin ser «tablas con tenant_id» de la lista general.
TABLAS_FIJAS = ("tenants", "demo_sesiones", "users")
#: Permisos por columnas (R5 y R6): `vendedor_sub`, `vendedor_email` y `users.email` quedan fuera.
COLUMNAS_PERMITIDAS = {
    "demo_sesiones": ("id", "tenant_id", "estado", "terminada_en", "persona_usuario_id"),
    "users": ("id",),
}

_SQL_ROL = (
    "SELECT rolsuper OR rolbypassrls OR rolcreaterole OR rolcreatedb FROM pg_catalog.pg_roles "
    "WHERE rolname = :rol"
)
_SQL_ESTADO_TABLAS = (
    "SELECT c.relname, c.relrowsecurity, "
    "has_table_privilege(:rol, c.oid, 'SELECT') AS lee, has_table_privilege(:rol, c.oid, 'DELETE') AS borra, "
    "EXISTS (SELECT 1 FROM pg_catalog.pg_policies p WHERE p.schemaname = 'public' AND p.tablename = c.relname "
    "        AND CAST(:rol AS name) = ANY (p.roles) AND p.cmd = 'SELECT') AS politica_lee, "
    "EXISTS (SELECT 1 FROM pg_catalog.pg_policies p WHERE p.schemaname = 'public' AND p.tablename = c.relname "
    "        AND CAST(:rol AS name) = ANY (p.roles) AND p.cmd = 'DELETE') AS politica_borra "
    "FROM pg_catalog.pg_class c WHERE c.relnamespace = 'public'::regnamespace AND c.relname = ANY (:tablas)"
)
_SQL_COLUMNA = "SELECT has_column_privilege(:rol, CAST(:tabla AS regclass), :columna, 'SELECT')"
_SQL_FUNCION = (
    "SELECT p.prosecdef, p.proconfig, "
    "(p.proacl IS NULL OR EXISTS (SELECT 1 FROM aclexplode(p.proacl) a "
    "                             WHERE a.grantee = 0 AND a.privilege_type = 'EXECUTE')) AS publica, "
    "has_function_privilege(:rol, p.oid, 'EXECUTE') AS ejecuta "
    "FROM pg_catalog.pg_proc p WHERE p.pronamespace = 'public'::regnamespace AND p.proname = :funcion"
)
#: Funciones que llaman las políticas que alcanzan a `purga_demo` (las suyas y las `TO public`) en las tablas
#: que purga y sobre las que no tiene EXECUTE: PostgreSQL rechazaría la sentencia entera.
_SQL_FUNCIONES_DE_POLITICAS = (
    "SELECT DISTINCT p.oid::regprocedure::text FROM pg_catalog.pg_policy pol "
    "JOIN pg_catalog.pg_depend d ON d.classid = 'pg_catalog.pg_policy'::regclass AND d.objid = pol.oid "
    "     AND d.refclassid = 'pg_catalog.pg_proc'::regclass "
    "JOIN pg_catalog.pg_proc p ON p.oid = d.refobjid "
    "JOIN pg_catalog.pg_class c ON c.oid = pol.polrelid AND c.relnamespace = 'public'::regnamespace "
    "WHERE pol.polcmd IN ('r', 'd', '*') AND c.relname = ANY (:tablas) "
    "AND (0 = ANY (pol.polroles) OR (SELECT oid FROM pg_catalog.pg_roles WHERE rolname = :rol) = ANY (pol.polroles)) "
    "AND NOT has_function_privilege(:rol, p.oid, 'EXECUTE') ORDER BY 1"
)


def _tablas_vigiladas(con) -> list[str]:
    from .purga import TABLAS_INMUTABLES, tablas_con_tenant  # import tardío: purga no depende de las guardias

    # Las inmutables las borra la función (DEMO-05d), pero `purga_demo` sigue necesitando SELECT y sus políticas
    # para comprobar que quedan con 0 filas.
    return sorted(set(tablas_con_tenant(con)) | set(TABLAS_FIJAS) | set(TABLAS_INMUTABLES))


def tablas_sin_rls(con) -> list[str]:
    """Tablas que toca la purga y no tienen RLS: las protegen los permisos y el filtro del código (R3, R4)."""
    filas = con.execute(text(_SQL_ESTADO_TABLAS), {"rol": ROL_PURGA, "tablas": _tablas_vigiladas(con)}).all()
    return sorted(f.relname for f in filas if not f.relrowsecurity)


def faltan_politicas(con) -> list[str]:
    """Lo que le falta a la base para que `purga_demo` purgue sin BYPASSRLS (R9). Vacío si está completa.

    Solo lee el catálogo; no confirma nada. Falla cerrada: cada carencia sale con su nombre.
    """
    if con.execute(text(_SQL_ROL), {"rol": ROL_PURGA}).first() is None:
        return [f"rol {ROL_PURGA}"]
    faltan: list[str] = []
    if con.execute(text(_SQL_ROL), {"rol": ROL_PURGA}).scalar_one():
        faltan.append(f"rol {ROL_PURGA} con privilegios especiales")
    vigiladas = _tablas_vigiladas(con)
    filas = {f.relname: f for f in con.execute(text(_SQL_ESTADO_TABLAS), {"rol": ROL_PURGA, "tablas": vigiladas})}
    for tabla in vigiladas:
        fila = filas.get(tabla)
        if fila is None:
            faltan.append(tabla)
            continue
        columnas = COLUMNAS_PERMITIDAS.get(tabla)
        if columnas is None:
            lee = fila.lee
        else:
            lee = all(con.execute(text(_SQL_COLUMNA), {"rol": ROL_PURGA, "tabla": f"public.{tabla}",
                                                       "columna": c}).scalar_one() for c in columnas)
        con_politicas = fila.politica_lee and fila.politica_borra
        if not (lee and fila.borra) or (fila.relrowsecurity and not con_politicas):
            faltan.append(tabla)
    funcion = con.execute(text(_SQL_FUNCION), {"rol": ROL_PURGA, "funcion": FUNCION_PERSONA}).all()
    if len(funcion) != 1:
        faltan.append(FUNCION_PERSONA)
    else:
        f = funcion[0]
        if not f.prosecdef or not any(str(o).startswith("search_path=") for o in (f.proconfig or [])):
            faltan.append(f"{FUNCION_PERSONA} (SECURITY DEFINER y search_path fijo)")
        if f.publica:
            faltan.append(f"{FUNCION_PERSONA} (EXECUTE para PUBLIC)")
        if not f.ejecuta:
            faltan.append(f"{FUNCION_PERSONA} (EXECUTE para {ROL_PURGA})")
    if con.execute(text(_SQL_COLUMNA), {"rol": ROL_PURGA, "tabla": "public.users", "columna": "email"}).scalar_one():
        faltan.append("users.email (SELECT para purga_demo)")
    for (firma,) in con.execute(text(_SQL_FUNCIONES_DE_POLITICAS), {"rol": ROL_PURGA, "tablas": vigiladas}):
        faltan.append(f"{firma} (EXECUTE para {ROL_PURGA}, la llama una política)")
    return faltan


# --- DEMO-05d: función de las tablas inmutables ------------------------------------------------------------

#: (tabla, trigger) que la función desactiva y rehabilita: la lista literal y cerrada de DEMO-05d §1.
TRIGGERS_INMUTABLES = frozenset({
    ("biblioteca_documentos_historial", "biblioteca_documento_historial_inmutable"),
    ("biblioteca_descargas", "biblioteca_descargas_inmutable"),
    ("biblioteca_eventos_documento", "biblioteca_evento_inmutable"),
    ("dpo_consultas_mensajes", "trg_dpo_consultas_mensajes_solo_agrega"),
    ("dpo_consultas", "trg_dpo_consultas_inmutable_tras_cierre"),
})
#: (tabla, trigger) de DELETE sobre una tabla con `tenant_id` que se sabe que no lanzan. Medido en la
#: PostgreSQL 16 con todas las migraciones de `origin/main` 3f0d147f: ninguno.
TRIGGERS_DELETE_SIN_EXCEPCION: frozenset[tuple[str, str]] = frozenset()

#: Triggers de usuario que se disparan en DELETE (bit 8 de `tgtype`) sobre tablas con `tenant_id`.
_SQL_TRIGGERS_DELETE = (
    "SELECT c.relname, t.tgname FROM pg_catalog.pg_trigger t "
    "JOIN pg_catalog.pg_class c ON c.oid = t.tgrelid "
    "WHERE NOT t.tgisinternal AND (t.tgtype & 8) <> 0 AND c.relnamespace = 'public'::regnamespace "
    "AND EXISTS (SELECT 1 FROM pg_catalog.pg_attribute a WHERE a.attrelid = c.oid AND a.attname = 'tenant_id' "
    "            AND a.attnum > 0 AND NOT a.attisdropped) "
    "ORDER BY 1, 2"
)


def falta_funcion_inmutables(con) -> list[str]:
    """Lo que impide borrar las tablas inmutables con la función de DEMO-05d (R6). Vacío si está completa.

    Solo lee el catálogo. Un trigger de DELETE desconocido sobre una tabla con `tenant_id` cuenta como falta:
    la función no lo desactiva y la purga fallaría a mitad, o dejaría filas que la lista no cubre.
    """
    from .purga import FUNCION_INMUTABLES  # import tardío: purga no depende de las guardias

    faltan: list[str] = []
    funcion = con.execute(text(_SQL_FUNCION), {"rol": ROL_PURGA, "funcion": FUNCION_INMUTABLES}).all()
    if len(funcion) != 1:
        faltan.append(FUNCION_INMUTABLES)
    else:
        f = funcion[0]
        if not f.prosecdef or not any(str(o).startswith("search_path=") for o in (f.proconfig or [])):
            faltan.append(f"{FUNCION_INMUTABLES} (SECURITY DEFINER y search_path fijo)")
        if f.publica:
            faltan.append(f"{FUNCION_INMUTABLES} (EXECUTE para PUBLIC)")
        if not f.ejecuta:
            faltan.append(f"{FUNCION_INMUTABLES} (EXECUTE para {ROL_PURGA})")
    conocidos = TRIGGERS_INMUTABLES | TRIGGERS_DELETE_SIN_EXCEPCION
    for tabla, trigger in con.execute(text(_SQL_TRIGGERS_DELETE)):
        if (tabla, trigger) not in conocidos:
            faltan.append(f"trigger {trigger} en {tabla} (lanza en DELETE y no está en TRIGGERS_INMUTABLES)")
    return faltan
