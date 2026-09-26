"""Enrutador REST de la sala ADPA Pre-análisis: pre-llenado asistido (la IA propone, el humano decide).

Contrato con el frontend: nombres de campo y formas JSON fijos. No se persiste ni registra contenido.
"""
from __future__ import annotations

import asyncio
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from pydantic import BaseModel, ConfigDict, Field
from starlette.formparsers import MultiPartParser

from api.dependencies import obtener_tenant_id_actual
from features.preanalisis.preanalisis_service import (
    CONTROL_ID_MAX,
    CONTROL_ID_MIN,
    MAX_BYTES_ARCHIVO,
    MAX_CARACTERES_FRAGMENTO,
    MAX_FRAGMENTOS_ANALISIS,
    ArchivoDemasiadoGrande,
    ControlContexto,
    DocumentoIlegible,
    FormatoNoSoportado,
    Fragmento,
    ProveedorFallo,
    ProveedorNoDisponible,
    analizar_control,
    estado_servicio,
    preparar_documento,
)

router = APIRouter(prefix="/preanalisis", tags=["Pre-análisis asistido de controles"])

MAX_BYTES_JSON = 128 * 1024
TIMEOUT_EXTRACCION_S = 20.0
_SEMAFORO_EXTRACCION = asyncio.Semaphore(2)

# El contenido del cliente no debe tocar disco: sube el umbral de volcado a archivo temporal del multipart (1 MB por defecto).
if hasattr(MultiPartParser, "spool_max_size"):
    MultiPartParser.spool_max_size = max(MultiPartParser.spool_max_size, 27 * 1024 * 1024)


async def _preparar_acotado(nombre: str, contenido: bytes, ctx: ControlContexto):
    """Extracción en hilo, con concurrencia limitada (el cupo se libera al terminar el hilo, no al expirar) y timeout."""
    await _SEMAFORO_EXTRACCION.acquire()
    try:
        tarea = asyncio.ensure_future(asyncio.to_thread(preparar_documento, nombre, contenido, ctx))
    except BaseException:
        _SEMAFORO_EXTRACCION.release()
        raise

    def _fin(t: "asyncio.Future") -> None:
        if not t.cancelled():
            t.exception()  # consume la excepción para evitar avisos si ya expiró
        _SEMAFORO_EXTRACCION.release()

    tarea.add_done_callback(_fin)
    try:
        return await asyncio.wait_for(asyncio.shield(tarea), TIMEOUT_EXTRACCION_S)
    except asyncio.TimeoutError as exc:
        raise DocumentoIlegible("El documento tardó demasiado en procesarse.") from exc


class EstadoResponse(BaseModel):
    disponible: bool
    proveedor: Optional[str] = None
    modelo: Optional[str] = None
    motivo: Optional[str] = None


class FragmentoRelevanteOut(BaseModel):
    texto: str
    origen: str
    relevancia: float


class PrepararResponse(BaseModel):
    formato: str
    caracteres_totales: int
    fragmentos: list[FragmentoRelevanteOut]
    pii_enmascarada: int
    advertencias: list[str]


class FragmentoIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    texto: str = Field(..., min_length=1, max_length=MAX_CARACTERES_FRAGMENTO)
    origen: str = Field("", max_length=200)


class AnalizarRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    control_id: int = Field(..., ge=CONTROL_ID_MIN, le=CONTROL_ID_MAX)
    control: str = Field("", max_length=500)
    enunciado: str = Field("", max_length=4000)
    evidencia_esperada: str = Field("", max_length=4000)
    referencia_normativa: str = Field("", max_length=1000)
    fragmentos: list[FragmentoIn] = Field(default_factory=list, max_length=MAX_FRAGMENTOS_ANALISIS)


class CitaOut(BaseModel):
    fragmento: str
    motivo: str


class AnalizarResponse(BaseModel):
    estado: str
    nivel_evidencia_maximo: int
    citas: list[CitaOut]
    citas_descartadas: int
    razonamiento: str
    limitaciones: list[str]
    modelo: str


@router.get("/estado", response_model=EstadoResponse)
def obtener_estado(tenant_id: str = Depends(obtener_tenant_id_actual)) -> EstadoResponse:
    e = estado_servicio()
    return EstadoResponse(disponible=e.disponible, proveedor=e.proveedor, modelo=e.modelo, motivo=e.motivo)


@router.post("/preparar", response_model=PrepararResponse)
async def preparar(
    archivo: Annotated[UploadFile, File(description="Documento a analizar (pdf, docx, xlsx, csv, txt, md)")],
    control_id: Annotated[int, Form(ge=CONTROL_ID_MIN, le=CONTROL_ID_MAX)],
    control: Annotated[str, Form(max_length=500)] = "",
    enunciado: Annotated[str, Form(max_length=4000)] = "",
    evidencia_esperada: Annotated[str, Form(max_length=4000)] = "",
    tenant_id: str = Depends(obtener_tenant_id_actual),
) -> PrepararResponse:
    contenido = await archivo.read(MAX_BYTES_ARCHIVO + 1)
    if len(contenido) > MAX_BYTES_ARCHIVO:
        raise HTTPException(413, "El archivo excede el límite de 25 MB.")
    ctx = ControlContexto(
        control_id=control_id, control=control, enunciado=enunciado, evidencia_esperada=evidencia_esperada
    )
    try:
        r = await _preparar_acotado(archivo.filename or "", contenido, ctx)
    except FormatoNoSoportado as exc:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, str(exc)) from exc
    except ArchivoDemasiadoGrande as exc:
        raise HTTPException(413, str(exc)) from exc
    except DocumentoIlegible as exc:
        raise HTTPException(422, str(exc)) from exc
    return PrepararResponse(
        formato=r.formato,
        caracteres_totales=r.caracteres_totales,
        fragmentos=[FragmentoRelevanteOut(texto=f.texto, origen=f.origen, relevancia=f.relevancia) for f in r.fragmentos],
        pii_enmascarada=r.pii_enmascarada,
        advertencias=r.advertencias,
    )


@router.post("/analizar", response_model=AnalizarResponse)
async def analizar(
    request: Request,
    cuerpo: AnalizarRequest,
    tenant_id: str = Depends(obtener_tenant_id_actual),
) -> AnalizarResponse:
    declarado = request.headers.get("content-length")
    if declarado and declarado.isdigit() and int(declarado) > MAX_BYTES_JSON:
        raise HTTPException(413, "El cuerpo de la solicitud es demasiado grande.")
    ctx = ControlContexto(
        control_id=cuerpo.control_id,
        control=cuerpo.control,
        enunciado=cuerpo.enunciado,
        evidencia_esperada=cuerpo.evidencia_esperada,
        referencia_normativa=cuerpo.referencia_normativa,
    )
    fragmentos = [Fragmento(texto=f.texto, origen=f.origen) for f in cuerpo.fragmentos]
    try:
        p = await analizar_control(ctx, fragmentos)
    except ProveedorNoDisponible as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
    except ProveedorFallo as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "El proveedor de IA no pudo completar el análisis.") from exc
    return AnalizarResponse(
        estado=p.estado,
        nivel_evidencia_maximo=p.nivel_evidencia_maximo,
        citas=[CitaOut(fragmento=c.fragmento, motivo=c.motivo) for c in p.citas],
        citas_descartadas=p.citas_descartadas,
        razonamiento=p.razonamiento,
        limitaciones=p.limitaciones,
        modelo=p.modelo,
    )
