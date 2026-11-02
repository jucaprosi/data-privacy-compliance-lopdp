"""Arbitro exogeno del motor de calculo del assessment SGPDP (escala SMARTCIDI, DIAG-08).

Fija las reglas de la matriz de madurez frente a la hoja de calculo canonica
(Assessment_Madurez_SGPDP, modelo SMARTCIDI), cuyas formulas por control son:

    M (nivel efectivo)  = MIN(K; L+1)     K nivel asignado 1-5, L evidencia 0-4
    N (score ponderado) = (M/5) * J
    O (base ponderada)  = J
    score de dimension  = SUMA(N) / SUMA(O)

El resultado es por dimension: el motor no combina dimensiones en una cifra de la
organizacion. Los topes (bloqueantes con M<3 -> 2, criticos con evidencia
insuficiente -> 3, cobertura por debajo del minimo -> nivel 0) se aplican dentro
de cada dimension.

Cada asercion numerica de este modulo se deriva de esas formulas a mano, no de
la salida del propio motor: es lo que permite que el test detecte una regresion
en vez de acompanarla.
"""
from typing import Optional

import pytest

from features.diagnostico.domain.models import RespuestaControl, SeveridadBrecha
from features.diagnostico.services.dimensiones_sgpdp import (
    COBERTURA_MINIMA_EMISION,
    DIMENSIONES_SGPDP,
    NIVELES_MADUREZ,
    NIVEL_TOPE_BRECHA_ESTRUCTURAL,
    NIVEL_TOPE_EVIDENCIA_INSUFICIENTE,
    UMBRAL_RIESGO_ALTO,
    UMBRAL_RIESGO_CRITICO,
    agregar_resultado_por_dimension,
    calcular_nivel_efectivo,
)

# Evidencia 4 (revisada): con ella el nivel asignado no queda acotado (4 + 1 = 5).
E_PLENA = 4


def respuesta(
    pregunta_id: int,
    nivel_asignado: Optional[int] = 5,
    evidencia: int = E_PLENA,
    criticidad: int = 3,
    dimension: str = "D01",
) -> RespuestaControl:
    return RespuestaControl(
        pregunta_id=pregunta_id,
        nivel_asignado=nivel_asignado,
        evidencia_nivel=evidencia,
        criticidad=criticidad,
        dimension_id=dimension,
        control=f"Control {pregunta_id}",
    )


def pendiente(pregunta_id: int, criticidad: int = 3, dimension: str = "D01") -> RespuestaControl:
    return respuesta(pregunta_id, None, 0, criticidad, dimension)


def _una_dimension(*respuestas):
    """Resultado de una dimension unica (D01)."""
    return agregar_resultado_por_dimension(list(respuestas))


def _por_id(resultado):
    return {d.id: d for d in resultado.dimensiones}


# --------------------------------------------------------------------------
# Catalogo: pesos y umbrales de nivel
# --------------------------------------------------------------------------


def test_pesos_de_dimension_suman_exactamente_uno():
    assert round(sum(d.peso for d in DIMENSIONES_SGPDP), 10) == 1.0


def test_pesos_de_riesgo_y_capacitacion_siguen_la_matriz_canonica():
    pesos = {d.id: d.peso for d in DIMENSIONES_SGPDP}
    assert pesos["D09"] == 0.11
    assert pesos["D10"] == 0.05


def test_umbrales_de_nivel_siguen_la_matriz_canonica():
    umbrales = {n.nivel: n.umbral_minimo for n in NIVELES_MADUREZ}
    assert umbrales == {1: 0.0, 2: 40.0, 3: 60.0, 4: 75.0, 5: 90.0}


def test_el_resultado_no_trae_cifra_global_de_la_organizacion():
    resultado = _una_dimension(respuesta(1))
    for campo in ("score_ponderado", "nivel_teorico", "nivel_ajustado", "madurez"):
        assert not hasattr(resultado, campo), campo


