"""Test del motor MTGE (Tratamientos a Gran Escala - Res. SPDP-SPD-2026-0005-R).
Invariante: INV_LOPDP_MTGE_DETERMINISTIC_TRIGGER.
"""
from features.riesgos_mtge.riesgos_mtge_service import evaluar_gran_escala_mtge
from features.riesgos_mtge.domain.models import EntradaCalculoMTGE, Titulares12Meses, TiposDatos, CategoriasDatos, Frecuencia, Permanencia, AlcanceGeografico, SupuestoDirecto

def entrada(**cambios):
    base = dict(actividad_rat_id="RAT-01", titulares_12_meses=Titulares12Meses.HASTA_1000, tipos_datos=TiposDatos.HASTA_10, categorias_datos=CategoriasDatos.BASICAS, frecuencia=Frecuencia.PUNTUAL, permanencia=Permanencia.OCASIONAL, alcance=AlcanceGeografico.LOCAL)
    base.update(cambios)
    return EntradaCalculoMTGE(**base)

def test_mtge_caso_directo_salud():
    """Un tratamiento masivo de salud activa Gran Escala por caso directo."""
    res = evaluar_gran_escala_mtge(entrada(supuestos_directos=(SupuestoDirecto.SALUD_O_CATEGORIAS_ESPECIALES,)))
    assert res.puntaje_mtge == 0
    assert res.es_gran_escala is True
    assert res.detona_dpo_obligatorio is True
    assert res.detona_eipd_obligatoria is True
    assert res.criterio_activacion == "CASO_DIRECTO_ART_14"

def test_mtge_calculo_parametrico_umbral():
    """Un tratamiento con alto volumen y datos sensibles supera el umbral paramétrico."""
    res = evaluar_gran_escala_mtge(entrada(titulares_12_meses=Titulares12Meses.MAS_DE_100000, tipos_datos=TiposDatos.MAS_DE_100, categorias_datos=CategoriasDatos.MULTIPLES_ESPECIALES_O_VULNERABLES_O_PENALES, frecuencia=Frecuencia.CONTINUA_O_TIEMPO_REAL, permanencia=Permanencia.PROLONGADA_DESDE_3_ANOS, alcance=AlcanceGeografico.GLOBAL_O_TRANSFRONTERIZO))
    assert res.puntaje_mtge == 17.0
    assert res.es_gran_escala is True
    assert res.detona_dpo_obligatorio is True
    assert res.detona_eipd_obligatoria is True
    assert res.criterio_activacion == "PUNTAJE_ART_8_10"

def test_mtge_tratamiento_ordinario_no_alcanza():
    """Un tratamiento local con pocos titulares y datos no sensibles no detona gran escala."""
    res = evaluar_gran_escala_mtge(entrada())
    assert res.puntaje_mtge == 4.0
    assert res.es_gran_escala is False
    assert res.detona_dpo_obligatorio is False
    assert res.detona_eipd_obligatoria is False
    assert res.criterio_activacion == "NO_ALCANZA_UMBRAL"

