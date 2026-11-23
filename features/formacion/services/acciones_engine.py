# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤engine ¤evidencias ¤rbac-tenant
"""Motor de gestión de acciones formativas y asignación de participantes (FOR-01)."""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.errors import ErrorNegocio
from features.formacion.domain import errores as e


async def _fijar_rls(session: AsyncSession, tenant_id: str, user_id: str) -> None:
    await session.execute(
        text("SELECT set_config('app.current_tenant_id', :t, true)"),
        {"t": tenant_id},
    )
    await session.execute(
        text("SELECT set_config('app.current_user_id', :u, true)"),
        {"u": user_id},
    )


async def crear_accion(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    *,
    contenido_id: str,
    nombre: str,
    inicio: date,
    fin: date,
    nota_minima: float = 70.0,
) -> dict[str, Any]:
    """Crea una acción formativa con rango de fechas y nota mínima."""
    await _fijar_rls(session, tenant_id, user_id)

    nombre = (nombre or "").strip()
    if not nombre:
        raise ValueError("El nombre de la acción es obligatorio.")
    if fin < inicio:
        raise ValueError("La fecha de fin debe ser posterior o igual a la de inicio.")
    if not (0.0 <= nota_minima <= 100.0):
        raise ValueError("La nota mínima debe estar entre 0 y 100.")

    aid = str(uuid.uuid4())
    await session.execute(
        text(
            """
            INSERT INTO formacion_acciones (id, tenant_id, contenido_id, nombre, inicio, fin, nota_minima, creado_por)
            VALUES (:id, :t, :cid, :nombre, :inicio, :fin, :nota, :creado_por)
            """
        ),
        {
            "id": aid,
            "t": tenant_id,
            "cid": contenido_id,
            "nombre": nombre,
            "inicio": inicio,
            "fin": fin,
            "nota": nota_minima,
            "creado_por": user_id,
        },
    )

    return {
        "id": aid,
        "tenant_id": tenant_id,
        "contenido_id": contenido_id,
        "nombre": nombre,
        "inicio": inicio.isoformat() if hasattr(inicio, "isoformat") else str(inicio),
        "fin": fin.isoformat() if hasattr(fin, "isoformat") else str(fin),
        "nota_minima": float(nota_minima),
        "creado_por": user_id,
        "total_participantes": 0,
        "terminados": 0,
    }


async def listar_acciones(
    session: AsyncSession, tenant_id: str, user_id: str
) -> list[dict[str, Any]]:
    """Lista las acciones formativas con métricas de avance de participantes."""
    await _fijar_rls(session, tenant_id, user_id)
    rows = (
        await session.execute(
            text(
                """
                SELECT a.id, a.tenant_id, a.contenido_id, a.nombre, a.inicio, a.fin, a.nota_minima, a.creado_por,
                       COUNT(p.id) AS total_participantes,
                       COUNT(p.terminado_en) AS terminados
                FROM formacion_acciones a
                LEFT JOIN formacion_participaciones p ON p.accion_id = a.id AND p.tenant_id = a.tenant_id
                WHERE a.tenant_id = :t
                GROUP BY a.id, a.tenant_id, a.contenido_id, a.nombre, a.inicio, a.fin, a.nota_minima, a.creado_por
                ORDER BY a.inicio DESC
                """
            ),
            {"t": tenant_id},
        )
    ).mappings().all()

    return [
        {
            "id": str(r["id"]),
            "tenant_id": r["tenant_id"],
            "contenido_id": str(r["contenido_id"]),
            "nombre": r["nombre"],
            "inicio": r["inicio"].isoformat() if hasattr(r["inicio"], "isoformat") else str(r["inicio"]),
            "fin": r["fin"].isoformat() if hasattr(r["fin"], "isoformat") else str(r["fin"]),
            "nota_minima": float(r["nota_minima"]),
            "creado_por": r["creado_por"],
            "total_participantes": int(r["total_participantes"] or 0),
            "terminados": int(r["terminados"] or 0),
        }
        for r in rows
    ]


async def anadir_participantes(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    *,
    accion_id: str,
    persona_ids: list[str],
) -> int:
    """Asigna participantes a una acción. R: 409 CONTENIDO_SIN_PREGUNTAS si el contenido no tiene preguntas."""
    await _fijar_rls(session, tenant_id, user_id)

    # 1. Obtener contenido_id de la acción
    accion = (
        await session.execute(
            text("SELECT contenido_id FROM formacion_acciones WHERE id = :id AND tenant_id = :t"),
            {"id": accion_id, "t": tenant_id},
        )
    ).mappings().first()
    if not accion:
        raise ValueError("Acción formativa no encontrada.")

    # 2. Verificar que el contenido tenga preguntas
    tiene_preguntas = (
        await session.execute(
            text("SELECT 1 FROM formacion_preguntas WHERE contenido_id = :cid AND tenant_id = :t LIMIT 1"),
            {"cid": accion["contenido_id"], "t": tenant_id},
        )
    ).scalar_one_or_none()
    if tiene_preguntas is None:
        raise ErrorNegocio(e.CONTENIDO_SIN_PREGUNTAS)

    # 3. Insertar participantes con enviado_en = now()
    ahora = datetime.now(timezone.utc)
    insertados = 0
    for pid in persona_ids:
        part_id = str(uuid.uuid4())
        res = await session.execute(
            text(
                """
                INSERT INTO formacion_participaciones (id, tenant_id, accion_id, persona_id, enviado_en)
                VALUES (:id, :t, :aid, :pid, :env)
                ON CONFLICT (accion_id, persona_id) DO NOTHING
                """
            ),
            {"id": part_id, "t": tenant_id, "aid": accion_id, "pid": pid, "env": ahora},
        )
        if res.rowcount > 0:
            insertados += 1

    return insertados


async def listar_participaciones_accion(
    session: AsyncSession, tenant_id: str, user_id: str, accion_id: str
) -> list[dict[str, Any]]:
    """Lista las participaciones de una acción formativa."""
    await _fijar_rls(session, tenant_id, user_id)
    rows = (
        await session.execute(
            text(
                """
                SELECT id, tenant_id, accion_id, persona_id, enviado_en, iniciado_en, terminado_en, nota, diploma_sha256
                FROM formacion_participaciones
                WHERE accion_id = :aid AND tenant_id = :t
                ORDER BY enviado_en ASC
                """
            ),
            {"aid": accion_id, "t": tenant_id},
        )
    ).mappings().all()

    return [
        {
            "id": str(r["id"]),
            "persona_id": r["persona_id"],
            "enviado_en": r["enviado_en"].isoformat() if hasattr(r["enviado_en"], "isoformat") else str(r["enviado_en"]),
            "iniciado_en": r["iniciado_en"].isoformat() if r["iniciado_en"] and hasattr(r["iniciado_en"], "isoformat") else r["iniciado_en"],
            "terminado_en": r["terminado_en"].isoformat() if r["terminado_en"] and hasattr(r["terminado_en"], "isoformat") else r["terminado_en"],
            "nota": float(r["nota"]) if r["nota"] is not None else None,
            "diploma_sha256": r["diploma_sha256"],
        }
        for r in rows
    ]
