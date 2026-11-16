# ¤¤developer-architect ¤seguridad ¤terceros
"""Router público de cuestionarios de garantías para encargados (TER-02).

Endpoints públicos:
- GET  /api/v1/publico/proveedor/{token}
- POST /api/v1/publico/proveedor/{token}
"""
from __future__ import annotations

import json
from typing import List
from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.db.session import get_session
from app_core.errors import ErrorNegocio
from features.terceros import terceros_service
from features.terceros.domain.cuestionario import CODIGO_ENLACE_NO_VALIDO

AUTO_REGISTRO = True

router = APIRouter(prefix="/publico/proveedor", tags=["Portal Proveedor - Garantías (TER-02)"])


CABECERAS_SEC12 = {
    "X-Robots-Tag": "noindex",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
}


def _aplicar_cabeceras_seguridad(response: Response) -> None:
    """SEC-12: Cabeceras obligatorias para portales externos."""
    for k, v in CABECERAS_SEC12.items():
        response.headers[k] = v


@router.get("/{token}")
async def ver_cuestionario_proveedor(
    token: str,
    response: Response,
    session: AsyncSession = Depends(get_session),
):
    _aplicar_cabeceras_seguridad(response)
    try:
        return await terceros_service.obtener_por_token(session, token)
    except ErrorNegocio as e:
        raise HTTPException(status_code=e.status_code, detail=e.code, headers=CABECERAS_SEC12)


@router.post("/{token}")
async def enviar_respuestas_proveedor(
    token: str,
    response: Response,
    respuestas: str = Form(..., description="JSON string con las respuestas"),
    archivos: List[UploadFile] = File(default=[]),
    session: AsyncSession = Depends(get_session),
):
    _aplicar_cabeceras_seguridad(response)
    try:
        try:
            respuestas_dict = json.loads(respuestas)
        except json.JSONDecodeError:
            raise HTTPException(status_code=422, detail="RESPUESTA_INCOMPLETA", headers=CABECERAS_SEC12)

        lista_archivos = []
        for f in archivos:
            contenido = await f.read()
            p_id = f.headers.get("x-pregunta-id") or (f.filename.split("_")[0] if f.filename else "G01")
            for prefix in ("G01", "G03", "G04", "G07", "G08", "G09", "G11", "G12", "G15"):
                if f.filename and f.filename.startswith(prefix):
                    p_id = prefix
                    break
            lista_archivos.append({
                "pregunta_id": p_id,
                "nombre": f.filename or "archivo.pdf",
                "contenido": contenido,
                "mime": f.content_type or "application/octet-stream",
            })

        return await terceros_service.responder_cuestionario(
            session, token, respuestas_dict, lista_archivos
        )
    except ErrorNegocio as e:
        raise HTTPException(status_code=e.status_code, detail=e.code, headers=CABECERAS_SEC12)
