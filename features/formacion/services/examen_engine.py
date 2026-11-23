# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤engine ¤evidencias ¤rbac-tenant
"""Motor de examen y calificación transaccional de participaciones (FOR-01)."""
from __future__ import annotations

import json
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.errors import ErrorNegocio
from app_core.pasillo import evidencias as pasillo_evidencias
from features.formacion.domain import errores as e
from features.formacion.services import diploma_engine


async def _fijar_rls(session: AsyncSession, tenant_id: str, user_id: str) -> None:
    await session.execute(
        text("SELECT set_config('app.current_tenant_id', :t, true)"),
        {"t": tenant_id},
    )
    await session.execute(
        text("SELECT set_config('app.current_user_id', :u, true)"),
        {"u": user_id},
    )


async def obtener_examen_participacion(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    participacion_id: str,
    persona_id: str,
) -> dict[str, Any]:
    """R5: Obtiene las preguntas del examen SIN el campo 'correcta'."""
    await _fijar_rls(session, tenant_id, user_id)

    row = (
        await session.execute(
            text(
                """
                SELECT p.id, p.persona_id, p.iniciado_en, p.terminado_en,
                       a.id AS accion_id, a.nombre AS accion_nombre, a.contenido_id,
                       a.inicio, a.fin, a.nota_minima
                FROM formacion_participaciones p
                JOIN formacion_acciones a ON a.id = p.accion_id AND a.tenant_id = p.tenant_id
                WHERE p.id = :pid AND p.tenant_id = :t
                """
            ),
            {"pid": participacion_id, "t": tenant_id},
        )
    ).mappings().first()

    if not row:
        raise ValueError("Participación no encontrada.")

    # Validar que la persona coincida
    if str(row["persona_id"]).strip().lower() != str(persona_id).strip().lower():
        raise ErrorNegocio(e.PERSONA_NO_VINCULADA)

    # Obtener preguntas sin 'correcta'
    preguntas_rows = (
        await session.execute(
            text(
                """
                SELECT id, orden, enunciado, opciones
                FROM formacion_preguntas
                WHERE contenido_id = :cid AND tenant_id = :t
                ORDER BY orden ASC
                """
            ),
            {"cid": row["contenido_id"], "t": tenant_id},
        )
    ).mappings().all()

    preguntas = [
        {
            "id": str(pr["id"]),
            "orden": pr["orden"],
            "enunciado": pr["enunciado"],
            "opciones": pr["opciones"] if isinstance(pr["opciones"], list) else json.loads(pr["opciones"]),
        }
        for pr in preguntas_rows
    ]

    return {
        "accion": row["accion_nombre"],
        "nota_minima": float(row["nota_minima"]),
        "inicio": row["inicio"].isoformat() if hasattr(row["inicio"], "isoformat") else str(row["inicio"]),
        "fin": row["fin"].isoformat() if hasattr(row["fin"], "isoformat") else str(row["fin"]),
        "iniciado_en": row["iniciado_en"].isoformat() if row["iniciado_en"] and hasattr(row["iniciado_en"], "isoformat") else row["iniciado_en"],
        "terminado_en": row["terminado_en"].isoformat() if row["terminado_en"] and hasattr(row["terminado_en"], "isoformat") else row["terminado_en"],
        "preguntas": preguntas,
    }


async def iniciar_examen_participacion(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    participacion_id: str,
    persona_id: str,
) -> dict[str, Any]:
    """R7: Inicia el examen de forma idempotente dentro de las fechas de la acción."""
    await _fijar_rls(session, tenant_id, user_id)

    row = (
        await session.execute(
            text(
                """
                SELECT p.id, p.persona_id, p.iniciado_en, p.terminado_en,
                       a.inicio, a.fin
                FROM formacion_participaciones p
                JOIN formacion_acciones a ON a.id = p.accion_id AND a.tenant_id = p.tenant_id
                WHERE p.id = :pid AND p.tenant_id = :t
                """
            ),
            {"pid": participacion_id, "t": tenant_id},
        )
    ).mappings().first()

    if not row:
        raise ValueError("Participación no encontrada.")

    if str(row["persona_id"]).strip().lower() != str(persona_id).strip().lower():
        raise ErrorNegocio(e.PERSONA_NO_VINCULADA)

    if row["terminado_en"] is not None:
        raise ErrorNegocio(e.EXAMEN_YA_RENDIDO)

    # Si ya estaba iniciado, retornar el mismo iniciado_en (idempotente)
    if row["iniciado_en"] is not None:
        iniciado_val = row["iniciado_en"]
        return {
            "iniciado_en": iniciado_val.isoformat() if hasattr(iniciado_val, "isoformat") else str(iniciado_val)
        }

    # Validar fechas
    hoy = date.today()
    inicio_fecha = row["inicio"] if isinstance(row["inicio"], date) else date.fromisoformat(str(row["inicio"]))
    fin_fecha = row["fin"] if isinstance(row["fin"], date) else date.fromisoformat(str(row["fin"]))
    if not (inicio_fecha <= hoy <= fin_fecha):
        raise ErrorNegocio(e.ACCION_FUERA_DE_FECHAS)

    ahora = datetime.now(timezone.utc)
    await session.execute(
        text(
            """
            UPDATE formacion_participaciones
            SET iniciado_en = :ini
            WHERE id = :pid AND tenant_id = :t AND iniciado_en IS NULL
            """
        ),
        {"ini": ahora, "pid": participacion_id, "t": tenant_id},
    )

    return {"iniciado_en": ahora.isoformat()}


