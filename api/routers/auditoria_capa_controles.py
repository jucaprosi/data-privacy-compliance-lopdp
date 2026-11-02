# ¤controles-periodicos ¤auditoria-capa ¤rbac-tenant
"""Controles periódicos (CAPA-02).

Contrato: governance/especificaciones/CAPA-02.md §2. Crea y retira quien gestiona; verifica el
`implementador` o el responsable del control (el motor lo comprueba); el `dpo` solo consulta (D-2).
Organización y autor salen del contexto autenticado.
"""
from typing import Literal, Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import require_role
from app_core.db.session import get_session
from features.auditoria_capa import auditoria_capa_service

AUTO_REGISTRO = True
router = APIRouter(prefix="/auditoria-capa", tags=["Auditoría y CAPA - Controles periódicos"])

ROLES_CONSULTA = ("implementador", "coordinador", "dpo", "admin_organizacion", "responsable_area")
ROLES_GESTION = ("implementador", "coordinador")
# El responsable puede tener cualquier rol salvo `dpo` (R2); el motor exige que el control sea suyo.
ROLES_VERIFICACION = ("implementador", "coordinador", "admin_organizacion", "responsable_area")
ROLES_VENCIMIENTO = ("implementador",)

_consulta = require_role(*ROLES_CONSULTA)
_gestion = require_role(*ROLES_GESTION)
_verificacion = require_role(*ROLES_VERIFICACION)
_vencimiento = require_role(*ROLES_VENCIMIENTO)

FiltroEstado = Optional[Literal["vigente", "vencido", "retirado"]]


@router.get("/controles")
async def listar(
    estado: FiltroEstado = None,
    ctx: dict = Depends(_consulta),
    session: AsyncSession = Depends(get_session),
):
    controles = await auditoria_capa_service.listar_controles(
        session, ctx["tenant_id"], ctx["user_id"], ctx["role"], estado=estado
    )
    return {"controles": [c.a_dict() for c in controles]}


@router.post("/controles", status_code=status.HTTP_201_CREATED)
async def crear(
    payload: auditoria_capa_service.CrearControlEntrada,
    ctx: dict = Depends(_gestion),
    session: AsyncSession = Depends(get_session),
):
    control = await auditoria_capa_service.crear_control(session, ctx["tenant_id"], ctx["user_id"], payload)
    return control.a_dict()


@router.post("/controles/vencer")
async def vencer(
    ctx: dict = Depends(_vencimiento),
    session: AsyncSession = Depends(get_session),
):
    resultado = await auditoria_capa_service.vencer_controles(session, ctx["tenant_id"], ctx["user_id"])
    return resultado.a_dict()


@router.post("/controles/{control_id}/verificaciones", status_code=status.HTTP_201_CREATED)
async def verificar(
    control_id: str,
    payload: auditoria_capa_service.VerificarControlEntrada,
    ctx: dict = Depends(_verificacion),
    session: AsyncSession = Depends(get_session),
):
    control, verificacion = await auditoria_capa_service.registrar_verificacion(
        session, ctx["tenant_id"], ctx["user_id"], ctx["role"], control_id, payload
    )
    return {"control": control.a_dict(), "verificacion": verificacion.a_dict()}


@router.post("/controles/{control_id}/retirar")
async def retirar(
    control_id: str,
    payload: auditoria_capa_service.RetirarControlEntrada,
    ctx: dict = Depends(_gestion),
    session: AsyncSession = Depends(get_session),
):
    control = await auditoria_capa_service.retirar_control(
        session, ctx["tenant_id"], ctx["user_id"], control_id, payload
    )
    return control.a_dict()
