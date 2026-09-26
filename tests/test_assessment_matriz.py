"""Arbitro exogeno del motor de calculo del assessment SGPDP.

Fija las reglas de la matriz de madurez frente a la hoja de calculo canonica
(Assessment_Madurez_SGPDP, modelo SMARTCIDI), cuyas formulas por control son:

    M (nivel efectivo)  = MIN(K; L+1)
    N (score ponderado) = (M/5) * J
    O (base ponderada)  = J
    score de dimension  = SUMA(N) / SUMA(O)
    madurez global      = SUMA(score * peso) / SUMA(pesos)

y cuyo Dashboard topa el nivel teorico con tres reglas independientes:
bloqueantes con M<3 (tope 2), criticos con evidencia insuficiente (tope 3) y
cobertura por debajo del minimo de emision (nivel 0).

Cada asercion numerica de este modulo se deriva de esas formulas a mano, no de
la salida del propio motor: es lo que permite que el test detecte una regresion
en vez de acompanarla.
"""
import pytest

from features.diagnostico.domain.models import EstadoCumplimiento, RespuestaControl, SeveridadBrecha
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

# E3 es el unico nivel de evidencia que reescalado (E * 4/3 = 4) no acota a un
# control declarado Conforme. Se usa para aislar la regla bajo prueba.
E_PLENA = 3


def respuesta(
    pregunta_id: int,
    cumple: EstadoCumplimiento = EstadoCumplimiento.CONFORME,
    evidencia: int = E_PLENA,
    criticidad: int = 3,
    dimension: str = "D01",
) -> RespuestaControl:
    return RespuestaControl(
        pregunta_id=pregunta_id,
        cumple=cumple,
        evidencia_nivel=evidencia,
        criticidad=criticidad,
        dimension_id=dimension,
        control=f"Control {pregunta_id}",
    )


def _una_dimension(*respuestas):
    """Resultado de una dimension unica; el score global coincide con el suyo."""
    return agregar_resultado_por_dimension(list(respuestas))


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


# --------------------------------------------------------------------------
# Nivel efectivo: MIN(nivel asignado, evidencia reescalada + 1)
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "cumple, evidencia, esperado",
    [
        # Conforme (5) con evidencia plena: la evidencia no acota.
        (EstadoCumplimiento.CONFORME, 3, 5.0),
        # Conforme (5) sin evidencia: el nivel cae a 1 aunque se declare todo.
        (EstadoCumplimiento.CONFORME, 0, 1.0),
        # Conforme (5) con E1: 1*(4/3)+1 = 2.333...
        (EstadoCumplimiento.CONFORME, 1, 1 * (4 / 3) + 1),
        # Parcial (3) con evidencia plena: manda lo declarado, no la evidencia.
        (EstadoCumplimiento.PARCIAL, 3, 3.0),
        # No Conforme (1) con evidencia plena: manda lo declarado.
        (EstadoCumplimiento.NO_CONFORME, 3, 1.0),
        # Pendiente no aporta nivel alguno.
        (EstadoCumplimiento.PENDIENTE, 3, 0.0),
    ],
)
def test_nivel_efectivo_es_el_minimo_entre_declaracion_y_evidencia(cumple, evidencia, esperado):
    assert calcular_nivel_efectivo(respuesta(1, cumple, evidencia)) == pytest.approx(esperado)


# --------------------------------------------------------------------------
# Score de dimension: ponderado por criticidad, base sobre todo lo aplicable
# --------------------------------------------------------------------------


def test_score_de_dimension_pondera_por_criticidad():
    # Criticidad 5 en nivel 1 y criticidad 1 en nivel 5.
    #   N = (1/5)*5 + (5/5)*1 = 1 + 1 = 2 ; O = 5 + 1 = 6  ->  33.3 %
    # Un promedio simple de niveles habria dado (1+5)/2/5 = 60 %.
    resultado = _una_dimension(
        respuesta(1, EstadoCumplimiento.NO_CONFORME, E_PLENA, criticidad=5),
        respuesta(2, EstadoCumplimiento.CONFORME, E_PLENA, criticidad=1),
    )
    assert resultado.dimensiones[0].score == pytest.approx(33.3)


