# ¤inteligencia-normativa ¤vigilancia-spdp ¤seguridad
"""Router del Centro de Vigilancia Normativa (NORM-02), bajo /api/v1/normativa.

El corpus es global. Lo leen el operador de la plataforma y cualquier rol activo de una organización; lo dispara y
lo revisa solo el operador (la identidad sale del token verificado, nunca de una cabecera de rol).
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Query, status
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import get_usuario_autenticado
from api.routers.plataforma import require_operador
from app_core.db.session import get_session
from features.inteligencia_normativa import inteligencia_normativa_service as svc
from features.organizacion import organizacion_service

errores = svc.errores  # los códigos estables llegan por la compuerta
AUTO_REGISTRO = True
PREFIJO = "/api/v1"

router = APIRouter(prefix="/normativa", tags=["Vigilancia normativa (SPDP)"])

_ESTADOS_HTTP = {
    errores.NORMATIVA_RESOLUCION_NO_ENCONTRADA: status.HTTP_404_NOT_FOUND,
    errores.NORMATIVA_NOTA_OBLIGATORIA: status.HTTP_422_UNPROCESSABLE_ENTITY,
    errores.NORMATIVA_ESTADO_NO_PERMITIDO: status.HTTP_422_UNPROCESSABLE_ENTITY,
    errores.NORMATIVA_ORIGINAL_NO_DISPONIBLE: status.HTTP_503_SERVICE_UNAVAILABLE,
}


def _http(exc: svc.ErrorNormativo) -> HTTPException:
    """Solo el código estable; nunca la URL ni el texto de la fuente."""
    return HTTPException(_ESTADOS_HTTP.get(exc.codigo, status.HTTP_500_INTERNAL_SERVER_ERROR), {"codigo": exc.codigo})


async def lector_del_corpus(
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    x_user_email: Optional[str] = Header(None, alias="X-User-Email"),
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
    x_role: Optional[str] = Header(None, alias="X-Role"),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Lectura: un rol activo de una organización (con X-Tenant-ID y X-Role) o, sin ellos, el operador."""
    if x_tenant_id:
        usuario = await get_usuario_autenticado(authorization, x_user_id or "", session)
        if not x_role or not await organizacion_service.has_active_role(session, x_tenant_id, usuario, x_role):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Sin membresía activa")
        return {"tipo": "organizacion", "usuario_id": usuario}
    operador = await require_operador(authorization, x_user_id, x_user_email, session)
    return {"tipo": "operador", "usuario_id": str(operador["id"])}


class RevisionRequest(BaseModel):
    estado: str = Field(..., max_length=30)
    nota: str = Field(default="", max_length=4000)


@router.get("/resoluciones")
async def listar(
    numero: Optional[str] = None, anio: Optional[int] = Query(None, ge=1990, le=2100), q: Optional[str] = None,
    organo: Optional[str] = None, materia: Optional[str] = None, estado: Optional[str] = None,
    pagina: int = Query(1, ge=1), por_pagina: int = Query(25, ge=1, le=100),
    _: dict = Depends(lector_del_corpus),
) -> dict:
    filtros = svc.FiltrosCatalogo(numero=numero, anio=anio, q=q, organo=organo, materia=materia, estado=estado,
                                  pagina=pagina, por_pagina=por_pagina)
    return (await svc.catalogo(filtros)).model_dump(mode="json")


@router.get("/resoluciones/{id_resolucion}")
async def detalle(id_resolucion: str, _: dict = Depends(lector_del_corpus)) -> dict:
    try:
        base = await svc.obtener_resolucion(id_resolucion)
        nota = await svc.detalle_con_nota(id_resolucion)
    except svc.ErrorNormativo as exc:
        raise _http(exc) from exc
    salida = base.model_dump(mode="json", exclude={"ruta_original"})
    salida["versiones"] = [{k: v for k, v in ver.items() if k != "ruta_original"} for ver in salida["versiones"]]
    salida["nota_revision"] = nota.nota_revision
    return salida


@router.get("/resoluciones/{id_resolucion}/original")
async def original(id_resolucion: str, _: dict = Depends(lector_del_corpus)) -> Response:
    """El PDF por el backend, con autorización previa; nunca por una ruta pública."""
    try:
        contenido = await svc.leer_original_de(id_resolucion)
    except svc.ErrorNormativo as exc:
        raise _http(exc) from exc
    return Response(content=contenido, media_type="application/pdf", headers={
        "Cache-Control": "no-store", "Content-Disposition": 'inline; filename="resolucion.pdf"',
        "X-Content-Type-Options": "nosniff",
    })


@router.post("/monitoreo", status_code=status.HTTP_202_ACCEPTED)
async def disparar(tareas: BackgroundTasks, _: dict = Depends(require_operador)) -> dict:
    tareas.add_task(svc.disparar_monitoreo, "manual")
    return {"estado": "aceptado"}


@router.get("/monitoreo")
async def bitacora(limite: int = Query(50, ge=1, le=200), _: dict = Depends(lector_del_corpus)) -> list[dict]:
    return [c.model_dump(mode="json") for c in await svc.bitacora(limite)]


@router.post("/resoluciones/{id_resolucion}/revision")
async def revisar(id_resolucion: str, cuerpo: RevisionRequest, operador: dict = Depends(require_operador)) -> dict:
    try:
        r = await svc.revisar_estado(id_resolucion, cuerpo.estado, cuerpo.nota, str(operador["id"]))
    except svc.ErrorNormativo as exc:
        raise _http(exc) from exc
    return r.model_dump(mode="json")
