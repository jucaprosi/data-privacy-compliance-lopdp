# ¤evidencias ¤evidencias-vigencia ¤rbac-tenant
"""Vigencia, visibilidad y paquete para inspección de las evidencias (EVI-02).

Existe solo con la bandera `EVIDENCIAS_SUBIDA_FIRMADA` encendida (apagada: 404), como las rutas de EVI-01.
Identidad y organización salen del token; el cuerpo nunca las trae.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, status
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import require_role
from app_core.db.session import get_session
from app_core.errors import ErrorNegocio
from app_core.pasillo import diagnostico as pasillo_diagnostico
from app_core.zona_negocio import hoy_negocio
from features.evidencias import evidencias_service as sala
errores_sala = sala.errores_sala

AUTO_REGISTRO = True
router = APIRouter(prefix="/evidencias", tags=["Evidencias: vigencia y paquete para inspección"])

_consulta = require_role(*sala.ROLES_CONSULTA_DOCUMENTOS)
_dpo = require_role("dpo")
_definir = require_role(*sala.ROLES_DEFINIR_ATRIBUTOS)
TAMANO_MAXIMO_ARCHIVO_BYTES = 10 * 1024 * 1024


def _exigir_bandera() -> None:
    # Va después del rol: se autentica (401), se autoriza (403) y solo entonces se mira la bandera (404).
    if not sala.subida_firmada_activa():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not Found")


def _almacen() -> object:
    return sala.almacen_de_evidencias()


def _hoy() -> date:
    """Día de negocio de Guayaquil, no el UTC: un documento que vence hoy sigue vigente hasta las 24:00 locales."""
    return hoy_negocio()


class DefinirAtributosRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vence_en: Optional[date] = Field(None, description="Fecha de vencimiento; vacía si no vence.")
    visible_para: Optional[list[str]] = Field(
        None, description="Roles que ven el documento; el DPO siempre lo ve. Vacío = los cuatro que consultan."
    )


class AtributosOut(BaseModel):
    documento_id: str
    codigo: str
    nombre_archivo: str
    tipo_mime: str
    tamano_bytes: int
    sha256_hash: str
    subido_en: datetime
    vence_en: Optional[date]
    vigente: bool
    visible_para: list[str]
    controles_vinculados: list[int]


class ListarAtributosResponse(BaseModel):
    total: int
    documentos: list[AtributosOut]


def _a_salida(d: sala.AtributosDocumento, hoy: date) -> AtributosOut:
    return AtributosOut(
        documento_id=d.documento_id, codigo=d.codigo, nombre_archivo=d.nombre_archivo, tipo_mime=d.tipo_mime,
        tamano_bytes=d.tamano_bytes, sha256_hash=d.sha256, subido_en=d.subido_en, vence_en=d.vence_en,
        vigente=d.vigente(hoy), visible_para=d.visible_para, controles_vinculados=d.controles,
    )


@router.get("/atributos", response_model=ListarAtributosResponse, dependencies=[Depends(_consulta), Depends(_exigir_bandera)])
async def listar_atributos(
    ctx: dict = Depends(_consulta), session: AsyncSession = Depends(get_session)
) -> ListarAtributosResponse:
    """Documentos con su vigencia y visibilidad; solo los que tu rol puede ver."""
    hoy = _hoy()
    documentos = await sala.listar_atributos(session, ctx["tenant_id"], ctx["user_id"], ctx["role"])
    return ListarAtributosResponse(total=len(documentos), documentos=[_a_salida(d, hoy) for d in documentos])


@router.put("/documentos/{documento_id}/atributos", response_model=dict, dependencies=[Depends(_definir), Depends(_exigir_bandera)])
async def definir_atributos(
    payload: DefinirAtributosRequest,
    documento_id: str = Path(..., min_length=1),
    ctx: dict = Depends(_definir),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Solo el DPO define la vigencia y la visibilidad."""
    await sala.fijar_atributos(
        session, ctx["tenant_id"], ctx["user_id"], ctx["role"], documento_id, payload.vence_en, payload.visible_para
    )
    return {"status": "SUCCESS"}


@router.get("/documentos/{documento_id}/archivo", dependencies=[Depends(_consulta), Depends(_exigir_bandera)])
async def descargar_documento(
    documento_id: str = Path(..., min_length=1),
    ctx: dict = Depends(_consulta),
    session: AsyncSession = Depends(get_session),
    almacen=Depends(_almacen),
) -> Response:
    """Descarga un documento si tu rol tiene visibilidad sobre él (403 si no)."""
    documento = await sala.atributos_de(session, ctx["tenant_id"], ctx["user_id"], documento_id)
    if not sala.puede_ver(ctx["role"], documento.visible_para):
        raise ErrorNegocio(errores_sala.SIN_VISIBILIDAD)
    contenido = almacen.descargar(documento.clave_almacen, TAMANO_MAXIMO_ARCHIVO_BYTES)
    if contenido is None:
        raise ErrorNegocio(errores_sala.CLAVE_NO_ENCONTRADA)
    return Response(
        content=contenido,
        media_type=documento.tipo_mime,
        headers={"Content-Disposition": f'attachment; filename="{documento.codigo}"'},
    )


@router.get("/paquete-inspeccion", dependencies=[Depends(_consulta), Depends(_exigir_bandera)])
async def paquete_inspeccion(
    ctx: dict = Depends(_consulta),
    session: AsyncSession = Depends(get_session),
    almacen=Depends(_almacen),
) -> Response:
    """ZIP con los documentos vigentes y visibles para tu rol, ordenado por requisito, con índice y huellas."""
    hoy = _hoy()
    nombres = {c["pregunta_id"]: c["control"] for c in pasillo_diagnostico.catalogo_de_controles()}
    contenido = await sala.armar_paquete(
        session, almacen, ctx["tenant_id"], ctx["user_id"], ctx["role"], hoy, nombres
    )
    return Response(
        content=contenido,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="paquete-inspeccion-{hoy.isoformat()}.zip"'},
    )
