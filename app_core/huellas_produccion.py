# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤rbac-tenant ¤arbitro
"""Guardia de base local, detección de nube (Cloud Run) y huella Cloud SQL de producción (RET-01 / SEC-15 / SEC-20).

- `es_base_local` / `exigir_base_local`: lista blanca única para desarrollo, pruebas y herramientas
  locales (`localhost`, `127.0.0.1`, `::1`; `/cloudsql/` y hosts remotos fallan cerrado).
- `corre_en_la_nube`: Cloud Run define `K_SERVICE`.
- SEC-20 (`INSTANCIA_CLOUD_SQL_PRODUCCION`, `apunta_a_produccion`, `base_es_produccion`): guardia
  contra la instancia y base de producción en Cloud SQL.

Sin dependencias del proyecto al importarse: lo usan el backend, Alembic, hooks, scripts y pruebas.
"""
from __future__ import annotations

import os
from typing import Mapping, Optional
from urllib.parse import parse_qs, unquote, urlparse, urlsplit

# Cloud Run define `K_SERVICE` (nombre del servicio) en el contrato del contenedor.
# https://docs.cloud.google.com/run/docs/container-contract (consultado 2026-11-06)
VARIABLES_DE_NUBE: tuple[str, ...] = ("K_SERVICE",)

# Lista blanca única de hosts locales (RET-01 / CTO 2026-11-13: `/cloudsql/` nunca es local).
HOSTS_LOCALES: tuple[str, ...] = ("localhost", "127.0.0.1", "::1")
VARIABLES_DE_BASE_LOCAL: tuple[str, ...] = ("TEST_DATABASE_URL", "DATABASE_URL", "MIGRATION_DATABASE_URL")

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


class BaseNoLocal(RuntimeError):
    """Se lanza cuando alguna variable de base apunta fuera de los hosts locales permitidos."""

    def __init__(self, variables: tuple[str, ...]) -> None:
        self.variables: tuple[str, ...] = tuple(variables)
        nombres = ", ".join(self.variables)
        super().__init__(
            f"[ENTORNO] {nombres} debe apuntar a una base local. "
            "La operación se detiene sin conectarse."
        )


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
    """Verdadero si `url` o el entorno del conector Cloud SQL nombran la instancia de producción. Pura."""
    return nombra_instancia_de_produccion(url) or conector_apunta_a_produccion(entorno)


def es_base_local(url: Optional[str], entorno: Optional[Mapping[str, str]] = None) -> bool:
    """Verdadero solo si `url` apunta a PostgreSQL en `localhost`, `127.0.0.1` o `::1` y no usa `/cloudsql/`."""
    if not url or not url.strip():
        return False
    texto = url.strip()
    if apunta_a_produccion(texto, entorno) or "/cloudsql/" in _decodificado(texto):
        return False
    try:
        partes = urlsplit(texto)
        _ = partes.port
    except ValueError:
        return False
    esquema = (partes.scheme or "").lower()
    if not (esquema == "postgres" or esquema.startswith("postgresql")):
        return False
    consulta = parse_qs(partes.query)
    if consulta.get("unix_sock"):
        return False
    hosts_query = [h.lower() for h in consulta.get("host", [])]
    if any(h not in HOSTS_LOCALES for h in hosts_query):
        return False
    host = (partes.hostname or "").lower()
    return host in HOSTS_LOCALES


def variables_no_locales(
    entorno: Optional[Mapping[str, str]] = None,
    variables: tuple[str, ...] = VARIABLES_DE_BASE_LOCAL,
    *,
    urls_sqlite_permitidas: tuple[str, ...] = (),
) -> tuple[str, ...]:
    """Nombres de variables definidas y no vacías que apuntan fuera de los hosts locales permitidos."""
    entorno = os.environ if entorno is None else entorno
    rechazadas: list[str] = []
    for nombre in variables:
        valor = (entorno.get(nombre) or "").strip()
        if not valor:
            continue
        if valor in urls_sqlite_permitidas and not conector_apunta_a_produccion(entorno):
            continue
        if not es_base_local(valor, entorno):
            rechazadas.append(nombre)
    return tuple(rechazadas)


def exigir_base_local(
    entorno: Optional[Mapping[str, str]] = None,
    variables: tuple[str, ...] = VARIABLES_DE_BASE_LOCAL,
) -> None:
    """Falla cerrado con `BaseNoLocal` (solo nombres de variables) si alguna URL definida no es local."""
    rechazadas = variables_no_locales(entorno, variables)
    if rechazadas:
        raise BaseNoLocal(rechazadas)


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
    """Verdadero si está definida `K_SERVICE` (Cloud Run, con cualquier valor, también vacío)."""
    entorno = os.environ if entorno is None else entorno
    return any(nombre in entorno for nombre in VARIABLES_DE_NUBE)
