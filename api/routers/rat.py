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
from features.rat.rat_service import ActividadRAT, BaseLegitimacion, CategoriaTitular
# === RAT-05 ===
from features.rat.rat_service import CondicionHabilitante
# === fin RAT-05 ===
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


# ¤rat
def _permiso_escritura_rat():
    """Escribe el coordinador. El DPO no: supervisa con independencia (art. 48 LOPDP,
    INV_LOPDP_DPO_INDEPENDENCE) y aprobar la finalidad del RAT le es incompatible
    (ACCIONES_INCOMPATIBLES_DPO en app_core/security.py)."""
    async def comprobar(ctx: dict = Depends(_contexto_rat)):
        if ctx["role"] == "dpo":
            raise HTTPException(403, "Violación SoD: El DPO no puede modificar el RAT.")
        if ctx["role"] != "coordinador":
            raise HTTPException(403, "Rol no autorizado para esta operación RAT")
        return ctx
    return comprobar


ESCRITURA = _permiso_escritura_rat()
LECTURA = _permiso_rat("coordinador", "dpo", "implementador", "admin_organizacion")
Origen = Annotated[str, Field(pattern=r"^(manual|plantilla:[^:\s]+)$")]


# ¤rat
class CrearActividadRATRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    codigo: str
    nombre: str
    area_responsable: str = ""
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
    # === RAT-05 ===
    condicion_habilitante: CondicionHabilitante | None = None
    # === fin RAT-05 ===
    # === RAT-08 ===
    area_id: str | None = None

    @model_validator(mode="after")
    def validar_area(self) -> "CrearActividadRATRequest":
        if not self.area_id and not (self.area_responsable and self.area_responsable.strip()):
            raise ValueError("area_responsable es obligatoria si no se indica area_id")
        return self
    # === fin RAT-08 ===


# ¤rat
class _Parche(BaseModel):
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="before")
    @classmethod
    def sin_nulos(cls, valores):
        if isinstance(valores, dict):
            permiten_none = {"area_id", "condicion_habilitante"}
            if not valores or any(v is None for k, v in valores.items() if k not in permiten_none):
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
    datos = payload.model_dump()
    # === RAT-08 ===
    if payload.area_id:
        from app_core.pasillo.organizacion import area_del_tenant
        area = await area_del_tenant(session, ctx["tenant_id"], payload.area_id)
        if not area:
            raise HTTPException(422, "AREA_NO_VALIDA")
        datos["area_responsable"] = area["nombre"]
    # === fin RAT-08 ===
    actividad = ActividadRAT(tenant_id=ctx["tenant_id"], **datos)
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
    # === RAT-08 ===
    from dataclasses import asdict
    from app_core.pasillo.organizacion import listar_areas
    areas = await listar_areas(session, ctx["tenant_id"])
    areas_vivas = {a["id"]: a["nombre"] for a in areas}
    lista = []
    for act in actividades:
        d = asdict(act) if hasattr(act, "__dataclass_fields__") else dict(act)
        if d.get("area_id") and d["area_id"] in areas_vivas:
            d["area_responsable"] = areas_vivas[d["area_id"]]
        lista.append(d)
    return {"tenant_id": ctx["tenant_id"], "total": len(lista), "actividades": lista}
    # === fin RAT-08 ===


@router.patch("/actividades/{rat_id}")
# ¤rat
async def editar_actividad(
    rat_id: str,
    payload: EditarActividadRATRequest,
    ctx: dict = Depends(ESCRITURA),
    session: AsyncSession = Depends(get_rat_session),
):
    cambios = payload.model_dump(exclude_unset=True)
    # === RAT-08 ===
    if "area_id" in cambios and cambios["area_id"] is not None:
        from app_core.pasillo.organizacion import area_del_tenant
        area = await area_del_tenant(session, ctx["tenant_id"], cambios["area_id"])
        if not area:
            raise HTTPException(422, "AREA_NO_VALIDA")
        cambios["area_responsable"] = area["nombre"]
    # === fin RAT-08 ===
    actividad = await editar_actividad_rat(
        session, ctx["tenant_id"], rat_id, cambios,
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
