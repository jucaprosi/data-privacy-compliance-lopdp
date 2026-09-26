"""Test del motor MTGE (Tratamientos a Gran Escala - Res. SPDP-SPD-2026-0005-R).
Invariante: INV_LOPDP_MTGE_DETERMINISTIC_TRIGGER.
"""
from features.riesgos_mtge.riesgos_mtge_service import evaluar_gran_escala_mtge
from features.riesgos_mtge.domain.models import EntradaCalculoMTGE, AlcanceGeografico

def test_mtge_caso_directo_salud():
    """Un tratamiento masivo de salud activa Gran Escala por caso directo."""
    entrada = EntradaCalculoMTGE(
        actividad_rat_id="RAT-SALUD-01",
        numero_titulares=5000,
        volumen_datos_por_titular=20,
        trata_datos_sensibles=True,
        frecuencia_permanente=True,
        alcance=AlcanceGeografico.PROVINCIAL,
        es_caso_directo_salud_masiva=True,
    )
    res = evaluar_gran_escala_mtge(entrada)
    assert res.puntaje_mtge == 150.0
    assert res.es_gran_escala is True
    assert res.detona_dpo_obligatorio is True
    assert res.detona_eipd_obligatoria is True
    assert res.criterio_activacion == "CASO_DIRECTO_SALUD"

def test_mtge_calculo_parametrico_umbral():
    """Un tratamiento con alto volumen y datos sensibles supera el umbral paramétrico."""
    entrada = EntradaCalculoMTGE(
        actividad_rat_id="RAT-RETAIL-01",
        numero_titulares=60000, # 50 puntos
        volumen_datos_por_titular=10,
        trata_datos_sensibles=True, # 35 puntos
        frecuencia_permanente=True, # 20 puntos
        alcance=AlcanceGeografico.NACIONAL, # 25 puntos -> Total: 130 puntos (>= 100)
    )
    res = evaluar_gran_escala_mtge(entrada)
    assert res.puntaje_mtge == 130.0
    assert res.es_gran_escala is True
    assert res.detona_dpo_obligatorio is True
    assert res.detona_eipd_obligatoria is True
    assert res.criterio_activacion == "UMBRAL_PUNTAJE"

def test_mtge_tratamiento_ordinario_no_alcanza():
    """Un tratamiento local con pocos titulares y datos no sensibles no detona gran escala."""
    entrada = EntradaCalculoMTGE(
        actividad_rat_id="RAT-LOCAL-01",
        numero_titulares=300, # 5 puntos
        volumen_datos_por_titular=3,
        trata_datos_sensibles=False, # 0 puntos
        frecuencia_permanente=False, # 0 puntos
        alcance=AlcanceGeografico.LOCAL_CANTONAL, # 5 puntos -> Total: 10 puntos (< 100)
    )
    res = evaluar_gran_escala_mtge(entrada)
    assert res.puntaje_mtge == 10.0
    assert res.es_gran_escala is False
    assert res.detona_dpo_obligatorio is False
    assert res.detona_eipd_obligatoria is False
    assert res.criterio_activacion == "NO_ALCANZA"

