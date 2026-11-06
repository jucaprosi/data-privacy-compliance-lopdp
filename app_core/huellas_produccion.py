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
from urllib.parse import urlparse

# Endpoint de Neon de la rama `production` (proyecto square-violet-52579154). Es la huella del host,
# no una credencial: sin usuario ni contraseña no abre nada.
HUELLA_HOST_PRODUCCION = "ep-late-hall-b50bpbk5"

# Vercel define `VERCEL=1` en build y en ejecución; Cloud Run define `K_SERVICE`.
# https://vercel.com/docs/environment-variables/system-environment-variables
# https://cloud.google.com/run/docs/container-contract#env-vars
VARIABLES_DE_NUBE = ("VERCEL", "K_SERVICE")


def host_de(url: Optional[str]) -> Optional[str]:
    """Host de una URL de conexión, en minúsculas y sin usuario ni contraseña; `None` si no tiene."""
    if not url or not url.strip():
        return None
    try:
        host = urlparse(url.strip()).hostname
    except ValueError:
        return None
    return host.lower() if host else None


def apunta_a_produccion(url: Optional[str]) -> bool:
    """Verdadero si el host de `url` es el de producción. Compara solo el host.

    Falla cerrado: una URL de la que no sale host, pero que contiene la huella, cuenta como producción.
    """
    host = host_de(url)
    if host is not None:
        return HUELLA_HOST_PRODUCCION in host
    return bool(url) and HUELLA_HOST_PRODUCCION in url.lower()


def corre_en_la_nube(entorno: Optional[Mapping[str, str]] = None) -> bool:
    """Verdadero si está definida `VERCEL` o `K_SERVICE` (con cualquier valor, también vacío)."""
    entorno = os.environ if entorno is None else entorno
    return any(nombre in entorno for nombre in VARIABLES_DE_NUBE)
