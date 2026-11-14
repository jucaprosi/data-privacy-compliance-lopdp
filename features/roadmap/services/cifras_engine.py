# ¤roadmap ¤arbitro ¤adpa
"""Las cifras de la Hoja de Ruta las calcula código determinista, no el modelo de lenguaje (RM-26).

`cifrar_plan` es una función pura: no lee el reloj (la fecha entra como argumento), no usa números
aleatorios, no consulta la base, no llama a ningún modelo y no escribe nada. La proyección del puntaje
trabaja sobre copias; la madurez acreditada de la organización no cambia (DIAG-12).
"""
from __future__ import annotations

import calendar
from datetime import date, timedelta
from typing import Any

# --- INICIO ADPA-04 ---
from app_core.pasillo import diagnostico as pasillo_diagnostico
# --- FIN ADPA-04 ---
from features.roadmap.domain.esfuerzo_controles import (
    HORAS_POR_PRIORIDAD,
    NIVEL_PROYECTADO,
    ORDEN_OLAS,
    ControlCifrado,
    OlaCifrada,
    PlanCifrado,
    prioridad_de_nivel,
)


def _sumar_meses(desde: date, meses: int) -> date:
    indice = desde.month - 1 + meses
    anio, mes = desde.year + indice // 12, indice % 12 + 1
    return date(anio, mes, min(desde.day, calendar.monthrange(anio, mes)[1]))


def _controles_con_tarea(contexto: dict[str, Any]) -> list[ControlCifrado]:
    controles = []
    for fila in contexto.get("respuestas_diagnostico", []):
        nivel = fila.get("nivel_asignado")
        prioridad = prioridad_de_nivel(nivel)
        if prioridad is not None:
            controles.append(ControlCifrado(str(fila["codigo"]), int(nivel), prioridad, HORAS_POR_PRIORIDAD[prioridad]))
    return sorted(controles, key=lambda c: c.control_ref)


def _score(contexto: dict[str, Any], refs_proyectados: frozenset[str]) -> tuple[Any, ...]:
    """Resultado por dimensión que devuelve el diagnóstico (por su compuerta) sobre una proyección; sin cifra global."""
    respuestas = []
    for fila in contexto.get("respuestas_diagnostico", []):
        copia = dict(fila)  # la proyección nunca toca el contexto
        if str(copia["codigo"]) in refs_proyectados:
            copia["nivel_asignado"] = NIVEL_PROYECTADO
        respuestas.append(
            pasillo_diagnostico.respuesta_control_desde_fila(
                copia, dimension_id=copia.get("dimension"), control=copia.get("control", "")
            )
        )
    return tuple(pasillo_diagnostico.evaluar_assessment_por_dimension(respuestas).dimensiones)


def cifrar_plan(contexto: dict[str, Any], variables: Any, hoy: date) -> PlanCifrado:
    """Olas, prioridades, horas, fechas y `score_objetivo` del plan, con el mismo resultado para la misma entrada."""
    controles = _controles_con_tarea(contexto)
    score = _score(contexto, frozenset(c.control_ref for c in controles))
    if not controles:
        return PlanCifrado(olas=(), score_objetivo=score)

    fin_plazo = _sumar_meses(hoy, int(variables.plazo_meses))
    dias_totales = (fin_plazo - hoy).days
    grupos = [(p, tuple(c for c in controles if c.prioridad == p)) for p in ORDEN_OLAS]
    grupos = [(p, cs) for p, cs in grupos if cs]
    horas_totales = sum(c.horas for _, cs in grupos for c in cs)

    olas, acumuladas, inicio = [], 0, hoy
    for i, (prioridad, cs) in enumerate(grupos):
        horas = sum(c.horas for c in cs)
        acumuladas += horas
        ultima = i == len(grupos) - 1
        fin = fin_plazo if ultima else hoy + timedelta(days=round(dias_totales * acumuladas / horas_totales))
        olas.append(OlaCifrada(prioridad=prioridad, controles=cs, horas=horas, inicio=inicio, fin=fin))
        inicio = fin
    return PlanCifrado(olas=tuple(olas), score_objetivo=score)
