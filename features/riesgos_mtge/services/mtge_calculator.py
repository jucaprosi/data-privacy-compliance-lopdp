"""Motor determinista de cálculo MTGE (Matriz de Tratamientos a Gran Escala).
Conforme a la Resolución SPDP-SPD-2026-0005-R e invariante INV_LOPDP_MTGE_DETERMINISTIC_TRIGGER.
"""
from features.riesgos_mtge.domain.models import EntradaCalculoMTGE, ResultadoMTGE

UMBRAL_GRAN_ESCALA_PUNTOS = 6.0  # Art. 10: P >= 6.
PUNTAJES = {
    "titulares_12_meses": {"HASTA_1000": 1, "HASTA_10000": 2, "HASTA_100000": 3, "MAS_DE_100000": 4},
    "tipos_datos": {"HASTA_10": .5, "HASTA_30": 1, "HASTA_100": 2, "MAS_DE_100": 3},
    "categorias_datos": {"BASICAS": .5, "UNA_ESPECIAL": 2, "MULTIPLES_ESPECIALES_O_VULNERABLES_O_PENALES": 3},
    "frecuencia": {"PUNTUAL": .5, "PERIODICA_O_RECURRENTE": 1, "CONTINUA_O_TIEMPO_REAL": 2},
    "permanencia": {"OCASIONAL": .5, "TEMPORAL_MENOS_DE_3_ANOS": 1, "PROLONGADA_DESDE_3_ANOS": 2},
    "alcance": {"LOCAL": 1, "NACIONAL": 2, "GLOBAL_O_TRANSFRONTERIZO": 3},
}

def calcular_mtge_actividad(entrada: EntradaCalculoMTGE) -> ResultadoMTGE:
    """Calcula si un tratamiento califica como Gran Escala por casos directos o por umbral MTGE."""
    if entrada.supuestos_directos:
        numerales = tuple(s.value for s in entrada.supuestos_directos)
        return ResultadoMTGE(entrada.actividad_rat_id, 0, True, True, True, True, True, "CASO_DIRECTO_ART_14", {}, numerales, "Gran escala por art. 14: " + ", ".join(numerales) + ". Efectos art. 12.")
    desglose = {campo: PUNTAJES[campo][getattr(entrada, campo).value] for campo in PUNTAJES}
    puntos = sum(desglose.values()); es_ge = puntos >= UMBRAL_GRAN_ESCALA_PUNTOS
    return ResultadoMTGE(entrada.actividad_rat_id, puntos, es_ge, es_ge, es_ge, es_ge, es_ge, "PUNTAJE_ART_8_10" if es_ge else "NO_ALCANZA_UMBRAL", desglose, (), f"P = {puntos:g} (art. 9); umbral art. 10: P >= 6.")
