"""Objeciones del DPO a las respuestas del diagnóstico (DIAG-07). ¤diagnostico ¤dpo-independencia

El DPO objeta una respuesta con un motivo antes de sellar; la objeción queda abierta (resuelta_en nulo)
hasta que el respondiente vuelve a guardar esa pregunta. Solo hay una objeción abierta por pregunta y no
se sella con ninguna abierta (R2 y R3). El historial se conserva: nada se borra.
"""
from typing import Any
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.audit import registrar_evento
from app_core.db.session import fijar_contexto_rls
from app_core.errors import ErrorNegocio
from features.diagnostico.services.asignacion_engine import listar_asignaciones
from features.diagnostico.services.respuestas_engine import listar_respuestas
from features.diagnostico.services.resultados_engine import nivel_sellado_y_verificacion, politica_evidencia
from features.diagnostico.domain.errores import (
    OBJECION_DUPLICADA,
    OBJECIONES_ABIERTAS,
    RESPUESTA_FUERA_DE_ASIGNACION,
)

LONGITUD_MINIMA_MOTIVO = 20


def clave_candado_sello(tenant_id: str) -> str:
    """Clave del candado advisory del sello: una organización tiene un solo diagnóstico (prueba y real)."""
    return f"diagnostico_resultados:{tenant_id}"


async def _serializar_con_el_sello(session: AsyncSession, tenant_id: str) -> None:
    """Toma el mismo candado que el sellado (resultados_engine): objetar y sellar no se cruzan."""
    await session.execute(
        text("SELECT pg_advisory_xact_lock(hashtext(:clave))"),
        {"clave": clave_candado_sello(tenant_id)},
    )


async def crear_objecion(
    session: AsyncSession, tenant_id: str, user_id: str, pregunta_id: int, motivo: str
) -> dict[str, Any]:
    """Abre la objeción; 409 si la pregunta ya tiene una abierta."""
    await fijar_contexto_rls(session, tenant_id, user_id)
    await _serializar_con_el_sello(session, tenant_id)
    abierta = (await session.execute(
        text(
            "SELECT 1 FROM diagnostico_objeciones "
            "WHERE tenant_id = :tenant_id AND pregunta_id = :pregunta_id AND resuelta_en IS NULL"
        ),
        {"tenant_id": tenant_id, "pregunta_id": pregunta_id},
    )).first()
    if abierta:
        raise ErrorNegocio(OBJECION_DUPLICADA)
    fila = (await session.execute(
        text(
            "INSERT INTO diagnostico_objeciones (id, tenant_id, pregunta_id, motivo, objetado_por) "
            "VALUES (:id, :tenant_id, :pregunta_id, :motivo, :objetado_por) "
            "RETURNING id, pregunta_id, motivo, objetado_por, objetado_en, resuelta_en"
        ),
        {
            "id": str(uuid4()), "tenant_id": tenant_id, "pregunta_id": pregunta_id,
            "motivo": motivo.strip(), "objetado_por": user_id,
        },
    )).mappings().one()
    await registrar_evento(
        session, tenant_id, "diagnostico_objecion", str(pregunta_id), "abierta",
        user_id=user_id, payload={"pregunta_id": pregunta_id},
    )
    return dict(fila)


async def listar_objeciones(
    session: AsyncSession, tenant_id: str, user_id: str, solo_abiertas: bool = False
) -> list[dict[str, Any]]:
    """Objeciones de la organización, la más reciente primero."""
    await fijar_contexto_rls(session, tenant_id, user_id)
    filas = (await session.execute(
        text(
            "SELECT id, pregunta_id, motivo, objetado_por, objetado_en, resuelta_en FROM diagnostico_objeciones "
            "WHERE tenant_id = :tenant_id AND (NOT :solo_abiertas OR resuelta_en IS NULL) "
            "ORDER BY objetado_en DESC, id DESC"
        ),
        {"tenant_id": tenant_id, "solo_abiertas": solo_abiertas},
    )).mappings().all()
    return [dict(fila) for fila in filas]


