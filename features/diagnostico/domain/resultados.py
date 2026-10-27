# ¤diagnostico ¤dpo-independencia
"""Resultado sellado del diagnóstico (DIAG-03): lo responde y lo sella el DPO.

Un resultado sellado es una fotografía que no se edita ni se borra: quién selló y cuándo, la
normativa, el alcance (tamaño de la organización y perfil de operación), las respuestas usadas
con el nivel de evidencia declarado y el sellado, y los cuatro indicadores calculados por el
servidor. La huella SHA-256 se encadena por organización, como la bitácora del DPO (DPO-01).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Optional

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


@dataclass(frozen=True)
class IndicadoresSellados:
    """Los cuatro indicadores: cumplimiento, madurez, respaldo con documentos y riesgo que queda."""

    cumplimiento: bool
    brechas_criticas: int
    madurez: float
    nivel_madurez: int
    respaldo_documental: float
    riesgo_residual: float
    preguntas_evaluadas: int
    preguntas_aplicables: int
    cobertura: float


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
    indicadores: IndicadoresSellados
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
            "respuestas": [asdict(r) for r in self.respuestas],
            "indicadores": asdict(self.indicadores),
            "huella_anterior": self.huella_anterior,
        }
