"""Router de la Hoja de Ruta Inteligente con RBAC.

Auth por headers: X-User-ID, X-Tenant-ID, X-Role.
Verifica membresía activa en user_tenant_roles.
"""
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.db.session import get_session
from app_core.schemas.roadmap_schema import (
    EvidenceValidation,
    GenerateRoadmapRequest,
    Role,
    TaskEvidenceUploadRequest,
    TaskEvidenceValidationRequest,
    TaskStatusUpdate,
)
from app_core.services import roadmap_service
from app_core.storage import r2

router = APIRouter(prefix="/roadmaps", tags=["Hoja de Ruta Inteligente"])

# Compatibilidad con rol legacy
ROLE_ALIASES = {"GESTOR_PROCESO": "encargado"}


async def get_context(
    x_user_id: str = Header(..., alias="X-User-ID"),
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    x_role: str = Header(..., alias="X-Role"),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Resuelve el contexto del usuario y verifica membresía activa."""
    role = ROLE_ALIASES.get(x_role, x_role)
    if role not in Role.__members__:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            f"Rol '{x_role}' no autorizado",
        )
    result = await session.execute(
        text(
            "SELECT 1 FROM user_tenant_roles "
            "WHERE user_id=:u AND tenant_id=:t AND role=:r "
            "AND (valid_to IS NULL OR valid_to > now())"
        ),
        {"u": x_user_id, "t": x_tenant_id, "r": role},
    )
    if not result.fetchone():
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Sin membresía activa")
    return {"user_id": x_user_id, "tenant_id": x_tenant_id, "role": role}


def require_role(*roles: str):
    """Dependency que exige que el usuario tenga uno de los roles indicados."""
    async def checker(ctx: dict = Depends(get_context)) -> dict:
        if ctx["role"] not in roles:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                f"Rol {ctx['role']} no autorizado para esta operación",
            )
        return ctx
    return checker


# ============================================================================
# Generación y consulta
# ============================================================================

@router.post("/generate", status_code=status.HTTP_202_ACCEPTED)
async def generate(
    payload: GenerateRoadmapRequest,
    ctx: dict = Depends(require_role("implementador")),
    session: AsyncSession = Depends(get_session),
):
    """Encola generación de roadmap. Solo implementador."""
    payload.tenant_id = ctx["tenant_id"]
    payload.user_id = ctx["user_id"]
    job_id = await roadmap_service.enqueue_generation(
        session, ctx["tenant_id"], ctx["user_id"], payload
    )
    return {"job_id": job_id}


@router.get("/jobs/{job_id}")
async def get_job(
    job_id: str,
    ctx: dict = Depends(get_context),
):
    """Estado del job de generación."""
    value = await roadmap_service.get_job(job_id)
    if not value:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job no encontrado")
    return value


@router.get("/{roadmap_id}")
async def get_roadmap(
    roadmap_id: str,
    ctx: dict = Depends(get_context),
    session: AsyncSession = Depends(get_session),
):
    """Roadmap completo con olas, tareas y evidencias."""
    value = await roadmap_service.get_roadmap(
        session, ctx["tenant_id"], roadmap_id
    )
    if not value:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Roadmap no encontrado")
    return value


@router.get("/{roadmap_id}/kpis")
async def get_kpis(
    roadmap_id: str,
    ctx: dict = Depends(get_context),
    session: AsyncSession = Depends(get_session),
):
    """KPIs agregados del roadmap."""
    return await roadmap_service.get_kpis(
        session, ctx["tenant_id"], roadmap_id
    )


# ============================================================================
# Gestión de tareas
# ============================================================================

@router.patch("/tasks/{task_id}")
async def patch_task(
    task_id: str,
    payload: TaskStatusUpdate,
    ctx: dict = Depends(require_role("implementador")),
    session: AsyncSession = Depends(get_session),
):
    """Cambia estado de una tarea. Solo implementador."""
    value = await roadmap_service.update_task_status(
        session, ctx["tenant_id"], ctx["user_id"], task_id, payload.status
    )
    if not value:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tarea no encontrada")
    return value


# ============================================================================
# Evidencia (R2)
# ============================================================================

@router.post("/tasks/{task_id}/evidence/upload-url")
async def evidence_upload_url(
    task_id: str,
    payload: TaskEvidenceUploadRequest,
    ctx: dict = Depends(require_role("responsable_area", "encargado")),
):
    """Genera URL prefirmada R2 para subir evidencia. Solo responsable/encargado."""
    key = r2.build_key(ctx["tenant_id"], task_id, payload.filename)
    return r2.generate_upload_url(key, payload.mime_type)


@router.post("/tasks/{task_id}/evidence", status_code=status.HTTP_201_CREATED)
async def register_evidence(
    task_id: str,
    r2_key: str,
    mime_type: str,
    file_size: int,
    file_hash: str | None = None,
    ctx: dict = Depends(require_role("responsable_area", "encargado")),
    session: AsyncSession = Depends(get_session),
):
    """Registra evidencia tras subida exitosa a R2."""
    return await roadmap_service.register_evidence_upload(
        session,
        ctx["tenant_id"],
        ctx["user_id"],
        task_id,
        r2_key,
        mime_type,
        file_size,
        file_hash,
    )


@router.get("/tasks/{task_id}/evidence")
async def list_evidence(
    task_id: str,
    ctx: dict = Depends(get_context),
    session: AsyncSession = Depends(get_session),
):
    """Lista evidencias de una tarea."""
    return await roadmap_service.list_evidence(
        session, ctx["tenant_id"], task_id
    )


@router.patch("/tasks/{task_id}/evidence/{evidence_id}")
async def validate_evidence(
    task_id: str,
    evidence_id: str,
    payload: TaskEvidenceValidationRequest,
    ctx: dict = Depends(require_role("encargado", "dpo", "implementador")),
    session: AsyncSession = Depends(get_session),
):
    """Valida o rechaza una evidencia. Solo encargado/dpo/implementador."""
    value = await roadmap_service.validate_evidence(
        session,
        ctx["tenant_id"],
        ctx["user_id"],
        evidence_id,
        payload.validation_status.value,
        payload.notes,
    )
    if not value:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Evidencia no encontrada"
        )
    return value
