# ¤adpa ¤rbac-tenant
# ¤¤developer-architect
"""GET /biblioteca/plantillas: catálogo de la pestaña «Plantillas». La organización sale de la sesión."""
from typing import Annotated
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from api.rbac import get_usuario_autenticado
from app_core.db.session import get_tenant_session
from features.biblioteca import biblioteca_service as biblioteca

AUTO_REGISTRO = True
router = APIRouter(prefix="/biblioteca", tags=["Biblioteca catálogo"])
Sesion = Annotated[AsyncSession, Depends(get_tenant_session)]
Actor = Annotated[str, Depends(get_usuario_autenticado)]


# ¤adpa ¤rbac-tenant
@router.get("/plantillas", response_model=list[biblioteca.PlantillaCatalogo])
async def listar(session: Sesion, actor: Actor, fuente: Annotated[str | None, Query()] = None,
                 tipo: Annotated[str | None, Query()] = None, ola: Annotated[int | None, Query()] = None):
    return await biblioteca.listar_catalogo(session, actor, fuente, tipo, ola)
