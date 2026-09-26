from fastapi import APIRouter, Depends
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app_core.security import get_current_tenant
from app_core.database import get_db_session
from features.ai_copilot.domain.models import AnalisisDiagnosticoRequest, PlanMitigacionResponse
from features.ai_copilot.ai_copilot_service import ejecutar_diagnostico_y_crear_tareas, listar_tareas_mitigacion

router = APIRouter(prefix="/ai", tags=["AI Copilot"])

@router.post("/diagnosticar", response_model=PlanMitigacionResponse)
async def diagnosticar_y_planificar(
    request: AnalisisDiagnosticoRequest,
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db_session)
):
    """Genera un análisis experto con IA y guarda las tareas de mitigación correspondientes."""
    return await ejecutar_diagnostico_y_crear_tareas(request, tenant_id, db)

@router.get("/mitigaciones", response_model=List[dict])
async def obtener_tareas_mitigacion(
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db_session)
):
    """Recupera la lista de tareas pendientes propuestas por la IA."""
    return await listar_tareas_mitigacion(tenant_id, db)
