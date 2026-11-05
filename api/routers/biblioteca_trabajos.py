# ¤adpa
# ¤¤developer-architect
# ¤rbac-tenant
"""Guardado con revisión esperada y trabajos de generación de Biblioteca (BIB-207).

Tenant, usuario y rol salen de la sesión autenticada, nunca del cuerpo. Pedir un archivo crea (o recupera,
con la misma clave de idempotencia) un trabajo persistente y lo procesa en segundo plano con sesiones
propias; el cliente consulta su estado. Generar no aprueba el documento ni cierra acciones.
"""
from typing import Annotated
from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from api.rbac import require_role
from api.routers.biblioteca_borradores import EDITORES, FUENTES
from app_core.db.session import async_session_factory, get_session
from features.biblioteca import biblioteca_service as biblioteca

AUTO_REGISTRO = True
router = APIRouter(prefix="/biblioteca/trabajos", tags=["Biblioteca trabajos"])
Sesion = Annotated[AsyncSession, Depends(get_session)]


# ¤adpa
def _programar(tareas: BackgroundTasks, ctx: dict, trabajo: biblioteca.Trabajo) -> None:
    if trabajo.estado == "pendiente":
        tareas.add_task(biblioteca.procesar_trabajo, async_session_factory, FUENTES, ctx["tenant_id"],
                        ctx["user_id"], trabajo.id)


# ¤adpa
@router.put("/borradores/{borrador_id}", response_model=biblioteca.Guardado,
            responses={409: {"description": "Conflicto: incluye la versión vigente y las diferencias"}})
async def guardar(borrador_id: str, entrada: biblioteca.GuardarBorrador, session: Sesion,
                  ctx: dict = Depends(require_role(*EDITORES))):
    try:
        return await biblioteca.guardar_con_revision(session, ctx["tenant_id"], ctx["user_id"], borrador_id, entrada)
    except biblioteca.ErrorConflicto as e:
        return JSONResponse(status_code=409, content={
            "detail": e.detail, "code": e.code, "action_required": e.action_required,
            "conflicto": e.conflicto.model_dump(mode="json")})


# ¤adpa
@router.post("/borradores/{borrador_id}/generaciones", status_code=202, response_model=biblioteca.Trabajo)
async def solicitar(borrador_id: str, pedido: biblioteca.PedirTrabajo, tareas: BackgroundTasks, session: Sesion,
                    ctx: dict = Depends(require_role(*EDITORES))):
    trabajo, _ = await biblioteca.solicitar_trabajo(session, ctx["tenant_id"], ctx["user_id"], borrador_id, pedido)
    await session.commit()  # el worker abre su propia sesión: el trabajo debe estar confirmado antes
    _programar(tareas, ctx, trabajo)
    return trabajo


# ¤adpa
@router.get("/borradores/{borrador_id}", response_model=list[biblioteca.Trabajo])
async def listar(borrador_id: str, session: Sesion, ctx: dict = Depends(require_role(*EDITORES))):
    return await biblioteca.listar_trabajos(session, ctx["tenant_id"], ctx["user_id"], borrador_id)


# ¤adpa
@router.get("/{trabajo_id}", response_model=biblioteca.Trabajo)
async def obtener(trabajo_id: str, session: Sesion, ctx: dict = Depends(require_role(*EDITORES))):
    return await biblioteca.obtener_trabajo(session, ctx["tenant_id"], ctx["user_id"], trabajo_id)


# ¤adpa
@router.post("/{trabajo_id}/reintentar", status_code=202, response_model=biblioteca.Trabajo)
async def reintentar(trabajo_id: str, tareas: BackgroundTasks, session: Sesion,
                     ctx: dict = Depends(require_role(*EDITORES))):
    trabajo = await biblioteca.reintentar_trabajo(session, ctx["tenant_id"], ctx["user_id"], ctx["role"], trabajo_id)
    await session.commit()
    _programar(tareas, ctx, trabajo)
    return trabajo
