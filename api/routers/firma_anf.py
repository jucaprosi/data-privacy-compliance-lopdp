# -*- coding: utf-8 -*-
# ¤firma-electronica ¤adpa ¤seguridad
"""API REST del firmado con ANF STB v2 en ambiente TEST (FIRMA-06, BBAP paso 2).

ANF no envía webhooks: el firmado se cierra consultándolo. `enviar` entrega el PDF y deja la sesión
en `pendiente_firma`; `sincronizar` pregunta una vez y, si ANF terminó, la cierra. Son dos pasos para
no retener una transacción los 90 s que ANF puede tardar. El webhook de FIRMA-04 no cambia.
Estas rutas nunca usan el boceto: una firma simulada no puede llegar a `firma_sessions`.
"""
import base64
import binascii
import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.errores import ErrorNegocio
from api.routers.firma_electronica import _a_salida, _tenant_uuid
from app_core.db.session import get_tenant_session
from app_core.errors import (
    ANF_NO_CONFIGURADO,
    ANF_NO_DISPONIBLE,
    ANF_RECHAZO,
    FIRMA_DOCUMENTO_INVALIDO,
    FIRMA_ESTADO_INVALIDO,
    FIRMA_PROVEEDOR_INVALIDO,
    FIRMA_SESION_NO_ENCONTRADA,
)
from features.firma_electronica import firma_electronica_service as firma

AUTO_REGISTRO = True
router = APIRouter(prefix="/firma/sesiones", tags=["firma-electronica"])
logger = logging.getLogger(__name__)

MAX_BASE64 = 5_600_000  # 4 MB de PDF: lo que cabe en el límite de cuerpo de Vercel (4,5 MB).
RE_PAGINA = r"^(primera|ultima|[1-9][0-9]*)\([0-9]{1,4}, ?[0-9]{1,4}\)$"


class EnvioAnf(BaseModel):
    """PDF de la sesión y posiciones de estampado con el formato `#(x, y)` de ANF."""

    documento_base64: str = Field(min_length=8, max_length=MAX_BASE64)
    paginas: list[Annotated[str, Field(pattern=RE_PAGINA)]] = Field(
        default_factory=lambda: list(firma.PAGINAS_ANF_DEFECTO), min_length=1, max_length=20
    )


def _pdf(documento_base64: str) -> bytes:
    try:
        pdf = base64.b64decode(documento_base64, validate=True)
    except (binascii.Error, ValueError):
        raise ErrorNegocio(FIRMA_DOCUMENTO_INVALIDO) from None
    if not pdf.startswith(b"%PDF-"):
        raise ErrorNegocio(FIRMA_DOCUMENTO_INVALIDO)
    return pdf


def _exigir_anf() -> None:
    if not firma.anf_stb_configurado():
        raise ErrorNegocio(ANF_NO_CONFIGURADO)


async def _sesion_anf(session: AsyncSession, firma_id: UUID, tenant_id: str) -> firma.FirmaSession:
    sesion = await firma.obtener_sesion(session, firma_id, tenant_id)
    if sesion is None:
        raise ErrorNegocio(FIRMA_SESION_NO_ENCONTRADA)
    if sesion.proveedor != "anf" or sesion.formato != "pdf":
        raise ErrorNegocio(FIRMA_PROVEEDOR_INVALIDO)
    return sesion


def _documento(sesion: firma.FirmaSession, tamano_bytes: int = 0) -> firma.DocumentoParaFirma:
    return firma.DocumentoParaFirma(
        documento_id=sesion.documento_id,
        tenant_id=str(sesion.tenant_id),
        nombre_archivo=f"{sesion.documento_id}.pdf",
        mime_type="application/pdf",
        sha256_original=sesion.sha256_original,
        tamano_bytes=tamano_bytes,
    )


