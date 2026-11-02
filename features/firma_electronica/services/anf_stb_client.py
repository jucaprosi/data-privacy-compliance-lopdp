# -*- coding: utf-8 -*-
# ¤adpa
# ¤firma-electronica
"""Cliente HTTP de ANF STB v2 en su ambiente TEST (FIRMA-06, BBAP paso 2).

Contrato: ficha técnica TEST de ANF (Swagger del servicio WS 1), resumido en
`governance/especificaciones/FIRMA-06.md`. El firmado es asíncrono: `POST /signs` devuelve un id y
`GET /signs/{id}/get-signed-documents` entrega el PDF cuando termina. ANF no envía webhooks.

Solo se habla con TEST: `entorno` es siempre `DEV` y un despliegue de producción se niega a llamar,
porque en TEST las firmas son precargadas y no tienen valor probatorio. Las credenciales salen de
`app_core.config` y nunca se registran en logs ni en auditoría.
"""
from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass, field
from typing import Any, Optional, Sequence
from urllib.parse import quote, urlsplit

import httpx

from app_core.config import config

CLIENTE_ANF = "SMART-CIDI"
ENTORNO_ANF = "DEV"
TIPO_CERT_PERSONA_NATURAL = "1"  # El único habilitado en TEST para la cédula de pruebas de ANF.
TAMANIO_FUENTE = 10
AMBIENTES_PRODUCCION = ("production", "prod", "produccion")

# Testigos que ANF exige en toda petición (al menos OTP o biométrico). En TEST no hay titular real.
TESTIGOS_TEST: dict[str, Any] = {
    "otp": True,
    "biometrico": False,
    "registroCivil": True,
    "aceptaEmisionFirma": True,
    "aceptaFirmar": True,
    "porcentajeVerificacion": 100,
    "cliente": CLIENTE_ANF,
    "entorno": ENTORNO_ANF,
}

_TIMEOUT = httpx.Timeout(45.0)
_TRANSPORTE: Optional[httpx.AsyncBaseTransport] = None  # Lo sustituyen las pruebas; None es la red real.


class AnfStbNoConfiguradoError(Exception):
    """Faltan URL o credenciales, la URL no es https o el despliegue es de producción."""


class AnfStbError(Exception):
    """Fallo de ANF. `definitivo` indica un rechazo documentado (400/409): reintentar no lo arregla."""

    def __init__(self, tipo: str, definitivo: bool):
        super().__init__(tipo)
        self.tipo = tipo
        self.definitivo = definitivo


@dataclass(frozen=True)
class DocumentoFirmadoAnf:
    """PDF firmado devuelto por ANF con la configuración de firmantes que él mismo repite."""
    pdf: bytes = field(repr=False)
    firmantes: list[dict[str, Any]]


def _usa_login() -> bool:
    return bool(config.anf_api_id.strip() and config.anf_api_password.get_secret_value())


def esta_configurado() -> bool:
    """Hay consumo remoto solo con URL https, credenciales y un despliegue que no sea producción."""
    if config.environment.strip().lower() in AMBIENTES_PRODUCCION:
        return False
    url = urlsplit(config.anf_stb_url.strip())
    return (
        url.scheme == "https"
        and bool(url.hostname)
        and (_usa_login() or bool(config.anf_api_token.get_secret_value()))
    )


def es_ambiente_de_pruebas() -> bool:
    return config.environment.strip().lower() == "test"


def _cliente() -> httpx.AsyncClient:
    if not esta_configurado():
        raise AnfStbNoConfiguradoError("ANF STB no está habilitado en este ambiente.")
    return httpx.AsyncClient(
        base_url=config.anf_stb_url.strip().rstrip("/"),
        timeout=_TIMEOUT,
        follow_redirects=False,
        transport=_TRANSPORTE,
    )


