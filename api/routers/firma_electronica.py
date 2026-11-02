# -*- coding: utf-8 -*-
# ¤firma-electronica ¤adpa ¤seguridad
"""API REST de la sala Firma Electrónica (FIRMA-04, BBAP paso 2).

Tres endpoints de sesiones resueltos con el tenant autenticado y un webhook público que se autentica
solo por la firma HMAC-SHA256 del cuerpo. Todo el acceso a datos pasa por la compuerta
`firma_electronica_service`. ANF y la pasarela siguen siendo bocetos sin red (D-4).
"""
import hashlib
import hmac
import logging
import os
from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.db.session import fijar_contexto_rls, get_session, get_tenant_session
from app_core.security import get_current_tenant
from features.firma_electronica import firma_electronica_service as firma

AUTO_REGISTRO = True
router = APIRouter(prefix="/firma", tags=["firma-electronica"])
logger = logging.getLogger(__name__)

SECRETO_WEBHOOK_ENV = "FIRMA_WEBHOOK_SECRET"
SESION_NO_EXISTE = "La sesión de firma no existe."


class SolicitudFirma(BaseModel):
    """Alta de una sesión de firma. La organización sale de la identidad, nunca del cuerpo."""

    documento_id: str = Field(min_length=1, max_length=100)
    firmante_id: str = Field(min_length=1, max_length=100)
    formato: Literal["pdf", "xml", "json"]
    proveedor: Literal["anf", "universign", "stub"]
    sha256_original: str = Field(pattern=r"^[0-9a-fA-F]{64}$")


class WebhookFirmaPayload(BaseModel):
    """Aviso del proveedor. `tenant_id` es necesario porque el webhook no trae identidad de usuario
    y la sesión solo se puede ubicar dentro de su organización."""

    firma_id: UUID
    tenant_id: UUID
    sha256_firmado: str = Field(min_length=1, max_length=128)
    timestamp_tsa: datetime
    certificado_json: Optional[dict] = None


def _verificar_hmac(payload: bytes, header_signature: Optional[str]) -> bool:
    """HMAC-SHA256 del cuerpo exacto, comparado en tiempo constante. Falla cerrada: sin secreto
    configurado o sin firma nunca se acepta (con clave vacía cualquiera podría falsificar el HMAC)."""
    secreto = os.environ.get(SECRETO_WEBHOOK_ENV, "")
    if not secreto or not header_signature:
        return False
    esperada = hmac.new(secreto.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    recibida = header_signature.strip().removeprefix("sha256=").lower()
    return hmac.compare_digest(esperada.encode("utf-8"), recibida.encode("utf-8"))


async def _tenant_uuid(tenant_id: str = Depends(get_current_tenant)) -> str:
    """Tenant autenticado; la tabla guarda UUID, así que un valor que no lo sea es un 422, no un 500."""
    try:
        return str(UUID(tenant_id))
    except ValueError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "El tenant debe ser un UUID.") from None


def _a_salida(sesion: firma.FirmaSession) -> dict:
    return {
        "firma_id": str(sesion.firma_id),
        "documento_id": sesion.documento_id,
        "firmante_id": sesion.firmante_id,
        "estado": sesion.estado,
        "formato": sesion.formato,
        "proveedor": sesion.proveedor,
        "sha256_original": sesion.sha256_original,
        "sha256_firmado": sesion.sha256_firmado,
        "timestamp_tsa": None if sesion.timestamp_tsa is None else sesion.timestamp_tsa.isoformat(),
        "certificado_json": sesion.certificado_json,
        "creado_en": sesion.creado_en.isoformat(),
        "actualizado_en": sesion.actualizado_en.isoformat(),
    }


@router.post("/sesiones", status_code=status.HTTP_201_CREATED)
async def crear_sesion(
    solicitud: SolicitudFirma,
    tenant_id: str = Depends(_tenant_uuid),
    session: AsyncSession = Depends(get_tenant_session),
):
    sesion = await firma.crear_sesion_firma(
        session,
        tenant_id,
        solicitud.documento_id.strip(),
        solicitud.firmante_id.strip(),
        solicitud.formato,
        solicitud.proveedor,
        solicitud.sha256_original.lower(),
    )
    return _a_salida(sesion)


@router.get("/sesiones/{firma_id}")
async def obtener_sesion(
    firma_id: UUID,
    tenant_id: str = Depends(_tenant_uuid),
    session: AsyncSession = Depends(get_tenant_session),
):
    sesion = await firma.obtener_sesion(session, firma_id, tenant_id)
    if sesion is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, SESION_NO_EXISTE)
    return _a_salida(sesion)


@router.get("/sesiones")
async def listar_sesiones(
    estado: Optional[str] = None,
    tenant_id: str = Depends(_tenant_uuid),
    session: AsyncSession = Depends(get_tenant_session),
):
    try:
        sesiones = await firma.listar_sesiones(session, tenant_id, estado)
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc
    return {"sesiones": [_a_salida(s) for s in sesiones]}


@router.post("/webhook")
async def webhook(
    request: Request,
    x_signature: Optional[str] = Header(None, alias="X-Signature"),
    session: AsyncSession = Depends(get_session),
):
    """Público: solo la firma HMAC-SHA256 autentica. Con firma inválida responde 401 sin interpretar
    el cuerpo ni tocar la base."""
    cuerpo = await request.body()
    if not _verificar_hmac(cuerpo, x_signature):
        logger.warning("Webhook de firma rechazado: HMAC inválido, ausente o secreto no configurado.")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "firma_invalida")
    try:
        payload = WebhookFirmaPayload.model_validate_json(cuerpo)
    except ValidationError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, exc.errors(include_url=False, include_context=False, include_input=False)
        ) from exc

    await fijar_contexto_rls(session, str(payload.tenant_id))
    try:
        sesion = await firma.marcar_firmado(
            session,
            payload.firma_id,
            payload.tenant_id,
            payload.sha256_firmado,
            payload.certificado_json or {},
            payload.timestamp_tsa,
        )
    except firma.SesionFirmaNoEncontradaError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, SESION_NO_EXISTE) from exc
    except firma.TransicionFirmaInvalidaError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    return {"firma_id": str(sesion.firma_id), "estado": sesion.estado}
