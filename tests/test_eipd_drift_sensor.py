# -*- coding: utf-8 -*-
"""
Tests para el Sensor de Deriva de Riesgo EIPD (Aporte 29)
"""

import pytest
from features.rat.domain.models import ActividadRAT, EIPD, EstadoEIPD, CategoriaTitular
from features.rat.services.mtge_engine import evaluar_deriva_riesgo_eipd, repo_eipd

@pytest.fixture(autouse=True)
def setup_teardown():
    # Limpiar estado antes de cada test para aislar el arnés
    repo_eipd.limpiar()
    yield
    repo_eipd.limpiar()

def test_deriva_riesgo_volumen_excedido():
    """Valida la transición a Obsoleto cuando el volumen supera el 25%."""
    rat = ActividadRAT(
        id="RAT-VOL-01",
        tenant_id="TENANT-1",
        volumen_titulares_estimado=1250 # Justo en el límite del 25% de 1000
    )
    
    eipd = EIPD(
        rat_id=rat.id,
        estado=EstadoEIPD.ACTIVA,
        volumen_titulares_aprobacion=1000,
        categorias_datos_aprobacion=["BASICOS"]
    )
    repo_eipd.guardar(eipd)
    
    # Evaluar justo en el límite (no debe mutar)
    evaluar_deriva_riesgo_eipd(rat)
    assert repo_eipd.obtener_activa_por_rat(rat.id) is not None
    assert eipd.estado == EstadoEIPD.ACTIVA
    
    # Supera el 25%
    rat.volumen_titulares_estimado = 1251
    evaluar_deriva_riesgo_eipd(rat)
    
    assert eipd.estado == EstadoEIPD.OBSOLETA_REQUIERE_ACTUALIZACION
    assert repo_eipd.obtener_activa_por_rat(rat.id) is None

def test_deriva_riesgo_adicion_biometricos():
    """Valida la transición a Obsoleto cuando se añade la categoría BIOMETRICOS."""
    rat = ActividadRAT(
        id="RAT-BIO-01",
        tenant_id="TENANT-1",
        volumen_titulares_estimado=1000,
        categorias_datos=["FINANCIEROS"]
    )
    
    eipd = EIPD(
        rat_id=rat.id,
        estado=EstadoEIPD.ACTIVA,
        volumen_titulares_aprobacion=1000,
        categorias_datos_aprobacion=["FINANCIEROS"]
    )
    repo_eipd.guardar(eipd)
    
    # No hay biométricos aún, debe seguir activa
    evaluar_deriva_riesgo_eipd(rat)
    assert eipd.estado == EstadoEIPD.ACTIVA
    
    # Se añaden datos biométricos
    rat.categorias_datos.append("BIOMETRICOS")
    evaluar_deriva_riesgo_eipd(rat)
    
    assert eipd.estado == EstadoEIPD.OBSOLETA_REQUIERE_ACTUALIZACION

def test_sin_deriva_riesgo():
    """Valida que la EIPD se mantenga ACTIVA si no hay deriva significativa."""
    rat = ActividadRAT(
        id="RAT-OK-01",
        tenant_id="TENANT-1",
        volumen_titulares_estimado=1100, # Menos del 25%
        categorias_datos=["SALUD"]
    )
    
    eipd = EIPD(
        rat_id=rat.id,
        estado=EstadoEIPD.ACTIVA,
        volumen_titulares_aprobacion=1000,
        categorias_datos_aprobacion=["SALUD"] # Ya estaba aprobado
    )
    repo_eipd.guardar(eipd)
    
    evaluar_deriva_riesgo_eipd(rat)
    assert eipd.estado == EstadoEIPD.ACTIVA
