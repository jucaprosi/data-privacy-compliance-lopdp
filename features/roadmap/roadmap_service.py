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

# === RM-20 ===
from features.roadmap.services.informe_estado_engine import generar_informe_estado as generar_informe_pdf
__all__.extend(["generar_informe_pdf"])
# === fin RM-20 ===

# === RM-19 ===
from features.roadmap.ai.roadmap_prompts import build_roadmap_prompt
from features.roadmap.services.contexto_generacion import (
    SinDiagnosticoError,
    armar_contexto_generacion,
)

__all__.extend([
    "SinDiagnosticoError",
    "armar_contexto_generacion",
    "build_roadmap_prompt",
])
# === fin RM-19 ===
# === RM-21 ===
# ¤hallazgos: compuerta única del plan de acción (INV_LOPDP_SINGLE_ACTION_PLAN). Las salas productoras
# registran hallazgos aquí; solo esta sala los convierte en tareas.
from features.roadmap.domain.hallazgo import (
    PATRON_CONTROL,
    ConvertirHallazgosEntrada,
    EstadoHallazgo,
    Hallazgo,
    OrigenHallazgo,
    ResultadoConversion,
    ResultadoRegistro,
    SeveridadHallazgo,
    origen_ref_diagnostico,
    validar_hallazgo,
)
from features.roadmap.services.hallazgo_engine import (
    crear_tareas_desde_hallazgos,
    listar_hallazgos,
    registrar_desde_diagnostico,
    registrar_hallazgo,
)

__all__.extend([
    "PATRON_CONTROL",
    "origen_ref_diagnostico",
    "validar_hallazgo",
    "ConvertirHallazgosEntrada",
    "EstadoHallazgo",
    "Hallazgo",
    "OrigenHallazgo",
    "ResultadoConversion",
    "ResultadoRegistro",
    "SeveridadHallazgo",
    "crear_tareas_desde_hallazgos",
    "listar_hallazgos",
    "registrar_desde_diagnostico",
    "registrar_hallazgo",
])
# === fin RM-21 ===

# === CAPA-02 ===
from features.roadmap.domain.hallazgo import ORIGEN_REF_MAX, TITULO_MAX  # noqa: E402
from features.roadmap.services.hallazgo_cierre_engine import cerrar_hallazgo  # noqa: E402

__all__.extend(["ORIGEN_REF_MAX", "TITULO_MAX", "cerrar_hallazgo"])
# === fin CAPA-02 ===

# === RM-23 ===
from features.roadmap.services.recordatorios_engine import (  # noqa: E402
    Aviso,
    Responsable,
    ResultadoRecordatorios,
    ejecutar_recordatorios,
    hoy_guayaquil,
    tipo_recordatorio,
)

__all__.extend(
    ["Aviso", "Responsable", "ResultadoRecordatorios", "ejecutar_recordatorios", "hoy_guayaquil", "tipo_recordatorio"]
)
# === fin RM-23 ===
