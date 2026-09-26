import io
import logging
from typing import Any, Dict, List

from fastapi import APIRouter, UploadFile, File, HTTPException, Body
from fastapi.responses import StreamingResponse, PlainTextResponse

from features.niif18.niif18_service import (
    procesar_balance_prueba,
    recalcular_estado_niif18,
    validar_mpm,
    generar_informe_niif18,
    exportar_excel_niif18,
    exportar_informe_markdown,
    exportar_informe_pdf,
)
from features.niif18.doctrine.doctrine_service import NIIF18DoctrineService

router = APIRouter(prefix="/niif18", tags=["NIIF 18 Reporting"])
logger = logging.getLogger("jubys_lopdp_json_logger")


def _error(exc: Exception) -> HTTPException:
    """Datos inválidos del cliente son 422; cualquier otra falla es 500."""
    if isinstance(exc, ValueError):
        return HTTPException(status_code=422, detail=str(exc))
    logger.error(f"Error NIIF 18: {exc}")
    return HTTPException(status_code=500, detail=str(exc))


def _cuentas_y_mpm(payload: Any) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], str]:
    """Acepta una lista de cuentas o un objeto {cuentas, mpm, empresa}."""
    if isinstance(payload, list):
        return payload, [], ""
    return payload.get("cuentas", []), payload.get("mpm", []) or [], str(payload.get("empresa", ""))


@router.post("/procesar-balance")
async def procesar_balance(file: UploadFile = File(...)):
    """
    Recibe un Balance de Prueba (Excel/CSV), mapea sus columnas, lo clasifica en las
    5 categorías de la NIIF 18 y devuelve subtotales, diagnóstico e indicadores.
    """
    if not (file.filename or "").lower().endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(status_code=400, detail="Formato de archivo no soportado.")
    try:
        return procesar_balance_prueba(await file.read(), file.filename)
    except Exception as e:
        raise _error(e)


@router.post("/recalcular-subtotales")
async def recalcular_balance(cuentas: List[Dict[str, Any]] = Body(...)):
    """Recalcula subtotales y diagnóstico tras la reclasificación del usuario."""
    try:
        return recalcular_estado_niif18(cuentas)
    except Exception as e:
        raise _error(e)


@router.post("/mpm")
async def registrar_mpm(payload: Dict[str, Any] = Body(...)):
    """Registra y valida una Medida de la Gerencia (MPM) con su efecto fiscal."""
    try:
        return validar_mpm(
            nombre=payload.get("nombre", ""),
            subtotal_base=payload.get("subtotal_base", "1. Resultado Operativo"),
            valor_base=float(payload.get("valor_base", 0.0)),
            ajuste=float(payload.get("ajuste", 0.0)),
            justificacion=payload.get("justificacion", ""),
        )
    except Exception as e:
        raise _error(e)


@router.post("/informe")
async def informe(payload: Any = Body(...)):
    """Diagnóstico, estado de resultados estructurado y recomendaciones de implementación."""
    try:
        cuentas, mpm, _ = _cuentas_y_mpm(payload)
        return generar_informe_niif18(cuentas, mpm)
    except Exception as e:
        raise _error(e)


@router.post("/exportar/excel")
async def exportar_excel(payload: Any = Body(...)):
    """Paquete Excel de cierre generado en memoria."""
    try:
        cuentas, mpm, _ = _cuentas_y_mpm(payload)
        return StreamingResponse(
            io.BytesIO(exportar_excel_niif18(cuentas, mpm)),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=estado_resultados_niif18.xlsx"},
        )
    except Exception as e:
        raise _error(e)


@router.post("/exportar/informe")
async def exportar_informe(payload: Any = Body(...)):
    """Informe de diagnóstico y recomendaciones en Markdown."""
    try:
        cuentas, mpm, empresa = _cuentas_y_mpm(payload)
        return PlainTextResponse(
            exportar_informe_markdown(cuentas, mpm, empresa),
            media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": "attachment; filename=informe_niif18.md"},
        )
    except Exception as e:
        raise _error(e)


@router.post("/exportar/pdf")
async def exportar_pdf(payload: Any = Body(...)):
    """Informe de diagnóstico y recomendaciones en PDF."""
    try:
        cuentas, mpm, empresa = _cuentas_y_mpm(payload)
        return StreamingResponse(
            io.BytesIO(exportar_informe_pdf(cuentas, mpm, empresa)),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=informe_niif18.pdf"},
        )
    except Exception as e:
        raise _error(e)


@router.get("/doctrina")
async def obtener_doctrina():
    """Devuelve los volúmenes para el Visor Doctrinal."""
    return NIIF18DoctrineService().get_all_doctrine()
