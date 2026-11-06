# ¤adpa ¤rbac-tenant
"""API BIB-303: evidencias y verificación del cierre de acciones canónicas.

Adaptador entre salas: Biblioteca recibe por inyección la consulta y la reapertura de acciones de
Roadmap, y su verificador se registra en el puerto `VerificadorDeCierre` de Roadmap (RM-24).
"""
from typing import Annotated
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from api.rbac import get_context, require_role
from app_core.db.session import get_session
from features.biblioteca import biblioteca_service as biblioteca
from features.roadmap import roadmap_service as roadmap

AUTO_REGISTRO = True
router = APIRouter(prefix="/biblioteca/verificaciones", tags=["Biblioteca verificaciones"])
Sesion = Annotated[AsyncSession, Depends(get_session)]
Consulta = Annotated[dict, Depends(get_context)]
Aporta = Annotated[dict, Depends(require_role("admin_organizacion", "implementador", "coordinador",
                                              "responsable_area"))]
Revisa = Annotated[dict, Depends(require_role("admin_organizacion", "coordinador", "dpo"))]

roadmap.registrar_verificador_cierre(biblioteca.VerificadorEvidencia())


@router.get("/acciones/{accion_id}", response_model=biblioteca.ExpedienteVerificacion)
async def expediente(accion_id: str, session: Sesion, ctx: Consulta):
    return await biblioteca.obtener_expediente(
        session, ctx["tenant_id"], ctx["user_id"], accion_id, roadmap.obtener_accion_para_enlace)


@router.post("/acciones/{accion_id}/evidencias", status_code=status.HTTP_201_CREATED,
             response_model=biblioteca.Evidencia)
async def registrar_evidencia(accion_id: str, entrada: biblioteca.RegistrarEvidencia, session: Sesion, ctx: Aporta):
    return await biblioteca.registrar_evidencia(
        session, ctx["tenant_id"], ctx["user_id"], accion_id, entrada, roadmap.obtener_accion_para_enlace)


@router.post("/acciones/{accion_id}/verificaciones", status_code=status.HTTP_201_CREATED,
             response_model=biblioteca.ExpedienteVerificacion)
async def registrar_verificacion(accion_id: str, entrada: biblioteca.RegistrarVerificacion, session: Sesion,
                                 ctx: Revisa):
    return await biblioteca.registrar_verificacion(
        session, ctx["tenant_id"], ctx["user_id"], accion_id, entrada,
        roadmap.obtener_accion_para_enlace, roadmap.reabrir_accion_no_conforme)
