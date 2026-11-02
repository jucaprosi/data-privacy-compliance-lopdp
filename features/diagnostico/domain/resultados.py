# ¤diagnostico ¤dpo-independencia
"""Resultado sellado del diagnóstico (DIAG-03): lo responde y lo sella el DPO.

Un resultado sellado es una fotografía que no se edita ni se borra: quién selló y cuándo, la
normativa, el alcance (tamaño de la organización y perfil de operación), las respuestas usadas
con el nivel de evidencia declarado y el sellado, y los indicadores calculados por el
servidor: nivel por dimensión, sin cifra global de la organización (DIAG-08). La huella SHA-256 se encadena por organización, como la bitácora del DPO (DPO-01).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Optional, Union

from features.diagnostico.domain.models import ESCALA_ANTERIOR, ESCALA_SELLADA

NORMATIVA_SELLADA = "LOPDP"
VERSION_NORMATIVA = "LOPDP-EC-2026.v1"
HUELLA_GENESIS = "0" * 64

# Selectores del perfil de operación de la ficha (frontend/src/lib/bancoPreguntas/perfil.ts).
CLAVES_PERFIL: tuple[str, ...] = (
    "internet",
    "publicidad",
    "camaras",
    "terceros",
    "nube",
    "exterior",
    "sistemas",
    "decisionesAutomaticas",
    "datosDelicados",
    "granCantidad",
    "obligadaDpd",
)
RESPUESTAS_PERFIL: frozenset[Optional[str]] = frozenset({"si", "no", None})


class SelladoNoPermitido(ValueError):
    """El diagnóstico no se puede sellar con lo que hay en el servidor."""


@dataclass(frozen=True)
class RespuestaSellada:
    pregunta_id: int
    control: str
    dimension: str
    estado: str
    criticidad: int
    nivel_declarado: int
    nivel_sellado: int
    con_documento: bool
    # Escala SMARTCIDI (DIAG-08); los sellados anteriores no lo traen y no se les añade.
    nivel_asignado: Optional[int] = None


@dataclass(frozen=True)
class DimensionSellada:
    dimension: str
    nombre: str
    nivel: int  # 0 (sin evaluación suficiente) o 1 a 5
    etiqueta: str
    score: float
    cobertura: float
    brechas_criticas: int
    brechas_altas: int


@dataclass(frozen=True)
class IndicadoresSellados:
    """Indicadores sellados: nivel por dimensión; ninguno combina dimensiones (R5)."""

    cumplimiento: bool
    brechas_criticas: int
    brechas_altas: int
    por_dimension: list[DimensionSellada]
    respaldo_documental: float
    preguntas_evaluadas: int
    preguntas_aplicables: int
    cobertura: float
    escala: str = ESCALA_SELLADA


def indicadores_desde_json(crudo: dict[str, Any]) -> Union[IndicadoresSellados, dict[str, Any]]:
    """Forma nueva como objeto; un sellado anterior se conserva tal cual para no alterar su huella."""
    if crudo.get("escala") != ESCALA_SELLADA:
        return dict(crudo)
    datos = dict(crudo)
    datos["por_dimension"] = [DimensionSellada(**d) for d in datos["por_dimension"]]
    return IndicadoresSellados(**datos)


def indicadores_a_salida(indicadores: Union[IndicadoresSellados, dict[str, Any]]) -> dict[str, Any]:
    """Indicadores para la API: un sellado sin escala se marca «anterior» al leer, sin escribir."""
    if isinstance(indicadores, dict):
        return {**indicadores, "escala": indicadores.get("escala", ESCALA_ANTERIOR)}
    return asdict(indicadores)


def es_resultado_anterior(indicadores: Union[IndicadoresSellados, dict[str, Any]]) -> bool:
    """True si el sellado es anterior a la escala SMARTCIDI (sus respuestas no traen nivel asignado)."""
    return isinstance(indicadores, dict) and indicadores.get("escala") != ESCALA_SELLADA


@dataclass
class ResultadoSellado:
    id: str
    tenant_id: str
    secuencia: int
    sellado_por: str
    sellado_en: datetime
    normativa: str
    version_normativa: str
    tamano: str
    perfil: dict[str, Optional[str]]
    respuestas: list[RespuestaSellada]
    indicadores: Union[IndicadoresSellados, dict[str, Any]]
    huella_anterior: str = HUELLA_GENESIS
    huella: str = ""

    def contenido(self) -> dict[str, Any]:
        """Lo que se sella: todo salvo la huella propia."""
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "secuencia": self.secuencia,
            "sellado_por": self.sellado_por,
            "sellado_en": self.sellado_en.isoformat(),
            "normativa": self.normativa,
            "version_normativa": self.version_normativa,
            "tamano": self.tamano,
            "perfil": dict(self.perfil),
            "respuestas": [respuesta_a_json(r) for r in self.respuestas],
            "indicadores": self.indicadores if isinstance(self.indicadores, dict) else asdict(self.indicadores),
            "huella_anterior": self.huella_anterior,
        }


def respuesta_a_json(respuesta: RespuestaSellada) -> dict[str, Any]:
    """Sin `nivel_asignado` nulo: un sellado de antes de DIAG-08 sigue verificando su huella."""
    crudo = asdict(respuesta)
    if crudo["nivel_asignado"] is None:
        del crudo["nivel_asignado"]
    return crudo
