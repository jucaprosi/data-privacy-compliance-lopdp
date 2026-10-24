# ¤¤security-engineer
"""RAT persistido por organización. Permisos de RAT-01. ¤rat ¤rbac-tenant"""
from typing import Annotated
from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field, create_model, model_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.audit import registrar_evento
from api.rbac import get_context, get_usuario_autenticado
from app_core.db.session import get_session
from features.rat.domain.models import ActividadRAT, BaseLegitimacion, CategoriaTitular
from features.rat.rat_service import (
    registrar_actividad_rat, listar_actividades_rat,
    editar_actividad_rat, eliminar_actividad_rat,
)

router = APIRouter(prefix="/rat", tags=["Registro de Actividades de Tratamiento (RAT)"])
# ¤rat
async def get_rat_session(
    x_user_id: str = Header(""),
    x_tenant_id: str = Header("tenant-default"),
):
    """Conserva los nombres de cabecera publicados usando la sesión del núcleo."""
    async with asynccontextmanager(get_session)(x_user_id, x_tenant_id) as session:
        yield session


# ¤rat
async def _contexto_rat(
    authorization: str | None = Header(None),
    x_user_id: str = Header(""),
    x_tenant_id: str = Header("tenant-default"),
    x_role: str = Header("GESTOR_PROCESO"),
    session: AsyncSession = Depends(get_rat_session),
):
    usuario = await get_usuario_autenticado(authorization, x_user_id, session)
    return await get_context(usuario, x_tenant_id, x_role, session)


# ¤rat
def _permiso_rat(*roles):
    async def comprobar(ctx: dict = Depends(_contexto_rat)):
        if ctx["role"] not in roles:
            raise HTTPException(403, "Rol no autorizado para esta operación RAT")
        return ctx
    return comprobar


ESCRITURA = _permiso_rat("coordinador", "dpo")
LECTURA = _permiso_rat("coordinador", "dpo", "implementador", "admin_organizacion")
Origen = Annotated[str, Field(pattern=r"^(manual|plantilla:[^:\s]+)$")]


# ¤rat
class CrearActividadRATRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    codigo: str
    nombre: str
    area_responsable: str
    finalidad: str
    base_legal: BaseLegitimacion = BaseLegitimacion.CONSENTIMIENTO
    categorias_titulares: list[CategoriaTitular] = Field(default_factory=list)
    categorias_datos: list[str] = Field(default_factory=list)
    datos_sensibles: bool = False
    volumen_titulares_estimado: int = Field(0, ge=0)
    transferencia_internacional: bool = False
    requiere_eipd: bool = False
    es_gran_escala: bool = False
    medio_soporte: str = ""
    encargados: list[str] = Field(default_factory=list)
    destinatarios: list[str] = Field(default_factory=list)
    pais_transferencia: str = ""
    plazo_conservacion: str = ""
    medidas_seguridad: list[str] = Field(default_factory=list)
    nivel_riesgo: str = ""
    decisiones_automatizadas: bool = False
    volumen_titulares_12_meses: int = Field(0, ge=0)
    observaciones_dpo: str = ""
    origen: Origen = "manual"


# ¤rat
class _Parche(BaseModel):
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="before")
    @classmethod
    def sin_nulos(cls, valores):
        if isinstance(valores, dict) and (
            not valores or any(v is None for v in valores.values())
        ):
            raise ValueError("Indique al menos un campo, sin valores nulos")
        return valores


# Conserva tipos y restricciones de creación; solo hace opcional su presencia.
EditarActividadRATRequest = create_model(
    "EditarActividadRATRequest", __base__=_Parche,
    **{
        nombre: (campo.rebuild_annotation(), None)
        for nombre, campo in CrearActividadRATRequest.model_fields.items()
    },
)


@router.post("/actividades")
# ¤rat
async def crear_actividad(
    payload: CrearActividadRATRequest,
    ctx: dict = Depends(ESCRITURA),
    session: AsyncSession = Depends(get_rat_session),
):
    actividad = ActividadRAT(tenant_id=ctx["tenant_id"], **payload.model_dump())
    guardada = await registrar_actividad_rat(session, actividad, ctx["user_id"])
    await registrar_evento(session, ctx["tenant_id"], "rat_actividad", guardada.id,
                           "crear", ctx["user_id"])
    return {"status": "SUCCESS", "actividad": guardada}


@router.get("/actividades")
# ¤rat
async def listar_actividades(
    ctx: dict = Depends(LECTURA),
    session: AsyncSession = Depends(get_rat_session),
):
    actividades = await listar_actividades_rat(session, ctx["tenant_id"])
    return {"tenant_id": ctx["tenant_id"], "total": len(actividades), "actividades": actividades}


@router.patch("/actividades/{rat_id}")
# ¤rat
async def editar_actividad(
    rat_id: str,
    payload: EditarActividadRATRequest,
    ctx: dict = Depends(ESCRITURA),
    session: AsyncSession = Depends(get_rat_session),
):
    actividad = await editar_actividad_rat(
        session, ctx["tenant_id"], rat_id, payload.model_dump(exclude_unset=True),
        ctx["user_id"],
    )
    if actividad is None:
        raise HTTPException(404, "Actividad RAT no encontrada")
    await registrar_evento(session, ctx["tenant_id"], "rat_actividad", rat_id,
                           "editar", ctx["user_id"], {"campos": sorted(payload.model_fields_set)})
    return {"status": "SUCCESS", "actividad": actividad}


@router.delete("/actividades/{rat_id}")
# ¤rat
async def eliminar_actividad(
    rat_id: str,
    ctx: dict = Depends(ESCRITURA),
    session: AsyncSession = Depends(get_rat_session),
):
    if not await eliminar_actividad_rat(session, ctx["tenant_id"], rat_id, ctx["user_id"]):
        raise HTTPException(404, "Actividad RAT no encontrada")
    await registrar_evento(session, ctx["tenant_id"], "rat_actividad", rat_id,
                           "baja", ctx["user_id"])
    return {"status": "SUCCESS"}
