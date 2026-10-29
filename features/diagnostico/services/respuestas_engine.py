"""Respuestas del diagnóstico guardadas por organización (DIAG-01).

El servidor es la fuente de verdad: lo que una persona responde lo ve el resto de su organización
y lo usa la generación de la hoja de ruta. Cada consulta fija el contexto RLS y filtra por
tenant_id; la política de la tabla lo exige además en la base.
"""
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.audit import registrar_evento
from app_core.db.session import fijar_contexto_rls
from features.diagnostico.domain.models import (
    NIVEL_ASIGNADO_MAX,
    NIVEL_ASIGNADO_MIN,
    NIVEL_EVIDENCIA_MAX,
    NIVEL_EVIDENCIA_MIN,
    estado_desde_nivel_asignado,
)

DIMENSIONES_VALIDAS = frozenset(f"D{i:02d}" for i in range(1, 11))

_COLUMNAS = (
    "pregunta_id, control, dimension, estado, nivel_asignado, nivel_evidencia, criticidad, es_critica, "
    "riesgo_base, respondido_por, actualizado_en"
)


class RespuestaFueraDeCatalogo(ValueError):
    """Dimensión fuera de D01-D10, control sin nombre o nivel fuera de la escala SMARTCIDI."""


async def listar_respuestas(session: AsyncSession, tenant_id: str, user_id: str) -> list[dict[str, Any]]:
    await fijar_contexto_rls(session, tenant_id, user_id)
    result = await session.execute(
        text(f"SELECT {_COLUMNAS} FROM diagnostico_respuestas WHERE tenant_id = :tenant_id ORDER BY pregunta_id"),
        {"tenant_id": tenant_id},
    )
    return [dict(row) for row in result.mappings().all()]


async def guardar_respuestas(
    session: AsyncSession, tenant_id: str, user_id: str, respuestas: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Guarda (inserta o reemplaza) las respuestas enviadas y devuelve las de la organización.

    Todo o nada: si una respuesta está fuera de catálogo o de escala no se guarda ninguna. El
    estado de conformidad no es una entrada: se deriva aquí del nivel asignado (DIAG-08). Un solo
    evento de auditoría por guardado, con las preguntas afectadas.
    """
    for respuesta in respuestas:
        if respuesta["dimension"] not in DIMENSIONES_VALIDAS or not respuesta["control"].strip():
            raise RespuestaFueraDeCatalogo(
                f"La pregunta {respuesta['pregunta_id']} tiene una dimensión fuera de D01-D10 o un control sin nombre"
            )
        if not NIVEL_ASIGNADO_MIN <= respuesta["nivel_asignado"] <= NIVEL_ASIGNADO_MAX:
            raise RespuestaFueraDeCatalogo(f"La pregunta {respuesta['pregunta_id']} tiene un nivel asignado fuera de 1 a 5")
        if not NIVEL_EVIDENCIA_MIN <= respuesta["nivel_evidencia"] <= NIVEL_EVIDENCIA_MAX:
            raise RespuestaFueraDeCatalogo(f"La pregunta {respuesta['pregunta_id']} tiene un nivel de evidencia fuera de 0 a 4")
    await fijar_contexto_rls(session, tenant_id, user_id)
    ahora = datetime.now(timezone.utc)
    for respuesta in respuestas:
        await session.execute(
            text(
                f"""
                INSERT INTO diagnostico_respuestas (tenant_id, {_COLUMNAS})
                VALUES (:tenant_id, :pregunta_id, :control, :dimension, :estado, :nivel_asignado, :nivel_evidencia,
                        :criticidad, :es_critica, :riesgo_base, :respondido_por, :actualizado_en)
                ON CONFLICT (tenant_id, pregunta_id) DO UPDATE SET
                  control = EXCLUDED.control, dimension = EXCLUDED.dimension,
                  estado = EXCLUDED.estado, nivel_asignado = EXCLUDED.nivel_asignado,
                  nivel_evidencia = EXCLUDED.nivel_evidencia,
                  criticidad = EXCLUDED.criticidad, es_critica = EXCLUDED.es_critica,
                  riesgo_base = EXCLUDED.riesgo_base, respondido_por = EXCLUDED.respondido_por,
                  actualizado_en = EXCLUDED.actualizado_en
                """
            ),
            {
                **respuesta,
                "estado": estado_desde_nivel_asignado(respuesta["nivel_asignado"]).value,
                "tenant_id": tenant_id,
                "respondido_por": user_id,
                "actualizado_en": ahora,
            },
        )
    if respuestas:
        await registrar_evento(
            session,
            tenant_id,
            "diagnostico_respuestas",
            tenant_id,
            "diagnostico_respuestas_guardadas",
            user_id,
            {"preguntas": sorted(r["pregunta_id"] for r in respuestas)},
        )
    return await listar_respuestas(session, tenant_id, user_id)
