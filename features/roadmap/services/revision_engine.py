# ¤roadmap ¤rbac-tenant
"""Motor de revisión humana con cuatro ojos antes de activar la Hoja de Ruta (RM-27).

Invariantes:
- R2: solo `coordinador` o `dpo` vigentes pueden activar (`generated` -> `active`).
- R3: quien generó la hoja (`generado_por`) no puede activarla (`REVISION_MISMA_PERSONA`).
- R5: hojas anteriores (`generado_por IS NULL` y `revisado_por IS NULL`) llevan etiqueta «sin revisión registrada».
- R6: activación atómica con `UPDATE ... WHERE status = 'generated' RETURNING`; la segunda petición concurrente devuelve `HOJA_YA_ACTIVA`.
- R-ADPA: roles vigentes consultados por `app_core/pasillo/organizacion.py`.
"""
from __future__ import annotations

import sys
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.audit import registrar_evento
from app_core.errors import ErrorNegocio
from app_core.pasillo import organizacion as pasillo_organizacion
from features.roadmap.domain.errores import (
    HOJA_PENDIENTE_DE_REVISION,
    HOJA_YA_ACTIVA,
    REVISION_MISMA_PERSONA,
)
from features.roadmap.services.contexto_tenant import set_session_context

ROLES_ACTIVACION = frozenset({"coordinador", "dpo"})
ETIQUETA_SIN_REVISION = "sin revisión registrada"


async def _roles_vigentes_usuario(
    session: AsyncSession, tenant_id: str, user_id: str
) -> set[str]:
    """Consulta roles vigentes vía pasillo de Organización y restablece el contexto RLS del llamante."""
    roles = await pasillo_organizacion.listar_roles_de_usuario(session, tenant_id, user_id)
    await set_session_context(session, tenant_id, user_id)
    return {r["role"] for r in roles}


async def obtener_estado_revision(
    session: AsyncSession,
    tenant_id: str,
    roadmap_id: str,
    user_id: str,
    rol: Optional[str] = None,
) -> dict[str, Any]:
    """Devuelve el estado de revisión humana de la hoja de ruta para el usuario y rol solicitantes."""
    nombres_roles = await _roles_vigentes_usuario(session, tenant_id, user_id)

    fila = (await session.execute(
        text("""
            SELECT r.id, r.status, r.generado_por, r.created_at, r.updated_at,
                   r.revisado_por, r.revisado_en,
                   ug.nombre AS generado_por_nombre,
                   ur.nombre AS revisado_por_nombre
            FROM roadmaps r
            LEFT JOIN users ug ON ug.id = r.generado_por
            LEFT JOIN users ur ON ur.id = r.revisado_por
            WHERE r.id = :rid AND r.tenant_id = :tid
        """),
        {"rid": roadmap_id, "tid": tenant_id},
    )).mappings().first()
    if not fila:
        raise LookupError("Hoja de ruta no encontrada")

    if rol is not None:
        tiene_rol_activador = rol in ROLES_ACTIVACION and rol in nombres_roles
    else:
        tiene_rol_activador = bool(nombres_roles & ROLES_ACTIVACION)

    generado_por = fila["generado_por"]
    revisado_por = fila["revisado_por"]
    status = fila["status"]
    es_autor = generado_por is not None and generado_por == user_id
    puede_activar = (
        status == "generated"
        and tiene_rol_activador
        and generado_por != user_id
    )
    etiqueta = ETIQUETA_SIN_REVISION if (generado_por is None and revisado_por is None) else None

    generado_ts = fila["updated_at"] or fila["created_at"]
    generado_en = generado_ts.isoformat() if (generado_por is not None and generado_ts is not None) else None
    revisado_en = fila["revisado_en"].isoformat() if fila["revisado_en"] is not None else None

    return {
        "status": status,
        "generado_por": generado_por,
        "generado_por_nombre": fila["generado_por_nombre"],
        "generado_en": generado_en,
        "revisado_por": revisado_por,
        "revisado_por_nombre": fila["revisado_por_nombre"],
        "revisado_en": revisado_en,
        "puede_activar": puede_activar,
        "es_autor": es_autor,
        "etiqueta": etiqueta,
    }