def _error_anf(exc: firma.AnfStbError) -> ErrorNegocio:
    logger.warning("ANF STB falló: %s (definitivo=%s)", exc.tipo, exc.definitivo)
    return ErrorNegocio(ANF_RECHAZO if exc.definitivo else ANF_NO_DISPONIBLE, action_required=exc.tipo)


@router.post("/{firma_id}/anf/enviar", status_code=status.HTTP_202_ACCEPTED)
async def enviar_a_anf(
    firma_id: UUID,
    envio: EnvioAnf,
    tenant_id: str = Depends(_tenant_uuid),
    session: AsyncSession = Depends(get_tenant_session),
):
    """Reserva la sesión y entrega el PDF a ANF. Si ANF falla, la reserva revierte a `borrador`."""
    _exigir_anf()
    sesion = await _sesion_anf(session, firma_id, tenant_id)
    if sesion.estado != "borrador":
        raise ErrorNegocio(FIRMA_ESTADO_INVALIDO)
    pdf = _pdf(envio.documento_base64)
    try:
        await firma.reservar_envio_anf(session, firma_id, tenant_id)
        solicitud_id = await firma.solicitar_firma_anf_stb(
            _documento(sesion, len(pdf)), sesion.firmante_id, pdf, envio.paginas
        )
        return _a_salida(await firma.registrar_solicitud_anf(session, firma_id, tenant_id, solicitud_id))
    except ValueError as exc:
        raise ErrorNegocio(FIRMA_DOCUMENTO_INVALIDO) from exc
    except firma.TransicionFirmaInvalidaError as exc:
        raise ErrorNegocio(FIRMA_ESTADO_INVALIDO) from exc
    except firma.AnfStbNoConfiguradoError as exc:
        raise ErrorNegocio(ANF_NO_CONFIGURADO) from exc
    except firma.AnfStbError as exc:
        raise _error_anf(exc) from exc


@router.post("/{firma_id}/anf/sincronizar")
async def sincronizar_con_anf(
    firma_id: UUID,
    response: Response,
    tenant_id: str = Depends(_tenant_uuid),
    session: AsyncSession = Depends(get_tenant_session),
):
    """Consulta ANF una vez: 202 si sigue firmando, 200 con el PDF firmado o con el rechazo."""
    _exigir_anf()
    sesion = await _sesion_anf(session, firma_id, tenant_id)
    solicitud_id = sesion.metadatos.get(firma.CLAVE_SOLICITUD)
    if sesion.estado != "pendiente_firma" or not solicitud_id:
        raise ErrorNegocio(FIRMA_ESTADO_INVALIDO)
    try:
        resultado = await firma.consultar_firma_anf_stb(_documento(sesion), sesion.firmante_id, solicitud_id)
    except firma.AnfStbNoConfiguradoError as exc:
        raise ErrorNegocio(ANF_NO_CONFIGURADO) from exc
    except firma.AnfStbError as exc:
        if not exc.definitivo:
            raise _error_anf(exc) from exc
        rechazada = await firma.rechazar_firma_anf(session, firma_id, tenant_id, exc.tipo)
        return {"firma_id": str(rechazada.firma_id), "estado": rechazada.estado, "anf_error": exc.tipo}
    if resultado is None:
        response.status_code = status.HTTP_202_ACCEPTED
        return {"firma_id": str(sesion.firma_id), "estado": sesion.estado}
    try:
        firmada = await firma.marcar_firmado(
            session, firma_id, tenant_id, resultado.sha256_firmado,
            resultado.metadatos_auditoria, resultado.timestamp_tsa,
        )
    except (firma.SesionFirmaNoEncontradaError, firma.TransicionFirmaInvalidaError) as exc:
        raise ErrorNegocio(FIRMA_ESTADO_INVALIDO) from exc
    return {
        "firma_id": str(firmada.firma_id),
        "estado": firmada.estado,
        "sha256_firmado": firmada.sha256_firmado,
        "documento_firmado_base64": base64.b64encode(resultado.pdf_firmado).decode("ascii"),
    }
