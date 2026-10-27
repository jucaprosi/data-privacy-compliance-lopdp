"""Router FastAPI para la Sala ADPA: Auditoría Anual y Planes de Acción (CAPA)."""
from contextlib import asynccontextmanager
from typing import AsyncGenerator, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import get_context, get_usuario_autenticado
from app_core.audit import registrar_evento
from app_core.db.session import get_session
from features.auditoria_capa.auditoria_capa_service import (
    EstadoCAPA,
    SeveridadHallazgo,
    TicketCAPA,
    TicketYaCerradoError,
    cerrar_ticket_capa,
    listar_tickets_capa,
    registrar_hallazgo_capa,
)
from features.organizacion.organizacion_service import list_tenant_users

AUTO_REGISTRO = True
PREFIJO = "/api/v1"

router = APIRouter(prefix="/capa", tags=["Auditoría y CAPA (Módulo 3)"])

ROLES_REGISTRO_CAPA = ("coordinador", "dpo")
ROLES_LECTURA_CAPA = (
    "admin_organizacion",
    "coordinador",
    "dpo",
    "implementador",
)
ROLES_CIERRE_CAPA = ("coordinador", "admin_organizacion")


class CrearTicketCAPARequest(BaseModel):
    control_id: str = Field(..., min_length=1)
    severidad: SeveridadHallazgo
    descripcion_hallazgo: str = Field(..., min_length=1)
    causa_raiz: str = ""
    accion_correctiva: str = Field(..., min_length=1)
    responsable_implementacion_id: str = Field(..., min_length=1)


class CerrarTicketCAPARequest(BaseModel):
    auditor_id: str = ""
    evidencia_id: str = Field(..., min_length=1)


class TicketCAPAResponse(BaseModel):
    id: str
    tenant_id: str
    control_id: str
    severidad: SeveridadHallazgo
    descripcion_hallazgo: str
    causa_raiz: str
    accion_correctiva: str
    responsable_implementacion_id: str
    creado_por: str = ""
    auditor_verificador_id: Optional[str] = None
    estado: EstadoCAPA
    evidencia_cierre_id: Optional[str] = None
    fecha_creacion: Optional[str] = None
    fecha_cierre: Optional[str] = None


def _serializar_ticket(t: TicketCAPA) -> TicketCAPAResponse:
    return TicketCAPAResponse(
        id=t.id,
        tenant_id=t.tenant_id,
        control_id=t.control_id,
        severidad=t.severidad,
        descripcion_hallazgo=t.descripcion_hallazgo,
        causa_raiz=t.causa_raiz,
        accion_correctiva=t.accion_correctiva,
        responsable_implementacion_id=t.responsable_implementacion_id,
        creado_por=t.creado_por,
        auditor_verificador_id=t.auditor_verificador_id or None,
        estado=t.estado,
        evidencia_cierre_id=t.evidencia_cierre_id or None,
        fecha_creacion=t.fecha_creacion.isoformat() if t.fecha_creacion else None,
        fecha_cierre=t.fecha_cierre.isoformat() if t.fecha_cierre else None,
    )


async def get_capa_session(
    x_user_id: str = Header(""),
    x_tenant_id: str = Header("tenant-default"),
) -> AsyncGenerator[AsyncSession, None]:
    """Conserva los nombres de cabecera publicados usando la sesión del núcleo."""
    async with asynccontextmanager(get_session)(x_user_id, x_tenant_id) as session:
        yield session


async def _contexto_capa(
    authorization: str | None = Header(None),
    x_user_id: str = Header(""),
    x_tenant_id: str = Header("tenant-default"),
    x_role: str = Header("implementador"),
    session: AsyncSession = Depends(get_capa_session),
) -> dict:
    usuario = await get_usuario_autenticado(authorization, x_user_id, session)
    return await get_context(usuario, x_tenant_id, x_role, session)


async def _contexto_cierre_capa(
    authorization: str | None = Header(None),
    x_user_id: str = Header(""),
    x_tenant_id: str = Header("tenant-default"),
    x_role: str = Header("implementador"),
    session: AsyncSession = Depends(get_capa_session),
) -> dict:
    if x_role in ("dpo", "DPD_DPO_INTERNO"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Violación SoD: El DPO tiene prohibido ejecutar o cerrar acciones correctivas directamente.",
        )
    usuario = await get_usuario_autenticado(authorization, x_user_id, session)
    ctx = await get_context(usuario, x_tenant_id, x_role, session)
    if ctx["role"] == "dpo":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Violación SoD: El DPO tiene prohibido ejecutar o cerrar acciones correctivas directamente.",
        )
    return ctx


