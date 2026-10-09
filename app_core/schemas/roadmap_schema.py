"""Contrato tipado y validación anti-alucinación para hojas de ruta."""
from datetime import date, datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

VALID_CONTROLS = {f"P{i}" for i in range(1, 74)}
VALID_DIMENSIONS = {f"D{i:02d}" for i in range(1, 11)}


class RoadmapStatus(str, Enum):
    draft = "draft"
    generated = "generated"
    active = "active"
    completed = "completed"


class TaskPriority(str, Enum):
    critica = "critica"
    alta = "alta"
    media = "media"


class TaskStatus(str, Enum):
    pendiente = "pendiente"
    en_progreso = "en_progreso"
    completada = "completada"
    bloqueada = "bloqueada"


class Role(str, Enum):
    responsable_area = "responsable_area"
    encargado = "encargado"
    dpo = "dpo"
    implementador = "implementador"
    admin_organizacion = "admin_organizacion"


class EvidenceValidation(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class PlanningVariables(BaseModel):
    plazo_meses: int = Field(ge=3, le=12)
    presupuesto: float = Field(ge=0)
    moneda: str = Field(min_length=3, max_length=3)
    equipo: List[str] = Field(min_length=1)
    dpo: str
    sistemas_proveedores: str = ""
    contratos_relevantes: str = ""
    prioridades_negocio: List[str] = Field(default_factory=list)
    evidencia_por_control: Dict[str, bool] = Field(default_factory=dict)
    restricciones_locales: str = ""
    idioma: str = Field(default="ES", pattern="^(ES|EN)$")

    @field_validator("evidencia_por_control")
    @classmethod
    def controls_are_real(cls, value):
        invalid = set(value) - VALID_CONTROLS
        if invalid:
            raise ValueError(f"Controles inválidos: {sorted(invalid)}")
        return value


class TaskEvidence(BaseModel):
    id: str
    task_id: str
    tenant_id: str
    r2_key: str
    mime_type: Optional[str] = None
    file_size: Optional[int] = None
    file_hash: Optional[str] = None
    uploaded_by: Optional[str] = None
    uploaded_at: Optional[datetime] = None
    validation_status: EvidenceValidation = EvidenceValidation.pending
    validated_by: Optional[str] = None
    validated_at: Optional[datetime] = None
    notes: Optional[str] = None


class TaskEvidenceUploadRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=500)
    mime_type: str = Field(min_length=1, max_length=100)
    file_size: int = Field(gt=0)


class TaskEvidenceValidationRequest(BaseModel):
    validation_status: EvidenceValidation
    notes: str = ""


class RoadmapTask(BaseModel):
    id: UUID | str
    control_ref: str
    dimension: str
    titulo: str
    descripcion: str
    responsable: str
    prioridad: TaskPriority
    esfuerzo_estimado_horas: int = Field(ge=1)
    dependencias: List[UUID | str] = Field(default_factory=list)
    entregable: str = Field(min_length=1)
    evidencia_requerida: List[str] = Field(min_length=1)
    kpi: str = Field(min_length=1)
    fecha_inicio: date
    fecha_fin: date
    area_id: Optional[str] = None
    evidence: List[TaskEvidence] = Field(default_factory=list)

    @field_validator("control_ref")
    @classmethod
    def valid_control(cls, value):
        if value not in VALID_CONTROLS:
            raise ValueError("control_ref no pertenece al catálogo P1-P73")
        return value

    @field_validator("dimension")
    @classmethod
    def valid_dimension(cls, value):
        if value not in VALID_DIMENSIONS:
            raise ValueError("dimension no pertenece a D01-D10")
        return value

    @model_validator(mode="after")
    def valid_dates(self):
        if self.fecha_fin < self.fecha_inicio:
            raise ValueError("fecha_fin anterior a fecha_inicio")
        return self


class RoadmapWave(BaseModel):
    id: str
    nombre: str
    plazo: str
    objetivo: str
    tareas: List[RoadmapTask]


class GlobalKpis(BaseModel):
    criticos_totales: int = Field(ge=0)
    altos_totales: int = Field(ge=0)
    score_objetivo: float = Field(ge=0, le=100)
    evidencia_verificada_objetivo: float = Field(ge=0, le=100)


class RoadmapDocument(BaseModel):
    roadmap_id: UUID | str
    tenant_id: str
    resumen_ejecutivo: str
    olas: List[RoadmapWave] = Field(min_length=1)
    kpis_globales: GlobalKpis


class GenerateRoadmapRequest(BaseModel):
    tenant_id: str
    user_id: str
    variables: PlanningVariables
    assessment: dict = Field(default_factory=dict)


class TaskStatusUpdate(BaseModel):
    status: TaskStatus
