# ¤rbac-tenant ¤arbitro
"""Huella de producción y detección de nube: un solo sitio (SEC-15).

`INV_LOPDP_HEADERS_NEVER_WITH_PRODUCTION`: el modo de cabeceras nunca arranca contra la base de
producción ni en la nube. Este módulo dice qué es producción y qué es nube; quien decide arrancar
o no es `app_core.security.exigir_arranque_seguro`. SEC-16 y SEC-17 importan de aquí
`corre_en_la_nube`.

Sin dependencias del proyecto: lo importan el backend, los scripts y las pruebas.
"""
from __future__ import annotations

import os
from typing import Mapping, Optional
from urllib.parse import unquote, urlparse

# Endpoint de Neon de la rama `production` (proyecto square-violet-52579154). Es la huella del host,
# no una credencial: sin usuario ni contraseña no abre nada.
HUELLA_HOST_PRODUCCION = "ep-late-hall-b50bpbk5"

# Vercel define `VERCEL=1` en build y en ejecución si el proyecto expone las variables de sistema
# («Enable access to System Environment Variables»); Cloud Run define `K_SERVICE` (nombre del servicio).
# https://vercel.com/docs/environment-variables/system-environment-variables (consultado 2026-11-06)
# https://docs.cloud.google.com/run/docs/container-contract (consultado 2026-11-06)
VARIABLES_DE_NUBE = ("VERCEL", "K_SERVICE")

# === SEC-20 ===
# Instancia de Cloud SQL de producción (EVYDENTIA). El conector la monta en /cloudsql/<instancia> y
# `deploy-gcp.yml` la declara en CLOUD_SQL_INSTANCE. Es un nombre, no una credencial.
INSTANCIA_CLOUD_SQL_PRODUCCION = "evydentia:us-central1:evydentia-production"
BASE_PRODUCCION = "evydentia_prod"
# Lista cerrada de variables donde el conector o el despliegue nombran la instancia.
VARIABLES_DEL_CONECTOR = ("INSTANCE_CONNECTION_NAME", "CLOUD_SQL_CONNECTION_NAME", "CLOUD_SQL_INSTANCE")
# Marcador invertido: solo las bases que NO son producción lo tienen.
VALORES_MARCADOR = ("pruebas", "demo")
TIEMPO_MAXIMO_MARCADOR = "2s"


def _decodificado(texto: str) -> str:
    """Texto en minúsculas tras decodificar %XX hasta que no cambie (como mucho 3 veces)."""
    actual = texto
    for _ in range(3):
        siguiente = unquote(actual)
        if siguiente == actual:
            break
        actual = siguiente
    return actual.lower()


def nombra_instancia_de_produccion(texto: Optional[str]) -> bool:
    """Verdadero si `texto` nombra la instancia de Cloud SQL de producción, en cualquier parte."""
    return bool(texto) and INSTANCIA_CLOUD_SQL_PRODUCCION in _decodificado(texto)


def conector_apunta_a_produccion(entorno: Optional[Mapping[str, str]] = None) -> bool:
    """Verdadero si alguna variable del conector nombra la instancia de producción."""
    entorno = os.environ if entorno is None else entorno
    return any(nombra_instancia_de_produccion(entorno.get(nombre)) for nombre in VARIABLES_DEL_CONECTOR)
# === fin SEC-20 ===


def host_de(url: Optional[str]) -> Optional[str]:
    """Host de una URL de conexión, en minúsculas y sin usuario ni contraseña; `None` si no tiene."""
    if not url or not url.strip():
        return None
    try:
        host = urlparse(url.strip()).hostname
    except ValueError:
        return None
    return host.lower() if host else None


def apunta_a_produccion(url: Optional[str], entorno: Optional[Mapping[str, str]] = None) -> bool:
    """Verdadero si `url` es de producción. Pura: no abre conexiones.

    - Neon: compara solo el host con la huella. Una URL sin host que contiene la huella cuenta como
      producción (falla cerrado).
    - Cloud SQL (SEC-20): la instancia de producción en cualquier parte de la URL (host=/cloudsql/…,
      unix_sock…), sin distinguir mayúsculas y tras decodificar, o en una variable del conector.
    """
    if nombra_instancia_de_produccion(url) or conector_apunta_a_produccion(entorno):
        return True
    host = host_de(url)
    if host is not None:
        return HUELLA_HOST_PRODUCCION in host
    return bool(url) and HUELLA_HOST_PRODUCCION in url.lower()


# === SEC-20 ===
_SQL_MARCADOR_CATALOGO = (
    "SELECT current_database() AS base, c.relkind, c.relowner = d.datdba AS del_dueno "
    "FROM pg_catalog.pg_database d "
    "LEFT JOIN pg_catalog.pg_namespace n ON n.nspname = 'public' "
    "LEFT JOIN pg_catalog.pg_class c ON c.relnamespace = n.oid AND c.relname = 'entorno_marcador' "
    "WHERE d.datname = current_database()"
)
# Siempre con esquema: una tabla temporal (pg_temp) del mismo nombre no la sombrea.
_SQL_MARCADOR_FILAS = "SELECT valor FROM public.entorno_marcador LIMIT 2"


def base_es_produccion(conexion, nombre_base: Optional[str] = None) -> bool:
    """Verdadero si la base de `conexion` (SQLAlchemy, síncrona y ya abierta) debe tratarse como producción.

    Producción si se llama `evydentia_prod` (`nombre_base` lo simula en las pruebas) o si no tiene un
    marcador válido: `public.entorno_marcador`, tabla normal del dueño de la base, con exactamente una fila
    'pruebas' o 'demo'. Un error o un tiempo agotado también cuentan como producción (falla cerrado).

    Corre en un SAVEPOINT que siempre se revierte, con `statement_timeout` local: no escribe nada, no deja
    abortada la transacción del llamador y no cambia sus ajustes. El OR con la URL lo hace la guardia.
    """
    from sqlalchemy import text

    try:
        punto = conexion.begin_nested()
    except Exception:
        return True
    try:
        conexion.execute(text("SELECT set_config('statement_timeout', :t, true)"), {"t": TIEMPO_MAXIMO_MARCADOR})
        fila = conexion.execute(text(_SQL_MARCADOR_CATALOGO)).mappings().first()
        if fila is None:
            return True
        base = (nombre_base if nombre_base is not None else fila["base"]) or ""
        if base.strip().lower() == BASE_PRODUCCION:
            return True
        if fila["relkind"] != "r" or not fila["del_dueno"]:
            return True
        valores = [v for (v,) in conexion.execute(text(_SQL_MARCADOR_FILAS)).all()]
        return not (len(valores) == 1 and isinstance(valores[0], str) and valores[0] in VALORES_MARCADOR)
    except Exception:
        return True
    finally:
        try:
            punto.rollback()
        except Exception:
            pass
# === fin SEC-20 ===


def corre_en_la_nube(entorno: Optional[Mapping[str, str]] = None) -> bool:
    """Verdadero si está definida `VERCEL` o `K_SERVICE` (con cualquier valor, también vacío).

    Limitación: en Vercel, `VERCEL` solo existe en ejecución si el proyecto tiene activada «Enable
    access to System Environment Variables». Con esa opción apagada devuelve falso en Vercel y las
    guardas que dependen de esta función (SEC-15, SEC-16, SEC-17) quedan inactivas sin aviso.
    """
    entorno = os.environ if entorno is None else entorno
    return any(nombre in entorno for nombre in VARIABLES_DE_NUBE)
