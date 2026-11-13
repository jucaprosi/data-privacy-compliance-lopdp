"""Compuerta pública de la sala ADPA: AI Copilot."""
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app_core.app_service import TareaMitigacionORM
from features.ai_copilot.domain.models import AnalisisDiagnosticoRequest, PlanMitigacionResponse
from features.ai_copilot.services.inference_engine import generar_plan_mitigacion
from features.ai_copilot.domain.assistant_models import ConsultaAsistente, RespuestaAsistente
from features.ai_copilot.services.implementation_assistant import responder_implementacion, sanitizar_consulta
from features.ai_copilot.services.assistant_provider import estado_proveedor_asistente

# === IA-05 ===
from app_core.errors import CodigoErrorNegocio, ErrorNegocio
from app_core.pasillo import inferencia as pasillo_inferencia
INFERENCIA_NO_DISPONIBLE = CodigoErrorNegocio(
    "COPILOTO_INFERENCIA_NO_DISPONIBLE", 503,
    "La inferencia con IA no está disponible en este momento. Contacte a la persona administradora de la plataforma.",
)


async def ejecutar_diagnostico_y_crear_tareas(
    request: AnalisisDiagnosticoRequest, 
    tenant_id: str, 
    db: AsyncSession
) -> PlanMitigacionResponse:
    """Invoca la IA y guarda las tareas sugeridas en la base de datos."""
    
    # 1. Inferencia
    no_disponible, _ = pasillo_inferencia.errores()
    try:
        plan = await generar_plan_mitigacion(request, tenant_id)
    except no_disponible as exc:
        raise ErrorNegocio(INFERENCIA_NO_DISPONIBLE) from exc
    
    # 2. Persistencia (Seguimiento)
    for tarea in plan.tareas_propuestas:
        nueva_tarea = TareaMitigacionORM(
            tenant_id=tenant_id,
            id_diagnostico=request.id_diagnostico,
            descripcion=tarea.descripcion,
            impacto_riesgo=tarea.impacto_riesgo,
            estado="PENDIENTE"
        )
        db.add(nueva_tarea)
        
    await db.commit()
    return plan
# === fin IA-05 ===

async def listar_tareas_mitigacion(tenant_id: str, db: AsyncSession) -> List[dict]:
    """Lista las tareas pendientes para el tenant (Tracking)."""
    result = await db.execute(select(TareaMitigacionORM).where(TareaMitigacionORM.tenant_id == tenant_id))
    tareas = result.scalars().all()
    
    return [
        {
            "id": t.id,
            "id_diagnostico": t.id_diagnostico,
            "descripcion": t.descripcion,
            "impacto_riesgo": t.impacto_riesgo,
            "estado": t.estado,
            "created_at": t.created_at.isoformat()
        }
        for t in tareas
    ]
