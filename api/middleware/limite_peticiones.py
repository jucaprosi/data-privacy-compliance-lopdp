# ¤seguridad ¤seguridad-tenant ¤copiloto-ia
"""Middleware ASGI de SEC-13: límite de peticiones por IP, usuario y organización.

- Responde 429 con `Retry-After` y `{"codigo": "LIMITE_PETICIONES", "politica": ...}` sin ejecutar la ruta.
- IA: se admite solo si caben `ia_usuario` e `ia_organizacion` (R3), antes de llamar al modelo.
- Almacén caído (R4): la IA se cierra con 503 `LIMITE_NO_DISPONIBLE`; el resto se abre con un aviso.
- La identidad sale del token y la organización de la membresía verificada, nunca del cuerpo.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Awaitable, Callable, Optional

from app_core.limites import (
    POLITICAS,
    Limitador,
    LimitadorPostgres,
    LimiteNoDisponible,
    Politica,
    politicas_de_ruta,
)

logger = logging.getLogger("jubys_lopdp_json_logger")


@dataclass(frozen=True)
class Identidad:
    usuario_id: Optional[str] = None
    organizacion_id: Optional[str] = None


Resolver = Callable[[dict, bool], Awaitable[Identidad]]


def _cabeceras(scope: dict) -> dict[str, str]:
    return {k.decode("latin-1").lower(): v.decode("latin-1") for k, v in scope.get("headers") or []}


def ip_cliente(scope: dict) -> str:
    """IP del cliente. Tras el balanceador de Google, la última entrada de X-Forwarded-For es la que
    añade la infraestructura (las anteriores las puede escribir el cliente)."""
    reenviada = _cabeceras(scope).get("x-forwarded-for", "")
    partes = [p.strip() for p in reenviada.split(",") if p.strip()]
    if partes:
        return partes[-1]
    cliente = scope.get("client")
    return cliente[0] if cliente else "desconocida"


async def resolver_oidc(scope: dict, es_ia: bool) -> Identidad:
    """Identidad verificada del token de Google; en IA, además, la membresía en la organización.

    Cualquier fallo deja la identidad vacía: la petición se cuenta por IP y la ruta la rechazará.
    """
    from app_core.security import autenticar_en_tenant, extraer_bearer, verificar_token_google

    cabeceras = _cabeceras(scope)
    autorizacion = cabeceras.get("authorization")
    try:
        if es_ia:
            tenant = (cabeceras.get("x-tenant-id") or "").strip()
            if tenant:
                usuario, _ = await autenticar_en_tenant(autorizacion, tenant)
                return Identidad(usuario.usuario_id, tenant)
        identidad = await verificar_token_google(extraer_bearer(autorizacion))
        return Identidad(usuario_id=f"sub:{identidad.sub}")
    except Exception:  # noqa: BLE001 - sin identidad verificada se limita por IP
        return Identidad()


# --- INICIO SEC-13a ---
from app_core.errors import ErrorNegocio  # noqa: E402


async def consumir_tope_ia(identidad: Identidad) -> None:
    """Tope total de IA de la organización (SEC-13a), con el contexto RLS del tenant."""
    from app_core.db.session import async_session_factory, fijar_contexto_rls
    from app_core.limites.tope_organizacion import consumir_generacion

    async with async_session_factory() as session:
        await fijar_contexto_rls(session, identidad.organizacion_id, identidad.usuario_id)
        await consumir_generacion(session, identidad.organizacion_id)
        await session.commit()
# --- FIN SEC-13a ---


def _cuerpo(datos: dict) -> bytes:
    return json.dumps(datos).encode()


class LimitePeticionesMiddleware:
    def __init__(
        self,
        app,  # noqa: ANN001
        limitador: Optional[Limitador] = None,
        resolver: Resolver = resolver_oidc,
        politicas: Optional[dict[str, Politica]] = None,
    ) -> None:
        self.app = app
        self.limitador = limitador or LimitadorPostgres()
        self.resolver = resolver
        self.politicas = politicas or POLITICAS

    async def __call__(self, scope, receive, send) -> None:  # noqa: ANN001
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        nombres = politicas_de_ruta(scope.get("path", ""), scope.get("method", "GET"))
        if not nombres:
            await self.app(scope, receive, send)
            return
        politicas = [self.politicas[n] for n in nombres]
        es_ia = any(p.es_ia for p in politicas)
        ip = ip_cliente(scope)
        identidad = Identidad() if politicas[0].ambito == "ip" else await self.resolver(scope, es_ia)

        rechazo: Optional[tuple[Politica, int]] = None
        try:
            for p in politicas:
                if p.ambito == "ip":
                    identificador = f"ip:{ip}"
                elif p.ambito == "organizacion":
                    if not identidad.organizacion_id:
                        continue
                    identificador = f"org:{identidad.organizacion_id}"
                else:
                    identificador = identidad.usuario_id or f"ip:{ip}"
                resultado = await self.limitador.consumir(p, identificador)
                if not resultado.admitido and rechazo is None:
                    rechazo = (p, resultado.retry_after)
        except LimiteNoDisponible as exc:
            if es_ia:
                logger.error("Limitador no disponible: IA cerrada (%s)", exc)
                await self._responder(send, 503, {"codigo": "LIMITE_NO_DISPONIBLE"})
                return
            logger.warning("Limitador no disponible: petición admitida sin límite (%s)", exc)
            await self.app(scope, receive, send)
            return

        if rechazo is not None:
            politica, espera = rechazo
            await self._responder(
                send,
                429,
                {"codigo": "LIMITE_PETICIONES", "politica": politica.nombre},
                [(b"retry-after", str(espera).encode())],
            )
            return
        # --- INICIO SEC-13a ---
        if es_ia and identidad.organizacion_id:
            try:
                await consumir_tope_ia(identidad)
            except ErrorNegocio as exc:
                await self._responder(send, exc.status_code, {"codigo": exc.code, "mensaje": exc.detail})
                return
            except Exception as exc:  # noqa: BLE001 - tope no verificable: la IA se cierra (R4)
                logger.error("Tope de IA no disponible: IA cerrada (%s)", type(exc).__name__)
                await self._responder(send, 503, {"codigo": "LIMITE_NO_DISPONIBLE"})
                return
        # --- FIN SEC-13a ---
        await self.app(scope, receive, send)

    @staticmethod
    async def _responder(send, estado: int, datos: dict, extra: Optional[list] = None) -> None:  # noqa: ANN001
        cuerpo = _cuerpo(datos)
        await send(
            {
                "type": "http.response.start",
                "status": estado,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(cuerpo)).encode()),
                    *(extra or []),
                ],
            }
        )
        await send({"type": "http.response.body", "body": cuerpo})