def test_control_sin_responder_computa_como_cero_y_no_se_excluye():
    # Uno Conforme con criticidad 3 y otro Pendiente con criticidad 3:
    #   N = (5/5)*3 = 3 ; O = 3 + 3 = 6  ->  50 %
    # Renormalizando sobre lo respondido habria dado 100 %.
    resultado = _una_dimension(
        respuesta(1, EstadoCumplimiento.CONFORME, E_PLENA, criticidad=3),
        respuesta(2, EstadoCumplimiento.PENDIENTE, 0, criticidad=3),
    )
    assert resultado.dimensiones[0].score == pytest.approx(50.0)


def test_madurez_global_no_se_renormaliza_sobre_las_dimensiones_evaluadas():
    # D01 (peso 0,12) al 100 %; las otras nueve son aplicables pero estan sin
    # responder, luego aportan 0 con su peso completo:
    #   global = 0,12 * 100 / 1,00 = 12,0
    # Renormalizando sobre las dimensiones con datos habria dado 100,0.
    respuestas = [respuesta(i, dimension="D01") for i in range(1, 6)]
    for indice, dim in enumerate(DIMENSIONES_SGPDP[1:], start=100):
        respuestas.append(respuesta(indice, EstadoCumplimiento.PENDIENTE, 0, dimension=dim.id))
    resultado = agregar_resultado_por_dimension(respuestas)
    assert resultado.score_ponderado == pytest.approx(12.0)


def test_dimension_sin_controles_aplicables_no_arrastra_el_ponderado():
    # Si el catalogo podado no exige nada de una dimension, esa dimension queda
    # fuera del ponderado: no computa como cero. Solo D01 es aplicable aqui.
    resultado = agregar_resultado_por_dimension(
        [respuesta(i, dimension="D01") for i in range(1, 6)]
    )
    assert resultado.score_ponderado == pytest.approx(100.0)


# --------------------------------------------------------------------------
# Severidad de brechas: riesgo = (5 - nivel efectivo) * criticidad
# --------------------------------------------------------------------------


def test_umbrales_de_severidad_siguen_la_matriz_canonica():
    assert (UMBRAL_RIESGO_CRITICO, UMBRAL_RIESGO_ALTO) == (15.0, 9.0)


def test_brecha_critica_exige_riesgo_quince():
    # No Conforme (nivel 1) con criticidad 4: riesgo = (5-1)*4 = 16 >= 15.
    critica = _una_dimension(respuesta(1, EstadoCumplimiento.NO_CONFORME, E_PLENA, criticidad=4))
    assert critica.brechas_criticas == 1
    assert critica.brechas[0].severidad == SeveridadBrecha.CRITICO

    # Parcial (nivel 3) con criticidad 5: riesgo = (5-3)*5 = 10 -> Alto, no critico.
    alta = _una_dimension(respuesta(1, EstadoCumplimiento.PARCIAL, E_PLENA, criticidad=5))
    assert (alta.brechas_criticas, alta.brechas_altas) == (0, 1)
    assert alta.brechas[0].severidad == SeveridadBrecha.ALTO


def test_riesgo_bajo_el_umbral_alto_no_genera_brecha():
    # Parcial (nivel 3) con criticidad 4: riesgo = (5-3)*4 = 8 < 9.
    resultado = _una_dimension(respuesta(1, EstadoCumplimiento.PARCIAL, E_PLENA, criticidad=4))
    assert (resultado.brechas_criticas, resultado.brechas_altas) == (0, 0)
    assert resultado.brechas == []


# --------------------------------------------------------------------------
# Topes de nivel: bloqueantes, evidencia insuficiente y cobertura
# --------------------------------------------------------------------------


