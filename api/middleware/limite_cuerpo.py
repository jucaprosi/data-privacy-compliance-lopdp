"""Middleware ASGI puro: corta con 413 cuerpos excesivos de /api/v1/preanalisis antes de que se procesen."""
from __future__ import annotations

import json

PREFIJO = "/api/v1/preanalisis"
LIMITE_PREPARAR = 26 * 1024 * 1024
LIMITE_ANALIZAR = 128 * 1024
_MENSAJE = json.dumps({"detail": "El cuerpo de la solicitud excede el límite permitido."}).encode()


def _limite_para(ruta: str) -> int | None:
    if not (ruta == PREFIJO or ruta.startswith(PREFIJO + "/")):
        return None
    return LIMITE_PREPARAR if ruta.rstrip("/").endswith("/preparar") else LIMITE_ANALIZAR


class LimiteCuerpoMiddleware:
    def __init__(self, app) -> None:  # noqa: ANN001
        self.app = app

    async def __call__(self, scope, receive, send) -> None:  # noqa: ANN001
        limite = _limite_para(scope.get("path", "")) if scope["type"] == "http" else None
        if limite is None:
            await self.app(scope, receive, send)
            return
        declarado = dict(scope.get("headers") or []).get(b"content-length")
        if declarado is not None and declarado.strip().isdigit() and int(declarado) > limite:
            await self._rechazar(send)
            return

        acumulado = 0
        iniciada = False
        rechazado = False

        async def recibir():  # noqa: ANN202
            nonlocal acumulado, rechazado
            if rechazado:
                return {"type": "http.disconnect"}
            mensaje = await receive()
            if mensaje["type"] == "http.request":
                acumulado += len(mensaje.get("body", b""))
                if acumulado > limite:
                    # FastAPI convertiría una excepción aquí en 400: se responde 413 de inmediato y se simula desconexión.
                    rechazado = True
                    if not iniciada:
                        await self._rechazar(send)
                    return {"type": "http.disconnect"}
            return mensaje

        async def enviar(mensaje) -> None:  # noqa: ANN001
            nonlocal iniciada
            if rechazado:
                return  # ya se respondió 413; se descarta cualquier respuesta posterior de la app
            if mensaje["type"] == "http.response.start":
                iniciada = True
            await send(mensaje)

        try:
            await self.app(scope, recibir, enviar)
        except Exception:  # noqa: BLE001
            if not rechazado:
                raise

    @staticmethod
    async def _rechazar(send) -> None:  # noqa: ANN001
        await send(
            {
                "type": "http.response.start",
                "status": 413,
                "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(_MENSAJE)).encode()), (b"connection", b"close")],
            }
        )
        await send({"type": "http.response.body", "body": _MENSAJE})