async def resolver_por_guardado(
    session: AsyncSession, tenant_id: str, user_id: str, preguntas: list[int]
) -> list[int]:
    """Cierra las objeciones abiertas de las preguntas guardadas; devuelve las preguntas resueltas (R2)."""
    await fijar_contexto_rls(session, tenant_id, user_id)
    resueltas: list[int] = []
    for pregunta_id in sorted(set(preguntas)):
        cerradas = (await session.execute(
            text(
                "UPDATE diagnostico_objeciones SET resuelta_en = now() "
                "WHERE tenant_id = :tenant_id AND pregunta_id = :pregunta_id AND resuelta_en IS NULL "
                "RETURNING id"
            ),
            {"tenant_id": tenant_id, "pregunta_id": pregunta_id},
        )).all()
        if cerradas:
            resueltas.append(pregunta_id)
            await registrar_evento(
                session, tenant_id, "diagnostico_objecion", str(pregunta_id), "resuelta",
                user_id=user_id, payload={"pregunta_id": pregunta_id},
            )
    return resueltas


async def exigir_sin_objeciones_abiertas(session: AsyncSession, tenant_id: str, user_id: str) -> None:
    """R3: no se sella con una objeción abierta (409).

    Toma el candado del sellado y lo conserva hasta el final de la transacción: llamada desde el mismo
    manejador que sella, ninguna objeción se abre entre la comprobación y el sello.
    """
    await fijar_contexto_rls(session, tenant_id, user_id)
    await _serializar_con_el_sello(session, tenant_id)
    if await listar_objeciones(session, tenant_id, user_id, solo_abiertas=True):
        raise ErrorNegocio(OBJECIONES_ABIERTAS)


# --- Quién escribe (R1) -------------------------------------------------------------------------
ROL_ADMINISTRADOR = "admin_organizacion"
ROL_QUE_NO_RESPONDE = "dpo"


async def exigir_puede_escribir(
    session: AsyncSession, tenant_id: str, user_id: str, rol: str, dimensiones: set[str]
) -> None:
    """R1: el administrador escribe en todas las dimensiones; el encargado vigente, solo en las suyas.

    El lote es todo o nada: si una sola dimensión no le corresponde, no se guarda ninguna (403). El `dpo`
    nunca escribe, aunque figure como encargado (ORG-13 lo impide; aquí se cierra por defensa).
    """
    if rol == ROL_QUE_NO_RESPONDE:
        raise ErrorNegocio(RESPUESTA_FUERA_DE_ASIGNACION)
    if rol == ROL_ADMINISTRADOR:
        return
    propias = {
        fila["dimension"]
        for fila in await listar_asignaciones(session, tenant_id, user_id)
        if fila["responsable_user_id"] == user_id
    }
    if not dimensiones <= propias:
        raise ErrorNegocio(RESPUESTA_FUERA_DE_ASIGNACION)


# --- Revisión del DPO (grilla declarado / calculado) --------------------------------------------

async def filas_de_revision(
    session: AsyncSession, tenant_id: str, user_id: str, controles_con_documento: set[int]
) -> list[dict[str, Any]]:
    """Por pregunta guardada: lo declarado y el nivel de evidencia que el sello calcularía hoy (R3).

    El nivel calculado sale de la misma regla del sellado (`nivel_sellado_y_verificacion`) con la
    política vigente; es de solo lectura: nadie lo edita.
    """
    politica = politica_evidencia()
    filas = []
    for r in await listar_respuestas(session, tenant_id, user_id):
        con_documento = int(r["pregunta_id"]) in controles_con_documento
        nivel, _ = nivel_sellado_y_verificacion(int(r["nivel_evidencia"]), con_documento, politica)
        filas.append({
            "pregunta_id": r["pregunta_id"],
            "control": r["control"],
            "dimension": r["dimension"],
            "estado": r["estado"],
            "nivel_asignado": r.get("nivel_asignado"),
            "nivel_evidencia": r["nivel_evidencia"],
            "no_aplica": bool(r.get("no_aplica")),
            "justificacion_no_aplica": r.get("justificacion_no_aplica"),
            "con_documento": con_documento,
            "nivel_calculado": nivel,
        })
    return sorted(filas, key=lambda f: f["pregunta_id"])
