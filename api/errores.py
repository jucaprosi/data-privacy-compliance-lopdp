# ¤adpa
"""Manejador y excepciones de negocio para la API REST.

Convierte excepciones semánticas de dominio (ErrorNegocio) en respuestas JSON
compatibles con clientes existentes:
{
    "detail": "<mensaje>",
    "code": "<CODIGO_ERROR>",
    "action_required": "<accion_o_null>"
}
"""
from typing import Optional, Union
from fastapi import Request
from fastapi.responses import JSONResponse

from app_core.errors import CodigoErrorNegocio, CATALOGO_ERRORES


# --- INICIO ADPA-02 ---
from app_core.errors import ErrorNegocio
# --- FIN ADPA-02 ---


async def error_negocio_handler(request: Request, exc: ErrorNegocio) -> JSONResponse:
    """Manejador de excepciones para ErrorNegocio registrado en FastAPI."""
    cuerpo = {
        "detail": exc.detail,
        "code": exc.code,
        "action_required": exc.action_required,
    }
    return JSONResponse(status_code=exc.status_code, content=cuerpo)