# --------------------------------------------------------------------------
# Nivel efectivo: MIN(nivel asignado, evidencia + 1), sin reescalar
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "asignado, evidencia, esperado",
    [
        (5, 4, 5.0),   # evidencia revisada: no acota
        (4, 4, 4.0),   # el nivel asignado se toma tal cual
        (2, 4, 2.0),
        (5, 0, 1.0),   # sin evidencia el nivel cae a 1 aunque se declare todo
        (5, 1, 2.0),
        (5, 2, 3.0),
        (3, 4, 3.0),   # manda lo declarado, no la evidencia
        (1, 4, 1.0),
        (None, 4, 0.0),  # nivel asignado nulo: pendiente, computa cero
    ],
)
def test_nivel_efectivo_es_el_minimo_entre_declaracion_y_evidencia(asignado, evidencia, esperado):
    assert calcular_nivel_efectivo(respuesta(1, asignado, evidencia)) == pytest.approx(esperado)


# --------------------------------------------------------------------------
# Score de dimension: ponderado por criticidad, base sobre todo lo aplicable
# --------------------------------------------------------------------------


def test_score_de_dimension_pondera_por_criticidad():
    # Criticidad 5 en nivel 1 y criticidad 1 en nivel 5.
    #   N = (1/5)*5 + (5/5)*1 = 1 + 1 = 2 ; O = 5 + 1 = 6  ->  33.3 %
    # Un promedio simple de niveles habria dado (1+5)/2/5 = 60 %.
    resultado = _una_dimension(
        respuesta(1, 1, E_PLENA, criticidad=5),
        respuesta(2, 5, E_PLENA, criticidad=1),
    )
    assert resultado.dimensiones[0].score == pytest.approx(33.3)


def test_control_sin_responder_computa_como_cero_y_no_se_excluye():
    # Uno en nivel 5 con criticidad 3 y otro pendiente con criticidad 3:
    #   N = (5/5)*3 = 3 ; O = 3 + 3 = 6  ->  50 %
    # Renormalizando sobre lo respondido habria dado 100 %.
    resultado = _una_dimension(respuesta(1, 5, E_PLENA, criticidad=3), pendiente(2, criticidad=3))
    assert resultado.dimensiones[0].score == pytest.approx(50.0)


def test_las_dimensiones_sin_responder_no_arrastran_a_las_demas():
    # D01 al 100 %; las otras nueve son aplicables pero estan sin responder: cada una
    # queda sin nivel y D01 conserva el suyo. Nada se promedia entre dimensiones.
    respuestas = [respuesta(i, dimension="D01") for i in range(1, 6)]
    for indice, dim in enumerate(DIMENSIONES_SGPDP[1:], start=100):
        respuestas.append(pendiente(indice, dimension=dim.id))
    por_id = _por_id(agregar_resultado_por_dimension(respuestas))
    assert (por_id["D01"].score, por_id["D01"].nivel) == (100.0, 5)
    assert all(por_id[d.id].nivel == 0 for d in DIMENSIONES_SGPDP[1:])


def test_dimension_sin_controles_aplicables_no_reporta_items():
    resultado = agregar_resultado_por_dimension([respuesta(i, dimension="D01") for i in range(1, 6)])
    por_id = _por_id(resultado)
    assert por_id["D01"].nivel == 5
    assert por_id["D02"].items_aplicables == 0


@pytest.mark.parametrize("asignado, nivel", [(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)])
def test_nivel_de_dimension_por_rangos_de_score(asignado, nivel):
    # Un control unico con evidencia plena: score = asignado/5*100.
    #   1 -> 20 (rango 0-39: nivel 1) ; 2 -> 40 (40-59: 2) ; 3 -> 60 (60-74: 3)
    #   4 -> 80 (75-89: 4) ; 5 -> 100 (90-100: 5)
    assert _una_dimension(respuesta(1, asignado)).dimensiones[0].nivel == nivel


# --------------------------------------------------------------------------
# Severidad de brechas: riesgo = (5 - nivel efectivo) * criticidad
# --------------------------------------------------------------------------


def test_umbrales_de_severidad_siguen_la_matriz_canonica():
    assert (UMBRAL_RIESGO_CRITICO, UMBRAL_RIESGO_ALTO) == (15.0, 9.0)


