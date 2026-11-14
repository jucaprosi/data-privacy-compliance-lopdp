# ¤roadmap ¤arbitro
"""RM-26: las cifras de la Hoja de Ruta las calcula código determinista. Sin base de datos.

Mutaciones ejecutadas (cada una dejó la prueba en rojo y se restauró):
- cifras_engine: usar `date.today()` o `random` en cifrar_plan -> test_mismo_diagnostico_mismo_plan.
- esfuerzo_controles: cambiar PRIORIDAD_POR_NIVEL (p. ej. 2: "media") -> test_prioridad_y_horas_por_nivel.
- cifras_engine._score: devolver una media simple de niveles propia -> test_score_objetivo_usa_el_puntaje_del_diagnostico.
- cifras_engine._score: modificar `contexto` en lugar de la copia -> test_proyeccion_no_toca_la_madurez.
"""
from __future__ import annotations

import copy
import types
from datetime import date

from app_core.pasillo import diagnostico as pasillo_diagnostico
from features.roadmap import roadmap_service as sala

HOY = date(2026, 1, 1)
VARIABLES = types.SimpleNamespace(plazo_meses=6)


def _contexto(niveles: dict[int, int | None]) -> dict:
    catalogo = {c["pregunta_id"]: c for c in pasillo_diagnostico.catalogo_de_controles()}
    filas = []
    for pid, nivel in niveles.items():
        c = catalogo[pid]
        filas.append({
            "codigo": f"P{pid}", "pregunta_id": pid, "control": c["control"], "dimension": c["dimension"],
            "nivel_asignado": nivel, "nivel_evidencia": 2, "criticidad": 3, "es_critica": False,
        })
    return {"respuestas_diagnostico": filas}


def _puntaje_oficial(contexto: dict, proyectar: set[int]) -> float:
    respuestas = []
    for f in contexto["respuestas_diagnostico"]:
        fila = dict(f)
        if f["pregunta_id"] in proyectar:
            fila["nivel_asignado"] = 4
        respuestas.append(pasillo_diagnostico.respuesta_control_desde_fila(fila, dimension_id=fila["dimension"], control=fila["control"]))
    dims = [d for d in pasillo_diagnostico.evaluar_assessment_por_dimension(respuestas).dimensiones if d.items_evaluados > 0]
    return round(sum(d.score * d.peso for d in dims) / sum(d.peso for d in dims), 1)


def test_mismo_diagnostico_mismo_plan():
    ctx = _contexto({1: 1, 2: 2, 3: 3, 4: 4, 5: 5})
    a, b = sala.cifrar_plan(ctx, VARIABLES, HOY), sala.cifrar_plan(copy.deepcopy(ctx), VARIABLES, HOY)
    assert isinstance(a, sala.PlanCifrado) and a == b


def test_prioridad_y_horas_por_nivel():
    plan = sala.cifrar_plan(_contexto({1: 1, 2: 2, 3: 3, 4: 4, 5: 5}), VARIABLES, HOY)
    por_ref = {c.control_ref: c for o in plan.olas for c in o.controles}
    assert set(por_ref) == {"P1", "P2", "P3"}
    assert [(por_ref[r].prioridad, por_ref[r].horas) for r in ("P1", "P2", "P3")] == [("critica", 40), ("alta", 24), ("media", 16)]
    assert [o.prioridad for o in plan.olas] == ["critica", "alta", "media"]


def test_fechas_en_proporcion_a_las_horas():
    ctx = _contexto({1: 1, 2: 1, 3: 2, 4: 2, 5: 3, 6: 3})
    plan = sala.cifrar_plan(ctx, VARIABLES, HOY)
    assert [o.horas for o in plan.olas] == [80, 48, 32]
    assert plan.olas[0].inicio == HOY
    assert all(a.fin == b.inicio for a, b in zip(plan.olas, plan.olas[1:]))
    assert plan.olas[-1].fin == date(2026, 7, 1)
    total = (plan.olas[-1].fin - HOY).days
    for o in plan.olas:
        assert abs((o.fin - o.inicio).days - total * o.horas / 160) <= 1
    assert sala.HORAS_POR_PRIORIDAD == {"critica": 40, "alta": 24, "media": 16}


def test_score_objetivo_usa_el_puntaje_del_diagnostico():
    ctx = _contexto({1: 1, 2: 2, 3: 3, 4: 4, 5: 5})
    plan = sala.cifrar_plan(ctx, VARIABLES, HOY)
    assert plan.score_objetivo == _puntaje_oficial(ctx, {1, 2, 3})
    assert plan.score_objetivo > _puntaje_oficial(ctx, set())


def test_proyeccion_no_toca_la_madurez():
    ctx = _contexto({1: 1, 2: 2, 3: 3, 4: 4, 5: 5})
    antes = copy.deepcopy(ctx)
    sala.cifrar_plan(ctx, VARIABLES, HOY)
    assert ctx == antes


def test_sin_tareas_sin_olas():
    ctx = _contexto({1: 4, 2: 5, 3: 4})
    plan = sala.cifrar_plan(ctx, VARIABLES, HOY)
    assert plan.olas == ()
    assert plan.score_objetivo == _puntaje_oficial(ctx, set())
