# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤¤backend-developer
# ¤rbac-tenant ¤evidencias
"""Rutas de API para la sala Formación (FOR-01)."""
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import get_context, require_role
from app_core.db.session import get_session
from app_core.errors import ErrorNegocio
from app_core.pasillo import formacion as pasillo_formacion
from app_core.pasillo import organizacion as pasillo_organizacion
from features.formacion.formacion_service import (
    AccionCreate,
    AccionOut,
    CoberturaOut,
    ContenidoCreate,
    ContenidoOut,
    ExamenOut,
    ExamenSubmitRequest,
    ExamenSubmitResponse,
    IniciarExamenResponse,
    ParticipantesAddRequest,
    PreguntaCreate,
    PreguntaOut,
    errores as e,
)

AUTO_REGISTRO = True

router = APIRouter(prefix="/formacion", tags=["Formación y Capacitación (FOR-01)"])

_ESCRIBEN = require_role("implementador", "coordinador", "admin_organizacion")
_LEEN = require_role(
    "implementador",
    "coordinador",
    "admin_organizacion",
    "auditor",
    "dpo",
    "responsable_area",
)


async def _obtener_persona_participante(session: AsyncSession, ctx: dict) -> str:
    """Resuelve la persona_id del inventario vinculada al email del usuario autenticado."""
    # Consultar email del usuario autenticado
    u_row = (
        await session.execute(
            text("SELECT email FROM users WHERE id = :uid"),
            {"uid": ctx["user_id"]},
        )
    ).mappings().first()
    email = u_row["email"] if u_row else ctx.get("email", "")

    persona = await pasillo_organizacion.persona_de_usuario(session, ctx["tenant_id"], email)
    if not persona:
        raise ErrorNegocio(e.PERSONA_NO_VINCULADA)
    return str(persona["id"])


# 1. Contenidos
@router.post("/contenidos", status_code=status.HTTP_201_CREATED, response_model=ContenidoOut)
async def crear_contenido_endpoint(
    payload: ContenidoCreate,
    ctx: dict = Depends(_ESCRIBEN),
    session: AsyncSession = Depends(get_session),
):
    return await pasillo_formacion.crear_contenido(
        session=session,
        tenant_id=ctx["tenant_id"],
        user_id=ctx["user_id"],
        titulo=payload.titulo,
        tipo=payload.tipo,
        referencia=payload.referencia,
    )


@router.get("/contenidos", response_model=list[ContenidoOut])
async def listar_contenidos_endpoint(
    ctx: dict = Depends(_LEEN),
    session: AsyncSession = Depends(get_session),
):
    return await pasillo_formacion.listar_contenidos(
        session=session,
        tenant_id=ctx["tenant_id"],
        user_id=ctx["user_id"],
    )


# 2. Banco de preguntas por contenido
@router.post("/contenidos/{id}/preguntas", status_code=status.HTTP_201_CREATED, response_model=PreguntaOut)
async def crear_pregunta_endpoint(
    id: str,
    payload: PreguntaCreate,
    ctx: dict = Depends(_ESCRIBEN),
    session: AsyncSession = Depends(get_session),
):
    return await pasillo_formacion.crear_pregunta(
        session=session,
        tenant_id=ctx["tenant_id"],
        user_id=ctx["user_id"],
        contenido_id=id,
        enunciado=payload.enunciado,
        opciones=payload.opciones,
        correcta=payload.correcta,
    )


@router.get("/contenidos/{id}/preguntas", response_model=list[PreguntaOut])
async def listar_preguntas_endpoint(
    id: str,
    ctx: dict = Depends(_ESCRIBEN),
    session: AsyncSession = Depends(get_session),
):
    return await pasillo_formacion.listar_preguntas(
        session=session,
        tenant_id=ctx["tenant_id"],
        user_id=ctx["user_id"],
        contenido_id=id,
    )


# 3. Acciones formativas
@router.post("/acciones", status_code=status.HTTP_201_CREATED, response_model=AccionOut)
async def crear_accion_endpoint(
    payload: AccionCreate,
    ctx: dict = Depends(_ESCRIBEN),
    session: AsyncSession = Depends(get_session),
):
    return await pasillo_formacion.crear_accion(
        session=session,
        tenant_id=ctx["tenant_id"],
        user_id=ctx["user_id"],
        contenido_id=payload.contenido_id,
        nombre=payload.nombre,
        inicio=payload.inicio,
        fin=payload.fin,
        nota_minima=payload.nota_minima,
    )


@router.get("/acciones", response_model=list[AccionOut])
async def listar_acciones_endpoint(
    ctx: dict = Depends(_LEEN),
    session: AsyncSession = Depends(get_session),
):
    return await pasillo_formacion.listar_acciones(
        session=session,
        tenant_id=ctx["tenant_id"],
        user_id=ctx["user_id"],
    )


@router.post("/acciones/{id}/participantes", status_code=status.HTTP_201_CREATED)
async def anadir_participantes_endpoint(
    id: str,
    payload: ParticipantesAddRequest,
    ctx: dict = Depends(_ESCRIBEN),
    session: AsyncSession = Depends(get_session),
):
    insertados = await pasillo_formacion.anadir_participantes(
        session=session,
        tenant_id=ctx["tenant_id"],
        user_id=ctx["user_id"],
        accion_id=id,
        persona_ids=payload.persona_ids,
    )
    return {"status": "SUCCESS", "anadidos": insertados}


