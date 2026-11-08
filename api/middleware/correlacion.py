# ¤¤backend-developer
"""Middleware ASGI de correlación (OPS-07) ¤observabilidad.

Asigna o propaga `X-Request-ID` (solo si es un UUID válido), registra una línea por petición
con método, ruta sin consulta, código y duración, y convierte los errores no controlados en un
500 genérico con la traza saneada en el registro.
"""
from __future__ import annotations

import json
import logging
import time
import uuid

from app_core.observabilidad import fijar_contexto, limpiar_contexto, registrar_error

CABECERA = b"x-request-id"


def _request_id_valido(valor: bytes | None) -> str | None:
    if not valor:
        return None
    try:
        return str(uuid.UUID(valor.decode("latin-1").strip()))
    except (ValueError, UnicodeDecodeError):
        return None


class CorrelacionMiddleware:
    def __init__(self, app, registro: logging.Logger | None = None) -> None:  # noqa: ANN001
        self.app = app
        self.registro = registro or logging.getLogger("evydentia")

    async def __call__(self, scope, receive, send) -> None:  # noqa: ANN001
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        cabeceras = dict(scope.get("headers") or [])
        request_id = _request_id_valido(cabeceras.get(CABECERA)) or str(uuid.uuid4())
        scope.setdefault("state", {})["request_id"] = request_id
        token = fijar_contexto(request_id=request_id, method=scope.get("method"), path=scope.get("path", ""))
        inicio = time.perf_counter()
        estado = {"status": 500, "enviado": False}

        async def enviar(mensaje) -> None:  # noqa: ANN001
            if mensaje["type"] == "http.response.start":
                estado["status"] = mensaje["status"]
                estado["enviado"] = True
                otras = [(k, v) for k, v in mensaje.get("headers", []) if k.lower() != CABECERA]
                mensaje = {**mensaje, "headers": otras + [(CABECERA, request_id.encode())]}
            await send(mensaje)

        try:
            await self.app(scope, receive, enviar)
        except Exception as exc:  # noqa: BLE001 - frontera del proceso: se registra y se responde 500
            registrar_error(self.registro, exc)
            if not estado["enviado"]:
                cuerpo = json.dumps({"detail": "Error interno.", "request_id": request_id}).encode()
                await enviar({"type": "http.response.start", "status": 500,
                              "headers": [(b"content-type", b"application/json")]})
                await send({"type": "http.response.body", "body": cuerpo})
        finally:
            state = scope.get("state") or {}
            self.registro.info(
                "peticion",
                extra={
                    "status": estado["status"],
                    "duration_ms": round((time.perf_counter() - inicio) * 1000, 1),
                    "tenant_id": state.get("tenant_id"),
                    "user_id": state.get("user_id"),
                },
            )
            limpiar_contexto(token)
