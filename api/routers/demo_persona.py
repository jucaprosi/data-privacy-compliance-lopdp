# -*- coding: utf-8 -*-
# ¤demo ¤seguridad
"""`POST /api/v1/demo/persona` (DEMO-01, FLUJOS_Y_MATRIZ_DEMO_EVYDENTIA.md §1.2 y §1.7).

Solo existe con `APP_ENV=demo`: fuera de la demo el módulo no se registra (`AUTO_REGISTRO` es falso) y todo
`/api/v1/demo/*` responde 404. Con la demo, este módulo registra además el resolutor de identidad de la sala
en el gancho de DEMO-08, por el pasillo de `demo`, una sola vez por proceso.

La identidad sale del token de Google verificado: ni una cabecera ni `AUTH_MODE` deciden quién es el vendedor.
La respuesta es la persona activa; su `rol` es el `X-Role` con el que el navegador pide en adelante, y
`require_role` lo sigue comprobando contra `user_tenant_roles`.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.db.session import get_session
from app_core.entorno.guardias import entorno_actual
from app_core.pasillo import demo as pasillo_demo
from app_core.security import extraer_bearer, registrar_resolutor_identidad, verificar_token_google
from features.demo import demo_service

AUTO_REGISTRO = entorno_actual() == "demo"

router = APIRouter(prefix="/demo", tags=["Demo comercial"])

if AUTO_REGISTRO:
    registrar_resolutor_identidad(pasillo_demo.resolver_usuario)


def _respuesta_de_error(error: Exception) -> JSONResponse | None:
    """Cuerpo congelado `{codigo, mensaje}` de un error de la demo; None si es otro error.

    El router solo entra por la compuerta (ADPA): reconoce el `ErrorDemo` por su forma, sin importar el dominio.
    """
    cuerpo = getattr(error, "cuerpo", None)
    status_code = getattr(error, "status_code", None)
    if callable(cuerpo) and isinstance(status_code, int):
        return JSONResponse(status_code=status_code, content=cuerpo())
    return None


class CuerpoPersona(BaseModel):
    persona_usuario_id: str = Field(min_length=1, max_length=200)


@router.post("/persona")
async def cambiar_persona(
    cuerpo: CuerpoPersona,
    authorization: str | None = Header(None),
    session: AsyncSession = Depends(get_session),
):
    """Cambia la persona activa del vendedor; 403 `DEMO_PERSONA_AJENA` si no es de su demostración."""
    identidad = await verificar_token_google(extraer_bearer(authorization))
    try:
        persona = await demo_service.cambiar_persona(session, identidad.sub, cuerpo.persona_usuario_id)
    except Exception as error:  # noqa: BLE001 - los ErrorDemo llevan cuerpo congelado; el resto sube
        respuesta = _respuesta_de_error(error)
        if respuesta is None:
            raise
        return respuesta
    return persona.a_dict()
