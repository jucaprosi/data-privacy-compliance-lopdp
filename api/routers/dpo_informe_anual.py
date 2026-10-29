# ¤dpo-informe-anual
"""Informe anual del DPO e inscripción del delegado ante la SPDP (DPO-02).

- POST /api/v1/dpo/informe-anual: genera el informe de un año (solo `dpo`).
- GET  /api/v1/dpo/informe-anual?anio=: lo consulta cualquier rol con membresía activa.
- GET  /api/v1/dpo/informe-anual/documento?anio=: descarga Markdown con la huella de la cadena en el pie.
- POST /api/v1/dpo/inscripcion: registra una entrada del historial (solo `admin_organizacion`).
- GET  /api/v1/dpo/inscripcion: vigente e historial (dpo, admin_organizacion, coordinador).

Identidad y organización salen de la sesión (membresía verificada); el cuerpo no las admite.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import get_context, require_role
from app_core.audit import registrar_evento
from app_core.db.session import get_session
from features.dpo_cockpit.dpo_cockpit_service import (
    consultar_historial_inscripcion_spdp,
    documento_informe_anual_dpo,
    generar_informe_anual_dpo,
    registrar_inscripcion_spdp,
)

AUTO_REGISTRO = True

router = APIRouter(prefix="/dpo", tags=["Cockpit del DPD/DPO · informe anual e inscripción"])


class InformeAnualRequest(BaseModel):
    anio: int


class InscripcionRequest(BaseModel):
    inscrito: bool
    fecha_inscripcion: Optional[date] = None
    numero_tramite: Optional[str] = None


def _serializar_inscripcion(i) -> dict:
    return {
        "id": i.id,
        "inscrito": i.inscrito,
        "fecha_inscripcion": i.fecha_inscripcion.isoformat() if i.fecha_inscripcion else None,
        "numero_tramite": i.numero_tramite,
        "registrado_por": i.registrado_por,
        "registrado_at": i.registrado_at.isoformat() if i.registrado_at else None,
    }


@router.post("/informe-anual")
async def generar_informe_anual(
    payload: InformeAnualRequest,
    ctx: dict = Depends(require_role("dpo")),
    session: AsyncSession = Depends(get_session),
):
    """Genera el informe de un año a partir de la bitácora de la organización."""
    informe = await generar_informe_anual_dpo(session, ctx["tenant_id"], payload.anio)
    await registrar_evento(
        session,
        tenant_id=ctx["tenant_id"],
        user_id=ctx["user_id"],
        entity_type="dpo_informe_anual",
        entity_id=f"{ctx['tenant_id']}:{payload.anio}",
        action="generar_informe_anual",
        payload={"anio": payload.anio, "huella_cadena": informe["cadena"]["huella"]},
    )
    return informe


@router.get("/informe-anual")
async def consultar_informe_anual(
    anio: int = Query(...),
    ctx: dict = Depends(get_context),
    session: AsyncSession = Depends(get_session),
):
    """Consulta el informe de un año (cualquier rol con membresía activa)."""
    return await generar_informe_anual_dpo(session, ctx["tenant_id"], anio)


@router.get("/informe-anual/documento")
async def descargar_informe_anual(
    anio: int = Query(...),
    ctx: dict = Depends(get_context),
    session: AsyncSession = Depends(get_session),
):
    """Descarga el informe como documento; la huella de la cadena va en el pie."""
    informe = await generar_informe_anual_dpo(session, ctx["tenant_id"], anio)
    return Response(
        content=documento_informe_anual_dpo(informe),
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="informe-dpo-{anio}.md"'},
    )


@router.post("/inscripcion")
async def registrar_inscripcion(
    payload: InscripcionRequest,
    ctx: dict = Depends(require_role("admin_organizacion")),
    session: AsyncSession = Depends(get_session),
):
    """Agrega una entrada al historial de inscripción ante la SPDP."""
    nueva = await registrar_inscripcion_spdp(
        session,
        ctx["tenant_id"],
        ctx["user_id"],
        payload.inscrito,
        payload.fecha_inscripcion,
        payload.numero_tramite,
    )
    await registrar_evento(
        session,
        tenant_id=ctx["tenant_id"],
        user_id=ctx["user_id"],
        entity_type="dpo_inscripcion",
        entity_id=nueva.id,
        action="registrar_inscripcion_spdp",
        payload={"inscrito": nueva.inscrito},
    )
    return _serializar_inscripcion(nueva)


@router.get("/inscripcion")
async def consultar_inscripcion(
    ctx: dict = Depends(require_role("dpo", "admin_organizacion", "coordinador")),
    session: AsyncSession = Depends(get_session),
):
    """Inscripción vigente y su historial."""
    historial = await consultar_historial_inscripcion_spdp(session, ctx["tenant_id"])
    return {
        "tenant_id": ctx["tenant_id"],
        "vigente": _serializar_inscripcion(historial[0]) if historial else None,
        "historial": [_serializar_inscripcion(i) for i in historial],
    }
