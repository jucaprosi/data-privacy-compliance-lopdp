"""Exportación del RAT a XLSX y PDF (RAT-06). ¤rat ¤rbac-tenant

Contrato: governance/especificaciones/RAT-06.md §2. Organización e identidad salen del contexto autenticado.
La huella viaja en `X-Huella-SHA256` para que la interfaz la muestre tras descargar.
"""
from typing import Literal

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from api.routers.rat import LECTURA, get_rat_session
from app_core.audit import registrar_evento
from features.rat import rat_service

AUTO_REGISTRO = True
router = APIRouter(prefix="/rat", tags=["Registro de Actividades de Tratamiento (RAT)"])


@router.get("/exportar")
async def exportar(
    formato: Literal["xlsx", "pdf"],
    ctx: dict = Depends(LECTURA),
    session: AsyncSession = Depends(get_rat_session),
):
    exportacion = await rat_service.exportar_rat_vigente(session, ctx["tenant_id"], formato)
    await registrar_evento(
        session, ctx["tenant_id"], "rat_exportacion", exportacion.huella, "exportado", ctx["user_id"], {"formato": formato},
    )
    return Response(
        content=exportacion.contenido,
        media_type=exportacion.media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{exportacion.nombre_archivo}"',
            "X-Huella-SHA256": exportacion.huella,
        },
    )
