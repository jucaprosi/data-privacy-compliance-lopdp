# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤engine ¤evidencias ¤rbac-tenant
"""Motor de gestión de contenidos y banco de preguntas de formación (FOR-01)."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
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


async def crear_contenido(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    *,
    titulo: str,
    tipo: str,
    referencia: str,
) -> dict[str, Any]:
    """Crea un contenido formativo (PDF o video)."""
    await _fijar_rls(session, tenant_id, user_id)

    titulo = (titulo or "").strip()
    referencia = (referencia or "").strip()
    if not titulo:
        raise ValueError("El título del contenido es obligatorio.")
    if tipo not in ("pdf", "video"):
        raise ValueError("El tipo debe ser 'pdf' o 'video'.")
    if not referencia:
        raise ValueError("La referencia es obligatoria.")

    cid = str(uuid.uuid4())
    creado_en = datetime.now(timezone.utc)
    await session.execute(
        text(
            """
            INSERT INTO formacion_contenidos (id, tenant_id, titulo, tipo, referencia, creado_por, creado_en)
            VALUES (:id, :t, :titulo, :tipo, :ref, :creado_por, :creado_en)
            """
        ),
        {
            "id": cid,
            "t": tenant_id,
            "titulo": titulo,
            "tipo": tipo,
            "ref": referencia,
            "creado_por": user_id,
            "creado_en": creado_en,
        },
    )

    return {
        "id": cid,
        "tenant_id": tenant_id,
        "titulo": titulo,
        "tipo": tipo,
        "referencia": referencia,
        "creado_por": user_id,
        "creado_en": creado_en.isoformat(),
    }


async def listar_contenidos(
    session: AsyncSession, tenant_id: str, user_id: str
) -> list[dict[str, Any]]:
    """Lista todos los contenidos formativos de la organización."""
    await _fijar_rls(session, tenant_id, user_id)
    rows = (
        await session.execute(
            text(
                """
                SELECT id, tenant_id, titulo, tipo, referencia, creado_por, creado_en
                FROM formacion_contenidos
                WHERE tenant_id = :t
                ORDER BY creado_en DESC
                """
            ),
            {"t": tenant_id},
        )
    ).mappings().all()

    return [
        {
            "id": str(r["id"]),
            "tenant_id": r["tenant_id"],
            "titulo": r["titulo"],
            "tipo": r["tipo"],
            "referencia": r["referencia"],
            "creado_por": r["creado_por"],
            "creado_en": r["creado_en"].isoformat() if hasattr(r["creado_en"], "isoformat") else str(r["creado_en"]),
        }
        for r in rows
    ]


async def crear_pregunta(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    *,
    contenido_id: str,
    enunciado: str,
    opciones: list[str],
    correcta: int,
) -> dict[str, Any]:
    """Crea una pregunta en el banco. R6: se congela si hay participaciones iniciadas."""
    await _fijar_rls(session, tenant_id, user_id)

    # R6: Banco congelado si alguna acción vinculada tiene participación iniciada
    iniciada = (
        await session.execute(
            text(
                """
                SELECT 1
                FROM formacion_participaciones p
                JOIN formacion_acciones a ON a.id = p.accion_id AND a.tenant_id = p.tenant_id
                WHERE a.contenido_id = :cid AND a.tenant_id = :t AND p.iniciado_en IS NOT NULL
                LIMIT 1
                """
            ),
            {"cid": contenido_id, "t": tenant_id},
        )
    ).scalar_one_or_none()

    if iniciada is not None:
        raise ErrorNegocio(e.PREGUNTAS_CONGELADAS)

    if not opciones or len(opciones) < 2 or len(opciones) > 6:
        raise ValueError("Las opciones deben ser entre 2 y 6.")
    if not (0 <= correcta < len(opciones)):
        raise ValueError(f"Índice de respuesta correcta inválido: {correcta}")

    # Asignar orden automáticamente
    max_orden = (
        await session.execute(
            text(
                "SELECT COALESCE(MAX(orden), -1) FROM formacion_preguntas WHERE contenido_id = :cid AND tenant_id = :t"
            ),
            {"cid": contenido_id, "t": tenant_id},
        )
    ).scalar() or -1
    nuevo_orden = max_orden + 1

    pid = str(uuid.uuid4())
    await session.execute(
        text(
            """
            INSERT INTO formacion_preguntas (id, tenant_id, contenido_id, orden, enunciado, opciones, correcta)
            VALUES (:id, :t, :cid, :orden, :enunciado, CAST(:opciones AS jsonb), :correcta)
            """
        ),
        {
            "id": pid,
            "t": tenant_id,
            "cid": contenido_id,
            "orden": nuevo_orden,
            "enunciado": enunciado.strip(),
            "opciones": json.dumps(opciones),
            "correcta": correcta,
        },
    )

    return {
        "id": pid,
        "orden": nuevo_orden,
        "enunciado": enunciado.strip(),
        "opciones": opciones,
        "correcta": correcta,
    }


async def listar_preguntas(
    session: AsyncSession, tenant_id: str, user_id: str, contenido_id: str
) -> list[dict[str, Any]]:
    """Lista las preguntas de un contenido con su respuesta correcta (solo roles que gestionan)."""
    await _fijar_rls(session, tenant_id, user_id)
    rows = (
        await session.execute(
            text(
                """
                SELECT id, orden, enunciado, opciones, correcta
                FROM formacion_preguntas
                WHERE contenido_id = :cid AND tenant_id = :t
                ORDER BY orden ASC
                """
            ),
            {"cid": contenido_id, "t": tenant_id},
        )
    ).mappings().all()

    return [
        {
            "id": str(r["id"]),
            "orden": r["orden"],
            "enunciado": r["enunciado"],
            "opciones": r["opciones"] if isinstance(r["opciones"], list) else json.loads(r["opciones"]),
            "correcta": r["correcta"],
        }
        for r in rows
    ]
