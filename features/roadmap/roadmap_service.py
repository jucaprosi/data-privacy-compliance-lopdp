"""Compuerta pública de la sala ADPA: Hoja de Ruta (generación, olas y tareas, evidencia, KPIs, auditoría).

Todas las operaciones reciben tenant_id y user_id explícitos; cada consulta fija
set_config('app.current_tenant_id', ...) para RLS.
Cada tarea posterior edita solo su sección reservada (# === <ID> === … # === fin <ID> ===).
"""
from __future__ import annotations

from features.roadmap.domain.models import (
    EvidenceValidation,
    GenerateRoadmapRequest,
    GlobalKpis,
    PlanningVariables,
    RoadmapDocument,
    RoadmapStatus,
    RoadmapTask,
    RoadmapWave,
    TaskEvidence,
    TaskEvidenceUploadRequest,
    TaskEvidenceValidationRequest,
    TaskPriority,
    TaskStatus,
    TaskStatusUpdate,
    VALID_CONTROLS,
    VALID_DIMENSIONS,
)
from features.roadmap.services.alcance_area_engine import ensure_task_in_area_scope
from features.roadmap.services.auditoria_engine import registrar_auditoria
from features.roadmap.services.consulta_engine import get_kpis, get_roadmap
from features.roadmap.services.evidencia_engine import (
    list_evidence,
    register_evidence_upload,
    validate_evidence,
)
from features.roadmap.services.generacion_engine import enqueue_generation, get_job
from features.roadmap.services.tarea_estado_engine import update_task_status

__all__ = [
    "VALID_CONTROLS",
    "VALID_DIMENSIONS",
    "EvidenceValidation",
    "GenerateRoadmapRequest",
    "GlobalKpis",
    "PlanningVariables",
    "RoadmapDocument",
    "RoadmapStatus",
    "RoadmapTask",
    "RoadmapWave",
    "TaskEvidence",
    "TaskEvidenceUploadRequest",
    "TaskEvidenceValidationRequest",
    "TaskPriority",
    "TaskStatus",
    "TaskStatusUpdate",
    "enqueue_generation",
    "ensure_task_in_area_scope",
    "get_job",
    "get_kpis",
    "get_roadmap",
    "list_evidence",
    "register_evidence_upload",
    "registrar_auditoria",
    "update_task_status",
    "validate_evidence",
]

# === RM-07 ===
from features.roadmap.services.tarea_edicion_engine import (
    TaskDetailsUpdate,
    edit_task_details,
)

__all__.extend([
    "TaskDetailsUpdate",
    "edit_task_details",
])
# === fin RM-07 ===

# === RM-08 ===
from features.roadmap.services.tarea_asignacion_engine import (
    assign_task_to_responsable,
)

__all__.extend([
    "assign_task_to_responsable",
])
# === fin RM-08 ===

# === RM-09 ===
from features.roadmap.services.auditoria_consulta_engine import (
    get_roadmap_audit_log,
)

__all__.extend([
    "get_roadmap_audit_log",
])
# === fin RM-09 ===

# === RM-12 ===
from features.roadmap.services.generacion_engine import (
    generate_roadmap_document,
    GeneracionRoadmapError,
)
from features.roadmap.ai.client import (
    call_roadmap_llm,
    TruncatedOutputError,
    LLMTimeoutError,
)
from features.roadmap.ai.roadmap_prompts import (
    SYSTEM_PROMPT,
    build_roadmap_prompt,
    get_roadmap_schema_str,
)

__all__.extend([
    "generate_roadmap_document",
    "GeneracionRoadmapError",
    "call_roadmap_llm",
    "TruncatedOutputError",
    "LLMTimeoutError",
    "SYSTEM_PROMPT",
    "build_roadmap_prompt",
    "get_roadmap_schema_str",
])
# === fin RM-12 ===

# === RM-13 ===
from features.roadmap.services.generacion_en_linea import (
    generate_roadmap_inline,
)

__all__.extend([
    "generate_roadmap_inline",
])
# === fin RM-13 ===

# === RM-17 ===
from features.roadmap.ai.roadmap_prompts import SYSTEM_PROMPT

__all__.extend(["SYSTEM_PROMPT"])
# === fin RM-17 ===

# === RM-18 ===
from features.roadmap.ai.client import DEFAULT_TIMEOUT_SECONDS

__all__.extend(["DEFAULT_TIMEOUT_SECONDS"])
# === fin RM-18 ===
