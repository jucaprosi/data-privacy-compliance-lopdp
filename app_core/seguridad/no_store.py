# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤seguridad-tenant
"""Middleware ASGI puro (SEC-25): toda respuesta de /api/v1/* sale sin caché salvo que la ruta fije la suya."""
from __future__ import annotations

from app_core.cache import CABECERA_NO_STORE

PREFIJO_API = "/api/v1"
_NOMBRE = next(iter(CABECERA_NO_STORE)).lower().encode("latin-1")
_VALOR = next(iter(CABECERA_NO_STORE.values())).encode("latin-1")


def _es_api(ruta: str) -> bool:
    return ruta == PREFIJO_API or ruta.startswith(PREFIJO_API + "/")


class NoStoreMiddleware:
    def __init__(self, app) -> None:  # noqa: ANN001
        self.app = app

    async def __call__(self, scope, receive, send) -> None:  # noqa: ANN001
        if scope["type"] != "http" or not _es_api(scope.get("path", "")):
            await self.app(scope, receive, send)
            return

        async def enviar(mensaje) -> None:  # noqa: ANN001
            if mensaje["type"] == "http.response.start":
                cabeceras = list(mensaje.get("headers") or [])
                if not any(nombre.lower() == _NOMBRE for nombre, _ in cabeceras):
                    cabeceras.append((_NOMBRE, _VALOR))
                mensaje = {**mensaje, "headers": cabeceras}
            await send(mensaje)

        await self.app(scope, receive, enviar)
