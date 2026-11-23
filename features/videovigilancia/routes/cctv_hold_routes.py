# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤videovigilancia-cctv ¤incidentes ¤derechos ¤conservacion ¤seguridad-tenant ¤rbac-tenant ¤adpa
"""Rutas de Congelamiento Forense (Hold Legal) y Purga Quincenal CCTV (CCTV-02)."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.db.session import get_session
from app_core.security import MODO_HEADERS, modo_autenticacion, roles_activos, usuario_verificado
from features.videovigilancia import videovigilancia_service as svc

router = APIRouter(prefix="/videovigilancia", tags=["Videovigilancia Hold Legal"])


def _contexto(roles_permitidos: tuple[str, ...]):
    async def dependencia(
        authorization: Optional[str] = Header(None),
        x_user_id: str = Header("", alias="X-User-ID"),
        x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
        x_role: str = Header(..., alias="X-Role"),
        session: AsyncSession = Depends(get_session),
    ) -> dict:
        if modo_autenticacion() == MODO_HEADERS:
            if not x_user_id:
                raise HTTPException(422, "Falta la cabecera X-User-ID")
            usuario = x_user_id
        else:
            usuario = (await usuario_verificado(session, authorization)).usuario_id
        if x_role not in roles_permitidos:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Rol no autorizado para esta operación")
        if x_role not in await roles_activos(session, x_tenant_id, usuario):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Sin membresía activa")
        return {"tenant_id": x_tenant_id, "user_id": usuario, "role": x_role}

    return dependencia


_hold = _contexto(svc.ROLES_HOLD_LEGAL)
_purga = _contexto(svc.ROLES_PURGA)
_consulta = _contexto(svc.ROLES_CONSULTA_CLIPS)


class SolicitudHoldLegal(BaseModel):
    expediente_origen_tipo: str = Field(..., description="'INCIDENTE' | 'ARCOP'")
    expediente_origen_id: str = Field(..., description="ID del expediente en la sala respectiva")
    motivo: Optional[str] = Field(None, description="Motivo opcional del congelamiento")


class SolicitudCrearClip(BaseModel):
    camara_id: str
    sha256_clip: str
    fecha_captura: datetime
    expira_en: Optional[datetime] = None
    hold_legal_activo: bool = False
    expediente_origen_tipo: Optional[str] = None
    expediente_origen_id: Optional[str] = None
    bucket_actual: str = "short-ttl"


class SolicitudPurgaQuincenal(BaseModel):
    fecha_corte: Optional[datetime] = None


def _clip_a_dict(clip: Any) -> dict[str, Any]:
    return {
        "id": str(clip.id),
        "tenant_id": clip.tenant_id,
        "camara_id": str(clip.camara_id),
        "sha256_clip": clip.sha256_clip,
        "fecha_captura": clip.fecha_captura.isoformat() if clip.fecha_captura else None,
        "expira_en": clip.expira_en.isoformat() if clip.expira_en else None,
        "hold_legal_activo": bool(clip.hold_legal_activo),
        "expediente_origen_tipo": clip.expediente_origen_tipo,
        "expediente_origen_id": clip.expediente_origen_id,
        "bucket_actual": clip.bucket_actual,
        "acta_destruccion_hash": clip.acta_destruccion_hash,
    }


@router.post("/clips/{clip_id}/hold-legal", status_code=status.HTTP_200_OK)
async def congelar_clip_hold_legal(
    clip_id: str,
    solicitud: SolicitudHoldLegal,
    ctx: dict = Depends(_hold),
    session: AsyncSession = Depends(get_session),
):
    """R2: Promueve el clip al bucket WORM 'long-retention' con Object Lock."""
    clip = await svc.aplicar_hold_legal(
        session,
        ctx["tenant_id"],
        clip_id,
        solicitud.expediente_origen_tipo,
        solicitud.expediente_origen_id,
        user_id=ctx["user_id"],
    )
    return _clip_a_dict(clip)


@router.post("/purga-quincenal/ejecutar", status_code=status.HTTP_200_OK)
async def ejecutar_purga_quincenal(
    solicitud: Optional[SolicitudPurgaQuincenal] = None,
    ctx: dict = Depends(_purga),
    session: AsyncSession = Depends(get_session),
):
    """R1 y R3: Destruye clips ordinarios >= 15 días y emite el acta SHA-256."""
    corte = solicitud.fecha_corte if solicitud else None
    return await svc.ejecutar_purga_quincenal(session, ctx["tenant_id"], ctx["user_id"], corte)


@router.get("/clips", status_code=status.HTTP_200_OK)
async def listar_clips(
    limite: int = 200,
    incluir_destruidos: bool = False,
    ctx: dict = Depends(_consulta),
    session: AsyncSession = Depends(get_session),
):
    """Línea de tiempo de clips de los últimos 15 días."""
    clips = await svc.listar_clips(session, ctx["tenant_id"], limite, incluir_destruidos)
    return [_clip_a_dict(c) for c in clips]


@router.get("/clips/{clip_id}", status_code=status.HTTP_200_OK)
async def obtener_clip_detalle(
    clip_id: str,
    ctx: dict = Depends(_consulta),
    session: AsyncSession = Depends(get_session),
):
    clip = await svc.obtener_clip(session, ctx["tenant_id"], clip_id)
    if clip is None:
        raise svc.errores.error(svc.errores.CCTV_CLIP_NO_ENCONTRADO)
    return _clip_a_dict(clip)


@router.delete("/clips/{clip_id}", status_code=status.HTTP_200_OK)
async def eliminar_clip(
    clip_id: str,
    ctx: dict = Depends(_purga),
    session: AsyncSession = Depends(get_session),
):
    """Intento de eliminación directa: rechaza con 409 si está bajo Hold Legal."""
    await svc.eliminar_clip(session, ctx["tenant_id"], clip_id, ctx["user_id"])
    return {"mensaje": "Clip destruido correctamente"}


@router.post("/clips", status_code=status.HTTP_201_CREATED)
async def registrar_clip(
    solicitud: SolicitudCrearClip,
    ctx: dict = Depends(_purga),
    session: AsyncSession = Depends(get_session),
):
    """Registra y custodia un nuevo clip de videovigilancia."""
    clip = await svc.crear_clip(
        session,
        ctx["tenant_id"],
        solicitud.camara_id,
        solicitud.sha256_clip,
        solicitud.fecha_captura,
        solicitud.expira_en,
        solicitud.hold_legal_activo,
        solicitud.expediente_origen_tipo,
        solicitud.expediente_origen_id,
        solicitud.bucket_actual,
    )
    return _clip_a_dict(clip)


@router.get("/purga-quincenal/actas", status_code=status.HTTP_200_OK)
async def listar_actas_purga(
    limite: int = 100,
    ctx: dict = Depends(_consulta),
    session: AsyncSession = Depends(get_session),
):
    """Historial de actas quincenales emitidas."""
    return await svc.listar_actas_purga(session, ctx["tenant_id"], limite)
