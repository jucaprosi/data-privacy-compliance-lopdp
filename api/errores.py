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


class ErrorNegocio(Exception):
    """Excepción de negocio tipada con código semántico."""

    def __init__(
        self,
        codigo_o_obj: Union[str, CodigoErrorNegocio],
        detail: Optional[str] = None,
        status_code: Optional[int] = None,
        action_required: Optional[str] = None,
    ):
        if isinstance(codigo_o_obj, CodigoErrorNegocio):
            self.code: str = codigo_o_obj.codigo
            self.status_code: int = status_code or codigo_o_obj.status_code
            self.detail: str = detail or codigo_o_obj.mensaje_defecto
            self.action_required: Optional[str] = (
                action_required if action_required is not None else codigo_o_obj.action_required
            )
        elif isinstance(codigo_o_obj, str):
            self.code = codigo_o_obj
            cat = CATALOGO_ERRORES.get(codigo_o_obj)
            if cat:
                self.status_code = status_code or cat.status_code
                self.detail = detail or cat.mensaje_defecto
                self.action_required = (
                    action_required if action_required is not None else cat.action_required
                )
            else:
                self.status_code = status_code or 400
                self.detail = detail or codigo_o_obj
                self.action_required = action_required
        else:
            raise TypeError("codigo_o_obj debe ser str o CodigoErrorNegocio")

        super().__init__(self.detail)


async def error_negocio_handler(request: Request, exc: ErrorNegocio) -> JSONResponse:
    """Manejador de excepciones para ErrorNegocio registrado en FastAPI."""
    cuerpo = {
        "detail": exc.detail,
        "code": exc.code,
        "action_required": exc.action_required,
    }
    return JSONResponse(status_code=exc.status_code, content=cuerpo)
