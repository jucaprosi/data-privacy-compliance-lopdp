# ¤mtge-granescala ¤arbitro
"""MTGE-01: el cálculo de gran escala sigue la Res. SPDP-SPD-2026-0005-R.

Bordes de cada tramo del art. 8 (incluido el hueco 100.001-100.999, decisión del propietario),
umbral del art. 10, ejemplos del art. 11, supuestos del art. 14 y efectos del art. 12.
"""
import pytest

from features.riesgos_mtge.riesgos_mtge_service import (
    AlcanceGeografico as A,
    CategoriasDatos as C,
    EntradaCalculoMTGE,
    Frecuencia as F,
    Permanencia as P,
    SupuestoDirecto,
    evaluar_gran_escala_mtge,
)


def entrada(**cambios) -> EntradaCalculoMTGE:
    """Tratamiento mínimo: 1 + 0,5 + 0,5 + 0,5 + 0,5 + 1 = 4 puntos."""
    base = dict(
        actividad_rat_id="t", titulares_12_meses=500, tipos_datos_por_titular=5,
        categorias_datos=C.BASICAS, frecuencia=F.PUNTUAL, permanencia=P.OCASIONAL, alcance=A.LOCAL,
    )
    return EntradaCalculoMTGE(**{**base, **cambios})


def calcular(**cambios):
    return evaluar_gran_escala_mtge(entrada(**cambios))


@pytest.mark.parametrize("titulares, puntos", [
    (0, 1), (1_000, 1),  # 8.1.1
    (1_001, 2), (10_000, 2),  # 8.1.2
    (10_001, 3), (100_000, 3),  # 8.1.3
    (100_001, 4), (100_999, 4),  # hueco del texto: 4 puntos (decisión del propietario)
    (101_000, 4), (5_000_000, 4),  # 8.1.4
])
def test_art_8_1_titulares(titulares, puntos):
    assert calcular(titulares_12_meses=titulares).desglose["titulares"] == puntos


@pytest.mark.parametrize("tipos, puntos", [(1, 0.5), (10, 0.5), (11, 1), (30, 1), (31, 2), (100, 2), (101, 3)])
def test_art_8_2_tipos_de_datos(tipos, puntos):
    assert calcular(tipos_datos_por_titular=tipos).desglose["volumen"] == puntos


@pytest.mark.parametrize("variable, valor, clave, puntos", [
    ("categorias_datos", C.BASICAS, "categorias", 0.5),
    ("categorias_datos", C.UNA_ESPECIAL, "categorias", 2),
    ("categorias_datos", C.VARIAS_ESPECIALES_VULNERABLES_O_PENALES, "categorias", 3),
    ("frecuencia", F.PUNTUAL, "frecuencia", 0.5),
    ("frecuencia", F.PERIODICA, "frecuencia", 1),
    ("frecuencia", F.CONTINUA, "frecuencia", 2),
    ("permanencia", P.OCASIONAL, "permanencia", 0.5),
    ("permanencia", P.TEMPORAL, "permanencia", 1),
    ("permanencia", P.PROLONGADA, "permanencia", 2),
    ("alcance", A.LOCAL, "geografia", 1),
    ("alcance", A.NACIONAL, "geografia", 2),
    ("alcance", A.GLOBAL_O_TRANSFRONTERIZO, "geografia", 3),
])
def test_art_8_3_a_8_6(variable, valor, clave, puntos):
    assert calcular(**{variable: valor}).desglose[clave] == puntos


def test_art_9_suma_las_seis_variables():
    r = calcular(titulares_12_meses=20_000, tipos_datos_por_titular=40, categorias_datos=C.UNA_ESPECIAL,
                 frecuencia=F.CONTINUA, permanencia=P.PROLONGADA, alcance=A.NACIONAL)
    assert r.desglose == {"titulares": 3, "volumen": 2, "categorias": 2, "frecuencia": 2, "permanencia": 2, "geografia": 2}
    assert r.puntaje_mtge == 13


def test_art_10_umbral_5_5_no_y_6_si():
    cinco_y_medio = calcular(titulares_12_meses=5_000, tipos_datos_por_titular=20)  # 2 + 1 + 0,5 + 0,5 + 0,5 + 1
    seis = calcular(titulares_12_meses=5_000, tipos_datos_por_titular=20, frecuencia=F.PERIODICA)  # + 0,5
    assert (cinco_y_medio.puntaje_mtge, cinco_y_medio.es_gran_escala, cinco_y_medio.criterio_activacion) == (5.5, False, "NO_ALCANZA_UMBRAL")
    assert (seis.puntaje_mtge, seis.es_gran_escala, seis.criterio_activacion) == (6, True, "PUNTAJE_ART_10")


def test_art_11_1_magnitud_media_alta_supera_el_umbral():
    # «más de 10.000 titulares, frecuencia continua y ámbito nacional»
    r = calcular(titulares_12_meses=10_001, frecuencia=F.CONTINUA, alcance=A.NACIONAL)
    assert r.es_gran_escala


@pytest.mark.parametrize("condicion", [{"permanencia": P.PROLONGADA}, {"alcance": A.NACIONAL}])
def test_art_11_2_magnitud_baja_no_alcanza_aunque_sea_prolongado_o_nacional(condicion):
    # «hasta 1.000 titulares, 10 tipos de datos y datos no sensibles … aun cuando fuere prolongado o de
    # alcance nacional». Con las dos condiciones a la vez suma 6,5 y sí alcanza: el ejemplo vale para
    # cada una por separado («o»), como prevé su matiz «en condiciones ordinarias».
    r = calcular(titulares_12_meses=1_000, tipos_datos_por_titular=10, **condicion)
    assert not r.es_gran_escala


def test_art_11_2_con_las_dos_condiciones_a_la_vez_si_alcanza():
    r = calcular(titulares_12_meses=1_000, tipos_datos_por_titular=10, permanencia=P.PROLONGADA, alcance=A.NACIONAL)
    assert r.puntaje_mtge == 6.5 and r.es_gran_escala


@pytest.mark.parametrize("supuesto", list(SupuestoDirecto))
def test_art_14_califica_sin_mtge(supuesto):
    r = calcular(supuestos_directos=(supuesto,))  # el puntaje (4) no llega al umbral
    assert r.es_gran_escala and r.criterio_activacion == "CALIFICACION_DIRECTA_ART_14"
    assert r.supuestos_directos == (supuesto.value,)
    assert r.puntaje_mtge == 4  # se informa igual, como evidencia


def test_art_14_numerales_del_texto():
    assert [s.value for s in SupuestoDirecto] == ["14.1", "14.2", "14.3", "14.4", "14.5.a", "14.5.b", "14.6", "14.7"]


@pytest.mark.parametrize("cambios, gran_escala", [({}, False), ({"frecuencia": F.CONTINUA, "titulares_12_meses": 50_000}, True)])
def test_art_12_efectos_solo_si_es_gran_escala(cambios, gran_escala):
    r = calcular(**cambios)
    assert (r.detona_eipd_obligatoria, r.detona_dpo_obligatorio, r.incluir_en_rat, r.medidas_reforzadas) == (gran_escala,) * 4


@pytest.mark.parametrize("cambios", [{"titulares_12_meses": -1}, {"tipos_datos_por_titular": 0}])
def test_cifras_imposibles_se_rechazan(cambios):
    with pytest.raises(ValueError):
        calcular(**cambios)
