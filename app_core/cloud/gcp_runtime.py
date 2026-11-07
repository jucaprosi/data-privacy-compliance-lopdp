"""Runtime de Cloud Run: pooler, clientes perezosos y secretos por ADC (GCP-01).

`¤cloud-run-perf` `¤seguridad-tenant` `¤adpa`

R2 · Tras un pooler transaccional (PgBouncer de Neon `-pooler` o Cloud SQL
Proxy) psycopg3 no debe preparar sentencias: la conexión física cambia entre
transacciones y aparecería `DuplicatePreparedStatement`.

R3 · Los clientes de Google Cloud (Storage, Vertex AI, DLP, Secret Manager) se
crean al primer uso, nunca al importar: el arranque en frío de Cloud Run no paga
su coste y los worktrees sin credenciales siguen importando el backend.

Los secretos se leen con Application Default Credentials (ADC); si el entorno ya
trae la variable, manda la variable y no se llama a la nube.
"""

from __future__ import annotations

import importlib
import importlib.util
import os
import threading
from typing import Any, Callable
from urllib.parse import urlsplit

# Fábricas de clientes por nombre lógico: (módulo, atributo invocable).
_FABRICAS: dict[str, tuple[str, str]] = {
    "storage": ("google.cloud.storage", "Client"),
    "secretmanager": ("google.cloud.secretmanager", "SecretManagerServiceClient"),
    "dlp": ("google.cloud.dlp_v2", "DlpServiceClient"),
    "vertexai": ("vertexai", "init"),
}

_clientes: dict[str, Any] = {}
_candado = threading.Lock()


def es_pooler_transaccional(url: str | None) -> bool:
    """True si la URL apunta a un pooler transaccional (PgBouncer o Cloud SQL Proxy)."""
    if os.environ.get("DB_POOLER_TRANSACCIONAL", "").strip().lower() in {"1", "true", "si", "sí"}:
        return True
    if not url:
        return False
    try:
        partes = urlsplit(url)
        host = (partes.hostname or "").lower()
    except ValueError:
        return False
    if "-pooler" in host:
        return True
    # Cloud SQL Proxy: socket Unix /cloudsql/<instancia> en la query o en el host.
    return "/cloudsql/" in url or host.startswith("cloudsql")


def argumentos_motor(url: str | None) -> dict[str, Any]:
    """`connect_args` para `create_async_engine`; desactiva sentencias preparadas tras un pooler."""
    if es_pooler_transaccional(url):
        return {"prepare_threshold": None}
    return {}


def cliente_gcp(nombre: str, fabrica: Callable[[], Any] | None = None) -> Any:
    """Devuelve el cliente `nombre`, creándolo una sola vez al primer uso (thread-safe)."""
    cliente = _clientes.get(nombre)
    if cliente is not None:
        return cliente
    with _candado:
        cliente = _clientes.get(nombre)
        if cliente is None:
            if fabrica is None:
                if nombre not in _FABRICAS:
                    raise KeyError(f"Cliente de Google Cloud desconocido: {nombre}")
                modulo, atributo = _FABRICAS[nombre]
                fabrica = getattr(importlib.import_module(modulo), atributo)
            cliente = fabrica()
            _clientes[nombre] = cliente
    return cliente


def clientes_iniciados() -> tuple[str, ...]:
    """Nombres de los clientes ya creados (para telemetría y pruebas)."""
    return tuple(sorted(_clientes))


def _reiniciar_clientes() -> None:
    """Solo para pruebas: olvida los clientes creados."""
    with _candado:
        _clientes.clear()


def leer_secreto(nombre: str, proyecto: str | None = None, version: str = "latest") -> str | None:
    """Lee un secreto: primero la variable de entorno, luego Secret Manager por ADC.

    Sin proyecto (`GOOGLE_CLOUD_PROJECT`) devuelve None en vez de fallar: un worktree
    local sin nube sigue funcionando con su `.env`.
    """
    valor = os.environ.get(nombre)
    if valor:
        return valor
    proyecto = proyecto or os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not proyecto:
        return None
    cliente = cliente_gcp("secretmanager")
    ruta = f"projects/{proyecto}/secrets/{nombre}/versions/{version}"
    respuesta = cliente.access_secret_version(request={"name": ruta})
    return respuesta.payload.data.decode("utf-8")


def _modulo_disponible(nombre: str) -> bool:
    return importlib.util.find_spec(nombre) is not None


def telemetria_cloudrun() -> dict[str, Any]:
    """Estado del chasis para `GET /api/v1/health/cloudrun`; sin secretos ni datos personales."""
    return {
        "en_cloud_run": bool(os.environ.get("K_SERVICE")),
        "revision": os.environ.get("K_REVISION"),
        "uvloop": _modulo_disponible("uvloop"),
        "httptools": _modulo_disponible("httptools"),
        "pooler_transaccional": es_pooler_transaccional(os.environ.get("DATABASE_URL")),
        "adc_proyecto": bool(os.environ.get("GOOGLE_CLOUD_PROJECT")),
        "clientes_iniciados": list(clientes_iniciados()),
    }
