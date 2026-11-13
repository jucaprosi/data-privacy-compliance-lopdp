# ¤regulation-code
# ¤paquete-normativo
# ¤seguridad
"""Router del paquete normativo como dato (REG-01), bajo /api/v1/plataforma/paquetes.

- Lectura: cualquier usuario autenticado (get_usuario_autenticado).
- Escritura: solo el operador de la plataforma, identificado con el token verificado
  (require_operador de ORG-09, nunca una cabecera en modo oidc); sin operador, 403 NO_ES_OPERADOR.
  La base vuelve a comprobar que el operador existe y está activo y guarda las invariantes
  (funciones SECURITY DEFINER de la migración reg01_paquetes_normativos).
"""
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import get_usuario_autenticado
from api.routers.plataforma import require_operador
from app_core.db.session import get_session
from app_core.errors import ErrorNegocio
from features.regulacion_rag import regulacion_rag_service as svc
from features.regulacion_rag.domain import errores

AUTO_REGISTRO = True

router = APIRouter(prefix="/plataforma/paquetes", tags=["Paquetes normativos"])


async def operador_paquetes(
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    x_user_email: Optional[str] = Header(None, alias="X-User-Email"),
    session: AsyncSession = Depends(get_session),
) -> str:
    """Id del operador activo; un 403 de ORG-09 se responde con el código NO_ES_OPERADOR."""
    try:
        operador = await require_operador(
            authorization=authorization, x_user_id=x_user_id, x_user_email=x_user_email, session=session
        )
    except HTTPException as exc:
        if exc.status_code == status.HTTP_403_FORBIDDEN:
            raise ErrorNegocio(errores.NO_ES_OPERADOR) from None
        raise
    return operador["id"]


@router.get("")
async def listar(
    _usuario: str = Depends(get_usuario_autenticado),
    session: AsyncSession = Depends(get_session),
) -> dict:
    return {"paquetes": [p.model_dump(mode="json") for p in await svc.listar_paquetes(session)]}


@router.get("/{paquete_id}")
async def detalle(
    paquete_id: str,
    _usuario: str = Depends(get_usuario_autenticado),
    session: AsyncSession = Depends(get_session),
) -> dict:
    return (await svc.detalle_paquete(session, paquete_id)).model_dump(mode="json")


@router.get("/{codigo}/parametros")
async def parametros(
    codigo: str,
    _usuario: str = Depends(get_usuario_autenticado),
    session: AsyncSession = Depends(get_session),
) -> dict:
    lista = await svc.parametros_publicados(session, codigo)
    return {"parametros": [p.model_dump(mode="json") for p in lista]}


@router.post("/{codigo}/versiones", status_code=status.HTTP_201_CREATED)
async def crear_version(
    codigo: str,
    entrada: svc.VersionEntrada,
    operador: str = Depends(operador_paquetes),
    session: AsyncSession = Depends(get_session),
) -> dict:
    return (await svc.crear_version_paquete(session, operador, codigo, entrada.version)).model_dump(mode="json")


@router.put("/{paquete_id}/parametros/{clave}")
async def fijar_parametro(
    paquete_id: str,
    clave: str,
    entrada: svc.ParametroEntrada,
    operador: str = Depends(operador_paquetes),
    session: AsyncSession = Depends(get_session),
) -> dict:
    return (await svc.fijar_parametro_paquete(session, operador, paquete_id, clave, entrada)).model_dump(mode="json")


@router.post("/{paquete_id}/publicar")
async def publicar(
    paquete_id: str,
    operador: str = Depends(operador_paquetes),
    session: AsyncSession = Depends(get_session),
) -> dict:
    return (await svc.publicar_paquete(session, operador, paquete_id)).model_dump(mode="json")
