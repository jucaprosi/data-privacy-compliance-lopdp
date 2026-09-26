# -*- coding: utf-8 -*-
"""
Motor Reactivo de Re-Evaluación Continua EIPD (Sensor de Deriva de Riesgo)
=========================================================================
Implementa la optimización del Aporte 29 para la transición automática de estados EIPD.
"""

from typing import Optional
from features.rat.domain.models import ActividadRAT, EIPD, EstadoEIPD

class EIPDRepository:
    def __init__(self):
        self._store = {}
        
    def guardar(self, eipd: EIPD) -> EIPD:
        self._store[eipd.id] = eipd
        return eipd
        
    def obtener_activa_por_rat(self, rat_id: str) -> Optional[EIPD]:
        for eipd in self._store.values():
            if eipd.rat_id == rat_id and eipd.estado == EstadoEIPD.ACTIVA:
                return eipd
        return None

    def limpiar(self):
        self._store.clear()

# Repositorio Singleton en memoria para tests
repo_eipd = EIPDRepository()

def evaluar_deriva_riesgo_eipd(rat_actualizado: ActividadRAT) -> Optional[EIPD]:
    """
    Sensor de Deriva de Riesgo:
    Si el tenant ya tiene una EIPD activa, pero su RAT se altera sustancialmente:
    1. Volumen de titulares > 25% respecto a aprobación.
    2. Adición de categoría 'BIOMETRICOS' que no estaba antes.
    La EIPD pasa a 'Obsoleto - Requiere Actualización'.
    """
    eipd_activa = repo_eipd.obtener_activa_por_rat(rat_actualizado.id)
    if not eipd_activa:
        return None

    mutar = False
    
    # Regla 1: Incremento de volumen > 25%
    limite_volumen = eipd_activa.volumen_titulares_aprobacion * 1.25
    if rat_actualizado.volumen_titulares_estimado > limite_volumen:
        mutar = True
        
    # Regla 2: Nueva categoría Biométricos
    categorias_actuales = [c.upper() for c in rat_actualizado.categorias_datos]
    categorias_aprobacion = [c.upper() for c in eipd_activa.categorias_datos_aprobacion]
    
    if "BIOMETRICOS" in categorias_actuales and "BIOMETRICOS" not in categorias_aprobacion:
        mutar = True

    if mutar:
        eipd_activa.estado = EstadoEIPD.OBSOLETA_REQUIERE_ACTUALIZACION
        repo_eipd.guardar(eipd_activa)
        
    return eipd_activa
