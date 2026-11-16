# ¤¤backend-developer
# ¤rbac-tenant ¤auditoria-capa ¤hallazgos
"""Rutas de API para la auditoría con grilla de verificación por dominio y acta por área (CAPA-04)."""
from typing import Any, Literal, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import require_role
from app_core.db.session import get_session
from app_core.errors import ErrorNegocio
from app_core.pasillo import auditoria_capa as pasillo_auditoria

AUTO_REGISTRO = True

router = APIRouter(prefix="/auditoria-capa", tags=["Auditoría y Grilla de Verificación (CAPA-04)"])

# Roles según especificación CAPA-04 §2
_ROLES_CREAR = require_role("implementador", "coordinador")
_ROLES_LISTAR = require_role("implementador", "coordinador", "auditor")
_ROLES_AUDITOR = require_role("auditor")
_ROLES_VER_ACTA = require_role("auditor", "dpo", "admin_organizacion")


class CrearAuditoriaRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nombre: str = Field(..., min_length=1, max_length=120)
    alcance: list[str] = Field(..., min_length=1)
    equipo: list[str] = Field(..., min_length=1)


class ActualizarFilaRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    verificado: int = Field(..., ge=1, le=5)
    riesgo_final: int
    evidencia_sha256: Optional[str] = None


class VerificarCierreRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    resultado: Literal["conforme", "no_conforme"]
    motivo: str = Field(..., min_length=10)


@router.post("/auditorias", status_code=status.HTTP_201_CREATED)
async def crear_auditoria_endpoint(
    payload: CrearAuditoriaRequest,
    ctx: dict = Depends(_ROLES_CREAR),
    session: AsyncSession = Depends(get_session),
):
    """Crea una auditoría precargando filas desde el último resultado sellado (R1)."""
    return await pasillo_auditoria.crear_auditoria(
        session=session,
        tenant_id=ctx["tenant_id"],
        user_id=ctx["user_id"],
        nombre=payload.nombre,
        alcance=payload.alcance,
        equipo=payload.equipo,
    )


@router.get("/auditorias")
async def listar_auditorias_endpoint(
    ctx: dict = Depends(_ROLES_LISTAR),
    session: AsyncSession = Depends(get_session),
):
    """Lista las auditorías de la organización con su avance."""
    return await pasillo_auditoria.listar_auditorias(
        session=session,
        tenant_id=ctx["tenant_id"],
        user_id=ctx["user_id"],
    )


@router.get("/auditorias/{id}")
async def obtener_auditoria_endpoint(
    id: str,
    ctx: dict = Depends(_ROLES_LISTAR),
    session: AsyncSession = Depends(get_session),
):
    """Obtiene los detalles de una auditoría, incluyendo sus filas y actas."""
    auditoria = await pasillo_auditoria.obtener_auditoria(
        session=session,
        tenant_id=ctx["tenant_id"],
        user_id=ctx["user_id"],
        auditoria_id=id,
    )
    if not auditoria:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Auditoría no encontrada")
    return auditoria


@router.put("/auditorias/{id}/filas/{control_ref}")
async def actualizar_fila_endpoint(
    id: str,
    control_ref: str,
    payload: ActualizarFilaRequest,
    ctx: dict = Depends(_ROLES_AUDITOR),
    session: AsyncSession = Depends(get_session),
):
    """Actualiza una fila de verificación. Solo miembros del equipo auditor."""
    auditoria = await pasillo_auditoria.obtener_auditoria(
        session=session,
        tenant_id=ctx["tenant_id"],
        user_id=ctx["user_id"],
        auditoria_id=id,
    )
    if not auditoria:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Auditoría no encontrada")

    if ctx["user_id"] not in auditoria["equipo"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo miembros del equipo auditor pueden actualizar filas de esta auditoría.",
        )

    return await pasillo_auditoria.actualizar_fila_auditoria(
        session=session,
        tenant_id=ctx["tenant_id"],
        user_id=ctx["user_id"],
        auditoria_id=id,
        control_ref=control_ref,
        verificado=payload.verificado,
        riesgo_final=payload.riesgo_final,
        evidencia_sha256=payload.evidencia_sha256,
    )


@router.post("/auditorias/{id}/areas/{area_id}/acta", status_code=status.HTTP_201_CREATED)
async def levantar_acta_endpoint(
    id: str,
    area_id: str,
    ctx: dict = Depends(_ROLES_AUDITOR),
    session: AsyncSession = Depends(get_session),
):
    """Levanta y firma el acta de auditoría de un área (R4). Solo miembros del equipo auditor."""
    auditoria = await pasillo_auditoria.obtener_auditoria(
        session=session,
        tenant_id=ctx["tenant_id"],
        user_id=ctx["user_id"],
        auditoria_id=id,
    )
    if not auditoria:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Auditoría no encontrada")

    if ctx["user_id"] not in auditoria["equipo"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo miembros del equipo auditor pueden levantar y firmar actas.",
        )

    return await pasillo_auditoria.levantar_y_firmar_acta(
        session=session,
        tenant_id=ctx["tenant_id"],
        user_id=ctx["user_id"],
        auditoria_id=id,
        area_id=area_id,
    )


@router.get("/auditorias/{id}/areas/{area_id}/acta")
async def obtener_acta_endpoint(
    id: str,
    area_id: str,
    ctx: dict = Depends(_ROLES_VER_ACTA),
    session: AsyncSession = Depends(get_session),
):
    """Obtiene el acta de un área con su contenido custodiado (R4)."""
    return await pasillo_auditoria.obtener_acta(
        session=session,
        tenant_id=ctx["tenant_id"],
        user_id=ctx["user_id"],
        auditoria_id=id,
        area_id=area_id,
    )


@router.post("/hallazgos/{hallazgo_id}/verificar-cierre", status_code=status.HTTP_201_CREATED)
async def verificar_cierre_endpoint(
    hallazgo_id: str,
    payload: VerificarCierreRequest,
    ctx: dict = Depends(_ROLES_AUDITOR),
    session: AsyncSession = Depends(get_session),
):
    """Verifica el cierre de la acción de un hallazgo (R3 y R5). Solo auditor."""
    return await pasillo_auditoria.verificar_cierre_hallazgo(
        session=session,
        tenant_id=ctx["tenant_id"],
        user_id=ctx["user_id"],
        hallazgo_id=hallazgo_id,
        resultado=payload.resultado,
        motivo=payload.motivo,
    )


@router.get("/cierres-pendientes")
async def listar_cierres_pendientes_endpoint(
    ctx: dict = Depends(_ROLES_AUDITOR),
    session: AsyncSession = Depends(get_session),
):
    """Lista las acciones del plan cerradas que requieren verificación del auditor."""
    return await pasillo_auditoria.listar_cierres_pendientes(
        session=session,
        tenant_id=ctx["tenant_id"],
        user_id=ctx["user_id"],
    )
