# ¤¤developer-architect
# ¤rbac-tenant ¤seguridad ¤api-integraciones
"""Rutas de gestión de suscripciones a webhooks firmados HMAC-SHA256 (API-02b).

Acceso restringido exclusivamente a `admin_organizacion`.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import require_role
from app_core.db.session import get_session
from app_core.integraciones import webhooks as webhooks_svc

AUTO_REGISTRO = True

router = APIRouter(prefix="/integraciones/webhooks", tags=["Integraciones"])

_SOLO_ADMIN = require_role("admin_organizacion")


class CrearWebhookRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    url: str = Field(..., max_length=2048)
    eventos: list[str] = Field(default_factory=list)


@router.post("", status_code=status.HTTP_201_CREATED)
async def crear_webhook(
    payload: CrearWebhookRequest,
    ctx: dict = Depends(_SOLO_ADMIN),
    session: AsyncSession = Depends(get_session),
):
    webhook, secreto_en_claro = await webhooks_svc.crear_suscripcion(
        session=session,
        tenant_id=ctx["tenant_id"],
        url=payload.url,
        eventos=payload.eventos,
        usuario_id=ctx["user_id"],
    )
    return {
        "status": "SUCCESS",
        "webhook": webhook,
        "secreto_en_claro": secreto_en_claro,
    }


@router.get("")
async def listar_webhooks(
    ctx: dict = Depends(_SOLO_ADMIN),
    session: AsyncSession = Depends(get_session),
):
    webhooks = await webhooks_svc.listar_suscripciones(
        session=session,
        tenant_id=ctx["tenant_id"],
    )
    return {"webhooks": webhooks}


@router.post("/{id}/rotar-secreto")
async def rotar_secreto_webhook(
    id: str,
    ctx: dict = Depends(_SOLO_ADMIN),
    session: AsyncSession = Depends(get_session),
):
    webhook, secreto_en_claro = await webhooks_svc.rotar_secreto(
        session=session,
        tenant_id=ctx["tenant_id"],
        suscripcion_id=id,
        usuario_id=ctx["user_id"],
    )
    return {
        "status": "SUCCESS",
        "webhook": webhook,
        "secreto_en_claro": secreto_en_claro,
    }


@router.post("/{id}/desactivar")
async def desactivar_webhook(
    id: str,
    ctx: dict = Depends(_SOLO_ADMIN),
    session: AsyncSession = Depends(get_session),
):
    webhook = await webhooks_svc.desactivar_suscripcion(
        session=session,
        tenant_id=ctx["tenant_id"],
        suscripcion_id=id,
        usuario_id=ctx["user_id"],
    )
    return {"status": "SUCCESS", "webhook": webhook}


@router.post("/{id}/probar")
async def probar_webhook(
    id: str,
    ctx: dict = Depends(_SOLO_ADMIN),
    session: AsyncSession = Depends(get_session),
):
    return await webhooks_svc.probar_suscripcion(
        session=session,
        tenant_id=ctx["tenant_id"],
        suscripcion_id=id,
        usuario_id=ctx["user_id"],
    )
