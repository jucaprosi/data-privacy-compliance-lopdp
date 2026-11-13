# ¤regulation-code
# ¤paquete-normativo
# ¤seguridad
"""Router del paquete normativo como dato (REG-01), bajo /api/v1/plataforma/paquetes.

- Lectura: cualquier usuario autenticado (get_usuario_autenticado).
- Escritura: solo el operador de la plataforma, identificado con el token verificado
  (misma identidad que ORG-09, nunca una cabecera en modo oidc); sin operador, 403 NO_ES_OPERADOR.
  La base vuelve a comprobar que el operador existe y está activo y guarda las invariantes
  (funciones SECURITY DEFINER de la migración reg01_paquetes_normativos).
"""
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import get_usuario_autenticado
from app_core.db.session import get_session
from app_core.errors import ErrorNegocio
from app_core.security import MODO_HEADERS, extraer_bearer, modo_autenticacion, verificar_token_google
from features.plataforma import plataforma_service
from features.regulacion_rag import regulacion_rag_service as svc

AUTO_REGISTRO = True

router = APIRouter(prefix="/plataforma/paquetes", tags=["Paquetes normativos"])


async def operador_paquetes(
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    x_user_email: Optional[str] = Header(None, alias="X-User-Email"),
    session: AsyncSession = Depends(get_session),
) -> str:
    """Id del operador activo, con la misma identidad que ORG-09 (token verificado en oidc).

    Las cabeceras solo cuentan en modo headers (pruebas). Un 403 de ORG-09 se responde con NO_ES_OPERADOR.
    """
    if modo_autenticacion() == MODO_HEADERS:
        email = (x_user_email or "").strip().lower()
        sub = (x_user_id or "").strip()
        if not email and not sub:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Falta la identidad.")
    else:
        identidad = await verificar_token_google(extraer_bearer(authorization))
        email, sub = identidad.email, identidad.sub
    try:
        operador = await plataforma_service.verificar_operador(session, email=email, sub=sub)
    except HTTPException as exc:
        if exc.status_code == status.HTTP_403_FORBIDDEN:
            raise ErrorNegocio(svc.NO_ES_OPERADOR) from None
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
