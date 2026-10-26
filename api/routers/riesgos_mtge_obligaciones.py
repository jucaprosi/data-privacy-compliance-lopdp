# ¤mtge-granescala
# ¤rbac-tenant
"""Router API para las obligaciones del tratamiento a gran escala (MTGE-02).

Fuente legal: Res. SPDP-SPD-2026-0005-R (Arts. 15-18 y Disposición Transitoria).
Permisos:
- Escribe (POST/DELETE): 'dpo'.
- Consulta (GET): 'dpo', 'coordinador', 'admin_organizacion'.
- Fecha de vigencia de la norma (Disposición Transitoria): la registra 'admin_organizacion' o 'dpo'.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import require_role
from app_core.db.session import get_session
from features.riesgos_mtge import riesgos_mtge_service
from features.riesgos_mtge.riesgos_mtge_service import (
    AuditoriaGranEscalaCreate,
    ConfiguracionVigenciaCreate,
    EstadoObligacionesResponse,
    InformeAnualCreate,
    PoliticaPrivacidadCreate,
)

router = APIRouter(prefix="/riesgos/mtge/obligaciones", tags=["Obligaciones Gran Escala (MTGE-02)"])

_consulta_roles = require_role("dpo", "coordinador", "admin_organizacion")
_dpo_role = require_role("dpo")
_admin_o_dpo = require_role("admin_organizacion", "dpo")


@router.get("", response_model=EstadoObligacionesResponse)
async def get_estado_obligaciones(
    ctx: dict = Depends(_consulta_roles),
    session: AsyncSession = Depends(get_session),
):
    """Calcula el estado consolidado de todas las obligaciones de gran escala para el tenant."""
    return await riesgos_mtge_service.calcular_estado_obligaciones(session, ctx["tenant_id"])


@router.post("/vigencia")
async def post_fecha_vigencia(
    payload: ConfiguracionVigenciaCreate,
    ctx: dict = Depends(_admin_o_dpo),
    session: AsyncSession = Depends(get_session),
):
    """Registra la fecha de publicación oficial de la resolución para el cómputo de los 90 días (Transitoria)."""
    fv = await riesgos_mtge_service.registrar_fecha_vigencia(
        session, ctx["tenant_id"], ctx["user_id"], payload
    )
    return {"status": "ok", "fecha_vigencia_norma": fv}


@router.get("/auditorias")
async def get_auditorias(
    ctx: dict = Depends(_consulta_roles),
    session: AsyncSession = Depends(get_session),
):
    """Lista las auditorías anuales y certificaciones equivalentes registradas (Art. 17)."""
    return await riesgos_mtge_service.listar_auditorias(session, ctx["tenant_id"])


@router.post("/auditorias", status_code=status.HTTP_201_CREATED)
async def post_auditoria(
    payload: AuditoriaGranEscalaCreate,
    ctx: dict = Depends(_dpo_role),
    session: AsyncSession = Depends(get_session),
):
    """Registra una auditoría periódica o certificación equivalente (Art. 17). Requiere rol dpo."""
    return await riesgos_mtge_service.registrar_auditoria(
        session, ctx["tenant_id"], ctx["user_id"], payload
    )


@router.delete("/auditorias/{auditoria_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_auditoria(
    auditoria_id: str,
    ctx: dict = Depends(_dpo_role),
    session: AsyncSession = Depends(get_session),
):
    """Elimina una auditoría. Prohibido antes de 5 años desde su fecha (Art. 17 -> 409 Conflict)."""
    await riesgos_mtge_service.eliminar_auditoria(
        session, ctx["tenant_id"], auditoria_id, ctx["user_id"]
    )


@router.get("/informes-anuales")
async def get_informes_anuales(
    ctx: dict = Depends(_consulta_roles),
    session: AsyncSession = Depends(get_session),
):
    """Lista los informes anuales de cumplimiento registrados (Art. 18)."""
    return await riesgos_mtge_service.listar_informes_anuales(session, ctx["tenant_id"])


@router.post("/informes-anuales", status_code=status.HTTP_201_CREATED)
async def post_informe_anual(
    payload: InformeAnualCreate,
    ctx: dict = Depends(_dpo_role),
    session: AsyncSession = Depends(get_session),
):
    """Registra un informe anual de cumplimiento (Art. 18). Requiere rol dpo."""
    return await riesgos_mtge_service.registrar_informe_anual(
        session, ctx["tenant_id"], ctx["user_id"], payload
    )


@router.delete("/informes-anuales/{informe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_informe_anual(
    informe_id: str,
    ctx: dict = Depends(_dpo_role),
    session: AsyncSession = Depends(get_session),
):
    """Elimina un informe anual. Prohibido antes de 5 años desde su fecha (Art. 18 -> 409 Conflict)."""
    await riesgos_mtge_service.eliminar_informe_anual(
        session, ctx["tenant_id"], informe_id, ctx["user_id"]
    )


@router.get("/politicas-privacidad")
async def get_politicas_privacidad(
    ctx: dict = Depends(_consulta_roles),
    session: AsyncSession = Depends(get_session),
):
    """Lista las constancias de políticas de privacidad registradas (Art. 18)."""
    return await riesgos_mtge_service.listar_politicas_privacidad(session, ctx["tenant_id"])


@router.post("/politicas-privacidad", status_code=status.HTTP_201_CREATED)
async def post_politica_privacidad(
    payload: PoliticaPrivacidadCreate,
    ctx: dict = Depends(_dpo_role),
    session: AsyncSession = Depends(get_session),
):
    """Registra constancia de versión de política de privacidad que identifica gran escala (Art. 18)."""
    return await riesgos_mtge_service.registrar_politica_privacidad(
        session, ctx["tenant_id"], ctx["user_id"], payload
    )
