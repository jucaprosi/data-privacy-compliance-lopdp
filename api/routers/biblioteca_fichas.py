# ¤adpa ¤rbac-tenant
# ¤¤developer-architect
"""Ficha de plantilla y «Mi plantilla» (BIB-103). La organización sale de la sesión verificada, nunca del cuerpo.

Cruza a Organización por su compuerta para saber qué datos tiene la organización (solo si existen, no sus valores).
"""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from api.rbac import get_context
from app_core.db.session import get_session
from features.biblioteca import biblioteca_service as biblioteca
from features.organizacion import organizacion_service as organizacion

AUTO_REGISTRO = True
router = APIRouter(prefix="/biblioteca", tags=["Biblioteca fichas"])
Sesion = Annotated[AsyncSession, Depends(get_session)]
Contexto = Annotated[dict, Depends(get_context)]
ROLES_QUE_COPIAN = frozenset({"dpo", "admin_organizacion", "coordinador", "implementador"})


# ¤adpa
async def claves_disponibles(session: AsyncSession, tenant_id: str) -> frozenset[str]:
    """Variables cuyo dato la organización ya tiene (sin sus valores): domicilio y contactos, y delegado vigente."""
    datos = await organizacion.obtener_variables_documentales(session, tenant_id)
    claves = {clave for clave, valor in datos["valores"].items() if valor not in (None, "")}
    designaciones = await organizacion.listar_designaciones_formales(session, tenant_id, organizacion.TipoDesignacion.dpd)
    if any(d.get("revocada_at") is None for d in designaciones):
        claves |= {"dpo.nombre", "dpo.correo", "dpo.fecha_designacion"}
    return frozenset(claves)


# ¤adpa
@router.get("/plantillas/{plantilla_id}")
async def ficha(plantilla_id: str, session: Sesion, ctx: Contexto):
    disponibles = await claves_disponibles(session, ctx["tenant_id"])
    return await biblioteca.obtener_ficha(session, ctx["user_id"], ctx["tenant_id"], plantilla_id, disponibles)


# ¤adpa
@router.post("/plantillas/{plantilla_id}/copias", status_code=201)
async def copiar(plantilla_id: str, session: Sesion, ctx: Contexto):
    if ctx["role"] not in ROLES_QUE_COPIAN:
        raise HTTPException(status.HTTP_403_FORBIDDEN, f"Rol {ctx['role']} no autorizado para esta operación")
    return await biblioteca.crear_copia(session, ctx["user_id"], ctx["tenant_id"], plantilla_id)