async def activar_hoja_ruta(
    session: AsyncSession,
    tenant_id: str,
    roadmap_id: str,
    user_id: str,
    rol: Optional[str] = None,
) -> dict[str, Any]:
    """Activa una hoja de ruta (`generated` -> `active`) validando rol vigente y principio de cuatro ojos."""
    nombres_roles = await _roles_vigentes_usuario(session, tenant_id, user_id)
    autorizado = (
        (rol in ROLES_ACTIVACION and rol in nombres_roles)
        if rol is not None
        else bool(nombres_roles & ROLES_ACTIVACION)
    )
    if not autorizado:
        raise pasillo_organizacion.error_rbac(
            403, "Solo un coordinador o el DPO pueden activar la hoja de ruta."
        )

    fila = (await session.execute(
        text("""
            SELECT id, status, generado_por, revisado_por, revisado_en
            FROM roadmaps
            WHERE id = :rid AND tenant_id = :tid
        """),
        {"rid": roadmap_id, "tid": tenant_id},
    )).mappings().first()
    if not fila:
        raise LookupError("Hoja de ruta no encontrada")

    if fila["status"] == "active":
        raise ErrorNegocio(HOJA_YA_ACTIVA)
    if fila["generado_por"] is not None and fila["generado_por"] == user_id:
        raise ErrorNegocio(REVISION_MISMA_PERSONA)
    if fila["status"] != "generated":
        raise ErrorNegocio(
            HOJA_PENDIENTE_DE_REVISION,
            detail="La hoja de ruta debe estar generada antes de activarse.",
        )

    actualizada = (await session.execute(
        text("""
            UPDATE roadmaps
            SET status = 'active',
                revisado_por = :uid,
                revisado_en = now(),
                updated_at = now()
            WHERE id = :rid AND tenant_id = :tid AND status = 'generated'
            RETURNING id, status, revisado_por, revisado_en
        """),
        {"uid": user_id, "rid": roadmap_id, "tid": tenant_id},
    )).mappings().first()
    if not actualizada:
        await session.rollback()
        raise ErrorNegocio(HOJA_YA_ACTIVA)

    revisor_nombre = (await session.execute(
        text("SELECT nombre FROM users WHERE id = :uid"),
        {"uid": user_id},
    )).scalar()

    await registrar_evento(
        session,
        tenant_id,
        "roadmap",
        roadmap_id,
        "roadmap_activated",
        user_id,
        {"rol": rol or ("dpo" if "dpo" in nombres_roles else "coordinador")},
    )
    await session.commit()

    return {
        "status": actualizada["status"],
        "revisado_por": actualizada["revisado_por"],
        "revisado_por_nombre": revisor_nombre,
        "revisado_en": actualizada["revisado_en"].isoformat() if actualizada["revisado_en"] else None,
    }


def registrar_en_compuerta() -> None:
    """Expone las operaciones y códigos RM-27 en `features.roadmap.roadmap_service` sin editar su archivo."""
    compuerta = sys.modules.get("features.roadmap.roadmap_service")
    if compuerta is None:
        return
    from features.roadmap.services.generacion_en_linea import registrar_regeneracion_hoja

    exportados = {
        "activar_hoja_ruta": activar_hoja_ruta,
        "obtener_estado_revision": obtener_estado_revision,
        "registrar_regeneracion_hoja": registrar_regeneracion_hoja,
        "REVISION_MISMA_PERSONA": REVISION_MISMA_PERSONA,
        "HOJA_YA_ACTIVA": HOJA_YA_ACTIVA,
        "HOJA_PENDIENTE_DE_REVISION": HOJA_PENDIENTE_DE_REVISION,
    }
    publicos = getattr(compuerta, "__all__", None)
    for nombre, valor in exportados.items():
        setattr(compuerta, nombre, valor)
        if isinstance(publicos, list) and nombre not in publicos:
            publicos.append(nombre)


registrar_en_compuerta()
