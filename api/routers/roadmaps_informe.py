# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
"""Descarga del informe PDF del estado de la hoja de ruta (RM-20)."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import get_context
from app_core.db.session import get_session
from features.roadmap import roadmap_service

router = APIRouter(prefix="/roadmaps", tags=["Roadmap"])


@router.get("/{roadmap_id}/informe.pdf")
async def descargar_informe(
    roadmap_id: str, ctx: dict = Depends(get_context), session: AsyncSession = Depends(get_session),
):
    """Los cinco roles lo descargan, cada uno con su alcance; queda constancia en audit_events."""
    try:
        pdf, informe_id, etiqueta_revision = await roadmap_service.generar_informe_pdf_con_revision(
            session, ctx["tenant_id"], roadmap_id, ctx["user_id"], ctx["role"]
        )
    except LookupError:
        raise HTTPException(404, "Hoja de ruta no encontrada")
    headers = {
        "Content-Disposition": f'attachment; filename="informe-{roadmap_id}.pdf"',
        "X-Report-ID": informe_id,
    }
    if etiqueta_revision:
        headers["X-Roadmap-Revision"] = etiqueta_revision
    return Response(
        pdf,
        media_type="application/pdf",
        headers=headers,
    )
