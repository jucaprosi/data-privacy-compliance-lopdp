# ¤vigilancia-spdp ¤inteligencia-normativa
"""Conector resiliente hacia las secciones oficiales de la SPDP (NORM-01, R4).

- Peticiones en serie, con una pausa de cortesía (2 s como mínimo) entre una y otra.
- Hasta 3 reintentos con espera exponencial, solo ante errores transitorios (5xx, tiempo agotado).
- Si la fuente responde 403, 429 o con una página de verificación, se detiene: `FuenteBloqueada`.
  El conector no evade controles del sitio ni reintenta en bucle.
- `User-Agent` genérico de la plataforma; sin datos de ninguna organización.
- La URL base viene de `NORMATIVA_SPDP_URL_BASE`; sin ella falla cerrado (`FuenteSinConfigurar`).
"""
from __future__ import annotations

import asyncio
import hashlib
import os
import re
from dataclasses import dataclass
from html import unescape
from typing import Awaitable, Callable
from urllib.parse import urljoin

import httpx

from features.inteligencia_normativa.domain.errores import (
    ArchivoDemasiadoGrande,
    ArchivoNoPdf,
    FuenteBloqueada,
    FuenteNoDisponible,
    FuenteSinConfigurar,
)

VARIABLE_URL_BASE = "NORMATIVA_SPDP_URL_BASE"
USER_AGENT = "EvydentiaMonitorNormativo/1.0"
SECCIONES = {
    "resoluciones": "/resoluciones/",
    "marco_normativo": "/marco-normativo/",
    "consultas_absueltas": "/consultas-absueltas/",
}
PAUSA_CORTESIA_SEGUNDOS = 2.0
MAXIMO_REINTENTOS = 3
ESPERA_BASE_SEGUNDOS = 1.0
TIMEOUT_SEGUNDOS = 30.0
MAXIMO_BYTES = 50 * 1024 * 1024
CABECERA_PDF = b"%PDF-"
CODIGOS_BLOQUEO = (403, 429)
MARCAS_VERIFICACION = ("captcha", "cf-challenge", "attention required", "verifying you are human", "verificando que")

_ENLACE_PDF = re.compile(r"<a\b[^>]*?href=[\"']([^\"']+\.pdf(?:\?[^\"']*)?)[\"'][^>]*>(.*?)</a>", re.I | re.S)
_ETIQUETAS = re.compile(r"<[^>]+>")


@dataclass(frozen=True)
class EnlacePdf:
    url: str
    titulo: str
    seccion: str


@dataclass(frozen=True)
class Descarga:
    contenido: bytes
    sha256: str
    tamano: int


def extraer_enlaces(html: str, url_pagina: str, seccion: str) -> list[EnlacePdf]:
    """Enlaces a PDF de una página de sección, sin duplicados y en el orden de aparición."""
    vistos: dict[str, EnlacePdf] = {}
    for href, texto in _ENLACE_PDF.findall(html):
        url = urljoin(url_pagina, unescape(href))
        titulo = re.sub(r"\s+", " ", unescape(_ETIQUETAS.sub(" ", texto))).strip()
        vistos.setdefault(url, EnlacePdf(url=url, titulo=titulo, seccion=seccion))
    return list(vistos.values())


def _es_pagina_de_verificacion(cuerpo: bytes) -> bool:
    muestra = cuerpo[:4096].lower()
    return any(marca.encode() in muestra for marca in MARCAS_VERIFICACION)


