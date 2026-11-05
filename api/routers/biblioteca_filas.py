# ¤adpa
# ¤¤developer-architect
# ¤rbac-tenant
"""Tablas de captura de un borrador (BIB-203). La organización sale de la sesión, nunca del cuerpo.

Aquí se conectan las compuertas RAT (tratamientos de la organización) y Roadmap (plan canónico, para PLA)
con Biblioteca, que no las importa. Ambas se leen; nada se escribe fuera de `biblioteca_filas`.
"""
from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from api.rbac import require_role
from app_core.db.session import get_session
from features.biblioteca import biblioteca_service as biblioteca
from features.rat import rat_service
from features.roadmap import roadmap_service

AUTO_REGISTRO = True
router = APIRouter(prefix="/biblioteca/filas", tags=["Biblioteca tablas de captura"])
Sesion = Annotated[AsyncSession, Depends(get_session)]
EDITORES = ("admin_organizacion", "dpo", "coordinador", "implementador")


# ¤adpa
async def _tratamientos(session: AsyncSession, tenant_id: str) -> list[str]:
    return [a.id for a in await rat_service.listar_actividades_rat(session, tenant_id)]


# ¤adpa
@router.get("/esquemas")
async def esquemas(ctx: dict = Depends(require_role(*EDITORES))) -> dict:
    return biblioteca.esquemas_filas()


# ¤adpa
@router.get("/plan/{roadmap_id}", response_model=list[biblioteca.FilaPlan])
async def plan(roadmap_id: str, session: Sesion, ctx: dict = Depends(require_role(*EDITORES))):
    return biblioteca.filas_del_plan(await roadmap_service.get_roadmap(session, ctx["tenant_id"], roadmap_id))


# ¤adpa
@router.get("/{borrador_id}/{tabla}", response_model=list[biblioteca.Fila])
async def listar(borrador_id: str, tabla: str, session: Sesion, ctx: dict = Depends(require_role(*EDITORES))):
    return await biblioteca.listar_filas(session, ctx["tenant_id"], ctx["user_id"], borrador_id, tabla)


# ¤adpa
@router.post("/{borrador_id}/validar", response_model=biblioteca.Previa)
async def validar(borrador_id: str, entrada: biblioteca.PegarFilas, session: Sesion,
                  ctx: dict = Depends(require_role(*EDITORES))):
    return await biblioteca.validar_filas(session, _tratamientos, ctx["tenant_id"], ctx["user_id"], borrador_id, entrada)


# ¤adpa
@router.post("/{borrador_id}", status_code=201, response_model=list[biblioteca.Fila])
async def confirmar(borrador_id: str, entrada: biblioteca.PegarFilas, session: Sesion,
                    ctx: dict = Depends(require_role(*EDITORES))):
    return await biblioteca.confirmar_filas(session, _tratamientos, ctx["tenant_id"], ctx["user_id"], borrador_id, entrada)


# ¤adpa
@router.put("/fila/{fila_id}", response_model=biblioteca.Fila)
async def editar(fila_id: str, entrada: biblioteca.EditarFila, session: Sesion,
                 ctx: dict = Depends(require_role(*EDITORES))):
    return await biblioteca.editar_fila(session, _tratamientos, ctx["tenant_id"], ctx["user_id"], fila_id, entrada)