def test_brecha_critica_exige_riesgo_quince():
    # Nivel 1 con criticidad 4: riesgo = (5-1)*4 = 16 >= 15.
    critica = _una_dimension(respuesta(1, 1, E_PLENA, criticidad=4))
    assert critica.brechas_criticas == 1
    assert critica.brechas[0].severidad == SeveridadBrecha.CRITICO

    # Nivel 3 con criticidad 5: riesgo = (5-3)*5 = 10 -> Alto, no critico.
    alta = _una_dimension(respuesta(1, 3, E_PLENA, criticidad=5))
    assert (alta.brechas_criticas, alta.brechas_altas) == (0, 1)
    assert alta.brechas[0].severidad == SeveridadBrecha.ALTO


def test_riesgo_bajo_el_umbral_alto_no_genera_brecha():
    # Nivel 3 con criticidad 4: riesgo = (5-3)*4 = 8 < 9.
    resultado = _una_dimension(respuesta(1, 3, E_PLENA, criticidad=4))
    assert (resultado.brechas_criticas, resultado.brechas_altas) == (0, 0)
    assert resultado.brechas == []


# --------------------------------------------------------------------------
# Topes de nivel dentro de la dimension: bloqueantes, evidencia insuficiente, cobertura
# --------------------------------------------------------------------------


def _todo_en_cinco_menos(pregunta_id: int, **cambios):
    """40 controles en nivel 5 con evidencia plena salvo uno; cuatro por dimension."""
    respuestas = [
        respuesta(i, criticidad=3, dimension=DIMENSIONES_SGPDP[i % 10].id)
        for i in range(1, 41)
    ]
    base = respuestas[pregunta_id - 1]
    respuestas[pregunta_id - 1] = respuesta(
        pregunta_id,
        cambios.get("asignado", 5),
        cambios.get("evidencia", E_PLENA),
        cambios.get("criticidad", 3),
        base.dimension_id,
    )
    return respuestas


def test_control_bloqueante_degradado_topa_la_dimension_en_dos():
    # El control 7 cae en D08 con criticidad 5 y nivel 1. En D08: tres controles de
    # criticidad 3 en nivel 5 (N = 9) y uno de criticidad 5 en nivel 1 (N = 1);
    # O = 9 + 5 = 14 -> 71,4 %, rango 60-74 -> nivel 3, y el bloqueante lo topa en 2.
    resultado = agregar_resultado_por_dimension(_todo_en_cinco_menos(7, asignado=1, criticidad=5))
    por_id = _por_id(resultado)
    assert por_id["D08"].score == pytest.approx(71.4)
    assert por_id["D08"].ajuste_por_brecha_estructural is True
    assert por_id["D08"].nivel == NIVEL_TOPE_BRECHA_ESTRUCTURAL
    assert resultado.controles_bloqueantes_degradados == 1
    # El tope no sale de su dimension.
    assert all(d.nivel == 5 and not d.ajuste_por_brecha_estructural for d in resultado.dimensiones if d.id != "D08")


def test_criticidad_alta_sin_evidencia_suficiente_topa_la_dimension_en_tres():
    # Control 7 (D08) con criticidad 4, nivel 5 y evidencia 1: efectivo = min(5, 2) = 2.
    # N = 9 + (2/5)*4 = 10,6 ; O = 9 + 4 = 13 -> 81,5 %, rango 75-89 -> nivel 4, topado en 3.
    # No es bloqueante (criticidad 4): el tope es 3, no 2.
    resultado = agregar_resultado_por_dimension(_todo_en_cinco_menos(7, evidencia=1, criticidad=4))
    d08 = _por_id(resultado)["D08"]
    assert d08.score == pytest.approx(81.5)
    assert d08.ajuste_por_evidencia_insuficiente is True
    assert d08.ajuste_por_brecha_estructural is False
    assert resultado.controles_sin_evidencia_suficiente == 1
    assert d08.nivel == NIVEL_TOPE_EVIDENCIA_INSUFICIENTE


def test_cobertura_bajo_el_minimo_deja_la_dimension_sin_nivel():
    # 4 de 10 controles respondidos: 40 % < 60 %.
    respuestas = [respuesta(i) for i in range(1, 5)] + [pendiente(i) for i in range(5, 11)]
    resultado = agregar_resultado_por_dimension(respuestas)
    d01 = _por_id(resultado)["D01"]
    assert resultado.cobertura_porcentaje == pytest.approx(40.0)
    assert d01.nivel == 0
    assert d01.nivel_etiqueta == "Sin evaluación suficiente"