class ConectorSpdp:
    def __init__(
        self,
        cliente: httpx.AsyncClient | None = None,
        *,
        url_base: str | None = None,
        pausa: float = PAUSA_CORTESIA_SEGUNDOS,
        espera_base: float = ESPERA_BASE_SEGUNDOS,
        reintentos: int = MAXIMO_REINTENTOS,
        dormir: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self._cliente = cliente
        self._url_base = url_base
        self._pausa = pausa
        self._espera_base = espera_base
        self._reintentos = reintentos
        self._dormir = dormir
        self._peticiones = 0

    @property
    def peticiones(self) -> int:
        return self._peticiones

    def _base(self) -> str:
        base = (self._url_base or os.environ.get(VARIABLE_URL_BASE, "")).strip()
        if not base.startswith("https://"):
            raise FuenteSinConfigurar(VARIABLE_URL_BASE)
        return base if base.endswith("/") else base + "/"

    async def __aenter__(self) -> "ConectorSpdp":
        if self._cliente is None:
            self._cliente = httpx.AsyncClient(
                timeout=httpx.Timeout(TIMEOUT_SEGUNDOS), follow_redirects=False,
                headers={"User-Agent": USER_AGENT},
            )
            self._propio = True
        else:
            self._propio = False
        return self

    async def __aexit__(self, *_: object) -> None:
        if self._propio and self._cliente is not None:
            await self._cliente.aclose()

    async def _esperar_cortesia(self) -> None:
        if self._peticiones > 0:
            await self._dormir(self._pausa)
        self._peticiones += 1

    async def _con_reintentos(self, accion: Callable[[], Awaitable[object]]) -> object:
        ultimo: Exception | None = None
        for intento in range(self._reintentos + 1):
            await self._esperar_cortesia()
            try:
                return await accion()
            except (FuenteBloqueada, ArchivoNoPdf, ArchivoDemasiadoGrande):
                raise
            except (httpx.TransportError, FuenteNoDisponible) as exc:
                ultimo = exc
                if intento < self._reintentos:
                    await self._dormir(self._espera_base * (2 ** intento))
        raise FuenteNoDisponible(type(ultimo).__name__ if ultimo else "")

    @staticmethod
    def _revisar_estado(respuesta: httpx.Response) -> None:
        if respuesta.status_code in CODIGOS_BLOQUEO:
            raise FuenteBloqueada(str(respuesta.status_code))
        if respuesta.status_code >= 500:
            raise FuenteNoDisponible(str(respuesta.status_code))
        if respuesta.status_code >= 400:
            raise FuenteNoDisponible(str(respuesta.status_code))

    async def listar(self, seccion: str) -> list[EnlacePdf]:
        """Enlaces a PDF de una sección oficial."""
        url = urljoin(self._base(), SECCIONES[seccion].lstrip("/"))

        async def pedir() -> list[EnlacePdf]:
            respuesta = await self._cliente.get(url, headers={"User-Agent": USER_AGENT})
            self._revisar_estado(respuesta)
            if _es_pagina_de_verificacion(respuesta.content):
                raise FuenteBloqueada("verificacion")
            return extraer_enlaces(respuesta.text, url, seccion)

        return await self._con_reintentos(pedir)  # type: ignore[return-value]

    async def descargar(self, url: str) -> Descarga:
        """Descarga en streaming: valida `%PDF-` y calcula el SHA-256 mientras llegan los bytes."""

        async def pedir() -> Descarga:
            async with self._cliente.stream("GET", url, headers={"User-Agent": USER_AGENT}) as respuesta:
                self._revisar_estado(respuesta)
                hash_ = hashlib.sha256()
                partes: list[bytes] = []
                total = 0
                cabecera_revisada = False
                async for trozo in respuesta.aiter_bytes():
                    partes.append(trozo)
                    total += len(trozo)
                    if total > MAXIMO_BYTES:
                        raise ArchivoDemasiadoGrande()
                    hash_.update(trozo)
                    if not cabecera_revisada and total >= len(CABECERA_PDF):
                        inicio = b"".join(partes)
                        if _es_pagina_de_verificacion(inicio):
                            raise FuenteBloqueada("verificacion")
                        if not inicio.startswith(CABECERA_PDF):
                            raise ArchivoNoPdf()
                        cabecera_revisada = True
                if not cabecera_revisada:
                    raise ArchivoNoPdf()
            return Descarga(contenido=b"".join(partes), sha256=hash_.hexdigest(), tamano=total)

        return await self._con_reintentos(pedir)  # type: ignore[return-value]
