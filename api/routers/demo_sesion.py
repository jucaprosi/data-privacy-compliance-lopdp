# -*- coding: utf-8 -*-
# ¤demo
"""Ciclo de la demo comercial (DEMO-02): `/api/v1/demo/entrar`, `/terminar` y `/estado`.

Solo existe con `APP_ENV=demo`: en cualquier otro entorno el router no se registra y `/demo/*` responde 404.
La identidad sale del token de Google verificado (el vendedor no es usuario de la base demo). Los errores
llevan el cuerpo congelado `{codigo, mensaje}` de FLUJOS_Y_MATRIZ_DEMO_EVYDENTIA.md §1.7. Nunca devuelve el
correo ni el `sub` del vendedor.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Header, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.db.session import get_session
from app_core.entorno import entorno_actual
from app_core.errors import CATALOGO_ERRORES
from app_core.security import IdentidadVerificada, extraer_bearer, verificar_token_google
from features.demo import demo_service

AUTO_REGISTRO = entorno_actual() == "demo"

router = APIRouter(prefix="/demo", tags=["Demo comercial"])


async def identidad_del_vendedor(authorization: Optional[str] = Header(None)) -> IdentidadVerificada:
    return await verificar_token_google(extraer_bearer(authorization))


def _cuerpo_de(error: Exception) -> JSONResponse | None:
    """Respuesta congelada de un error de la demo (`ErrorDemo`: `status_code` y `cuerpo()`); None si es otro.

    El router solo entra por la compuerta, así que reconoce el error por su forma y no importa el dominio.
    """
    cuerpo = getattr(error, "cuerpo", None)
    status_code = getattr(error, "status_code", None)
    if callable(cuerpo) and isinstance(status_code, int):
        return JSONResponse(status_code=status_code, content=cuerpo())
    return None


def _no_disponible() -> JSONResponse:
    codigo = CATALOGO_ERRORES["DEMO_NO_DISPONIBLE"]
    return JSONResponse(status_code=codigo.status_code,
                        content={"codigo": codigo.codigo, "mensaje": codigo.mensaje_defecto})


def _o_relanzar(error: Exception) -> JSONResponse:
    respuesta = _cuerpo_de(error)
    if respuesta is None:
        raise error
    return respuesta


@router.post("/entrar", status_code=status.HTTP_201_CREATED)
async def entrar(
    identidad: IdentidadVerificada = Depends(identidad_del_vendedor),
    session: AsyncSession = Depends(get_session),
):
    """Abre la demo del vendedor: 201 con el estado; 403, 409 o 503 con el cuerpo congelado."""
    try:
        estado = await demo_service.entrar(session, identidad.sub, identidad.email)
    except Exception as error:  # noqa: BLE001 - los ErrorDemo llevan cuerpo congelado; el resto sube
        return _o_relanzar(error)
    return estado.a_dict()


@router.post("/terminar", status_code=status.HTTP_204_NO_CONTENT)
async def terminar(
    identidad: IdentidadVerificada = Depends(identidad_del_vendedor),
    session: AsyncSession = Depends(get_session),
):
    """Vence la demo con motivo `terminar`; la aplicación no borra nada (los datos los purga el job nocturno)."""
    await demo_service.terminar(session, identidad.sub)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/estado")
async def estado(
    identidad: IdentidadVerificada = Depends(identidad_del_vendedor),
    session: AsyncSession = Depends(get_session),
):
    """Organización, persona activa, `personas[]` y vencimiento; 401 `DEMO_VENCIDA` si la demo terminó."""
    try:
        return (await demo_service.estado(session, identidad.sub)).a_dict()
    except NotImplementedError:  # el motor de DEMO-01 aún no está desplegado
        return _no_disponible()
    except Exception as error:  # noqa: BLE001
        return _o_relanzar(error)
