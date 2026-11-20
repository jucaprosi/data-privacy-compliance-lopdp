"""Abstracción del proveedor de IA sobre Vertex AI. Sin simulación: sin configuración no hay proveedor."""
from __future__ import annotations

import logging
from typing import Protocol

from app_core.pasillo import inferencia as pasillo_inferencia
from features.preanalisis.domain.models import (
    EstadoProveedor,
    PropuestaModelo,
    ProveedorFallo,
    ProveedorNoDisponible,
)

logger = logging.getLogger(__name__)

MODELO_POR_DEFECTO = "gemini-2.5-flash"
PROVEEDOR_NOMBRE = "Google Vertex AI"
TIMEOUT_SEGUNDOS = 60.0
MOTIVO_NO_DISPONIBLE = (
    "El pre-llenado asistido no está disponible en este momento. "
    "Contacte a la persona administradora de la plataforma."
)


class ProveedorIA(Protocol):
    nombre: str
    modelo: str

    async def proponer(self, sistema: str, usuario: str) -> PropuestaModelo: ...


class ProveedorVertex:
    """Cliente de pre-análisis respaldado por Vertex AI vía la compuerta de inferencia."""

    def __init__(self, modelo: str = MODELO_POR_DEFECTO) -> None:
        self.nombre = PROVEEDOR_NOMBRE
        self.modelo = modelo

    async def proponer(
        self,
        sistema: str,
        usuario: str,
        *,
        org_id: str | None = "preanalisis",
    ) -> PropuestaModelo:
        if not isinstance(org_id, str) or not org_id.strip():
            raise ProveedorNoDisponible(MOTIVO_NO_DISPONIBLE)
        InferenciaNoDisponible, _ = pasillo_inferencia.errores()
        try:
            salida = await pasillo_inferencia.generar_estructurado(
                sistema,
                usuario,
                PropuestaModelo,
                modelo=self.modelo,
                org_id=org_id,
            )
        except InferenciaNoDisponible as exc:
            logger.warning("Compuerta de pre-análisis no disponible: %s", type(exc).__name__)
            if not pasillo_inferencia.estado().disponible:
                raise ProveedorNoDisponible(MOTIVO_NO_DISPONIBLE) from exc
            raise ProveedorFallo("El proveedor de IA no respondió correctamente.") from exc
        except Exception as exc:  # noqa: BLE001
            logger.warning("Fallo del proveedor de pre-análisis: %s", type(exc).__name__)
            raise ProveedorFallo("El proveedor de IA no respondió correctamente.") from exc
        if salida is None:
            raise ProveedorFallo("El proveedor de IA no devolvió una propuesta válida.")
        if isinstance(salida, PropuestaModelo):
            return salida
        return PropuestaModelo.model_validate(salida)


_proveedor_de_prueba: ProveedorIA | None = None


def inyectar_proveedor_de_prueba(proveedor: ProveedorIA | None) -> None:
    """SOLO PARA PRUEBAS: fuerza un proveedor falso. Nunca usar en código de producción."""
    global _proveedor_de_prueba
    _proveedor_de_prueba = proveedor


def restablecer_proveedor_entorno() -> None:
    """Descarta cualquier proveedor inyectado y vuelve al configurado en la plataforma."""
    inyectar_proveedor_de_prueba(None)


def obtener_proveedor() -> ProveedorIA | None:
    if _proveedor_de_prueba is not None:
        return _proveedor_de_prueba
    if not pasillo_inferencia.estado().disponible:
        return None
    return ProveedorVertex(modelo=MODELO_POR_DEFECTO)


def _formatear_ubicacion(cruda: object) -> str | None:
    if not isinstance(cruda, str):
        return None
    limpia = cruda.strip()
    if not limpia:
        return None
    return limpia if limpia.startswith("servidores ") else f"servidores en {limpia}"


def estado_proveedor() -> EstadoProveedor:
    if _proveedor_de_prueba is not None:
        return EstadoProveedor(
            True,
            _proveedor_de_prueba.nombre,
            _proveedor_de_prueba.modelo,
            None,
            getattr(_proveedor_de_prueba, "ubicacion", None),
        )
    est = pasillo_inferencia.estado()
    if not est.disponible:
        return EstadoProveedor(False, None, None, MOTIVO_NO_DISPONIBLE, None)
    return EstadoProveedor(
        True,
        PROVEEDOR_NOMBRE,
        MODELO_POR_DEFECTO,
        None,
        _formatear_ubicacion(getattr(est, "ubicacion", None)),
    )
