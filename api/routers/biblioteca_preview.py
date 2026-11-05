# ¤adpa
# ¤¤developer-architect
# ¤rbac-tenant
"""Vista previa y fidelidad (BIB-206). Tenant e identidad salen de la sesión.

La vista previa usa la misma instantánea y el mismo modelo de salida que el archivo de BIB-205; emitir
desde ella solo procede si la revisión y la instantánea siguen vigentes. Nada de esto aprueba el documento.
"""
from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from api.rbac import require_role
from api.routers.biblioteca_borradores import EDITORES, FUENTES
from app_core.db.session import get_session
from features.biblioteca import biblioteca_service as biblioteca

AUTO_REGISTRO = True
router = APIRouter(prefix="/biblioteca/preview", tags=["Biblioteca vista previa"])
Sesion = Annotated[AsyncSession, Depends(get_session)]


# ¤adpa
@router.post("/borradores/{borrador_id}", response_model=biblioteca.VistaPrevia)
async def previsualizar(borrador_id: str, pedido: biblioteca.PedirGeneracion, session: Sesion,
                        ctx: dict = Depends(require_role(*EDITORES))):
    return await biblioteca.previsualizar(session, FUENTES, ctx["tenant_id"], ctx["user_id"], borrador_id, pedido)


# ¤adpa
@router.post("/borradores/{borrador_id}/emitir", status_code=201, response_model=biblioteca.Generacion)
async def emitir(borrador_id: str, pedido: biblioteca.EmitirDesdeVista, session: Sesion,
                 ctx: dict = Depends(require_role(*EDITORES))):
    return await biblioteca.emitir_desde_vista(session, FUENTES, ctx["tenant_id"], ctx["user_id"], borrador_id, pedido)