def _leer(respuesta: httpx.Response, rechazo_definitivo: bool = True) -> Any:
    """JSON de un 200, o `AnfStbError` con el `typeCode` de ANF. Solo 400 y 409 son rechazos."""
    if respuesta.status_code != 200:
        try:
            cuerpo = respuesta.json()
        except ValueError:
            cuerpo = None
        tipo = cuerpo.get("typeCode") if isinstance(cuerpo, dict) else None
        definitivo = rechazo_definitivo and respuesta.status_code in (400, 409)
        raise AnfStbError(str(tipo or f"HTTP{respuesta.status_code}"), definitivo)
    try:
        return respuesta.json()
    except ValueError:
        raise AnfStbError("RespuestaInvalida", False) from None


async def _token(cliente: httpx.AsyncClient) -> str:
    """JWT de 10 minutos por operación: es más simple y seguro que retenerlo en un proceso serverless."""
    if not _usa_login():
        return config.anf_api_token.get_secret_value()
    # Un 400 aquí es de credenciales, no de la firma: no debe cerrar ninguna sesión.
    respuesta = await cliente.post(
        "/auth", json={"id": config.anf_api_id.strip(), "password": config.anf_api_password.get_secret_value()}
    )
    token = _leer(respuesta, rechazo_definitivo=False)
    if not isinstance(token, str) or not token:
        raise AnfStbError("RespuestaInvalida", False)
    return token


async def solicitar_firma(pdf: bytes, descripcion: str, firmante_id: str, paginas: Sequence[str]) -> str:
    """`POST /signs` con un documento y un firmante precargado; devuelve el id de la petición."""
    peticion = {
        "certificadoEs": False,
        "withTSU": True,
        "testigos": TESTIGOS_TEST,
        "documentos": [
            {
                "descripcion": descripcion,
                "documento": base64.b64encode(pdf).decode("ascii"),
                "firmantes": [
                    {
                        "id": firmante_id,
                        "tipoCert": TIPO_CERT_PERSONA_NATURAL,
                        "tamanioFuente": TAMANIO_FUENTE,
                        "paginas": list(paginas),
                    }
                ],
            }
        ],
    }
    try:
        async with _cliente() as cliente:
            cabeceras = {"Authorization": await _token(cliente)}
            solicitud_id = _leer(await cliente.post("/signs", json=peticion, headers=cabeceras))
    except httpx.HTTPError:
        raise AnfStbError("SinRespuesta", False) from None
    if not isinstance(solicitud_id, str) or not solicitud_id:
        raise AnfStbError("RespuestaInvalida", False)
    return solicitud_id


def _documento_firmado(cuerpo: Any, descripcion: str) -> DocumentoFirmadoAnf:
    """Valida el arreglo de ANF: un PDF de verdad, no solo un 200."""
    documentos = cuerpo if isinstance(cuerpo, list) else []
    documento = next((d for d in documentos if isinstance(d, dict) and d.get("descripcion") == descripcion), None)
    if documento is None:
        raise AnfStbError("RespuestaInvalida", False)
    try:
        pdf = base64.b64decode(documento.get("documento", ""), validate=True)
    except (binascii.Error, TypeError, ValueError):
        raise AnfStbError("RespuestaInvalida", False) from None
    if not pdf.startswith(b"%PDF-"):
        raise AnfStbError("RespuestaInvalida", False)
    firmantes = documento.get("firmantes")
    return DocumentoFirmadoAnf(pdf=pdf, firmantes=firmantes if isinstance(firmantes, list) else [])


async def consultar_documentos(solicitud_id: str, descripcion: str) -> Optional[DocumentoFirmadoAnf]:
    """`GET /signs/{id}/get-signed-documents`. `None` mientras ANF siga firmando (responde un texto)."""
    try:
        async with _cliente() as cliente:
            cabeceras = {"Authorization": await _token(cliente), "Content-Type": "application/json"}
            respuesta = await cliente.get(
                f"/signs/{quote(solicitud_id, safe='')}/get-signed-documents", headers=cabeceras
            )
    except httpx.HTTPError:
        raise AnfStbError("SinRespuesta", False) from None
    cuerpo = _leer(respuesta)
    return None if isinstance(cuerpo, str) else _documento_firmado(cuerpo, descripcion)


__all__ = [
    "AnfStbError",
    "AnfStbNoConfiguradoError",
    "DocumentoFirmadoAnf",
    "consultar_documentos",
    "es_ambiente_de_pruebas",
    "esta_configurado",
    "solicitar_firma",
]
