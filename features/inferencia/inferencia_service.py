# ¤gemini-vertex ¤arbitro
"""Compuerta de inferencia Gemini en Vertex AI sin clave (IA-03): DLP previo, tope de organización, falla cerrada."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable

from pydantic import BaseModel

from app_core.dlp_sanitizer import sanitizar_texto_pii
from features.inferencia.domain.errores import MOTIVO_NEUTRO, InferenciaNoDisponible
from features.inferencia.domain.modelos_permitidos import MODELOS_PERMITIDOS
from features.inferencia.domain.prompts import PromptVersionado
from features.inferencia.domain.regiones import UBICACION_POR_REGION
from features.inferencia.domain.traza import Traza
from features.inferencia.services import cliente_vertex

logger = logging.getLogger(__name__)

__all__ = [
    "EstadoProveedor",
    "InferenciaNoDisponible",
    "MODELOS_PERMITIDOS",
    "MOTIVO_NEUTRO",
    "estado",
    "PromptVersionado",
    "Traza",
    "generar_estructurado",
    "generar_trazado",
    "registrar_traza",
    "inyectar_cliente_de_prueba",
    "inyectar_consumidor_de_prueba",
]


@dataclass(frozen=True)
class EstadoProveedor:
    disponible: bool
    proveedor: str | None
    modelo: str | None
    motivo: str | None
    region: str | None = None
    ubicacion: str | None = None


_cliente = None
_cliente_de_prueba = None
_consumidor_de_prueba: Callable | None = None


def inyectar_cliente_de_prueba(cliente) -> None:
    """SOLO PARA PRUEBAS: cliente falso."""
    global _cliente_de_prueba
    _cliente_de_prueba = cliente


def inyectar_consumidor_de_prueba(consumidor: Callable | None) -> None:
    """SOLO PARA PRUEBAS: sustituye el consumo del tope (corrutina `f(org_id)`)."""
    global _consumidor_de_prueba
    _consumidor_de_prueba = consumidor


def _region_valida() -> tuple[str, str]:
    """(región, ubicación) o InferenciaNoDisponible si falta o no tiene etiqueta."""
    _, region = cliente_vertex.configuracion()
    ubicacion = UBICACION_POR_REGION.get(region)
    if ubicacion is None:
        raise InferenciaNoDisponible()
    return region, ubicacion


def estado() -> EstadoProveedor:
    """Sin conectar: solo mira configuración y mapa de regiones."""
    try:
        region, ubicacion = _region_valida()
    except InferenciaNoDisponible:
        return EstadoProveedor(False, None, None, MOTIVO_NEUTRO)
    return EstadoProveedor(True, "vertex-ai", None, None, region, ubicacion)


def _obtener_cliente():
    global _cliente
    _region_valida()
    if _cliente_de_prueba is not None:
        return _cliente_de_prueba
    if _cliente is None:
        _cliente = cliente_vertex.crear_cliente()
    return _cliente


async def _consumir_tope(org_id: str) -> None:
    if _consumidor_de_prueba is not None:
        await _consumidor_de_prueba(org_id)
        return
    from app_core.db.session import async_session_factory, fijar_contexto_rls
    from app_core.limites.tope_organizacion import consumir_generacion

    async with async_session_factory() as session:
        await fijar_contexto_rls(session, org_id, "inferencia")
        await consumir_generacion(session, org_id)
        await session.commit()


async def _generar(
    sistema: str, usuario: str, esquema: type[BaseModel], *, modelo: str, org_id: str
) -> tuple[BaseModel, object]:
    """Núcleo común: (resultado validado, respuesta cruda). Falla cerrada: sin plan simulado ni respaldo."""
    if modelo not in MODELOS_PERMITIDOS:
        raise InferenciaNoDisponible()
    await _consumir_tope(org_id)  # ErrorNegocio 429 si se agotó; no llega al cliente
    sistema_seguro = sanitizar_texto_pii(sistema)
    usuario_seguro = sanitizar_texto_pii(usuario)
    try:
        cliente = _obtener_cliente()
        ultimo: Exception | None = None
        for _ in range(2):  # un reintento como máximo
            try:
                respuesta = await cliente_vertex.generar_json(
                    cliente, modelo, sistema_seguro, usuario_seguro, esquema
                )
                texto = getattr(respuesta, "text", None)
                if not texto:
                    raise ValueError("respuesta vacía")
                return esquema.model_validate_json(texto), respuesta
            except Exception as exc:  # noqa: BLE001
                ultimo = exc
        raise ultimo  # type: ignore[misc]
    except InferenciaNoDisponible:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.warning("Fallo de inferencia Vertex: %s", type(exc).__name__)
        raise InferenciaNoDisponible() from exc


async def generar_estructurado(
    sistema: str, usuario: str, esquema: type[BaseModel], *, modelo: str, org_id: str
) -> BaseModel:
    """Una generación estructurada validada contra `esquema`. Se retira cuando IA-05 e IA-06 usen `generar_trazado`."""
    resultado, _ = await _generar(sistema, usuario, esquema, modelo=modelo, org_id=org_id)
    return resultado


async def generar_trazado(
    prompt: PromptVersionado,
    valores: dict,
    esquema: type[BaseModel],
    *,
    modelo: str,
    org_id: str,
    corpus_sha256: str | None = None,
) -> tuple[BaseModel, Traza]:
    """Generación con traza (invariante 64). Falla cerrada si Vertex no devuelve `model_version`."""
    usuario = prompt.renderizar(valores)
    resultado, respuesta = await _generar(prompt.sistema, usuario, esquema, modelo=modelo, org_id=org_id)
    version = getattr(respuesta, "model_version", None)
    if not isinstance(version, str) or not version.strip():
        logger.warning("Vertex no devolvió la versión del modelo")
        raise InferenciaNoDisponible()
    return resultado, Traza(
        sala=prompt.sala,
        tenant_id=org_id,
        modelo_version=version.strip(),
        modelo_solicitado=modelo,
        prompt_id=prompt.id,
        prompt_version=prompt.version,
        corpus_sha256=corpus_sha256,
    )


async def registrar_traza(session, traza: Traza, entidad: str, entidad_id: str) -> None:
    """Escribe la traza en la sesión del llamador, en la misma transacción que el resultado: no hace commit.

    La sesión ya debe traer el contexto RLS del tenant; la política rechaza cualquier otro `tenant_id`.
    """
    from sqlalchemy import text

    await session.execute(
        text(
            "INSERT INTO trazas_ia (id, tenant_id, sala, entidad, entidad_id, modelo_version, modelo_solicitado, "
            "prompt_id, prompt_version, corpus_sha256) "
            "VALUES (:id, :tenant_id, :sala, :entidad, :entidad_id, :modelo_version, :modelo_solicitado, "
            ":prompt_id, :prompt_version, :corpus_sha256)"
        ),
        {
            "id": traza.id, "tenant_id": traza.tenant_id, "sala": traza.sala, "entidad": entidad,
            "entidad_id": entidad_id, "modelo_version": traza.modelo_version,
            "modelo_solicitado": traza.modelo_solicitado, "prompt_id": traza.prompt_id,
            "prompt_version": traza.prompt_version, "corpus_sha256": traza.corpus_sha256,
        },
    )
