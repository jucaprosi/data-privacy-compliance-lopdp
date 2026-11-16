# -*- coding: utf-8 -*-
# ¤seguridad-tenant ¤adpa
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.entorno.guardias import entorno_actual, validar_arranque, ENTORNOS_FICTICIOS
from app_core.errors import ErrorNegocio
from features.plataforma.services.operador_engine import registrar_auditoria_plataforma

PREFIJO_RUC_SINTETICO = "999999999"


@dataclass(frozen=True)
class OrganizacionSintetica:
    id: str
    nombre_comercial: str
    razon_social: str
    ruc: str
    sector: str
    tamano: str


def id_de_usuario(correo: str) -> str:
    return hashlib.sha256(correo.strip().lower().encode("utf-8")).hexdigest()


def _validar_entorno_sintetico() -> None:
    try:
        entorno = entorno_actual()
        if entorno not in ENTORNOS_FICTICIOS:
            raise ErrorNegocio("ENTORNO_NO_SINTETICO", f"Entorno '{entorno}' no está en entornos ficticios permitidos")
        validar_arranque()
    except Exception as e:
        if isinstance(e, ErrorNegocio):
            raise
        raise ErrorNegocio("ENTORNO_NO_SINTETICO", f"Validación de arranque falló: {e}")


async def asegurar_organizacion_sintetica(session: AsyncSession, datos: OrganizacionSintetica) -> bool:
    """Crea la organización o confirma la existente; devuelve True si la creó."""
    _validar_entorno_sintetico()

    if not datos.ruc.startswith(PREFIJO_RUC_SINTETICO):
        raise ErrorNegocio("RUC_NO_SINTETICO", f"El RUC '{datos.ruc}' no lleva la marca sintética")

    # R2: INSERT ... ON CONFLICT DO NOTHING RETURNING id
    res = await session.execute(
        text(
            "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, sector, tamano, activo) "
            "VALUES (:id, :n, :r, :ruc, :sec, :tam, TRUE) "
            "ON CONFLICT (id) DO NOTHING RETURNING id"
        ),
        {
            "id": datos.id,
            "n": datos.nombre_comercial,
            "r": datos.razon_social,
            "ruc": datos.ruc,
            "sec": datos.sector,
            "tam": datos.tamano,
        },
    )
    creada_id = res.scalar_one_or_none()

    # Relectura por id y RUC
    fila = (await session.execute(
        text("SELECT id, ruc_identificacion FROM tenants WHERE id = :id OR ruc_identificacion = :ruc"),
        {"id": datos.id, "ruc": datos.ruc},
    )).first()

    if fila is None:
        raise ErrorNegocio("ORGANIZACION_NO_DISPONIBLE", "No se encontró la organización tras la inserción")

    # R3: Solo organizaciones sintéticas
    if not (fila[1] and fila[1].startswith(PREFIJO_RUC_SINTETICO)):
        raise ErrorNegocio("ORGANIZACION_NO_SINTETICA", "Existe una organización con esta clave sin marca sintética")

    creada = creada_id is not None
    if creada:
        # R7: Auditoría
        await registrar_auditoria_plataforma(
            session=session,
            actor_id="sistema",
            actor_tipo="sistema",
            accion="alta_sintetica",
            tenant_id=datos.id,
            payload={"origen": "sintetica", "entorno": entorno_actual()},
        )
    return creada


async def asegurar_persona_sintetica(
    session: AsyncSession, tenant_id: str, correo: str, nombre: str
) -> tuple[str, bool]:
    """Crea la persona o devuelve la existente; devuelve (user_id, creada)."""
    _validar_entorno_sintetico()

    # Verificar que tenant_id sea sintético
    fila_tenant = (await session.execute(
        text("SELECT ruc_identificacion FROM tenants WHERE id = :t"),
        {"t": tenant_id},
    )).first()
    if not fila_tenant or not (fila_tenant[0] and fila_tenant[0].startswith(PREFIJO_RUC_SINTETICO)):
        raise ErrorNegocio("ORGANIZACION_NO_DISPONIBLE", f"El tenant '{tenant_id}' no existe o no es sintético")

    correo = correo.strip().lower()
    uid = id_de_usuario(correo)

    # R2: INSERT ... ON CONFLICT (id) DO NOTHING RETURNING id
    res = await session.execute(
        text(
            "INSERT INTO users (id, email, nombre, activo) "
            "VALUES (:id, :e, :n, TRUE) ON CONFLICT (id) DO NOTHING RETURNING id"
        ),
        {"id": uid, "e": correo, "n": nombre},
    )
    creada_id = res.scalar_one_or_none()

    # Relectura
    fila_user = (await session.execute(
        text("SELECT id FROM users WHERE id = :id OR lower(email) = :e"),
        {"id": uid, "e": correo},
    )).first()
    if not fila_user:
        raise ErrorNegocio("ORGANIZACION_NO_DISPONIBLE", "No se encontró el usuario tras la inserción")

    creada = creada_id is not None
    if creada:
        # R7: Auditoría
        await registrar_auditoria_plataforma(
            session=session,
            actor_id="sistema",
            actor_tipo="sistema",
            accion="persona_sintetica",
            tenant_id=tenant_id,
            payload={"origen": "sintetica", "entorno": entorno_actual()},
        )

    return (fila_user[0], creada)
