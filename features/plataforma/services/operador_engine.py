# ¤seguridad
# ¤rbac-tenant
"""Lógica de negocio y persistencia para la sala Plataforma (ORG-09)."""
from __future__ import annotations

import hashlib
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.audit import registrar_evento
from features.organizacion import organizacion_service
from features.organizacion.organizacion_service import RoleGrant, UserCreate
from features.plataforma.domain.models import (
    AceptarInvitacionRequest,
    AceptarInvitacionResponse,
    AltaOrganizacionResponse,
    OrganizacionCrearRequest,
    OrganizacionResumen,
)


def _hash_codigo(codigo: str) -> str:
    """Calcula SHA-256 del código de invitación."""
    return hashlib.sha256(codigo.strip().encode("utf-8")).hexdigest()


async def registrar_auditoria_plataforma(
    session: AsyncSession,
    actor_tipo: str,
    actor_id: str,
    accion: str,
    tenant_id: Optional[str] = None,
    payload: Optional[dict[str, Any]] = None,
) -> str:
    """Registra un evento append-only en auditoria_plataforma."""
    ev_id = str(uuid4())
    payload_json = json.dumps(payload or {})
    await session.execute(
        text(
            """
            INSERT INTO auditoria_plataforma (
                id, actor_tipo, actor_id, accion, tenant_id, payload, created_at
            ) VALUES (
                :id, :actor_tipo, :actor_id, :accion, :tenant_id, CAST(:payload AS jsonb), NOW()
            )
            """
        ),
        {
            "id": ev_id,
            "actor_tipo": actor_tipo,
            "actor_id": actor_id,
            "accion": accion,
            "tenant_id": tenant_id,
            "payload": payload_json,
        },
    )
    return ev_id


async def verificar_operador(session: AsyncSession, email: str, sub: Optional[str] = None) -> dict:
    """Verifica si el usuario autenticado está registrado como operador_plataforma activo."""
    email_limpio = email.strip().lower()
    fila = (
        await session.execute(
            text(
                """
                SELECT id, email, google_sub, nombre, activo
                FROM operadores_plataforma
                WHERE (LOWER(email) = :email OR (google_sub IS NOT NULL AND google_sub = :sub))
                  AND activo
                """
            ),
            {"email": email_limpio, "sub": sub or ""},
        )
    ).mappings().first()

    if not fila:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso restringido: no tiene permisos de operador de la plataforma.",
        )

    # Si tenía sub nulo y ahora viene sub, vincularlo
    if sub and not fila["google_sub"]:
        await session.execute(
            text("UPDATE operadores_plataforma SET google_sub = :sub, updated_at = NOW() WHERE id = :id"),
            {"sub": sub, "id": fila["id"]},
        )

    return dict(fila)


