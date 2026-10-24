"""Bordes vinculantes de la Res. SPDP-SPD-2026-0005-R."""
import pytest
from features.riesgos_mtge.domain.models import *
from features.riesgos_mtge.services.mtge_calculator import calcular_mtge_actividad

def e(**k):
    d=dict(actividad_rat_id="x", titulares_12_meses=Titulares12Meses.HASTA_1000, tipos_datos=TiposDatos.HASTA_10, categorias_datos=CategoriasDatos.BASICAS, frecuencia=Frecuencia.PUNTUAL, permanencia=Permanencia.OCASIONAL, alcance=AlcanceGeografico.LOCAL); d.update(k); return EntradaCalculoMTGE(**d)

@pytest.mark.parametrize("valor,puntos", [(Titulares12Meses.HASTA_1000,1),(Titulares12Meses.HASTA_10000,2),(Titulares12Meses.HASTA_100000,3),(Titulares12Meses.MAS_DE_100000,4)])
def test_articulo_8_titulares_y_hueco(valor,puntos):
    assert calcular_mtge_actividad(e(titulares_12_meses=valor)).desglose["titulares_12_meses"] == puntos

def test_articulos_9_y_10_umbral_55_vs_6():
    cinco_y_medio = e(titulares_12_meses=Titulares12Meses.HASTA_10000, tipos_datos=TiposDatos.HASTA_30, categorias_datos=CategoriasDatos.BASICAS, frecuencia=Frecuencia.PUNTUAL, permanencia=Permanencia.OCASIONAL, alcance=AlcanceGeografico.LOCAL)
    seis = e(titulares_12_meses=Titulares12Meses.HASTA_10000, tipos_datos=TiposDatos.HASTA_30, categorias_datos=CategoriasDatos.BASICAS, frecuencia=Frecuencia.PERIODICA_O_RECURRENTE, permanencia=Permanencia.OCASIONAL, alcance=AlcanceGeografico.LOCAL)
    assert calcular_mtge_actividad(cinco_y_medio).puntaje_mtge == 5.5
    assert not calcular_mtge_actividad(cinco_y_medio).es_gran_escala
    assert calcular_mtge_actividad(seis).puntaje_mtge == 6
    assert calcular_mtge_actividad(seis).es_gran_escala

@pytest.mark.parametrize("supuesto", list(SupuestoDirecto))
def test_articulo_14_califica_directamente(supuesto):
    resultado = calcular_mtge_actividad(e(supuestos_directos=(supuesto,)))
    assert resultado.es_gran_escala and supuesto.value in resultado.supuestos_directos
