# ¤¤backend-developer
"""Registro estructurado compatible con Cloud Logging y Error Reporting (OPS-07).

¤observabilidad ¤seguridad-tenant
R1: todo mensaje y toda traza pasan por el saneador DLP antes de escribirse.
R2: las entradas de una petición comparten su request_id (contextvars).
R3: no se registran consultas, cuerpos ni cabeceras de autorización.
"""
from __future__ import annotations

import contextvars
import datetime
import json
import logging
import re
import sys
import traceback

from app_core.dlp_sanitizer import DLP_TOKEN, sanitizar_texto_pii

NOMBRE_REGISTRO = "evydentia"
_TIPO_ERROR_REPORTING = "type.googleapis.com/google.devtools.clouderrorreporting.v1beta1.ReportedErrorEvent"
# RUC ecuatoriano: 13 dígitos terminados en 001 (el saneador DLP cubre cédula, correo y teléfono).
_RUC = re.compile(r"(?<!\w)[0-9]{10}001(?!\w)")
_CAMPOS = ("request_id", "tenant_id", "user_id", "method", "path", "status", "duration_ms")

_contexto: contextvars.ContextVar[dict] = contextvars.ContextVar("ops07_contexto", default={})


# ¤sanear-registro
def sanear(texto: str) -> str:
    """Quita cédulas, RUC, correos y teléfonos de un texto destinado al registro."""
    if not texto:
        return texto
    return sanitizar_texto_pii(_RUC.sub(DLP_TOKEN, str(texto)))


def fijar_contexto(**campos) -> contextvars.Token:
    """Fija campos de correlación (request_id, tenant_id, user_id interno…) para la petición en curso."""
    nuevo = {**_contexto.get(), **{k: v for k, v in campos.items() if v is not None}}
    return _contexto.set(nuevo)


def limpiar_contexto(token: contextvars.Token | None = None) -> None:
    if token is not None:
        _contexto.reset(token)
    else:
        _contexto.set({})


def request_id_actual() -> str | None:
    return _contexto.get().get("request_id")


class FormateadorNube(logging.Formatter):
    """Una línea JSON por entrada, con `severity` y `message` como los lee Cloud Logging."""

    def format(self, record: logging.LogRecord) -> str:
        entrada = {
            "severity": record.levelname,
            "time": datetime.datetime.fromtimestamp(record.created, datetime.UTC).isoformat(),
        }
        contexto = _contexto.get()
        for campo in _CAMPOS:
            valor = getattr(record, campo, None)
            if valor is None:
                valor = contexto.get(campo)
            if valor is not None:
                entrada[campo] = valor
        if "path" in entrada:
            entrada["path"] = str(entrada["path"]).split("?", 1)[0]
        mensaje = sanear(record.getMessage())
        if record.exc_info:
            traza = "".join(traceback.format_exception(*record.exc_info))
            mensaje = f"{mensaje}\n{sanear(traza)}"
            entrada["@type"] = _TIPO_ERROR_REPORTING
        entrada["message"] = mensaje
        return json.dumps(entrada, ensure_ascii=False, default=str)


def configurar_registro(nivel: int = logging.INFO, flujo=None) -> logging.Logger:
    """Configura el registro `evydentia` con salida JSON a stdout (idempotente)."""
    registro = logging.getLogger(NOMBRE_REGISTRO)
    registro.setLevel(nivel)
    registro.propagate = False
    for previo in [h for h in registro.handlers if getattr(h, "_ops07", False)]:
        registro.removeHandler(previo)
    manejador = logging.StreamHandler(flujo or sys.stdout)
    manejador._ops07 = True  # type: ignore[attr-defined]
    manejador.setFormatter(FormateadorNube())
    registro.addHandler(manejador)
    return registro


def registrar_error(registro: logging.Logger, exc: BaseException, mensaje: str = "Error no controlado") -> None:
    """Escribe una excepción en el formato que Error Reporting agrupa, con la traza saneada."""
    registro.error(mensaje, exc_info=(type(exc), exc, exc.__traceback__))
