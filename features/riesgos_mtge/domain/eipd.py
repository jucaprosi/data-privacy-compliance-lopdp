# ¤riesgos-eipd ¤mtge-granescala
# ¤¤backend-developer
"""MTGE-03: modelos de la EIPD guiada de ocho pasos.

Los catálogos de fases y amenazas viven en código hasta REG-01. Son ESTIMADO: no salen de una fuente
oficial registrada en governance/apoyo/CITAS_LEGALES_VERIFICADAS.md y no citan artículos.
"""
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

PASOS_TOTALES = 8
PASO_DECISION = 7
TEXTO_MAX = 4000


class NivelRiesgo(str, Enum):
    bajo = "bajo"
    medio = "medio"
    alto = "alto"


class Decision(str, Enum):
    aceptar = "aceptar"
    medidas = "medidas"
    consulta_previa = "consulta_previa"


# ESTIMADO (sin fuente verificada): fases del ciclo de vida del dato.
FASES_CICLO_VIDA: dict[str, str] = {
    "recogida": "Recogida",
    "almacenamiento": "Almacenamiento",
    "uso": "Uso y tratamiento",
    "comunicacion": "Comunicación a terceros",
    "conservacion": "Conservación",
    "supresion": "Supresión",
}

# ESTIMADO (sin fuente verificada): amenazas frecuentes por fase.
AMENAZAS: dict[str, str] = {
    "acceso_no_autorizado": "Acceso no autorizado",
    "perdida_datos": "Pérdida o destrucción de datos",
    "alteracion": "Alteración no autorizada",
    "finalidad_distinta": "Uso para una finalidad distinta",
    "exceso_datos": "Recogida de más datos de los necesarios",
    "transferencia_sin_garantia": "Comunicación sin garantías adecuadas",
    "conservacion_excesiva": "Conservación más allá del plazo",
    "reidentificacion": "Reidentificación de titulares",
}


class _Cuerpo(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CrearEipd(_Cuerpo):
    tratamiento_id: str = Field(min_length=1, max_length=120)


class Paso1(_Cuerpo):
    obligatoria: bool


class Paso2(_Cuerpo):
    consulta_titulares: str = Field(min_length=1, max_length=TEXTO_MAX)


class Paso3(_Cuerpo):
    fases: list[str] = Field(min_length=1)
    amenazas: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def _catalogo(self):
        if set(self.fases) - set(FASES_CICLO_VIDA) or set(self.amenazas) - set(AMENAZAS):
            raise ValueError("Fase o amenaza fuera del catálogo")
        return self


class Paso4(_Cuerpo):
    necesidad: str = Field(min_length=1, max_length=TEXTO_MAX)


class Paso5(_Cuerpo):
    puntos: list[str] = Field(default_factory=list, max_length=50)

    @model_validator(mode="after")
    def _limpios(self):
        self.puntos = [p.strip()[:TEXTO_MAX] for p in self.puntos if p.strip()]
        return self


class Paso6(_Cuerpo):
    riesgo_inherente: NivelRiesgo
    riesgo_residual: NivelRiesgo


class Paso7(_Cuerpo):
    decision: Optional[Decision] = None
    decision_texto: Optional[str] = Field(default=None, max_length=TEXTO_MAX)

    @model_validator(mode="after")
    def _justificada(self):
        if self.decision is not None and not (self.decision_texto or "").strip():
            raise ValueError("La decisión exige justificación")
        return self


MODELOS_PASO: dict[int, type[_Cuerpo]] = {1: Paso1, 2: Paso2, 3: Paso3, 4: Paso4, 5: Paso5, 6: Paso6, 7: Paso7}


class PuntoCorregir(BaseModel):
    id: str
    texto: str
    hallazgo_id: Optional[str]


class Eipd(BaseModel):
    id: str
    tratamiento_id: str
    obligatoria: bool
    obligatoria_por_ley: bool
    motivo_obligatoriedad: str
    paso_actual: int
    consulta_titulares: Optional[str]
    ciclo_vida: Optional[dict]
    necesidad: Optional[str]
    riesgo_inherente: Optional[NivelRiesgo]
    riesgo_residual: Optional[NivelRiesgo]
    decision: Optional[Decision]
    decision_texto: Optional[str]
    informe_sha256: Optional[str]
    cerrada_en: Optional[datetime]
    creado_en: datetime
    puntos: list[PuntoCorregir] = Field(default_factory=list)


class CierreEipd(BaseModel):
    informe_sha256: str


class InformeEipd(BaseModel):
    informe: dict
    informe_sha256: str
    integro: bool
