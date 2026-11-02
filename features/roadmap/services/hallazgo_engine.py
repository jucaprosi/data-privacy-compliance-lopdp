# ¤roadmap ¤hallazgos ¤rbac-tenant
"""Motor de hallazgos (RM-21): registrar hallazgos con origen y convertirlos en tareas del plan único.

Reglas (governance/especificaciones/RM-21.md §3):
- R1 compuerta única: solo esta sala inserta en `hallazgos` y crea tareas correctoras.
- R2/R3 productor diagnóstico: brechas CRÍTICAS del último resultado sellado, clave `<resultado_id>:P<n>`.
- R4 conversión transaccional: una tarea por hallazgo, con `hallazgo_id`; el hallazgo pasa a `en_tratamiento`.
- R6 auditoría en `audit_events` por cada hallazgo registrado o convertido.
Cada consulta fija `app.current_tenant_id` (RLS) y además filtra por `tenant_id`.
"""
from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import bindparam, text
from sqlalchemy.ext.asyncio import AsyncSession

from api.errores import ErrorNegocio
from app_core.audit import registrar_evento
from app_core.errors import CodigoErrorNegocio
from features.diagnostico import diagnostico_service
from features.roadmap.domain.hallazgo import (
    DIMENSION_POR_DEFECTO,
    MOTIVO_YA_CONVERTIDO,
    EstadoHallazgo,
    Hallazgo,
    OrigenHallazgo,
    ResultadoConversion,
    ResultadoRegistro,
    SeveridadHallazgo,
    origen_ref_diagnostico,
    validar_hallazgo,
)
from features.roadmap.services.contexto_tenant import set_session_context

# Códigos de negocio de RM-21 (mismo patrón que tarea_edicion_engine: el catálogo central no es de esta tarea).
DIAG_SIN_RESULTADO = CodigoErrorNegocio(
    codigo="DIAG_SIN_RESULTADO",
    status_code=404,
    mensaje_defecto="La organización no tiene ningún resultado sellado del diagnóstico.",
    action_required="sellar_diagnostico",
)
HALLAZGO_NO_ENCONTRADO = CodigoErrorNegocio(
    codigo="HALLAZGO_NO_ENCONTRADO",
    status_code=404,
    mensaje_defecto="Algún hallazgo pedido no existe en la organización.",
)
ROADMAP_NO_ENCONTRADO = CodigoErrorNegocio(
    codigo="ROADMAP_NO_ENCONTRADO",
    status_code=404,
    mensaje_defecto="La hoja de ruta o la ola no existen en la organización.",
)
HALLAZGO_CERRADO = CodigoErrorNegocio(
    codigo="HALLAZGO_CERRADO",
    status_code=409,
    mensaje_defecto="Algún hallazgo pedido está cerrado y no se convierte.",
)
HALLAZGO_SIN_CONTROL = CodigoErrorNegocio(
    codigo="HALLAZGO_SIN_CONTROL",
    status_code=409,
    mensaje_defecto="Algún hallazgo pedido no tiene control P1-P80 y la tarea lo exige.",
)

_COLUMNAS = (
    "h.id, h.origen, h.origen_ref, h.control_ref, h.dimension, h.severidad, h.titulo, "
    "h.descripcion, h.estado, h.creado_en, t.id AS tarea_id"
)


def _fila_a_hallazgo(fila) -> Hallazgo:
    return Hallazgo(
        id=fila["id"],
        origen=fila["origen"],
        origen_ref=fila["origen_ref"],
        control_ref=fila["control_ref"],
        dimension=fila["dimension"],
        severidad=fila["severidad"],
        titulo=fila["titulo"],
        descripcion=fila["descripcion"],
        estado=fila["estado"],
        tarea_id=fila["tarea_id"],
        creado_en=fila["creado_en"],
    )