def test_cobertura_en_el_minimo_exacto_si_emite_nivel():
    # 6 de 10: la cota es inclusiva, 60 % califica.
    respuestas = [respuesta(i) for i in range(1, 7)] + [pendiente(i) for i in range(7, 11)]
    resultado = agregar_resultado_por_dimension(respuestas)
    assert resultado.cobertura_porcentaje == pytest.approx(COBERTURA_MINIMA_EMISION)
    assert _por_id(resultado)["D01"].nivel > 0


def test_dimension_con_cobertura_insuficiente_no_reporta_nivel():
    # D01 al 100 % y D02 con 1 de 5 respondidos (20 %).
    respuestas = [respuesta(i, dimension="D01") for i in range(1, 6)]
    respuestas.append(respuesta(10, dimension="D02"))
    respuestas += [pendiente(i, dimension="D02") for i in range(11, 15)]
    por_id = _por_id(agregar_resultado_por_dimension(respuestas))
    assert por_id["D01"].nivel == 5
    assert por_id["D02"].nivel == 0
    assert por_id["D02"].nivel_etiqueta == "Sin evaluación suficiente"


# --------------------------------------------------------------------------
# Caso completo cotejado a mano contra la hoja canonica
# --------------------------------------------------------------------------


def test_caso_completo_reproduce_la_hoja_canonica():
    """Diez controles, uno por dimension, con el calculo desarrollado a mano.

    Cada dimension queda con un unico control, luego su score es (M/5)*100 y su
    nivel sale de los rangos 0-39, 40-59, 60-74, 75-89 y 90-100.
    """
    casos = [
        # (dimension, nivel asignado, evidencia, criticidad, M esperado, nivel esperado)
        ("D01", 5, 4, 3, 5, 5),
        ("D02", 3, 4, 5, 3, 3),
        ("D03", 5, 2, 3, 3, 3),
        ("D04", 1, 4, 4, 1, 1),
        ("D05", 5, 4, 2, 5, 5),
        ("D06", 3, 1, 3, 2, 2),
        ("D07", 5, 4, 5, 5, 5),
        ("D08", 5, 0, 3, 1, 1),
        ("D09", 3, 4, 4, 3, 3),
        ("D10", 5, 4, 2, 5, 5),
    ]
    respuestas = [
        respuesta(indice + 1, asignado, evidencia, criticidad, dim)
        for indice, (dim, asignado, evidencia, criticidad, _, _) in enumerate(casos)
    ]
    resultado = agregar_resultado_por_dimension(respuestas)
    por_id = _por_id(resultado)
    for dim, _, _, _, m, nivel in casos:
        assert por_id[dim].score == pytest.approx(round(m / 5 * 100, 1)), dim
        assert por_id[dim].nivel == nivel, dim

    # D02 tiene criticidad 5 en nivel 3: no baja de 3, no es bloqueante degradado.
    # D04 tiene criticidad 4 en nivel 1 con evidencia plena: no topa por evidencia,
    # pero su riesgo (5-1)*4 = 16 lo hace brecha critica.
    # D08 tiene criticidad 3 y evidencia 0: por debajo de criticidad 4, no topa.
    assert resultado.controles_bloqueantes_degradados == 0
    assert resultado.controles_sin_evidencia_suficiente == 0

    # Brechas: riesgo por control = (5 - M) * J.
    #   D01 0 | D02 (5-3)*5 = 10 Alto | D03 (5-3)*3 = 6 | D04 16 Critico
    #   D05 0 | D06 (5-2)*3 = 9 Alto | D07 0 | D08 (5-1)*3 = 12 Alto
    #   D09 (5-3)*4 = 8 | D10 0
    assert resultado.brechas_criticas == 1
    assert resultado.brechas_altas == 3
    assert resultado.brechas[0].pregunta_id == 4
    assert resultado.brechas[0].riesgo == pytest.approx(16.0)
