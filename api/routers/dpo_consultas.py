# ¤dpo-cockpit ¤evidencias
"""Consultas de la organización al DPO (DPO-03).

- GET  /api/v1/dpo/consultas?estado=: propias, o todas si el rol es dpo, admin_organizacion o coordinador.
- POST /api/v1/dpo/consultas: abre una consulta (cualquier rol con membresía activa).
- POST /api/v1/dpo/consultas/{id}/mensajes: autor o dpo; tras el cierre, 409 CONSULTA_CERRADA.
- POST /api/v1/dpo/consultas/{id}/cerrar: solo `dpo`; asienta la OPINION_CONSULTIVA y la huella del hilo.

Identidad y organización salen de la sesión (membresía verificada); el cuerpo no las admite.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import get_context, require_role
from app_core.db.session import get_session
from features.dpo_cockpit.dpo_cockpit_service import (
    Consulta,
    MensajeConsulta,
    cerrar_consulta_dpo,
    crear_consulta_dpo,
    enviar_mensaje_consulta_dpo,
    listar_consultas_dpo,
)

AUTO_REGISTRO = True

router = APIRouter(prefix="/dpo/consultas", tags=["Cockpit del DPD/DPO · consultas de la organización"])


class ConsultaNueva(BaseModel):
    asunto: str
    texto: str


class MensajeNuevo(BaseModel):
    texto: str


class CierreConsulta(BaseModel):
    respuesta: str


def _mensaje(m: MensajeConsulta, usuario: str) -> dict:
    return {
        "secuencia": m.secuencia,
        "autor_rol": m.autor_rol,
        "autor_nombre": m.autor_nombre,
        "es_mio": m.autor_id == usuario,
        "texto": m.texto,
        "creado_en": m.creado_en.isoformat(),
    }


def _consulta(c: Consulta, usuario: str) -> dict:
    return {
        "id": c.id,
        "asunto": c.asunto,
        "estado": c.estado,
        "creado_en": c.creado_en.isoformat(),
        "cerrada_en": c.cerrada_en.isoformat() if c.cerrada_en else None,
        "huella_hilo": c.evidencia_sha256,
        "mensajes": [_mensaje(m, usuario) for m in c.mensajes],
    }


@router.get("")
async def listar(
    estado: Optional[str] = Query(None),
    ctx: dict = Depends(get_context),
    session: AsyncSession = Depends(get_session),
):
    consultas = await listar_consultas_dpo(session, ctx["tenant_id"], ctx["user_id"], ctx["role"], estado)
    return {"consultas": [_consulta(c, ctx["user_id"]) for c in consultas]}


@router.post("", status_code=201)
async def crear(
    payload: ConsultaNueva,
    ctx: dict = Depends(get_context),
    session: AsyncSession = Depends(get_session),
):
    c = await crear_consulta_dpo(session, ctx["tenant_id"], ctx["user_id"], ctx["role"], payload.asunto, payload.texto)
    return _consulta(c, ctx["user_id"])


@router.post("/{consulta_id}/mensajes", status_code=201)
async def enviar_mensaje(
    consulta_id: str,
    payload: MensajeNuevo,
    ctx: dict = Depends(get_context),
    session: AsyncSession = Depends(get_session),
):
    m = await enviar_mensaje_consulta_dpo(
        session, ctx["tenant_id"], consulta_id, ctx["user_id"], ctx["role"], payload.texto
    )
    return _mensaje(m, ctx["user_id"])


@router.post("/{consulta_id}/cerrar")
async def cerrar(
    consulta_id: str,
    payload: CierreConsulta,
    ctx: dict = Depends(require_role("dpo")),
    session: AsyncSession = Depends(get_session),
):
    c = await cerrar_consulta_dpo(
        session, ctx["tenant_id"], consulta_id, ctx["user_id"], ctx["role"], payload.respuesta
    )
    return {"dictamen_id": c.dictamen_id, "evidencia_sha256": c.evidencia_sha256, **_consulta(c, ctx["user_id"])}
