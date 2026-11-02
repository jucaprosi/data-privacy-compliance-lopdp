# ¤firma-electronica
"""Rutas públicas de aceptación (FIRMA-02) — sin autenticación de usuario.

El token en la URL identifica el enlace; no requiere cabeceras de identidad ni tenant.
R4: solo devuelve los datos del propio enlace; nunca datos del documento ni otras aceptaciones.
"""
from __future__ import annotations

import ipaddress
from typing import Optional

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from api.errores import ErrorNegocio
from app_core.db.session import get_session
from features.firma_electronica import firma_electronica_service as firma

AUTO_REGISTRO = True
router = APIRouter(prefix="/aceptar", tags=["aceptacion-publica"])


def _ip_cliente(request: Request) -> Optional[str]:
    """Extrae la IP real del cliente con soporte para proxies (X-Forwarded-For)."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        raw = forwarded.split(",")[0].strip()
    else:
        raw = request.client.host if request.client else None
    if not raw:
        return None
    try:
        return str(ipaddress.ip_address(raw))
    except ValueError:
        return None


class CuerpoAceptar(BaseModel):
    acepto: bool


@router.get("/{token}")
async def info_aceptacion(
    token: str,
    session: AsyncSession = Depends(get_session),
):
    """Devuelve nombre del documento, organización y sha256. No expone token ni otras aceptaciones."""
    info = await firma.obtener_info_publica(session, token)
    return {
        "nombre_documento": info.nombre_documento,
        "organizacion": info.organizacion,
        "sha256": info.sha256,
    }


@router.post("/{token}")
async def aceptar(
    token: str,
    cuerpo: CuerpoAceptar,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """Registra la aceptación y devuelve el acuse_sha256. El enlace queda desactivado tras el primer uso."""
    if not cuerpo.acepto:
        raise ErrorNegocio("ACEPTACION_REQUERIDA", detail="El campo acepto debe ser true.", status_code=422)
    ip = _ip_cliente(request)
    acuse_sha256 = await firma.registrar_aceptacion(session, token, ip)
    return {"acuse_sha256": acuse_sha256}