async def crear_organizacion_e_invitacion(
    session: AsyncSession,
    operador: dict,
    payload: OrganizacionCrearRequest,
) -> AltaOrganizacionResponse:
    """Crea una organización (tenant) y emite una invitación para el admin_organizacion inicial."""
    ruc = payload.ruc_identificacion.strip()
    existente = (
        await session.execute(
            text("SELECT id FROM tenants WHERE ruc_identificacion = :ruc"),
            {"ruc": ruc},
        )
    ).first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe una organización registrada con el RUC {ruc}.",
        )

    tenant_id = f"t-{uuid4().hex[:12]}"
    await session.execute(
        text(
            """
            INSERT INTO tenants (
                id, nombre_comercial, razon_social, ruc_identificacion, tamano, sector, activo, created_at, updated_at
            ) VALUES (
                :id, :nc, :rs, :ruc, :tam, :sec, TRUE, NOW(), NOW()
            )
            """
        ),
        {
            "id": tenant_id,
            "nc": payload.nombre_comercial.strip(),
            "rs": payload.razon_social.strip(),
            "ruc": ruc,
            "tam": payload.tamano,
            "sec": payload.sector.strip() if payload.sector else None,
        },
    )

    # Generar invitación
    codigo_plano = secrets.token_urlsafe(32)
    hash_codigo = _hash_codigo(codigo_plano)
    invitacion_id = str(uuid4())
    expira_en = datetime.now(timezone.utc) + timedelta(days=7)
    email_invitado = payload.email_admin_inicial.strip().lower()

    await session.execute(
        text(
            """
            INSERT INTO invitaciones_organizacion (
                id, tenant_id, email, codigo_hash, expira_en, estado, created_at, created_by
            ) VALUES (
                :id, :tenant_id, :email, :codigo_hash, :expira_en, 'emitida', NOW(), :created_by
            )
            """
        ),
        {
            "id": invitacion_id,
            "tenant_id": tenant_id,
            "email": email_invitado,
            "codigo_hash": hash_codigo,
            "expira_en": expira_en,
            "created_by": operador["id"],
        },
    )

    # Rastro de auditoría
    await registrar_auditoria_plataforma(
        session=session,
        actor_tipo="operador",
        actor_id=operador["id"],
        accion="crear_organizacion_e_invitacion",
        tenant_id=tenant_id,
        payload={
            "ruc": ruc,
            "nombre_comercial": payload.nombre_comercial,
            "email_invitado": email_invitado,
            "invitacion_id": invitacion_id,
        },
    )

    return AltaOrganizacionResponse(
        tenant_id=tenant_id,
        invitacion_id=invitacion_id,
        codigo_invitacion=codigo_plano,
        expira_en=expira_en,
        email_invitado=email_invitado,
    )


async def listar_organizaciones(
    session: AsyncSession,
    operador: dict,
) -> list[OrganizacionResumen]:
    """Lista las organizaciones registradas con metadatos permitidos (sin acceso a sus datos de tratamiento)."""
    rows = (
        await session.execute(
            text(
                """
                SELECT 
                    t.id, t.nombre_comercial, t.razon_social, t.ruc_identificacion,
                    t.tamano, t.sector, t.activo, t.created_at,
                    i.email AS email_admin_inicial, i.estado AS invitacion_estado
                FROM tenants t
                LEFT JOIN LATERAL (
                    SELECT email, estado 
                    FROM invitaciones_organizacion 
                    WHERE tenant_id = t.id 
                    ORDER BY created_at DESC 
                    LIMIT 1
                ) i ON TRUE
                ORDER BY t.created_at DESC
                """
            )
        )
    ).mappings().all()

    return [
        OrganizacionResumen(
            id=r["id"],
            nombre_comercial=r["nombre_comercial"],
            razon_social=r["razon_social"],
            ruc_identificacion=r["ruc_identificacion"],
            tamano=r["tamano"],
            sector=r["sector"],
            activo=r["activo"],
            created_at=r["created_at"],
            email_admin_inicial=r["email_admin_inicial"],
            invitacion_estado=r["invitacion_estado"],
        )
        for r in rows
    ]


async def revocar_invitacion(
    session: AsyncSession,
    operador: dict,
    invitacion_id: str,
) -> dict:
    """Revoca una invitación emitida si aún no ha sido aceptada."""
    fila = (
        await session.execute(
            text("SELECT id, tenant_id, estado FROM invitaciones_organizacion WHERE id = :id"),
            {"id": invitacion_id},
        )
    ).mappings().first()

    if not fila:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitación no encontrada.",
        )
    if fila["estado"] != "emitida":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede revocar una invitación en estado '{fila['estado']}'.",
        )

    await session.execute(
        text(
            """
            UPDATE invitaciones_organizacion
            SET estado = 'revocada', revoked_at = NOW(), revoked_by = :actor
            WHERE id = :id
            """
        ),
        {"id": invitacion_id, "actor": operador["id"]},
    )

    await registrar_auditoria_plataforma(
        session=session,
        actor_tipo="operador",
        actor_id=operador["id"],
        accion="revocar_invitacion",
        tenant_id=fila["tenant_id"],
        payload={"invitacion_id": invitacion_id},
    )

    return {"status": "ok", "mensaje": "Invitación revocada exitosamente."}


