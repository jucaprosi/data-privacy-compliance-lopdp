"""Cierre verificado de tareas: puerto del verificador externo (sala ADPA: Hoja de Ruta). ¤roadmap

RM-24. La hoja de ruta no sabe quién verifica: define el puerto `VerificadorDeCierre` y guarda
un solo verificador activo. Otra sala lo implementa y lo registra por la compuerta de Roadmap.
Sin verificador, o si responde `None`, el cierre se comporta como siempre.
"""
from __future__ import annotations

from typing import Optional, Protocol, runtime_checkable

from app_core.errors import ErrorNegocio
from app_core.errors import CodigoErrorNegocio

RM_CIERRE_SIN_EVIDENCIA = CodigoErrorNegocio(
    codigo="RM_CIERRE_SIN_EVIDENCIA",
    status_code=409,
    mensaje_defecto="La tarea no puede completarse: falta evidencia conforme.",
    action_required=None,
)


@runtime_checkable
class VerificadorDeCierre(Protocol):
    """True: evidencia conforme. False: no conforme (bloquea). None: sin opinión."""

    def evidencia_conforme(self, tenant_id: str, tarea_id: str) -> bool | None: ...


_verificador: Optional[VerificadorDeCierre] = None


def registrar_verificador_cierre(verificador: Optional[VerificadorDeCierre]) -> None:
    """Registra el único verificador activo; `None` lo retira."""
    global _verificador
    _verificador = verificador


def verificador_cierre_registrado() -> Optional[VerificadorDeCierre]:
    return _verificador


def exigir_cierre_conforme(tenant_id: str, tarea_id: str) -> None:
    """Rechaza con RM_CIERRE_SIN_EVIDENCIA (409) si el verificador responde False."""
    if _verificador is None:
        return
    if _verificador.evidencia_conforme(tenant_id, tarea_id) is False:
        raise ErrorNegocio(RM_CIERRE_SIN_EVIDENCIA)
