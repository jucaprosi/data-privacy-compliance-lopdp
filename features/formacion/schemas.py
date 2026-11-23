# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤schemas ¤evidencias ¤rbac-tenant
"""Esquemas Pydantic para la sala Formación (FOR-01)."""
from datetime import date, datetime
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class ContenidoCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    titulo: str = Field(..., min_length=1, max_length=120)
    tipo: Literal["pdf", "video"]
    referencia: str = Field(..., min_length=1)


class ContenidoOut(BaseModel):
    id: str
    tenant_id: str
    titulo: str
    tipo: str
    referencia: str
    creado_por: str
    creado_en: str


class PreguntaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enunciado: str = Field(..., min_length=1)
    opciones: list[str] = Field(..., min_length=2, max_length=6)
    correcta: int = Field(..., ge=0)


class PreguntaOut(BaseModel):
    id: str
    orden: int
    enunciado: str
    opciones: list[str]
    correcta: int


class PreguntaExamenOut(BaseModel):
    """R5: Modelo estricto para la persona que rinde el examen; prohibido exponer 'correcta'."""
    model_config = ConfigDict(extra="forbid")
    id: str
    orden: int
    enunciado: str
    opciones: list[str]


class AccionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    contenido_id: str = Field(..., min_length=1)
    nombre: str = Field(..., min_length=1, max_length=120)
    inicio: date
    fin: date
    nota_minima: float = Field(default=70.0, ge=0.0, le=100.0)


class AccionOut(BaseModel):
    id: str
    tenant_id: str
    contenido_id: str
    nombre: str
    inicio: str
    fin: str
    nota_minima: float
    creado_por: str
    total_participantes: int = 0
    terminados: int = 0


class ParticipantesAddRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    persona_ids: list[str] = Field(..., min_length=1)


class IniciarExamenResponse(BaseModel):
    iniciado_en: str


class ExamenOut(BaseModel):
    """R5: Vista del examen para la persona participante."""
    model_config = ConfigDict(extra="forbid")
    accion: str
    nota_minima: float
    inicio: str
    fin: str
    iniciado_en: Optional[str] = None
    terminado_en: Optional[str] = None
    preguntas: list[PreguntaExamenOut]


class ExamenSubmitRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    respuestas: list[int] = Field(...)


class ExamenSubmitResponse(BaseModel):
    nota: float
    aprobado: bool
    diploma_sha256: Optional[str] = None


class CoberturaOut(BaseModel):
    formadas: int
    obligadas: int
    cobertura: float
