# ¤adpa
# ¤¤developer-architect
# ¤rbac-tenant
"""Borradores de documentos desde una plantilla (BIB-201). La organización sale de la sesión, no del cuerpo.

Aquí se conectan las compuertas de otras salas (ORG-14, designaciones y RAT) con Biblioteca, que no las
importa. Todo es de solo lectura sobre esas salas.
"""
from datetime import datetime, timezone
from typing import Annotated, Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from api.rbac import get_context, require_role
from app_core.db.session import get_session
from features.biblioteca import biblioteca_service as biblioteca
from features.organizacion import organizacion_service
from features.rat import rat_service

AUTO_REGISTRO = True
router = APIRouter(prefix="/biblioteca/borradores", tags=["Biblioteca borradores"])
Sesion = Annotated[AsyncSession, Depends(get_session)]
EDITORES = ("admin_organizacion", "dpo", "coordinador", "implementador")


# ¤adpa
async def _organizacion(session: AsyncSession, tenant_id: str) -> dict[str, Any]:
    return (await organizacion_service.obtener_variables_documentales(session, tenant_id))["valores"]


# ¤adpa
async def _dpd_vigente(session: AsyncSession, tenant_id: str) -> dict[str, Any] | None:
    ahora = datetime.now(timezone.utc)
    for d in await organizacion_service.listar_designaciones_formales(
            session, tenant_id, organizacion_service.TipoDesignacion.dpd):
        if d["revocada_at"] is None and (d["valid_to"] is None or d["valid_to"] > ahora):
            return {"nombre": d["usuario_nombre"], "correo": d["usuario_email"],
                    "fecha_designacion": d["fecha_designacion"]}
    return None


# ¤adpa
async def _actividades(session: AsyncSession, tenant_id: str) -> list[dict[str, Any]]:
    return [vars(a) for a in await rat_service.listar_actividades_rat(session, tenant_id)]


FUENTES = biblioteca.FuentesDatos(organizacion=_organizacion, dpd_vigente=_dpd_vigente, actividades=_actividades)


# ¤adpa
@router.post("", status_code=201, response_model=biblioteca.Borrador)
async def crear(entrada: biblioteca.EntradaBorrador, session: Sesion, ctx: dict = Depends(require_role(*EDITORES))):
    return await biblioteca.crear_borrador(session, FUENTES, ctx["tenant_id"], ctx["user_id"], entrada)


# ¤adpa
@router.get("/{identificador}", response_model=biblioteca.Borrador)
async def obtener(identificador: str, session: Sesion, ctx: dict = Depends(require_role(*EDITORES))):
    return await biblioteca.obtener_borrador(session, FUENTES, ctx["tenant_id"], ctx["user_id"], identificador)


# ¤adpa
@router.put("/{identificador}", response_model=biblioteca.Borrador)
async def guardar(identificador: str, entrada: biblioteca.GuardarBorrador, session: Sesion,
                  ctx: dict = Depends(require_role(*EDITORES))):
    return await biblioteca.guardar_borrador(session, FUENTES, ctx["tenant_id"], ctx["user_id"], identificador, entrada)
