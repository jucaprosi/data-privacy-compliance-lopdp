# ¤seguridad ¤seguridad-tenant ¤copiloto-ia
"""Middleware ASGI de SEC-13: límite de peticiones por IP, usuario y organización.

- Responde 429 con `Retry-After` y `{"codigo": "LIMITE_PETICIONES", "politica": ...}` sin ejecutar la ruta.
- IA: se admite solo si caben `ia_usuario` e `ia_organizacion` (R3), antes de llamar al modelo.
- Almacén caído (R4): la IA se cierra con 503 `LIMITE_NO_DISPONIBLE`; el resto se abre con un aviso.
- La identidad sale del token y la organización de la membresía verificada, nunca del cuerpo.
"""
from __future__ import annotations

import ipaddress
import json
import logging
import os
from dataclasses import dataclass
from typing import Awaitable, Callable, Mapping, Optional

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


# --- INICIO SEC-21 ---
# IP del cliente tras los proxies de confianza (riesgo del CTO; regla del Arquitecto endurecida por Seguridad).
# `PROXIES_CONFIABLES = n` es el número de proxies de confianza delante de la aplicación; cada uno añade una
# entrada por la derecha de X-Forwarded-For. Lo que antepone el cliente queda a la izquierda y nunca se lee.
# Saltzer y Schroeder (1975), «Fail-safe defaults»: ante lo dudoso, una clave común, nunca una IP elegible.
VARIABLE_PROXIES = "PROXIES_CONFIABLES"
CLAVE_COMUN = "desconocida"
PREFIJO_IPV6 = 64


def proxies_confiables(entorno: Optional[Mapping[str, str]] = None) -> int:
    """`n` de `PROXIES_CONFIABLES`. En la nube (`K_SERVICE`) es obligatoria; fuera de ella, 0 si falta.

    Un valor que no es un entero ≥ 0 en ASCII lanza `RuntimeError` también fuera de la nube. No nombra el valor.
    """
    from app_core.config import corre_en_cloud_run

    entorno = os.environ if entorno is None else entorno
    valor = (entorno.get(VARIABLE_PROXIES) or "").strip()
    if not valor:
        if corre_en_cloud_run(entorno):
            raise RuntimeError(f"SEC-21: en la nube {VARIABLE_PROXIES} es obligatoria (entero ≥ 0).")
        return 0
    if not (valor.isascii() and valor.isdigit()):
        raise RuntimeError(f"SEC-21: {VARIABLE_PROXIES} debe ser un entero ≥ 0.")
    return int(valor)


def _entradas_xff(scope: dict) -> list[str]:
    """Todas las cabeceras X-Forwarded-For, unidas en orden, sin espacios ni entradas vacías."""
    valores = [v.decode("latin-1") for k, v in scope.get("headers") or [] if k.decode("latin-1").lower() == "x-forwarded-for"]
    return [p.strip() for p in ",".join(valores).split(",") if p.strip()]


def _clave_de_ip(texto: str) -> Optional[str]:
    """IP normalizada (IPv6 agrupada por /64), o `None` si no es una IP."""
    try:
        ip = ipaddress.ip_address(texto)
    except ValueError:
        return None
    if ip.version == 6:
        if ip.ipv4_mapped is not None:
            return str(ip.ipv4_mapped)
        sin_ambito = ipaddress.IPv6Address(int(ip))  # sin «%interfaz»
        return str(ipaddress.ip_network(f"{sin_ambito}/{PREFIJO_IPV6}", strict=False))
    return str(ip)


def ip_cliente(scope: dict, proxies: Optional[int] = None) -> str:
    """IP del cliente para limitar por IP.

    n = 0: no hay proxy de confianza, X-Forwarded-For lo escribe el cliente y se ignora: `scope["client"]`
    (o la clave común si no viene). n ≥ 1: la entrada E[len(E)-n], la que añadió el proxy de confianza más
    externo; con menos entradas que n o una entrada que no es IP, la clave común (nunca E[0] ni `client`).
    """
    n = proxies_confiables() if proxies is None else proxies
    if n <= 0:
        cliente = scope.get("client")
        if not cliente or not cliente[0]:
            return CLAVE_COMUN
        return _clave_de_ip(cliente[0]) or cliente[0]
    entradas = _entradas_xff(scope)
    if len(entradas) < n:
        return CLAVE_COMUN
    return _clave_de_ip(entradas[len(entradas) - n]) or CLAVE_COMUN
# --- FIN SEC-21 ---


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
        proxies: Optional[int] = None,
    ) -> None:
        self.app = app
        self.limitador = limitador or LimitadorPostgres()
        self.resolver = resolver
        self.politicas = politicas or POLITICAS
        self.proxies = proxies_confiables() if proxies is None else proxies  # SEC-21: falla al arrancar en la nube

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
        ip = ip_cliente(scope, self.proxies)
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