def _todo_conforme_menos(pregunta_id: int, **cambios):
    """40 controles Conformes con evidencia plena salvo uno; cobertura 100 %."""
    respuestas = [
        respuesta(i, criticidad=3, dimension=DIMENSIONES_SGPDP[i % 10].id)
        for i in range(1, 41)
    ]
    base = respuestas[pregunta_id - 1]
    respuestas[pregunta_id - 1] = respuesta(
        pregunta_id,
        cambios.get("cumple", EstadoCumplimiento.CONFORME),
        cambios.get("evidencia", E_PLENA),
        cambios.get("criticidad", 3),
        base.dimension_id,
    )
    return respuestas


def test_control_bloqueante_degradado_topa_el_nivel_en_dos():
    # Un unico control de criticidad 5 en nivel 1 dentro de un assessment por lo
    # demas impecable: el score sigue siendo alto y el nivel igual cae a 2.
    resultado = agregar_resultado_por_dimension(
        _todo_conforme_menos(7, cumple=EstadoCumplimiento.NO_CONFORME, criticidad=5)
    )
    assert resultado.score_ponderado > 90.0
    assert resultado.nivel_teorico == 5
    assert resultado.ajuste_por_brecha_estructural is True
    assert resultado.controles_bloqueantes_degradados == 1
    assert resultado.nivel_ajustado == NIVEL_TOPE_BRECHA_ESTRUCTURAL


def test_criticidad_alta_sin_evidencia_suficiente_topa_el_nivel_en_tres():
    # Criticidad 4 declarada Conforme pero con evidencia E1: reescalada da
    # 1*(4/3) = 1,33 < 2, luego la evidencia no sostiene el nivel declarado.
    # El control no es bloqueante (criticidad 4), asi que el tope es 3, no 2.
    resultado = agregar_resultado_por_dimension(
        _todo_conforme_menos(7, evidencia=1, criticidad=4)
    )
    assert resultado.nivel_teorico == 5
    assert resultado.ajuste_por_evidencia_insuficiente is True
    assert resultado.controles_sin_evidencia_suficiente == 1
    assert resultado.ajuste_por_brecha_estructural is False
    assert resultado.nivel_ajustado == NIVEL_TOPE_EVIDENCIA_INSUFICIENTE


def test_cobertura_bajo_el_minimo_no_emite_nivel():
    # 4 de 10 controles respondidos: 40 % < 60 %.
    respuestas = [respuesta(i) for i in range(1, 5)]
    respuestas += [respuesta(i, EstadoCumplimiento.PENDIENTE, 0) for i in range(5, 11)]
    resultado = agregar_resultado_por_dimension(respuestas)
    assert resultado.cobertura_porcentaje == pytest.approx(40.0)
    assert resultado.cobertura_insuficiente is True
    assert resultado.nivel_ajustado == 0
    assert resultado.nivel_ajustado_etiqueta == "Sin evaluación suficiente"


def test_cobertura_en_el_minimo_exacto_si_emite_nivel():
    # 6 de 10: la cota es inclusiva, 60 % califica.
    respuestas = [respuesta(i) for i in range(1, 7)]
    respuestas += [respuesta(i, EstadoCumplimiento.PENDIENTE, 0) for i in range(7, 11)]
    resultado = agregar_resultado_por_dimension(respuestas)
    assert resultado.cobertura_porcentaje == pytest.approx(COBERTURA_MINIMA_EMISION)
    assert resultado.cobertura_insuficiente is False
    assert resultado.nivel_ajustado > 0


def test_dimension_con_cobertura_insuficiente_no_reporta_nivel():
    # D01 al 100 % y D02 con 1 de 5 respondidos (20 %).
    respuestas = [respuesta(i, dimension="D01") for i in range(1, 6)]
    respuestas.append(respuesta(10, dimension="D02"))
    respuestas += [
        respuesta(i, EstadoCumplimiento.PENDIENTE, 0, dimension="D02") for i in range(11, 15)
    ]
    por_id = {d.id: d for d in agregar_resultado_por_dimension(respuestas).dimensiones}
    assert por_id["D01"].nivel == 5
    assert por_id["D02"].nivel == 0
    assert por_id["D02"].nivel_etiqueta == "Sin evaluación suficiente"


