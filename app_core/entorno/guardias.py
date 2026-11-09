# ¤entorno-pruebas ¤seguridad
"""Guardias de arranque del entorno de pruebas y de la demo (PRD EVYDENTIA §5.5 y §5.6.2).

`entorno_actual()` es la única lectura de `APP_ENV`. Con `pruebas` o `demo`, `validar_arranque()`
impide arrancar si falta la huella del proyecto de producción, si esa huella coincide con el
proyecto de Google Cloud en el que corre el servicio, si aparece en `DATABASE_URL` o si
`AUTH_MODE=headers`. Los mensajes nombran la causa y nunca incluyen la URL de la base.
"""
from __future__ import annotations

import os
import urllib.request
from typing import Callable, Optional

from app_core.huellas_produccion import apunta_a_produccion

ENTORNOS_VALIDOS = ("development", "test", "pruebas", "demo", "production")
ENTORNOS_FICTICIOS = ("pruebas", "demo")

URL_METADATOS_PROYECTO = "http://metadata.google.internal/computeMetadata/v1/project/project-id"


class ErrorArranqueEntorno(RuntimeError):
    """El entorno declarado no permite arrancar el backend."""


def entorno_actual() -> str:
    """Devuelve el entorno de `APP_ENV` (por defecto `development`); un valor desconocido es error."""
    valor = os.environ.get("APP_ENV", "development").strip().lower() or "development"
    if valor not in ENTORNOS_VALIDOS:
        raise ErrorArranqueEntorno(
            f"APP_ENV no reconocido; valores válidos: {', '.join(ENTORNOS_VALIDOS)}."
        )
    return valor


def datos_ficticios(entorno: Optional[str] = None) -> bool:
    """Verdadero en `pruebas` y `demo`: los datos son sintéticos."""
    return (entorno or entorno_actual()) in ENTORNOS_FICTICIOS


def _proyecto_desde_metadatos(timeout: float = 1.0) -> Optional[str]:
    """Consulta el servidor de metadatos de Google Cloud; fuera de la nube devuelve None."""
    peticion = urllib.request.Request(URL_METADATOS_PROYECTO, headers={"Metadata-Flavor": "Google"})
    try:
        with urllib.request.urlopen(peticion, timeout=timeout) as respuesta:  # noqa: S310 (host fijo)
            return respuesta.read().decode("utf-8").strip() or None
    except Exception:
        return None


def proyecto_en_ejecucion(
    consultar_metadatos: Callable[[], Optional[str]] = _proyecto_desde_metadatos,
) -> Optional[str]:
    """Proyecto de Google Cloud donde corre el servicio, o None si es desconocido."""
    proyecto = os.environ.get("GOOGLE_CLOUD_PROJECT", "").strip()
    if proyecto:
        return proyecto
    return consultar_metadatos()


def validar_arranque(
    consultar_metadatos: Callable[[], Optional[str]] = _proyecto_desde_metadatos,
) -> str:
    """Valida el arranque y devuelve el entorno. Fuera de pruebas y demo no comprueba nada más."""
    entorno = entorno_actual()
    if entorno not in ENTORNOS_FICTICIOS:
        return entorno

    huella = os.environ.get("HUELLA_PROYECTO_PRODUCCION", "").strip()
    if not huella:
        raise ErrorArranqueEntorno(
            f"APP_ENV={entorno}: falta HUELLA_PROYECTO_PRODUCCION; no se puede comprobar que el "
            "servicio esté fuera del proyecto de producción."
        )
    if os.environ.get("AUTH_MODE", "").strip().lower() == "headers":
        raise ErrorArranqueEntorno(f"APP_ENV={entorno}: AUTH_MODE=headers no está permitido.")
    proyecto = proyecto_en_ejecucion(consultar_metadatos)
    if proyecto and proyecto.lower() == huella.lower():
        raise ErrorArranqueEntorno(
            f"APP_ENV={entorno}: el servicio corre en el proyecto de Google Cloud de producción."
        )
    if huella.lower() in os.environ.get("DATABASE_URL", "").lower():
        raise ErrorArranqueEntorno(
            f"APP_ENV={entorno}: DATABASE_URL contiene la huella del proyecto de producción."
        )
    # EP-11: la demo y las pruebas nunca arrancan contra la base de producción (SEC-15).
    if apunta_a_produccion(os.environ.get("DATABASE_URL")):
        raise ErrorArranqueEntorno(f"APP_ENV={entorno}: DATABASE_URL apunta a la base de producción.")
    return entorno
