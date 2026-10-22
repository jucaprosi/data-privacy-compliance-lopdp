# ¤seguridad
# ¤rbac-tenant
"""Router API para operaciones del Operador de la Plataforma e Invitaciones (ORG-09).

Endpoints bajo /api/v1/plataforma:
- POST /organizaciones: Alta de organización y emisión de invitación (solo operador).
- GET /organizaciones: Listado de organizaciones con metadatos permitidos (solo operador).
- POST /invitaciones/{id}/revocar: Revocación de invitación pendiente (solo operador).
- POST /invitaciones/aceptar: Aceptación de invitación por el invitado verificado (cualquier usuario verificado).
"""
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.db.session import get_session
from app_core.security import (
    extraer_bearer,
    modo_autenticacion,
    verificar_token_google,
    IdentidadVerificada,
    MODO_HEADERS,
)
from features.plataforma import plataforma_service
from features.plataforma.plataforma_service import (
    AceptarInvitacionRequest,
    AceptarInvitacionResponse,
    AltaOrganizacionResponse,
    OrganizacionCrearRequest,
    OrganizacionResumen,
)

AUTO_REGISTRO = True

router = APIRouter(prefix="/plataforma", tags=["Operador de la Plataforma"])


async def require_operador(
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    x_user_email: Optional[str] = Header(None, alias="X-User-Email"),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Valida la identidad y comprueba que sea un operador_plataforma activo."""
    modo = modo_autenticacion()
    if modo == MODO_HEADERS:
        # En modo headers (pruebas / desarrollo controlado)
        email = (x_user_email or "").strip().lower()
        sub = (x_user_id or "").strip()
        if not email and not sub:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Falta cabecera de identidad (X-User-Email o X-User-ID).",
            )
        return await plataforma_service.verificar_operador(session, email=email, sub=sub)
    else:
        token = extraer_bearer(authorization)
        identidad: IdentidadVerificada = await verificar_token_google(token)
        return await plataforma_service.verificar_operador(
            session, email=identidad.email, sub=identidad.sub
        )


async def get_identidad_verificada(
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    x_user_email: Optional[str] = Header(None, alias="X-User-Email"),
) -> IdentidadVerificada:
    """Extrae la identidad verificada para el flujo de aceptación de invitaciones."""
    modo = modo_autenticacion()
    if modo == MODO_HEADERS:
        email = (x_user_email or "").strip().lower()
        sub = (x_user_id or "").strip() or "test-sub"
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Falta cabecera de identidad (X-User-Email).",
            )
        return IdentidadVerificada(sub=sub, email=email)
    else:
        token = extraer_bearer(authorization)
        return await verificar_token_google(token)


@router.post("/organizaciones", status_code=status.HTTP_201_CREATED, response_model=AltaOrganizacionResponse)
async def crear_organizacion(
    payload: OrganizacionCrearRequest,
    operador: dict = Depends(require_operador),
    session: AsyncSession = Depends(get_session),
):
    """Crea una nueva organización y genera la invitación del administrador inicial."""
    return await plataforma_service.crear_organizacion_e_invitacion(
        session=session, operador=operador, payload=payload
    )


@router.get("/organizaciones", response_model=list[OrganizacionResumen])
async def listar_organizaciones(
    operador: dict = Depends(require_operador),
    session: AsyncSession = Depends(get_session),
):
    """Lista las organizaciones existentes con metadatos permitidos (sin acceso a sus datos de tratamiento)."""
    return await plataforma_service.listar_organizaciones(session=session, operador=operador)


@router.post("/invitaciones/{invitacion_id}/revocar")
async def revocar_invitacion(
    invitacion_id: str,
    operador: dict = Depends(require_operador),
    session: AsyncSession = Depends(get_session),
):
    """Revoca una invitación emitida si aún no ha sido aceptada."""
    return await plataforma_service.revocar_invitacion(
        session=session, operador=operador, invitacion_id=invitacion_id
    )


@router.post("/invitaciones/aceptar", response_model=AceptarInvitacionResponse)
async def aceptar_invitacion(
    payload: AceptarInvitacionRequest,
    identidad: IdentidadVerificada = Depends(get_identidad_verificada),
    session: AsyncSession = Depends(get_session),
):
    """Acepta una invitación de organización convirtiendo al usuario en admin_organizacion."""
    return await plataforma_service.aceptar_invitacion(
        session=session,
        email_verificado=identidad.email,
        sub_verificado=identidad.sub,
        payload=payload,
    )
