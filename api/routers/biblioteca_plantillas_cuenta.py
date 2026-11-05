# ¤adpa ¤rbac-tenant
# ¤¤developer-architect
"""Router de plantillas de la cuenta profesional (BIB-401).

Permite a los implementadores gestionar su catálogo personal de plantillas adaptadas
con marca y contenido propios, utilizables en sus organizaciones asignadas (ORG-15).
Solo accesible para el rol 'implementador'.
"""
from typing import Annotated
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import require_role
from app_core.db.session import get_session
from features.biblioteca import biblioteca_service as biblioteca

AUTO_REGISTRO = True
router = APIRouter(prefix="/biblioteca/plantillas-cuenta", tags=["Plantillas de cuenta"])

Sesion = Annotated[AsyncSession, Depends(get_session)]
ContextoImplementador = Annotated[dict, Depends(require_role("implementador"))]


# ¤adpa ¤rbac-tenant
@router.get("")
async def listar_plantillas_cuenta(
    session: Sesion,
    ctx: ContextoImplementador,
):
    """Lista las plantillas de la cuenta profesional del implementador."""
    return await biblioteca.listar_plantillas_cuenta(
        session=session,
        usuario_id=ctx["user_id"],
    )


# ¤adpa ¤rbac-tenant
@router.post("", status_code=status.HTTP_201_CREATED)
async def crear_plantilla_cuenta(
    entrada: biblioteca.PlantillaCuentaCreate,
    session: Sesion,
    ctx: ContextoImplementador,
):
    """Crea una copia de la maestra publicada para la cuenta profesional."""
    return await biblioteca.crear_plantilla_cuenta(
        session=session,
        usuario_id=ctx["user_id"],
        entrada=entrada,
    )


# ¤adpa ¤rbac-tenant
@router.get("/{id}")
async def obtener_plantilla_cuenta(
    id: str,
    session: Sesion,
    ctx: ContextoImplementador,
):
    """Obtiene el detalle de una plantilla de cuenta profesional."""
    return await biblioteca.obtener_plantilla_cuenta(
        session=session,
        usuario_id=ctx["user_id"],
        id_=id,
    )


# ¤adpa ¤rbac-tenant
@router.put("/{id}")
async def actualizar_plantilla_cuenta(
    id: str,
    entrada: biblioteca.PlantillaCuentaUpdate,
    session: Sesion,
    ctx: ContextoImplementador,
):
    """Actualiza el contenido o la marca de la plantilla de cuenta."""
    return await biblioteca.actualizar_plantilla_cuenta(
        session=session,
        usuario_id=ctx["user_id"],
        id_=id,
        entrada=entrada,
    )


# ¤adpa ¤rbac-tenant
@router.get("/{id}/diff")
async def diff_plantilla_cuenta(
    id: str,
    session: Sesion,
    ctx: ContextoImplementador,
):
    """Compara la copia de la cuenta con la versión maestra publicada vigente."""
    return await biblioteca.obtener_diff_maestra(
        session=session,
        usuario_id=ctx["user_id"],
        id_=id,
    )


# ¤adpa ¤rbac-tenant
@router.post("/{id}/aplicar-maestra")
async def aplicar_maestra_plantilla_cuenta(
    id: str,
    session: Sesion,
    ctx: ContextoImplementador,
):
    """Aplica la última versión de la maestra publicada a la copia de cuenta."""
    return await biblioteca.aplicar_maestra(
        session=session,
        usuario_id=ctx["user_id"],
        id_=id,
    )
