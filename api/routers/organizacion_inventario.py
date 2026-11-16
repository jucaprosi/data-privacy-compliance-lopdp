# ¤rbac-tenant ¤inventario
"""Router del inventario de activos, soportes y personas mínimas (ORG-17).

Endpoints (prefijo /api/v1/organizacion/inventario):
- GET   /activos                      lista (filtro opcional `tipo`); lo leen los cuatro roles de gestión.
- POST  /activos                      crea; admin_organizacion, implementador y coordinador.
- PATCH /activos/{id}                 edita o archiva.
- PUT   /activos/{id}/tratamientos    reemplaza los tratamientos del RAT vinculados.
- GET   /tratamientos                 tratamientos del RAT vinculables.
- GET   /personas, POST /personas, PATCH /personas/{id}

La organización y la identidad salen del contexto de la sesión; el cuerpo no las admite. La cédula
nunca se devuelve: la lista solo informa si existe.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import require_role
from app_core.db.session import get_session
from features.organizacion import organizacion_service as sala

AUTO_REGISTRO = True

router = APIRouter(prefix="/organizacion/inventario", tags=["Organización - Inventario"])

_LECTORES = ("admin_organizacion", "implementador", "coordinador", "dpo")
_ESCRITORES = ("admin_organizacion", "implementador", "coordinador")


@router.get("/activos")
async def get_activos(
    tipo: Optional[str] = None,
    ctx: dict = Depends(require_role(*_LECTORES)),
    session: AsyncSession = Depends(get_session),
):
    return await sala.listar_activos(session, ctx["tenant_id"], tipo)


@router.post("/activos", status_code=201)
async def post_activo(
    cuerpo: sala.ActivoCrear,
    ctx: dict = Depends(require_role(*_ESCRITORES)),
    session: AsyncSession = Depends(get_session),
):
    return await sala.crear_activo(session, ctx["tenant_id"], ctx["user_id"], cuerpo)


@router.patch("/activos/{activo_id}")
async def patch_activo(
    activo_id: str,
    cuerpo: sala.ActivoEditar,
    ctx: dict = Depends(require_role(*_ESCRITORES)),
    session: AsyncSession = Depends(get_session),
):
    return await sala.editar_activo(session, ctx["tenant_id"], ctx["user_id"], activo_id, cuerpo)


@router.put("/activos/{activo_id}/tratamientos")
async def put_tratamientos(
    activo_id: str,
    cuerpo: sala.VinculosTratamientos,
    ctx: dict = Depends(require_role(*_ESCRITORES)),
    session: AsyncSession = Depends(get_session),
):
    return await sala.reemplazar_vinculos_tratamientos(session, ctx["tenant_id"], ctx["user_id"], activo_id, cuerpo)


@router.get("/tratamientos")
async def get_tratamientos(
    ctx: dict = Depends(require_role(*_LECTORES)),
    session: AsyncSession = Depends(get_session),
):
    return await sala.tratamientos_disponibles(session, ctx["tenant_id"])


@router.get("/personas")
async def get_personas(
    ctx: dict = Depends(require_role(*_LECTORES)),
    session: AsyncSession = Depends(get_session),
):
    return await sala.listar_personas(session, ctx["tenant_id"])


@router.post("/personas", status_code=201)
async def post_persona(
    cuerpo: sala.PersonaCrear,
    ctx: dict = Depends(require_role(*_ESCRITORES)),
    session: AsyncSession = Depends(get_session),
):
    return await sala.crear_persona(session, ctx["tenant_id"], ctx["user_id"], cuerpo)


@router.patch("/personas/{persona_id}")
async def patch_persona(
    persona_id: str,
    cuerpo: sala.PersonaEditar,
    ctx: dict = Depends(require_role(*_ESCRITORES)),
    session: AsyncSession = Depends(get_session),
):
    return await sala.editar_persona(session, ctx["tenant_id"], ctx["user_id"], persona_id, cuerpo)
