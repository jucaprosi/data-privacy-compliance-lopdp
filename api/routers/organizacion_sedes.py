# ¤rbac-tenant ¤inventario
"""Router de sedes y clientes por encargo de la organización (ORG-18).

Endpoints (prefijo /api/v1/organizacion):
- GET/POST /sedes, PUT /sedes/{id}, POST /sedes/{id}/retirar
- GET/POST /clientes, PUT /clientes/{id}, POST /clientes/{id}/retirar   (409 NO_ES_ENCARGADA si no aplica)

Leen los cuatro roles de gestión; escriben admin_organizacion, implementador y coordinador. La organización
y la identidad salen del contexto de la sesión; el cuerpo no las admite.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import require_role
from app_core.db.session import get_session
from features.organizacion import organizacion_service as sala

AUTO_REGISTRO = True

router = APIRouter(prefix="/organizacion", tags=["Organización - Sedes y clientes"])

_LECTORES = ("admin_organizacion", "implementador", "coordinador", "dpo")
_ESCRITORES = ("admin_organizacion", "implementador", "coordinador")


@router.get("/sedes")
async def get_sedes(ctx: dict = Depends(require_role(*_LECTORES)), session: AsyncSession = Depends(get_session)):
    return await sala.listar_sedes(session, ctx["tenant_id"])


@router.post("/sedes", status_code=201)
async def post_sede(
    cuerpo: sala.SedeEntrada, ctx: dict = Depends(require_role(*_ESCRITORES)), session: AsyncSession = Depends(get_session),
):
    return await sala.crear_sede(session, ctx["tenant_id"], ctx["user_id"], cuerpo)


@router.put("/sedes/{sede_id}")
async def put_sede(
    sede_id: str, cuerpo: sala.SedeEntrada, ctx: dict = Depends(require_role(*_ESCRITORES)),
    session: AsyncSession = Depends(get_session),
):
    return await sala.editar_sede(session, ctx["tenant_id"], ctx["user_id"], sede_id, cuerpo)


@router.post("/sedes/{sede_id}/retirar")
async def post_retirar_sede(
    sede_id: str, ctx: dict = Depends(require_role(*_ESCRITORES)), session: AsyncSession = Depends(get_session),
):
    return await sala.retirar_sede(session, ctx["tenant_id"], ctx["user_id"], sede_id)


@router.get("/clientes")
async def get_clientes(ctx: dict = Depends(require_role(*_LECTORES)), session: AsyncSession = Depends(get_session)):
    return await sala.listar_clientes(session, ctx["tenant_id"])


@router.post("/clientes", status_code=201)
async def post_cliente(
    cuerpo: sala.ClienteEntrada, ctx: dict = Depends(require_role(*_ESCRITORES)),
    session: AsyncSession = Depends(get_session),
):
    return await sala.crear_cliente(session, ctx["tenant_id"], ctx["user_id"], cuerpo)


@router.put("/clientes/{cliente_id}")
async def put_cliente(
    cliente_id: str, cuerpo: sala.ClienteEntrada, ctx: dict = Depends(require_role(*_ESCRITORES)),
    session: AsyncSession = Depends(get_session),
):
    return await sala.editar_cliente(session, ctx["tenant_id"], ctx["user_id"], cliente_id, cuerpo)


@router.post("/clientes/{cliente_id}/retirar")
async def post_retirar_cliente(
    cliente_id: str, ctx: dict = Depends(require_role(*_ESCRITORES)), session: AsyncSession = Depends(get_session),
):
    return await sala.retirar_cliente(session, ctx["tenant_id"], ctx["user_id"], cliente_id)
