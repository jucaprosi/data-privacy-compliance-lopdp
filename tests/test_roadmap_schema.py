"""Tests unitarios del schema de roadmap. Sin base de datos."""
from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from app_core.schemas.roadmap_schema import (
    EvidenceValidation,
    GenerateRoadmapRequest,
    GlobalKpis,
    PlanningVariables,
    RoadmapDocument,
    RoadmapTask,
    RoadmapWave,
    Role,
    TaskEvidence,
    TaskEvidenceUploadRequest,
    TaskEvidenceValidationRequest,
    TaskPriority,
    TaskStatus,
    TaskStatusUpdate,
)


def _valid_vars() -> dict:
    return {
        "plazo_meses": 6,
        "presupuesto": 1000.0,
        "moneda": "USD",
        "equipo": ["DPO", "Legal"],
        "dpo": "Maria",
        "idioma": "ES",
    }


def _valid_task(**overrides) -> dict:
    today = date.today()
    base = {
        "id": "task-1",
        "control_ref": "P10",
        "dimension": "D02",
        "titulo": "Cerrar brecha P10",
        "descripcion": "Implementar medida.",
        "responsable": "Maria",
        "prioridad": TaskPriority.critica,
        "esfuerzo_estimado_horas": 8,
        "entregable": "Evidencia",
        "evidencia_requerida": ["doc"],
        "kpi": "Verificado",
        "fecha_inicio": today,
        "fecha_fin": today + timedelta(days=14),
    }
    base.update(overrides)
    return base


# ==================== PlanningVariables ====================

def test_planning_vars_valid():
    v = PlanningVariables(**_valid_vars())
    assert v.idioma == "ES"
    assert v.plazo_meses == 6


def test_planning_vars_rechaza_control_invalido():
    data = _valid_vars()
    data["evidencia_por_control"] = {"P999": True}
    with pytest.raises(ValidationError):
        PlanningVariables(**data)


def test_planning_vars_rechaza_plazo_fuera_de_rango():
    data = _valid_vars()
    data["plazo_meses"] = 2
    with pytest.raises(ValidationError):
        PlanningVariables(**data)
    data["plazo_meses"] = 13
    with pytest.raises(ValidationError):
        PlanningVariables(**data)


def test_planning_vars_rechaza_idioma_invalido():
    data = _valid_vars()
    data["idioma"] = "FR"
    with pytest.raises(ValidationError):
        PlanningVariables(**data)


# ==================== RoadmapTask ====================

def test_task_valid():
    t = RoadmapTask(**_valid_task())
    assert t.control_ref == "P10"
    assert t.prioridad == TaskPriority.critica


def test_task_rechaza_control_invalido():
    with pytest.raises(ValidationError):
        RoadmapTask(**_valid_task(control_ref="P999"))


def test_task_rechaza_control_no_numerico():
    with pytest.raises(ValidationError):
        RoadmapTask(**_valid_task(control_ref="PXX"))


def test_task_rechaza_dimension_invalida():
    with pytest.raises(ValidationError):
        RoadmapTask(**_valid_task(dimension="D11"))


def test_task_rechaza_fechas_invertidas():
    today = date.today()
    with pytest.raises(ValidationError):
        RoadmapTask(
            **_valid_task(
                fecha_inicio=today + timedelta(days=10),
                fecha_fin=today,
            )
        )


def test_task_acepta_limites_p1_p73_d01_d10():
    RoadmapTask(**_valid_task(control_ref="P1", dimension="D01"))
    RoadmapTask(**_valid_task(control_ref="P73", dimension="D10"))


# ==================== RoadmapDocument ====================

def test_document_valid():
    doc = RoadmapDocument(
        roadmap_id="rm-1",
        tenant_id="org-1",
        resumen_ejecutivo="Resumen",
        olas=[
            RoadmapWave(
                id="ola-1",
                nombre="Fundamentos",
                plazo="semanas 1-2",
                objetivo="Cerrar criticas",
                tareas=[RoadmapTask(**_valid_task())],
            )
        ],
        kpis_globales=GlobalKpis(
            criticos_totales=1,
            altos_totales=0,
            score_objetivo=80.0,
            evidencia_verificada_objetivo=80.0,
        ),
    )
    assert doc.tenant_id == "org-1"
    assert len(doc.olas) == 1


def test_document_rechaza_olas_vacias():
    with pytest.raises(ValidationError):
        RoadmapDocument(
            roadmap_id="rm-1",
            tenant_id="org-1",
            resumen_ejecutivo="x",
            olas=[],
            kpis_globales=GlobalKpis(
                criticos_totales=0,
                altos_totales=0,
                score_objetivo=50.0,
                evidencia_verificada_objetivo=50.0,
            ),
        )


# ==================== Enums ====================

def test_role_enums():
    assert Role.responsable_area.value == "responsable_area"
    assert Role.encargado.value == "encargado"
    assert Role.dpo.value == "dpo"
    assert Role.implementador.value == "implementador"
    assert Role.admin_organizacion.value == "admin_organizacion"


def test_task_status_enums():
    assert TaskStatus.pendiente.value == "pendiente"
    assert TaskStatus.en_progreso.value == "en_progreso"
    assert TaskStatus.completada.value == "completada"
    assert TaskStatus.bloqueada.value == "bloqueada"


def test_evidence_validation_enums():
    assert EvidenceValidation.pending.value == "pending"
    assert EvidenceValidation.approved.value == "approved"
    assert EvidenceValidation.rejected.value == "rejected"


# ==================== Evidencia ====================

def test_evidence_upload_request_valid():
    r = TaskEvidenceUploadRequest(
        filename="evidencia.pdf",
        mime_type="application/pdf",
        file_size=1024,
    )
    assert r.file_size == 1024


def test_evidence_upload_request_rechaza_size_cero():
    with pytest.raises(ValidationError):
        TaskEvidenceUploadRequest(
            filename="x.pdf",
            mime_type="application/pdf",
            file_size=0,
        )


def test_evidence_validation_request_valid():
    r = TaskEvidenceValidationRequest(
        validation_status=EvidenceValidation.approved,
        notes="Aprobada",
    )
    assert r.validation_status == EvidenceValidation.approved


# ==================== GenerateRoadmapRequest ====================

def test_generate_request_valid():
    r = GenerateRoadmapRequest(
        tenant_id="org-1",
        user_id="user-1",
        variables=PlanningVariables(**_valid_vars()),
    )
    assert r.tenant_id == "org-1"


def test_task_status_update_valid():
    u = TaskStatusUpdate(status=TaskStatus.completada)
    assert u.status == TaskStatus.completada
