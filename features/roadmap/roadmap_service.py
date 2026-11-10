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

# === RAT-05 ===
from features.roadmap.services.hallazgo_cierre_engine import reabrir_hallazgo  # noqa: E402

__all__.append("reabrir_hallazgo")
# === fin RAT-05 ===

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

# === RM-24 ===
from features.roadmap.services.cierre_verificado_engine import (  # noqa: E402
    RM_CIERRE_SIN_EVIDENCIA,
    VerificadorDeCierre,
    registrar_verificador_cierre,
)

__all__.extend(["RM_CIERRE_SIN_EVIDENCIA", "VerificadorDeCierre", "registrar_verificador_cierre"])
# === fin RM-24 ===

# === BIB-302 ===
from sqlalchemy import text as _sql_text  # noqa: E402


async def obtener_accion_para_enlace(session, tenant_id: str, accion_id: str):
    """Compuerta mínima: confirma que la acción canónica pertenece al tenant solicitante."""
    return (await session.execute(
        _sql_text("SELECT id,title,status,control_ref,hallazgo_id FROM roadmap_tasks "
                  "WHERE id=:id AND tenant_id=:t"),
        {"id": accion_id, "t": tenant_id},
    )).mappings().first()


__all__.append("obtener_accion_para_enlace")
# === fin BIB-302 ===

# === BIB-303 ===
from features.roadmap.services.cierre_verificado_engine import (  # noqa: E402
    verificador_cierre_registrado as _verificador_registrado,
)

_actualizar_estado_base = update_task_status


async def update_task_status(session, tenant_id, user_id, task_id, new_status):  # noqa: F811
    """Compuerta del cierre: si el verificador registrado sabe prepararse (consulta asíncrona de
    evidencia), se prepara antes de que el motor le pregunte de forma síncrona."""
    if new_status == TaskStatus.completada:
        preparar = getattr(_verificador_registrado(), "preparar", None)
        if preparar is not None:
            await preparar(session, tenant_id, user_id, task_id)
    return await _actualizar_estado_base(session, tenant_id, user_id, task_id, new_status)


async def reabrir_accion_no_conforme(session, tenant_id: str, user_id: str, accion_id: str) -> None:
    """Una verificación no conforme mantiene abierta la acción: si estaba completada, vuelve a en_progreso."""
    estado = (await session.execute(
        _sql_text("SELECT status FROM roadmap_tasks WHERE id=:id AND tenant_id=:t"),
        {"id": accion_id, "t": tenant_id},
    )).scalar()
    if estado == TaskStatus.completada.value:
        await _actualizar_estado_base(session, tenant_id, user_id, accion_id, TaskStatus.en_progreso)


verificador_cierre_registrado = _verificador_registrado
__all__.extend(["reabrir_accion_no_conforme", "verificador_cierre_registrado"])
# === fin BIB-303 ===

# === BIB-208 ===
async def acciones_para_instantanea(session, tenant_id: str, roadmap_id: str) -> list[dict]:
    """Solo lectura del plan canónico para la instantánea PLA-01 de Biblioteca: acciones del tenant y
    los IDs de su evidencia aprobada. No crea ni modifica acciones."""
    filas = (await session.execute(
        _sql_text("SELECT t.id,t.title,t.status,t.priority,t.end_date,t.owner,t.control_ref,t.hallazgo_id,"
                  "t.deliverable FROM roadmap_tasks t JOIN roadmap_waves w ON t.wave_id=w.id "
                  "JOIN roadmaps r ON w.roadmap_id=r.id "
                  "WHERE r.id=:r AND r.tenant_id=:t AND t.tenant_id=:t ORDER BY w.sort_order,t.start_date,t.id"),
        {"r": roadmap_id, "t": tenant_id},
    )).mappings().all()
    evidencias = (await session.execute(
        _sql_text("SELECT e.task_id,e.id FROM task_evidence e JOIN roadmap_tasks t ON e.task_id=t.id "
                  "JOIN roadmap_waves w ON t.wave_id=w.id "
                  "WHERE w.roadmap_id=:r AND e.tenant_id=:t AND t.tenant_id=:t AND e.validation_status='approved'"),
        {"r": roadmap_id, "t": tenant_id},
    )).all()
    aprobadas: dict[str, list[str]] = {}
    for tarea, evidencia in evidencias:
        aprobadas.setdefault(str(tarea), []).append(str(evidencia))
    return [{**dict(f), "evidencias_aprobadas": aprobadas.get(str(f["id"]), [])} for f in filas]


__all__.append("acciones_para_instantanea")
# === fin BIB-208 ===

# === FE-26 ===
from features.roadmap.domain.errores import RM_EVIDENCIA_NO_DISPONIBLE  # noqa: E402
from features.roadmap.domain.evidencia_fisica import (  # noqa: E402
    EvidenciaFisicaDesconocida,
    evidencia_fisica_activa,
)

__all__.extend(["RM_EVIDENCIA_NO_DISPONIBLE", "EvidenciaFisicaDesconocida", "evidencia_fisica_activa"])
# === fin FE-26 ===

# === DEMO-03c ===
from features.roadmap.services.clon_plantilla_engine import (  # noqa: E402
    clonar_desde_plantilla,
    sembrar_en_plantilla,
)

__all__.extend(["clonar_desde_plantilla", "sembrar_en_plantilla"])
# === fin DEMO-03c ===


# === ADPA-05 ===
# ¤adpa Los códigos de error de esta sala viven en features/roadmap/domain/errores.py y se registran al importarlo.
from features.roadmap.domain import errores as _errores_sala  # noqa: E402,F401
# === fin ADPA-05 ===


# === ORG-15 ===
# Sección reservada para ORG-15 (cartera por pertenencia).
# === fin ORG-15 ===
