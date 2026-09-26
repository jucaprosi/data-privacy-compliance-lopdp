# -*- coding: utf-8 -*-
"""
Regulación Service (Compuerta ADPA)
===================================
Punto de entrada único para la sala estanca de Regulación RAG.
Aisla las dependencias internas y expone servicios controlados.
"""

from typing import Dict, Any
from features.regulacion_rag.services.diff_engine import calcular_impacto_reforma
from features.regulacion_rag.services.rag_orchestrator import procesar_consulta_rag

def evaluar_impacto_resolucion(reforma: Dict[str, Any]) -> Dict[str, Any]:
    """
    Expone el servicio del Diff Engine hacia el exterior.
    No altera auditorías pasadas (garantizado por el diseño del engine).
    """
    return calcular_impacto_reforma(reforma)

def consultar_asistente_rag(consulta: str) -> Dict[str, Any]:
    """
    Expone el servicio del RAG Orchestrator hacia el exterior.
    Garantiza DLP y citación oficial.
    """
    return procesar_consulta_rag(consulta)
