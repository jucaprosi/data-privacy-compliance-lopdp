"""Enrutador REST para la Sala ADPA: Cockpit del DPD/DPO (Art. 48-50 LOPDP)."""
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import get_context, get_usuario_autenticado
from app_core.audit import registrar_evento
from app_core.db.session import get_session
from app_core.security import MODO_HEADERS, modo_autenticacion, roles_activos
from features.dpo_cockpit.dpo_cockpit_service import DictamenDPO, TipoDictamenDPO
from features.dpo_cockpit.dpo_cockpit_service import (
    AcuseYaRegistradoError,
    firmar_acuse_recibo_dpo,
    listar_bitacora_dpo,
    registrar_dictamen_dpo,
)

router = APIRouter(prefix="/dpo", tags=["Cockpit del DPD/DPO"])

ROLES_CONSULTA_BITACORA = ("dpo", "admin_organizacion", "coordinador")


def _serializar_dictamen(d: DictamenDPO) -> Dict[str, Any]:
    return {
        "id": d.id,
        "tenant_id": d.tenant_id,
        "dpo_id": d.dpo_id,
        "tipo": d.tipo.value if isinstance(d.tipo, TipoDictamenDPO) else str(d.tipo),
        "asunto": d.asunto,
        "referencia_normativa": d.referencia_normativa,
        "cuerpo": d.cuerpo,
        "fecha_emision": (
            d.fecha_emision.isoformat()
            if hasattr(d.fecha_emision, "isoformat")
            else str(d.fecha_emision)
        ),
        "es_vinculante": d.es_vinculante,
        "prev_hash": d.prev_hash,
        "sha256_hash": d.sha256_hash,
        "acuse_recibo_alta_direccion": d.acuse_recibo_alta_direccion,
        "acuse_por": d.acuse_por,
        "fecha_acuse": (
            d.fecha_acuse.isoformat()
            if d.fecha_acuse is not None and hasattr(d.fecha_acuse, "isoformat")
            else d.fecha_acuse
        ),
    }


async def get_dpo_session(
    x_user_id: str = Header(""),
    x_tenant_id: Optional[str] = Header(default="tenant-default"),
):
    """Conserva los nombres de cabecera publicados usando la sesión del núcleo."""
    async with asynccontextmanager(get_session)(x_user_id, x_tenant_id) as session:
        yield session


async def _contexto_dpo(
    request: Request,
    authorization: Optional[str] = Header(None),
    x_user_id: str = Header(""),
    x_tenant_id: Optional[str] = Header(default="tenant-default"),
    x_role: str = Header("GESTOR_PROCESO"),
    session: AsyncSession = Depends(get_dpo_session),
) -> dict:
    """Resuelve identidad, membresía activa y rol en el tenant para la bitácora del DPO."""
    if modo_autenticacion() != MODO_HEADERS:
        tenant_real = (request.headers.get("x-tenant-id") or "").strip()
        if not tenant_real:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Encabezado X-Tenant-ID obligatorio para resolver contexto de aislamiento.",
            )
        user_id = await get_usuario_autenticado(authorization, x_user_id, session)
        roles = await roles_activos(session, tenant_real, user_id)
        if not roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Sin membresía activa")
        role_hdr = (request.headers.get("x-role") or "").strip()
        if role_hdr:
            return await get_context(user_id, tenant_real, role_hdr, session)
        rol_efectivo = next(
            (r for r in ROLES_CONSULTA_BITACORA if r in roles),
            next(iter(roles)),
        )
        return {"user_id": user_id, "tenant_id": tenant_real, "role": rol_efectivo}

    tenant_id = (x_tenant_id or "").strip()
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Encabezado X-Tenant-ID obligatorio para resolver contexto de aislamiento.",
        )
    user_id = await get_usuario_autenticado(authorization, x_user_id, session)
    return await get_context(user_id, tenant_id, x_role, session)


class EmitirDictamenRequest(BaseModel):
    dpo_id: str = Field(
        default="",
        description="ID del Delegado de Protección de Datos (ignorado: se usa el usuario autenticado)",
    )
    tipo: TipoDictamenDPO = TipoDictamenDPO.OPINION_CONSULTIVA
    asunto: str = Field(..., min_length=1, description="Asunto o materia de la recomendación")
    referencia_normativa: str = Field(..., min_length=1, description="Artículos LOPDP o resoluciones aplicables")
    cuerpo: str = Field(..., min_length=1, description="Contenido técnico del dictamen")


@router.post("/dictamenes")
async def emitir_dictamen(
    payload: EmitirDictamenRequest,
    ctx: dict = Depends(_contexto_dpo),
    session: AsyncSession = Depends(get_dpo_session),
):
    """Emite un dictamen consultivo no vinculante y lo asienta en la bitácora inviolable."""
    if ctx["role"] != "dpo":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Rol {ctx['role']} no autorizado: solo el DPO puede emitir dictámenes.",
        )
    dictamen = DictamenDPO(
        tenant_id=ctx["tenant_id"],
        dpo_id=ctx["user_id"],
        tipo=payload.tipo,
        asunto=payload.asunto.strip(),
        referencia_normativa=payload.referencia_normativa.strip(),
        cuerpo=payload.cuerpo.strip(),
    )
    guardado = await registrar_dictamen_dpo(session, dictamen)
    serializado = _serializar_dictamen(guardado)
    await registrar_evento(
        session,
        tenant_id=ctx["tenant_id"],
        user_id=ctx["user_id"],
        entity_type="dpo_dictamen",
        entity_id=guardado.id,
        action="emitir_dictamen",
        payload=serializado,
    )
    return {"status": "SUCCESS", "dictamen": serializado}


@router.get("/bitacora")
async def consultar_bitacora(
    ctx: dict = Depends(_contexto_dpo),
    session: AsyncSession = Depends(get_dpo_session),
):
    """Recupera la bitácora histórica de diligencia del DPO."""
    if ctx["role"] not in ROLES_CONSULTA_BITACORA:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Rol {ctx['role']} no autorizado para consultar la bitácora del DPO.",
        )
    historial = await listar_bitacora_dpo(session, ctx["tenant_id"])
    return {
        "tenant_id": ctx["tenant_id"],
        "total": len(historial),
        "dictamenes": [_serializar_dictamen(d) for d in historial],
    }


@router.post("/dictamenes/{dictamen_id}/acuse")
async def firmar_acuse(
    dictamen_id: str,
    ctx: dict = Depends(_contexto_dpo),
    session: AsyncSession = Depends(get_dpo_session),
):
    """Registra la constancia formal de recepción del dictamen por la Alta Dirección."""
    if ctx["role"] != "admin_organizacion":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Rol {ctx['role']} no autorizado: solo la alta dirección (admin_organizacion) puede firmar el acuse.",
        )
    try:
        dictamen = await firmar_acuse_recibo_dpo(
            session, ctx["tenant_id"], dictamen_id, ctx["user_id"]
        )
    except AcuseYaRegistradoError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    if dictamen is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dictamen '{dictamen_id}' no encontrado en la bitácora.",
        )

    serializado = _serializar_dictamen(dictamen)
    await registrar_evento(
        session,
        tenant_id=ctx["tenant_id"],
        user_id=ctx["user_id"],
        entity_type="dpo_dictamen",
        entity_id=dictamen.id,
        action="acuse_recibo_alta_direccion",
        payload=serializado,
    )
    return {"status": "SUCCESS", "dictamen": serializado}
