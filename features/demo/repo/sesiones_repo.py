# -*- coding: utf-8 -*-
# ¤demo
"""Repositorio de `demo_sesiones` (DEMO-00). Sin borrados: las filas se vencen, nunca se eliminan.

El correo del vendedor se guarda en la tabla, pero nunca se escribe en los registros de la aplicación.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from features.demo.domain.sesion import EstadoSesion, MotivoFin, SesionDemo

#: Clave fija del candado de transacción que serializa el conteo frente a TOPE.
CANDADO_TOPE = 0x44454D4F

_COLUMNAS = (
    "id, vendedor_sub, vendedor_email, tenant_id, persona_usuario_id, estado, "
    "iniciada_en, ultima_actividad, terminada_en, motivo_fin"
)


def _a_sesion(fila) -> SesionDemo:
    m = fila._mapping
    return SesionDemo(
        id=m["id"],
        vendedor_sub=m["vendedor_sub"],
        vendedor_email=m["vendedor_email"],
        tenant_ids=(m["tenant_id"],) if m["tenant_id"] else (),
        persona_usuario_id=m["persona_usuario_id"],
        estado=EstadoSesion(m["estado"]),
        iniciada_en=m["iniciada_en"],
        ultima_actividad=m["ultima_actividad"],
        terminada_en=m["terminada_en"],
        motivo_fin=MotivoFin(m["motivo_fin"]) if m["motivo_fin"] else None,
    )


async def obtener_activa(session: AsyncSession, vendedor_sub: str) -> SesionDemo | None:
    fila = (
        await session.execute(
            text(f"SELECT {_COLUMNAS} FROM demo_sesiones WHERE vendedor_sub = :sub AND estado = 'activa'"),
            {"sub": vendedor_sub},
        )
    ).first()
    return _a_sesion(fila) if fila else None


async def contar_activas_con_candado(session: AsyncSession) -> int:
    """Toma `pg_advisory_xact_lock` y cuenta las activas; el candado dura hasta el fin de la transacción."""
    await session.execute(text("SELECT pg_advisory_xact_lock(:k)"), {"k": CANDADO_TOPE})
    resultado = await session.execute(text("SELECT count(*) FROM demo_sesiones WHERE estado = 'activa'"))
    return int(resultado.scalar_one())


async def insertar(
    session: AsyncSession,
    vendedor_sub: str,
    vendedor_email: str,
    tenant_id: str | None,
    persona_usuario_id: str | None,
    ahora: datetime,
) -> SesionDemo:
    """Inserta una sesión activa. El índice único parcial impide dos activas del mismo vendedor."""
    fila = (
        await session.execute(
            text(
                "INSERT INTO demo_sesiones (id, vendedor_sub, vendedor_email, tenant_id, persona_usuario_id, "
                "estado, iniciada_en, ultima_actividad) "
                "VALUES (:id, :sub, :email, :tenant, :persona, 'activa', :ahora, :ahora) "
                f"RETURNING {_COLUMNAS}"
            ),
            {
                "id": str(uuid.uuid4()),
                "sub": vendedor_sub,
                "email": vendedor_email,
                "tenant": tenant_id,
                "persona": persona_usuario_id,
                "ahora": ahora,
            },
        )
    ).one()
    return _a_sesion(fila)


async def renovar_actividad(
    session: AsyncSession, sesion_id: str, ahora: datetime, persona_usuario_id: str | None = None
) -> None:
    """Renueva la actividad y, si se indica, la persona activa."""
    await session.execute(
        text(
            "UPDATE demo_sesiones SET ultima_actividad = :ahora, "
            "persona_usuario_id = COALESCE(:persona, persona_usuario_id) "
            "WHERE id = :id AND estado = 'activa'"
        ),
        {"id": sesion_id, "ahora": ahora, "persona": persona_usuario_id},
    )


async def marcar_vencida(session: AsyncSession, sesion_id: str, motivo: MotivoFin, ahora: datetime) -> None:
    await session.execute(
        text(
            "UPDATE demo_sesiones SET estado = 'vencida', motivo_fin = :motivo, terminada_en = :ahora "
            "WHERE id = :id AND estado = 'activa'"
        ),
        {"id": sesion_id, "motivo": motivo.value, "ahora": ahora},
    )
