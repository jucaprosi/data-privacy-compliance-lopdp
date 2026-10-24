"""Compuerta del motor MTGE (Res. SPDP-SPD-2026-0005-R).

Los bordes de la norma están en tests/test_mtge_resolucion_0005.py; aquí, los tres caminos del
resultado a través de la compuerta pública de la sala.
Invariante: INV_LOPDP_MTGE_DETERMINISTIC_TRIGGER.
"""
from features.riesgos_mtge.riesgos_mtge_service import (
    AlcanceGeografico,
    CategoriasDatos,
    EntradaCalculoMTGE,
    Frecuencia,
    Permanencia,
    SupuestoDirecto,
    evaluar_gran_escala_mtge,
)


def entrada(**cambios) -> EntradaCalculoMTGE:
    base = dict(
        actividad_rat_id="RAT-01", titulares_12_meses=800, tipos_datos_por_titular=25,
        categorias_datos=CategoriasDatos.BASICAS, frecuencia=Frecuencia.PERIODICA,
        permanencia=Permanencia.TEMPORAL, alcance=AlcanceGeografico.LOCAL,
    )
    return EntradaCalculoMTGE(**{**base, **cambios})


def test_historia_clinica_es_gran_escala_directa():
    """Ejemplo de la matriz SALUDATA: consultorio con 800 pacientes, calificación directa 14.1."""
    r = evaluar_gran_escala_mtge(entrada(supuestos_directos=(SupuestoDirecto.SALUD_O_CATEGORIAS_ESPECIALES,)))
    assert r.es_gran_escala and r.criterio_activacion == "CALIFICACION_DIRECTA_ART_14"
    assert r.detona_dpo_obligatorio and r.detona_eipd_obligatoria


def test_puntaje_que_alcanza_el_umbral():
    r = evaluar_gran_escala_mtge(entrada(permanencia=Permanencia.PROLONGADA, alcance=AlcanceGeografico.NACIONAL))
    assert r.puntaje_mtge == 1 + 1 + 0.5 + 1 + 2 + 2
    assert r.es_gran_escala and r.criterio_activacion == "PUNTAJE_ART_10"


def test_tratamiento_ordinario_no_alcanza():
    r = evaluar_gran_escala_mtge(entrada())
    assert r.puntaje_mtge == 1 + 1 + 0.5 + 1 + 1 + 1
    assert not r.es_gran_escala and not r.detona_dpo_obligatorio
    assert r.criterio_activacion == "NO_ALCANZA_UMBRAL"