async def calificar_y_terminar_examen(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    participacion_id: str,
    persona_id: str,
    respuestas: list[int],
) -> dict[str, Any]:
    """R4: Califica y termina el examen en una sola transacción."""
    await _fijar_rls(session, tenant_id, user_id)

    row = (
        await session.execute(
            text(
                """
                SELECT p.id, p.persona_id, p.iniciado_en, p.terminado_en,
                       a.id AS accion_id, a.nombre AS accion_nombre, a.contenido_id,
                       a.inicio, a.fin, a.nota_minima
                FROM formacion_participaciones p
                JOIN formacion_acciones a ON a.id = p.accion_id AND a.tenant_id = p.tenant_id
                WHERE p.id = :pid AND p.tenant_id = :t
                """
            ),
            {"pid": participacion_id, "t": tenant_id},
        )
    ).mappings().first()

    if not row:
        raise ValueError("Participación no encontrada.")

    if str(row["persona_id"]).strip().lower() != str(persona_id).strip().lower():
        raise ErrorNegocio(e.PERSONA_NO_VINCULADA)

    if row["terminado_en"] is not None:
        raise ErrorNegocio(e.EXAMEN_YA_RENDIDO)

    if row["iniciado_en"] is None:
        raise ErrorNegocio(e.EXAMEN_NO_INICIADO)

    hoy = date.today()
    inicio_fecha = row["inicio"] if isinstance(row["inicio"], date) else date.fromisoformat(str(row["inicio"]))
    fin_fecha = row["fin"] if isinstance(row["fin"], date) else date.fromisoformat(str(row["fin"]))
    if not (inicio_fecha <= hoy <= fin_fecha):
        raise ErrorNegocio(e.ACCION_FUERA_DE_FECHAS)

    # 1. Obtener preguntas con su respuesta correcta
    preguntas_rows = (
        await session.execute(
            text(
                """
                SELECT id, orden, enunciado, opciones, correcta
                FROM formacion_preguntas
                WHERE contenido_id = :cid AND tenant_id = :t
                ORDER BY orden ASC
                """
            ),
            {"cid": row["contenido_id"], "t": tenant_id},
        )
    ).mappings().all()

    if not preguntas_rows:
        raise ErrorNegocio(e.CONTENIDO_SIN_PREGUNTAS)

    if len(respuestas) != len(preguntas_rows):
        raise ErrorNegocio(e.RESPUESTAS_INCOMPLETAS)

    for i, pr in enumerate(preguntas_rows):
        ops = pr["opciones"] if isinstance(pr["opciones"], list) else json.loads(pr["opciones"])
        if not (0 <= respuestas[i] < len(ops)):
            raise ErrorNegocio(e.RESPUESTAS_INCOMPLETAS)

    # 2. Calificar según R1
    correctas = sum(1 for i, pr in enumerate(preguntas_rows) if respuestas[i] == pr["correcta"])
    total = len(preguntas_rows)
    nota = round(100.0 * correctas / total, 1)
    aprobado = nota >= float(row["nota_minima"])

    diploma_sha256 = None
    if aprobado:
        # 3. Generar y custodiar constancia (R2)
        ahora_iso = datetime.now(timezone.utc).isoformat()
        contenido_constancia = diploma_engine.generar_contenido_constancia(
            persona_id=persona_id,
            accion_nombre=row["accion_nombre"],
            nota=nota,
            fecha_iso=ahora_iso,
        )

        res_custodia = await pasillo_evidencias.custodiar_documento_generado(
            session=session,
            tenant_id=tenant_id,
            user_id=user_id,
            contenido=contenido_constancia,
            tipo_mime="text/plain",
            tipo_evidencia="capacitacion",
            control_refs=["P73"],
            nombre=f"constancia_{persona_id}_{row['accion_id']}.txt",
        )
        diploma_sha256 = res_custodia["sha256"]

    # 4. Transaccional: UPDATE … WHERE terminado_en IS NULL (R4)
    ahora_term = datetime.now(timezone.utc)
    res_update = await session.execute(
        text(
            """
            UPDATE formacion_participaciones
            SET terminado_en = :term,
                nota = :nota,
                diploma_sha256 = :sha
            WHERE id = :pid AND tenant_id = :t AND terminado_en IS NULL
            RETURNING id
            """
        ),
        {
            "term": ahora_term,
            "nota": nota,
            "sha": diploma_sha256,
            "pid": participacion_id,
            "t": tenant_id,
        },
    )

    if res_update.scalar_one_or_none() is None:
        raise ErrorNegocio(e.EXAMEN_YA_RENDIDO)

    return {
        "nota": nota,
        "aprobado": aprobado,
        "diploma_sha256": diploma_sha256,
    }
