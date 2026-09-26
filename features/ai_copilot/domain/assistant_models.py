# ¤¤frontend-architect
"""Contratos acotados del asistente de implementación LOPDP."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ¤contrato
class Contrato(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ¤brechacontexto
class BrechaContexto(Contrato):
    pregunta_id: int = Field(ge=1, le=80)
    control: str = Field(min_length=1, max_length=500)
    dimension_id: str = Field(default="", max_length=20)
    severidad: Literal["Crítico", "Alto", "Medio"] = "Medio"


# ¤mensajecontexto
class MensajeContexto(Contrato):
    rol: Literal["usuario", "asistente"]
    contenido: str = Field(min_length=1, max_length=12000)


# ¤consultaasistente
class ConsultaAsistente(Contrato):
    pregunta: str = Field(min_length=1, max_length=4000)
    brechas: list[BrechaContexto] = Field(default_factory=list, max_length=80)
    historial: list[MensajeContexto] = Field(default_factory=list, max_length=12)
    brecha_id: int | None = Field(default=None, ge=1, le=80)
    estado: Literal["Por iniciar", "Implementación", "Seguimiento"] = "Por iniciar"

    @field_validator("pregunta")
    @classmethod
    def pregunta_no_vacia(cls, valor: str) -> str:
        if not valor.strip():
            raise ValueError("Escribe una consulta.")
        return valor.strip()

    @model_validator(mode="after")
    def validar_contexto(self):
        ids = [b.pregunta_id for b in self.brechas]
        if len(ids) != len(set(ids)):
            raise ValueError("No se permiten controles duplicados.")
        if self.brecha_id is not None and self.brecha_id not in ids:
            raise ValueError("La brecha seleccionada debe pertenecer al assessment enviado.")
        if sum(len(m.contenido) for m in self.historial) > 32000:
            raise ValueError("El historial excede el límite de contexto.")
        return self


# ¤fundamento
class Fundamento(Contrato):
    articulo: str
    titulo: str
    url: str
    version: str
    resumen: str


# ¤planimplementacion
class PlanImplementacion(Contrato):
    pregunta_id: int
    control: str
    severidad: str
    pasos: list[str]
    responsable_sugerido: str
    evidencias: list[str]
    criterio_cierre: str
    seguimiento: str
    fundamento: list[Fundamento]


# ¤respuestaasistente
class RespuestaAsistente(Contrato):
    pregunta: str
    respuesta: str
    modo: Literal["local", "deepseek", "sin_fuente"]
    fundamentos: list[Fundamento]
    planes: list[PlanImplementacion]
    advertencias: list[str]
    corpus_version: str
    dlp_aplicado: bool = True
