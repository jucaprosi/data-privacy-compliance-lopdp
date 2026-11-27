# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤adpa
# ¤¤developer-architect
"""Capacidades editoriales (BIB-118 y BIB-411).

- `GET /mias` (BIB-118): solo lectura; nunca 403 por no tener capacidades: el menú se pinta con esto.
- El equipo (BIB-411 §2): listar, conceder, retirar e historial, solo para operadores activos.
- R8: el actor es el operador del token verificado (`usuario_de_operador`, OPE-01 R2) en todos los entornos,
  también en la demo; en modo `headers` (pruebas) se lee `X-User-ID`.
"""
from typing import Annotated, Literal, Optional

from fastapi import APIRouter, Depends, Header, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.db.session import get_session
from app_core.errors import ErrorNegocio
from features.biblioteca import biblioteca_service as biblioteca

AUTO_REGISTRO = True
router = APIRouter(prefix="/biblioteca/capacidades", tags=["Biblioteca capacidades"])
Sesion = Annotated[AsyncSession, Depends(get_session)]


# === BIB-411 ===
# ¤adpa ¤seguridad
async def operador_de_la_peticion(
    authorization: Optional[str] = Header(None),
    x_user_id: str = Header("", alias="X-User-ID"),
    session: AsyncSession = Depends(get_session),
) -> Optional[str]:
    """R8: el `usuario_id` del operador del token, o None si quien llama no es operador activo."""
    from fastapi import HTTPException

    from app_core.pasillo import plataforma as pasillo_plataforma
    from app_core.security import MODO_HEADERS, extraer_bearer, modo_autenticacion, verificar_token_google

    if modo_autenticacion() == MODO_HEADERS:
        if not x_user_id:
            raise HTTPException(422, "Falta la cabecera X-User-ID")
        return x_user_id
    identidad = await verificar_token_google(extraer_bearer(authorization))
    return await pasillo_plataforma.usuario_de_operador(session, identidad.email, identidad.sub)


# ¤adpa ¤seguridad
async def operador_identificado(actor: Optional[str] = Depends(operador_de_la_peticion)) -> str:
    """R8: sin operador detrás del token, `BIB_SOLO_OPERADORES`."""
    if not actor:
        raise ErrorNegocio("BIB_SOLO_OPERADORES")
    return actor


# ¤adpa ¤seguridad
async def operador_activo(session: Sesion, actor: str = Depends(operador_identificado)) -> str:
    """§2: las rutas del equipo, solo para operadores activos (también en modo `headers`)."""
    from app_core.pasillo import plataforma as pasillo_plataforma

    if not await pasillo_plataforma.operador_activo(session, actor):
        raise ErrorNegocio("BIB_SOLO_OPERADORES")
    return actor


Operador = Annotated[str, Depends(operador_identificado)]
OperadorActivo = Annotated[str, Depends(operador_activo)]
# === fin BIB-411 ===


# ¤adpa
class MisCapacidades(BaseModel):
    capacidades: list[str]


# ¤adpa
@router.get("/mias", response_model=MisCapacidades)
async def mias(session: Sesion, actor: Annotated[Optional[str], Depends(operador_de_la_peticion)]):
    if not actor:
        return MisCapacidades(capacidades=[])
    return MisCapacidades(capacidades=sorted(await biblioteca.capacidades_propias(session, actor)))


# === BIB-411 ===
# ¤adpa
class MiembroEquipo(BaseModel):
    usuario_id: str
    nombre: str
    email: str
    ha_entrado: bool
    capacidades: list[str]


# ¤adpa
class CambioCapacidad(BaseModel):
    capacidad: str
    motivo: str


# ¤adpa
class ResultadoCambio(BaseModel):
    resultado: Literal["alta", "reactivacion", "vigente", "revocacion", "sin_vigente"]


# ¤adpa
class EventoCapacidad(BaseModel):
    id: int
    usuario_id: str
    capacidad: str
    accion: Literal["concedida", "retirada"]
    por: Optional[str]
    motivo: Optional[str]
    en: str


# ¤adpa
@router.get("/equipo", response_model=list[MiembroEquipo])
async def equipo(session: Sesion, actor: OperadorActivo):
    return await biblioteca.equipo_editorial(session)


# ¤adpa
@router.post("/equipo/{usuario_id}/conceder", response_model=ResultadoCambio)
async def conceder(usuario_id: str, entrada: CambioCapacidad, session: Sesion, actor: OperadorActivo):
    return ResultadoCambio(resultado=await biblioteca.conceder_capacidad(
        session, usuario_id, entrada.capacidad, actor, entrada.motivo))


# ¤adpa
@router.post("/equipo/{usuario_id}/retirar", response_model=ResultadoCambio)
async def retirar(usuario_id: str, entrada: CambioCapacidad, session: Sesion, actor: OperadorActivo):
    return ResultadoCambio(resultado=await biblioteca.revocar_capacidad(
        session, usuario_id, entrada.capacidad, actor, entrada.motivo))


# ¤adpa
@router.get("/equipo/historial", response_model=list[EventoCapacidad])
async def historial(session: Sesion, actor: OperadorActivo, usuario_id: str = Query(...)):
    return [{**e, "en": e["en"].isoformat() if hasattr(e["en"], "isoformat") else str(e["en"])}
            for e in await biblioteca.historial_capacidades(session, usuario_id)]
# === fin BIB-411 ===