# --------------------------------------------------------------------------
# Caso completo cotejado a mano contra la hoja canonica
# --------------------------------------------------------------------------


def test_caso_completo_reproduce_la_hoja_canonica():
    """Diez controles, uno por dimension, con el calculo desarrollado a mano.

    Cada dimension queda con un unico control, luego su score es (M/5)*100 y el
    global es la suma ponderada por los pesos del catalogo.
    """
    casos = [
        # (dimension, peso, cumple, evidencia, criticidad, M esperado)
        ("D01", 0.12, EstadoCumplimiento.CONFORME, 3, 3, 5.0),
        ("D02", 0.14, EstadoCumplimiento.PARCIAL, 3, 5, 3.0),
        ("D03", 0.08, EstadoCumplimiento.CONFORME, 2, 3, 2 * (4 / 3) + 1),
        ("D04", 0.08, EstadoCumplimiento.NO_CONFORME, 3, 4, 1.0),
        ("D05", 0.10, EstadoCumplimiento.CONFORME, 3, 2, 5.0),
        ("D06", 0.10, EstadoCumplimiento.PARCIAL, 1, 3, 1 * (4 / 3) + 1),
        ("D07", 0.14, EstadoCumplimiento.CONFORME, 3, 5, 5.0),
        ("D08", 0.08, EstadoCumplimiento.CONFORME, 0, 3, 1.0),
        ("D09", 0.11, EstadoCumplimiento.PARCIAL, 3, 4, 3.0),
        ("D10", 0.05, EstadoCumplimiento.CONFORME, 3, 2, 5.0),
    ]
    respuestas = [
        respuesta(indice + 1, cumple, evidencia, criticidad, dim)
        for indice, (dim, _, cumple, evidencia, criticidad, _) in enumerate(casos)
    ]
    resultado = agregar_resultado_por_dimension(respuestas)

    # Score por dimension: con un solo control, N/O = M/5.
    por_id = {d.id: d for d in resultado.dimensiones}
    esperados = {}
    for dim, _, _, _, _, m in casos:
        esperado = round(m / 5 * 100, 1)
        esperados[dim] = esperado
        assert por_id[dim].score == pytest.approx(esperado), dim

    # Global: suma ponderada; los pesos suman 1, asi que no hay renormalizacion.
    global_esperado = round(sum(peso * esperados[dim] for dim, peso, *_ in casos), 2)
    assert resultado.score_ponderado == pytest.approx(global_esperado)
    # 0,12*100 + 0,14*60 + 0,08*73,3 + 0,08*20 + 0,10*100
    # + 0,10*46,7 + 0,14*100 + 0,08*20 + 0,11*60 + 0,05*100 = 69,734
    assert global_esperado == pytest.approx(69.73)

    # Nivel teorico: 69,73 cae en el tramo [60, 75) -> nivel 3.
    assert resultado.nivel_teorico == 3

    # D02 tiene criticidad 5 en nivel 3: no baja de 3, no es bloqueante degradado.
    # D04 tiene criticidad 4 en nivel 1, con evidencia plena: no topa por evidencia,
    # pero su riesgo (5-1)*4 = 16 lo hace brecha critica.
    # D08 tiene criticidad 3 y evidencia E0: por debajo de criticidad 4, no topa.
    assert resultado.controles_bloqueantes_degradados == 0
    assert resultado.controles_sin_evidencia_suficiente == 0
    assert resultado.nivel_ajustado == 3

    # Brechas: riesgo por control = (5 - M) * J.
    #   D01 0 | D02 10 Alto | D03 (5-3,67)*3 = 4 | D04 16 Critico
    #   D05 0 | D06 (5-2,33)*3 = 8 | D07 0 | D08 (5-1)*3 = 12 Alto
    #   D09 (5-3)*4 = 8 | D10 0
    assert resultado.brechas_criticas == 1
    assert resultado.brechas_altas == 2
    assert resultado.brechas[0].pregunta_id == 4
    assert resultado.brechas[0].riesgo == pytest.approx(16.0)