async def registrar_hallazgo(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    origen: str,
    origen_ref: str,
    severidad: str,
    titulo: str,
    control_ref: Optional[str] = None,
    dimension: Optional[str] = None,
    descripcion: Optional[str] = None,
) -> tuple[str, bool]:
    """Registra un hallazgo; si el mismo hecho (origen, origen_ref) ya existe, devuelve el suyo sin crear."""
    validar_hallazgo(origen, origen_ref, severidad, titulo, control_ref, dimension)
    await set_session_context(session, tenant_id, user_id)
    nuevo_id = str(uuid.uuid4())
    insertado = (
        await session.execute(
            text(
                "INSERT INTO hallazgos (id, tenant_id, origen, origen_ref, control_ref, dimension, "
                "severidad, titulo, descripcion, creado_por) VALUES (:id, :t, :origen, :ref, :control, "
                ":dimension, :severidad, :titulo, :descripcion, :u) "
                "ON CONFLICT (tenant_id, origen, origen_ref) DO NOTHING RETURNING id"
            ),
            {
                "id": nuevo_id,
                "t": tenant_id,
                "origen": origen,
                "ref": origen_ref,
                "control": control_ref,
                "dimension": dimension,
                "severidad": severidad,
                "titulo": titulo,
                "descripcion": descripcion,
                "u": user_id,
            },
        )
    ).scalar()
    if insertado is None:
        existente = (
            await session.execute(
                text("SELECT id FROM hallazgos WHERE tenant_id = :t AND origen = :origen AND origen_ref = :ref"),
                {"t": tenant_id, "origen": origen, "ref": origen_ref},
            )
        ).scalar_one()
        return existente, False
    await registrar_evento(
        session, tenant_id, "hallazgo", nuevo_id, "registrado", user_id,
        {"origen": origen, "origen_ref": origen_ref},
    )
    return nuevo_id, True


async def registrar_desde_diagnostico(session: AsyncSession, tenant_id: str, user_id: str) -> ResultadoRegistro:
    """Primer productor (R2): las brechas críticas del resultado sellado de mayor secuencia.

    Se agregan solo las respuestas evaluadas del resultado sellado, con el nivel asignado, el nivel de
    evidencia sellado y la criticidad del banco que guarda el propio resultado: un control sin respuesta es falta
    de cobertura, no un hallazgo de madurez (dimensiones_sgpdp, «el dato faltante no es un hallazgo»).
    """
    resultados = await diagnostico_service.listar_resultados(session, tenant_id, user_id)
    if not resultados:
        raise ErrorNegocio(DIAG_SIN_RESULTADO)
    ultimo = max(resultados, key=lambda r: r.secuencia)
    # Un sellado anterior a la escala no trae nivel asignado: se deriva del estado solo al leerlo.
    anterior = diagnostico_service.es_resultado_anterior(ultimo.indicadores)
    pendiente = diagnostico_service.EstadoCumplimiento.PENDIENTE.value
    entradas = [
        diagnostico_service.respuesta_control_desde_fila(r, anterior=anterior)
        for r in ultimo.respuestas
        if r.nivel_asignado is not None or (anterior and r.estado != pendiente)
    ]
    evaluacion = diagnostico_service.evaluar_assessment_por_dimension(entradas)
    resultado = ResultadoRegistro()
    for brecha in evaluacion.brechas:
        if brecha.severidad != diagnostico_service.SeveridadBrecha.CRITICO:
            continue
        _, creado = await registrar_hallazgo(
            session,
            tenant_id,
            user_id,
            origen=OrigenHallazgo.diagnostico.value,
            origen_ref=origen_ref_diagnostico(ultimo.id, brecha.pregunta_id),
            severidad=SeveridadHallazgo.critica.value,
            titulo=f"P{brecha.pregunta_id} · {brecha.control}"[:200],
            control_ref=f"P{brecha.pregunta_id}",
            dimension=brecha.dimension_id,
            descripcion=(
                f"Brecha crítica del diagnóstico sellado n.º {ultimo.secuencia}: riesgo {brecha.riesgo} "
                f"con nivel efectivo {brecha.nivel_efectivo} en {brecha.dimension_nombre}."
            ),
        )
        if creado:
            resultado.creados += 1
        else:
            resultado.existentes += 1
    return resultado


