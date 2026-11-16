# ¤rbac-tenant ¤seguridad
"""Router de la papelera y la exportación completa de la organización (ORG-20).

Endpoints (prefijo /api/v1/organizacion):
- GET /papelera?entidad=, POST /papelera/{entidad}/{id}/restaurar    (admin_organizacion, implementador)
- POST /exportaciones (202), GET /exportaciones/{id}, GET /exportaciones/{id}/archivo   (admin_organizacion)

La organización y la identidad salen del contexto de la sesión; los cuerpos no las admiten. Ninguna ruta borra.
"""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import require_role
from app_core.db.session import async_session_factory, get_session
from features.organizacion import organizacion_service as sala

AUTO_REGISTRO = True

router = APIRouter(prefix="/organizacion", tags=["Organización - Papelera y exportación"])

_PAPELERA = ("admin_organizacion", "implementador")
_EXPORTA = ("admin_organizacion",)


def almacen_exportaciones() -> sala.AlmacenExportaciones:
    """Dependencia del almacén: falla cerrado hasta que EVI-04 entregue el adaptador real."""
    return sala.AlmacenNoDisponible()


@router.get("/papelera")
async def get_papelera(
    entidad: str | None = None, ctx: dict = Depends(require_role(*_PAPELERA)),
    session: AsyncSession = Depends(get_session),
):
    return await sala.listar_papelera(session, ctx["tenant_id"], entidad)


@router.post("/papelera/{entidad}/{registro_id}/restaurar")
async def post_restaurar(
    entidad: str, registro_id: str, ctx: dict = Depends(require_role(*_PAPELERA)),
    session: AsyncSession = Depends(get_session),
):
    await sala.restaurar_de_papelera(session, ctx["tenant_id"], ctx["user_id"], entidad, registro_id)
    return {}


@router.post("/exportaciones", status_code=202)
async def post_exportacion(
    tareas: BackgroundTasks, ctx: dict = Depends(require_role(*_EXPORTA)),
    session: AsyncSession = Depends(get_session), almacen: sala.AlmacenExportaciones = Depends(almacen_exportaciones),
):
    creada = await sala.solicitar_exportacion(session, ctx["tenant_id"], ctx["user_id"])
    await session.commit()  # la tarea de fondo abre otra sesión: la fila pendiente debe estar confirmada
    tareas.add_task(
        sala.generar_exportacion_en_segundo_plano, async_session_factory, almacen,
        ctx["tenant_id"], ctx["user_id"], creada["id"],
    )
    return creada


@router.get("/exportaciones/{export_id}")
async def get_exportacion(
    export_id: str, ctx: dict = Depends(require_role(*_EXPORTA)), session: AsyncSession = Depends(get_session),
):
    return await sala.consultar_exportacion(session, ctx["tenant_id"], export_id)


@router.get("/exportaciones/{export_id}/archivo")
async def get_archivo(
    export_id: str, ctx: dict = Depends(require_role(*_EXPORTA)), session: AsyncSession = Depends(get_session),
    almacen: sala.AlmacenExportaciones = Depends(almacen_exportaciones),
):
    contenido = await sala.descargar_exportacion(session, ctx["tenant_id"], ctx["user_id"], export_id, almacen)
    return Response(
        content=contenido, media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="exportacion-{export_id}.zip"', "Cache-Control": "no-store"},
    )
