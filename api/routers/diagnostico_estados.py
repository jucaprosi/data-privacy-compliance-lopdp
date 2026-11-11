# ¤diagnostico ¤diagnostico-estados ¤dpo-independencia ¤rbac-tenant
"""API de los estados del diagnóstico: el assessment actual (DIAG-12).

Solo el DPO emite un estado; el coordinador, el implementador y el administrador consultan. Un estado
sellado no se edita ni se borra. La organización y la identidad salen del token, nunca del cuerpo.
"""
from typing import Literal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import require_role
from app_core.db.session import get_session
from features.diagnostico import diagnostico_service

AUTO_REGISTRO = True
router = APIRouter(prefix="/diagnostico", tags=["Diagnóstico"])

ROLES_EMISION = ("dpo",)
ROLES_CONSULTA = ("dpo", "implementador", "coordinador", "admin_organizacion")

_emision = require_role(*ROLES_EMISION)
_consulta = require_role(*ROLES_CONSULTA)


@router.post("/estados", status_code=status.HTTP_201_CREATED)
async def emitir(ctx: dict = Depends(_emision), session: AsyncSession = Depends(get_session)):
    return await diagnostico_service.emitir_estado(session, ctx["tenant_id"], ctx["user_id"])


@router.get("/estados")
async def historial(ctx: dict = Depends(_consulta), session: AsyncSession = Depends(get_session)):
    estados = await diagnostico_service.listar_estados(session, ctx["tenant_id"], ctx["user_id"])
    alterado = diagnostico_service.primer_estado_alterado(estados)
    return {
        "estados": [diagnostico_service.estado_a_salida(e) for e in reversed(estados)],
        "cadena_integra": alterado is None,
        "primer_alterado": alterado["id"] if alterado else None,
    }


@router.get("/estados/{estado_id}/comparativo")
async def comparativo(
    estado_id: str,
    con: Literal["real", "anterior"] = Query("real"),
    ctx: dict = Depends(_consulta),
    session: AsyncSession = Depends(get_session),
):
    return await diagnostico_service.comparar_estado(session, ctx["tenant_id"], ctx["user_id"], estado_id, con)