async def listar_hallazgos(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    estado: Optional[str] = None,
    origen: Optional[str] = None,
) -> list[Hallazgo]:
    """Hallazgos de la organización, por severidad (crítica, alta, media) y del más reciente al más antiguo."""
    await set_session_context(session, tenant_id, user_id)
    params = {
        "t": tenant_id,
        "estado": EstadoHallazgo(estado).value if estado is not None else None,
        "origen": OrigenHallazgo(origen).value if origen is not None else None,
    }
    filas = await session.execute(
        text(
            f"SELECT {_COLUMNAS} FROM hallazgos h "
            "LEFT JOIN roadmap_tasks t ON t.hallazgo_id = h.id AND t.tenant_id = h.tenant_id "
            "WHERE h.tenant_id = :t "
            "AND (CAST(:estado AS VARCHAR) IS NULL OR h.estado = CAST(:estado AS VARCHAR)) "
            "AND (CAST(:origen AS VARCHAR) IS NULL OR h.origen = CAST(:origen AS VARCHAR)) "
            "ORDER BY CASE h.severidad WHEN 'critica' THEN 0 WHEN 'alta' THEN 1 ELSE 2 END, h.creado_en DESC, h.id"
        ),
        params,
    )
    return [_fila_a_hallazgo(f) for f in filas.mappings().all()]


async def crear_tareas_desde_hallazgos(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    roadmap_id: str,
    wave_id: str,
    hallazgo_ids: list[str],
) -> ResultadoConversion:
    """Convierte hallazgos en tareas de `wave_id` (R4). Valida todo antes de escribir: todos o ninguno."""
    await set_session_context(session, tenant_id, user_id)
    ola = (
        await session.execute(
            text(
                "SELECT w.id FROM roadmap_waves w JOIN roadmaps r ON r.id = w.roadmap_id "
                "WHERE w.id = :w AND w.roadmap_id = :r AND w.tenant_id = :t AND r.tenant_id = :t"
            ),
            {"w": wave_id, "r": roadmap_id, "t": tenant_id},
        )
    ).scalar()
    if ola is None:
        raise ErrorNegocio(ROADMAP_NO_ENCONTRADO)

    pedidos = list(dict.fromkeys(hallazgo_ids))
    # FOR UPDATE OF h serializa conversiones simultáneas del mismo hallazgo; el índice único parcial
    # ux_roadmap_tasks_hallazgo es la segunda barrera.
    filas = (
        await session.execute(
            text(
                f"SELECT {_COLUMNAS} FROM hallazgos h "
                "LEFT JOIN roadmap_tasks t ON t.hallazgo_id = h.id AND t.tenant_id = h.tenant_id "
                "WHERE h.tenant_id = :t AND h.id IN :ids FOR UPDATE OF h"
            ).bindparams(bindparam("ids", expanding=True)),
            {"t": tenant_id, "ids": pedidos},
        )
    ).mappings().all()
    por_id = {f["id"]: _fila_a_hallazgo(f) for f in filas}
    if set(pedidos) - set(por_id):
        raise ErrorNegocio(HALLAZGO_NO_ENCONTRADO)
    if any(h.estado == EstadoHallazgo.cerrado.value for h in por_id.values()):
        raise ErrorNegocio(HALLAZGO_CERRADO)
    if any(h.tarea_id is None and h.control_ref is None for h in por_id.values()):
        raise ErrorNegocio(HALLAZGO_SIN_CONTROL)

    resultado = ResultadoConversion()
    for hallazgo_id in pedidos:
        h = por_id[hallazgo_id]
        if h.tarea_id is not None:
            resultado.omitidos.append({"hallazgo_id": h.id, "motivo": MOTIVO_YA_CONVERTIDO})
            continue
        tarea_id = str(uuid.uuid4())
        await session.execute(
            text(
                "INSERT INTO roadmap_tasks (id, wave_id, tenant_id, control_ref, dimension, title, "
                "description, priority, status, hallazgo_id) VALUES (:id, :w, :t, :control, :dimension, "
                ":titulo, :descripcion, :prioridad, 'pendiente', :h)"
            ),
            {
                "id": tarea_id,
                "w": wave_id,
                "t": tenant_id,
                "control": h.control_ref,
                "dimension": h.dimension or DIMENSION_POR_DEFECTO,
                "titulo": h.titulo,
                "descripcion": h.descripcion,
                "prioridad": h.severidad,
                "h": h.id,
            },
        )
        await session.execute(
            text(
                "UPDATE hallazgos SET estado = 'en_tratamiento', actualizado_en = now() "
                "WHERE id = :h AND tenant_id = :t"
            ),
            {"h": h.id, "t": tenant_id},
        )
        await registrar_evento(
            session, tenant_id, "hallazgo", h.id, "convertido", user_id,
            {"origen": h.origen, "origen_ref": h.origen_ref, "tarea_id": tarea_id},
        )
        resultado.tareas.append({"tarea_id": tarea_id, "hallazgo_id": h.id})
    return resultado