@router.get("/acciones/{id}/participantes")
async def listar_participantes_endpoint(
    id: str,
    ctx: dict = Depends(_LEEN),
    session: AsyncSession = Depends(get_session),
):
    return await pasillo_formacion.listar_participaciones_accion(
        session=session,
        tenant_id=ctx["tenant_id"],
        user_id=ctx["user_id"],
        accion_id=id,
    )


# 4. Examen del participante
@router.get("/participaciones/{id}/examen", response_model=ExamenOut)
async def obtener_examen_endpoint(
    id: str,
    ctx: dict = Depends(get_context),
    session: AsyncSession = Depends(get_session),
):
    """R5: Obtiene las preguntas del examen sin la respuesta correcta."""
    persona_id = await _obtener_persona_participante(session, ctx)
    return await pasillo_formacion.obtener_examen_participacion(
        session=session,
        tenant_id=ctx["tenant_id"],
        user_id=ctx["user_id"],
        participacion_id=id,
        persona_id=persona_id,
    )


@router.post("/participaciones/{id}/iniciar", response_model=IniciarExamenResponse)
async def iniciar_examen_endpoint(
    id: str,
    ctx: dict = Depends(get_context),
    session: AsyncSession = Depends(get_session),
):
    """R7: Inicia el examen de forma idempotente."""
    persona_id = await _obtener_persona_participante(session, ctx)
    return await pasillo_formacion.iniciar_examen_participacion(
        session=session,
        tenant_id=ctx["tenant_id"],
        user_id=ctx["user_id"],
        participacion_id=id,
        persona_id=persona_id,
    )


@router.post("/participaciones/{id}/examen", response_model=ExamenSubmitResponse)
async def enviar_examen_endpoint(
    id: str,
    payload: ExamenSubmitRequest,
    ctx: dict = Depends(get_context),
    session: AsyncSession = Depends(get_session),
):
    """R4: Envía y califica el examen consumiendo el intento de forma transaccional."""
    persona_id = await _obtener_persona_participante(session, ctx)
    return await pasillo_formacion.calificar_y_terminar_examen(
        session=session,
        tenant_id=ctx["tenant_id"],
        user_id=ctx["user_id"],
        participacion_id=id,
        persona_id=persona_id,
        respuestas=payload.respuestas,
    )


# 5. Mis participaciones
@router.get("/mis-participaciones")
async def listar_mis_participaciones_endpoint(
    ctx: dict = Depends(get_context),
    session: AsyncSession = Depends(get_session),
):
    """Lista las participaciones de la persona autenticada para la vista 'Mi formación'."""
    try:
        persona_id = await _obtener_persona_participante(session, ctx)
    except ErrorNegocio:
        return []

    rows = (
        await session.execute(
            text(
                """
                SELECT p.id, p.accion_id, p.enviado_en, p.iniciado_en, p.terminado_en, p.nota, p.diploma_sha256,
                       a.nombre AS accion_nombre, a.inicio, a.fin, a.nota_minima
                FROM formacion_participaciones p
                JOIN formacion_acciones a ON a.id = p.accion_id AND a.tenant_id = p.tenant_id
                WHERE p.persona_id = :pid AND p.tenant_id = :t
                ORDER BY a.inicio DESC
                """
            ),
            {"pid": persona_id, "t": ctx["tenant_id"]},
        )
    ).mappings().all()

    return [
        {
            "id": str(r["id"]),
            "accion_id": str(r["accion_id"]),
            "accion_nombre": r["accion_nombre"],
            "inicio": r["inicio"].isoformat() if hasattr(r["inicio"], "isoformat") else str(r["inicio"]),
            "fin": r["fin"].isoformat() if hasattr(r["fin"], "isoformat") else str(r["fin"]),
            "nota_minima": float(r["nota_minima"]),
            "enviado_en": r["enviado_en"].isoformat() if hasattr(r["enviado_en"], "isoformat") else str(r["enviado_en"]),
            "iniciado_en": r["iniciado_en"].isoformat() if r["iniciado_en"] and hasattr(r["iniciado_en"], "isoformat") else r["iniciado_en"],
            "terminado_en": r["terminado_en"].isoformat() if r["terminado_en"] and hasattr(r["terminado_en"], "isoformat") else r["terminado_en"],
            "nota": float(r["nota"]) if r["nota"] is not None else None,
            "diploma_sha256": r["diploma_sha256"],
        }
        for r in rows
    ]


# 6. Cobertura
@router.get("/cobertura", response_model=CoberturaOut)
async def obtener_cobertura_endpoint(
    ctx: dict = Depends(_LEEN),
    session: AsyncSession = Depends(get_session),
):
    """R3: Calcula la cobertura de formación sobre personas activas."""
    return await pasillo_formacion.calcular_cobertura(
        session=session,
        tenant_id=ctx["tenant_id"],
        user_id=ctx["user_id"],
    )