async def aceptar_invitacion(
    session: AsyncSession,
    email_verificado: str,
    sub_verificado: str,
    payload: AceptarInvitacionRequest,
) -> AceptarInvitacionResponse:
    """Acepta una invitación de organización, creando al usuario y su rol admin_organizacion."""
    hash_cod = _hash_codigo(payload.codigo)
    ahora = datetime.now(timezone.utc)

    inv = (
        await session.execute(
            text(
                """
                SELECT id, tenant_id, email, expira_en, estado
                FROM invitaciones_organizacion
                WHERE codigo_hash = :hash
                FOR UPDATE
                """
            ),
            {"hash": hash_cod},
        )
    ).mappings().first()

    if not inv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Código de invitación inválido.",
        )

    if inv["estado"] == "aceptada":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La invitación ya ha sido utilizada.",
        )
    if inv["estado"] == "revocada":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La invitación ha sido revocada.",
        )
    if inv["expira_en"] < ahora or inv["estado"] == "caducada":
        # Marcar caducada si no lo estaba
        if inv["estado"] != "caducada":
            await session.execute(
                text("UPDATE invitaciones_organizacion SET estado = 'caducada' WHERE id = :id"),
                {"id": inv["id"]},
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La invitación ha caducado.",
        )

    # COMPROBACIÓN CRÍTICA (invariante y mutación): El correo de Google verificado debe coincidir
    if email_verificado.strip().lower() != inv["email"].strip().lower():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El correo verificado de Google no coincide con el destinatario de la invitación.",
        )

    tenant_id = inv["tenant_id"]

    # Crear o recuperar usuario a través de la compuerta de organización
    nombre_user = payload.nombre_usuario.strip() if payload.nombre_usuario else email_verificado.split("@")[0]
    user_res = await organizacion_service.create_or_get_user(
        session=session,
        payload=UserCreate(email=email_verificado, nombre=nombre_user),
    )
    user_id = user_res["id"]

    # Asegurar vinculación de google_sub
    if sub_verificado:
        await session.execute(
            text(
                """
                UPDATE users 
                SET google_sub = :sub, updated_at = NOW() 
                WHERE id = :u AND (google_sub IS NULL OR google_sub = :sub)
                """
            ),
            {"sub": sub_verificado, "u": user_id},
        )

    # Conceder rol admin_organizacion a través de la compuerta de organización
    await organizacion_service.grant_role(
        session=session,
        tenant_id=tenant_id,
        granted_by=user_id,
        payload=RoleGrant(user_id=user_id, role="admin_organizacion"),
    )

    # Marcar invitación como aceptada
    await session.execute(
        text(
            """
            UPDATE invitaciones_organizacion
            SET estado = 'aceptada', accepted_at = NOW(), accepted_by_user_id = :u
            WHERE id = :id
            """
        ),
        {"id": inv["id"], "u": user_id},
    )

    # Evento de auditoría en audit_events del tenant
    await registrar_evento(
        session=session,
        tenant_id=tenant_id,
        entity_type="organizacion",
        entity_id=tenant_id,
        action="aceptar_invitacion_admin_inicial",
        user_id=user_id,
        payload={"invitacion_id": inv["id"], "email": email_verificado},
    )

    # Evento de auditoría de plataforma
    await registrar_auditoria_plataforma(
        session=session,
        actor_tipo="invitado",
        actor_id=user_id,
        accion="aceptar_invitacion_organizacion",
        tenant_id=tenant_id,
        payload={"invitacion_id": inv["id"], "email": email_verificado},
    )

    return AceptarInvitacionResponse(
        tenant_id=tenant_id,
        user_id=user_id,
        email=email_verificado,
        rol_asignado="admin_organizacion",
        mensaje="Invitación aceptada exitosamente. Se ha concedido el rol de Administrador de Organización.",
    )
