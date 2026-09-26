"""Abstracción del proveedor de IA (compatible con OpenAI). Sin simulación: sin configuración no hay proveedor."""
from __future__ import annotations

import logging
import os
from typing import Protocol

from features.preanalisis.domain.models import (
    EstadoProveedor,
    PropuestaModelo,
    ProveedorFallo,
)

logger = logging.getLogger(__name__)

MODELO_POR_DEFECTO = "gpt-4o-mini"
TIMEOUT_SEGUNDOS = 60.0
MOTIVO_NO_DISPONIBLE = (
    "El pre-llenado asistido está deshabilitado. Configure PREANALISIS_API_KEY (o OPENAI_API_KEY) y, "
    "opcionalmente, PREANALISIS_BASE_URL (modelo local compatible con OpenAI) y PREANALISIS_MODEL."
)


class ProveedorIA(Protocol):
    nombre: str
    modelo: str

    async def proponer(self, sistema: str, usuario: str) -> PropuestaModelo: ...


class ProveedorOpenAICompatible:
    """Cliente OpenAI (o servidor compatible: vLLM/Ollama). La clave nunca se registra ni se expone."""

    def __init__(self, api_key: str | None, base_url: str | None, modelo: str) -> None:
        self._api_key = api_key
        self._base_url = base_url
        self.modelo = modelo
        self.nombre = "openai-compatible" if base_url else "openai"

    async def proponer(self, sistema: str, usuario: str) -> PropuestaModelo:
        try:
            from openai import AsyncOpenAI

            async with AsyncOpenAI(
                api_key=self._api_key or "sin-clave-local",
                base_url=self._base_url or None,
                timeout=TIMEOUT_SEGUNDOS,
                max_retries=1,
            ) as cliente:
                respuesta = await cliente.beta.chat.completions.parse(
                    model=self.modelo,
                    messages=[
                        {"role": "system", "content": sistema},
                        {"role": "user", "content": usuario},
                    ],
                    response_format=PropuestaModelo,
                    temperature=0,
                )
            propuesta = respuesta.choices[0].message.parsed
        except Exception as exc:  # noqa: BLE001
            logger.warning("Fallo del proveedor de pre-análisis: %s", type(exc).__name__)
            raise ProveedorFallo("El proveedor de IA no respondió correctamente.") from exc
        if propuesta is None:
            raise ProveedorFallo("El proveedor de IA no devolvió una propuesta válida.")
        return propuesta


_proveedor_de_prueba: ProveedorIA | None = None


def inyectar_proveedor_de_prueba(proveedor: ProveedorIA | None) -> None:
    """SOLO PARA PRUEBAS: fuerza un proveedor falso. Nunca usar en código de producción."""
    global _proveedor_de_prueba
    _proveedor_de_prueba = proveedor


def restablecer_proveedor_entorno() -> None:
    """Descarta cualquier proveedor inyectado y vuelve al configurado por entorno."""
    inyectar_proveedor_de_prueba(None)


def obtener_proveedor() -> ProveedorIA | None:
    if _proveedor_de_prueba is not None:
        return _proveedor_de_prueba
    api_key = (os.environ.get("PREANALISIS_API_KEY") or os.environ.get("OPENAI_API_KEY") or "").strip()
    base_url = (os.environ.get("PREANALISIS_BASE_URL") or "").strip()
    if not api_key and not base_url:
        return None
    modelo = (os.environ.get("PREANALISIS_MODEL") or "").strip() or MODELO_POR_DEFECTO
    return ProveedorOpenAICompatible(api_key or None, base_url or None, modelo)


def estado_proveedor() -> EstadoProveedor:
    p = obtener_proveedor()
    if p is None:
        return EstadoProveedor(False, None, None, MOTIVO_NO_DISPONIBLE)
    return EstadoProveedor(True, p.nombre, p.modelo, None)
