# ¤¤developer-architect ¤derechos ¤seguridad ¤adpa
"""Router público de solicitudes ARCO+ y configuración del portal (DER-02).

Contrato: governance/especificaciones/DER-02.md
- GET /publico/solicitud/{slug} -> público
- POST /publico/solicitud/{slug} -> público, límite 5 por IP y hora
- GET /publico/solicitud/seguir/{codigo} -> público, solo estado y fechas
- PUT /derechos/portal -> admin_organizacion
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import require_role
from app_core.db.session import get_session
from features.derechos_arco import derechos_arco_service

AUTO_REGISTRO = True

router = APIRouter(tags=["Portal Público Derechos ARCO (DER-02)"])


class SolicitudPublicaIn(BaseModel):
    derecho: str = Field(..., description="Tipo de derecho ARCO+ solicitado")
    nombre: str = Field(..., min_length=1, max_length=200, description="Nombre del titular")
    email: str = Field(..., min_length=3, max_length=255, description="Correo electrónico de contacto")
    descripcion: str = Field("", max_length=4000, description="Detalle o descripción de la solicitud")


class PortalConfigIn(BaseModel):
    activo: bool = Field(..., description="Habilitar o deshabilitar el portal público")
    slug: str = Field(..., min_length=3, max_length=48, description="Identificador único de URL")
    texto_bienvenida: Optional[str] = Field(None, max_length=2000, description="Mensaje de bienvenida personalizado")


def _obtener_ip_cliente(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


@router.get("/publico/solicitud/{slug}")
@router.get("/solicitud/{slug}")
async def obtener_info_portal(
    slug: str,
    session: AsyncSession = Depends(get_session),
):
    return await derechos_arco_service.obtener_portal_publico(session, slug)


@router.post("/publico/solicitud/{slug}", status_code=status.HTTP_201_CREATED)
@router.post("/solicitud/{slug}", status_code=status.HTTP_201_CREATED)
async def registrar_solicitud_portal(
    slug: str,
    payload: SolicitudPublicaIn,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    ip = _obtener_ip_cliente(request)
    return await derechos_arco_service.crear_solicitud_desde_portal(
        session=session,
        slug=slug,
        ip=ip,
        derecho=payload.derecho,
        nombre=payload.nombre,
        email=payload.email,
        descripcion=payload.descripcion,
    )


@router.get("/publico/solicitud/seguir/{codigo}")
@router.get("/solicitud/seguir/{codigo}")
async def consultar_seguimiento(
    codigo: str,
    session: AsyncSession = Depends(get_session),
):
    return await derechos_arco_service.consultar_seguimiento_portal(session, codigo)


@router.put("/derechos/portal")
async def actualizar_configuracion_portal(
    payload: PortalConfigIn,
    ctx: dict = Depends(require_role("admin_organizacion")),
    session: AsyncSession = Depends(get_session),
):
    tenant_id = ctx["tenant_id"]
    return await derechos_arco_service.configurar_portal(
        session=session,
        tenant_id=tenant_id,
        activo=payload.activo,
        slug=payload.slug,
        texto_bienvenida=payload.texto_bienvenida,
    )


@router.get("/derechos/portal")
async def consultar_configuracion_portal(
    ctx: dict = Depends(require_role("admin_organizacion", "coordinador", "dpo")),
    session: AsyncSession = Depends(get_session),
):
    tenant_id = ctx["tenant_id"]
    cfg = await derechos_arco_service.obtener_configuracion_portal(session, tenant_id)
    if not cfg:
        return {"activo": False, "slug": "", "texto_bienvenida": None}
    return cfg