@router.post(
    "/tickets",
    response_model=TicketCAPAResponse,
    status_code=status.HTTP_201_CREATED,
    responses={200: {"model": TicketCAPAResponse}},
)
async def crear_ticket(
    payload: CrearTicketCAPARequest,
    ctx: dict = Depends(_contexto_capa),
    session: AsyncSession = Depends(get_capa_session),
):
    if ctx["role"] not in ROLES_REGISTRO_CAPA:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Rol no autorizado para registrar hallazgos CAPA.",
        )

    responsable_id = payload.responsable_implementacion_id.strip()
    usuarios_activos = await list_tenant_users(session, ctx["tenant_id"])
    es_miembro_activo = any(
        u["id"] == responsable_id and bool(u.get("activo", True))
        for u in usuarios_activos
    )
    if not es_miembro_activo:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="El responsable de la acción debe ser un miembro activo de la organización.",
        )

    nuevo = TicketCAPA(
        tenant_id=ctx["tenant_id"],
        control_id=payload.control_id.strip(),
        severidad=payload.severidad,
        descripcion_hallazgo=payload.descripcion_hallazgo.strip(),
        causa_raiz=payload.causa_raiz.strip(),
        accion_correctiva=payload.accion_correctiva.strip(),
        responsable_implementacion_id=responsable_id,
        creado_por=ctx["user_id"],
    )
    creado = await registrar_hallazgo_capa(session, nuevo)
    await registrar_evento(
        session,
        tenant_id=ctx["tenant_id"],
        entity_type="capa_ticket",
        entity_id=creado.id,
        action="registrar_hallazgo",
        user_id=ctx["user_id"],
        payload={
            "control_id": creado.control_id,
            "severidad": creado.severidad.value,
            "responsable_implementacion_id": creado.responsable_implementacion_id,
            "creado_por": creado.creado_por,
            "estado": creado.estado.value,
        },
    )
    return _serializar_ticket(creado)


@router.get("/tickets", response_model=List[TicketCAPAResponse])
async def listar_tickets(
    ctx: dict = Depends(_contexto_capa),
    session: AsyncSession = Depends(get_capa_session),
):
    if ctx["role"] not in ROLES_LECTURA_CAPA:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Rol no autorizado para consultar hallazgos CAPA.",
        )
    tickets = await listar_tickets_capa(session, ctx["tenant_id"])
    return [_serializar_ticket(t) for t in tickets]


@router.post("/tickets/{ticket_id}/cerrar", response_model=TicketCAPAResponse)
async def cerrar_ticket(
    ticket_id: str,
    payload: CerrarTicketCAPARequest,
    ctx: dict = Depends(_contexto_cierre_capa),
    session: AsyncSession = Depends(get_capa_session),
):
    if ctx["role"] not in ROLES_CIERRE_CAPA:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Rol no autorizado para cerrar acciones correctivas CAPA.",
        )
    try:
        # Quien cierra y verifica es siempre el usuario autenticado; se ignora payload.auditor_id.
        cerrado = await cerrar_ticket_capa(
            session=session,
            tenant_id=ctx["tenant_id"],
            ticket_id=ticket_id,
            auditor_id=ctx["user_id"],
            evidencia_id=payload.evidencia_id,
        )
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except TicketYaCerradoError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    await registrar_evento(
        session,
        tenant_id=ctx["tenant_id"],
        entity_type="capa_ticket",
        entity_id=cerrado.id,
        action="cerrar_hallazgo",
        user_id=ctx["user_id"],
        payload={
            "auditor_verificador_id": cerrado.auditor_verificador_id,
            "evidencia_cierre_id": cerrado.evidencia_cierre_id,
            "estado": cerrado.estado.value,
            "fecha_cierre": cerrado.fecha_cierre.isoformat() if cerrado.fecha_cierre else None,
        },
    )
    return _serializar_ticket(cerrado)
