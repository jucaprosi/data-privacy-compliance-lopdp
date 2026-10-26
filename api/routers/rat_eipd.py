"""EIPD persistente: escritura exclusiva del DPO y lectura del resto de roles."""
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.routers.rat import get_rat_session
from api.rbac import get_context, get_usuario_autenticado
from app_core.audit import registrar_evento
from features.rat.rat_service import (
    RiesgoEIPD, aprobar_eipd_rat, comprobar_deriva_eipd_rat, crear_eipd_rat,
    editar_eipd_rat, leer_eipd_rat,
)

router = APIRouter(prefix="/rat/eipd", tags=["Evaluación de impacto"])
AUTO_REGISTRO = True


async def _contexto(
    authorization: str | None = Header(None), x_user_id: str = Header(""),
    x_tenant_id: str = Header("tenant-default"), x_role: str = Header("GESTOR_PROCESO"),
    session: AsyncSession = Depends(get_rat_session),
):
    usuario = await get_usuario_autenticado(authorization, x_user_id, session)
    return await get_context(usuario, x_tenant_id, x_role, session)


def _permiso(escritura=False):
    async def comprobar(ctx=Depends(_contexto)):
        roles = {"coordinador", "dpo", "implementador", "admin_organizacion", "responsable_area"}
        if ctx["role"] not in roles or escritura and ctx["role"] != "dpo":
            raise HTTPException(403, "Solo el DPO puede modificar o aprobar la EIPD")
        return ctx
    return comprobar


class RiesgoRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    descripcion: str
    probabilidad: int = Field(ge=1, le=5)
    impacto: int = Field(ge=1, le=5)
    medida: str = ""


class CrearEIPDRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rat_id: str
    descripcion: str
    riesgos: list[RiesgoRequest] = Field(min_length=1)


class EditarEIPDRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    descripcion: str


@router.post("")
async def crear(payload: CrearEIPDRequest, ctx=Depends(_permiso(True)),
                session: AsyncSession = Depends(get_rat_session)):
    riesgos = [RiesgoEIPD(**r.model_dump()) for r in payload.riesgos]
    eipd = await crear_eipd_rat(session, ctx["tenant_id"], payload.rat_id,
                                payload.descripcion, riesgos)
    if eipd is None:
        raise HTTPException(404, "Actividad RAT no encontrada")
    return {"eipd": eipd}


@router.get("/{eipd_id}")
async def leer(eipd_id: str, ctx=Depends(_permiso()),
               session: AsyncSession = Depends(get_rat_session)):
    eipd = await leer_eipd_rat(session, ctx["tenant_id"], eipd_id)
    if eipd is None:
        raise HTTPException(404, "EIPD no encontrada")
    return {"eipd": eipd}


@router.patch("/{eipd_id}")
async def editar(eipd_id: str, payload: EditarEIPDRequest, ctx=Depends(_permiso(True)),
                 session: AsyncSession = Depends(get_rat_session)):
    eipd = await editar_eipd_rat(session, ctx["tenant_id"], eipd_id, payload.descripcion)
    if eipd is None:
        raise HTTPException(404, "EIPD no encontrada")
    return {"eipd": eipd}


@router.post("/{eipd_id}/aprobar")
async def aprobar(eipd_id: str, ctx=Depends(_permiso(True)),
                  session: AsyncSession = Depends(get_rat_session)):
    eipd = await aprobar_eipd_rat(session, ctx["tenant_id"], eipd_id, ctx["user_id"])
    if eipd is None:
        raise HTTPException(404, "EIPD no encontrada")
    await registrar_evento(session, ctx["tenant_id"], "rat_eipd", eipd_id,
                           "aprobar", ctx["user_id"])
    return {"eipd": eipd}


@router.post("/rat/{rat_id}/evaluar-deriva")
async def evaluar_deriva(rat_id: str, ctx=Depends(_permiso(True)),
                         session: AsyncSession = Depends(get_rat_session)):
    deriva = await comprobar_deriva_eipd_rat(session, ctx["tenant_id"], rat_id)
    return {"requiere_actualizacion": deriva}
