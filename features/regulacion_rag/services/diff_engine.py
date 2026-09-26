# -*- coding: utf-8 -*-
"""
Diff Engine para Reformas SPDP
==============================
Motor de cálculo de impacto de reformas de la Superintendencia de Protección de Datos Personales (SPDP).
Calcula qué dominios G01-G16 y qué actividades del RAT se ven impactadas.
"""

from typing import Dict, List, Any

def calcular_impacto_reforma(reforma: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcula el impacto de una reforma SPDP sobre los dominios y el RAT.
    
    Args:
        reforma: Diccionario con la estructura de la resolución (YAML/JSON).
                 Ejemplo esperado:
                 {
                     "id_resolucion": "SPDP-2026-001",
                     "articulos_afectados": ["Art. 12", "Art. 14"],
                     "palabras_clave": ["consentimiento", "transferencia internacional"]
                 }
                 
    Returns:
        Diccionario con la lista de revalidaciones sugeridas, dominios y actividades RAT impactadas.
    """
    # Mapeo estático básico para el demo/motor inicial
    # En un entorno real, esto consultaría la base de conocimiento vectorial o grafo.
    mapa_dominios = {
        "consentimiento": ["G03", "G04"],
        "transferencia internacional": ["G12"],
        "medidas de seguridad": ["G08", "G09"],
        "derechos arco": ["G05", "G06"]
    }
    
    mapa_rat = {
        "consentimiento": ["Recopilación de Datos", "Marketing Directo"],
        "transferencia internacional": ["Uso de Cloud Externa", "Compartición con Terceros"],
        "medidas de seguridad": ["Almacenamiento en Base de Datos"],
        "derechos arco": ["Atención al Cliente"]
    }
    
    dominios_impactados = set()
    actividades_rat_impactadas = set()
    
    palabras_clave = reforma.get("palabras_clave", [])
    
    for pk in palabras_clave:
        pk_lower = pk.lower()
        if pk_lower in mapa_dominios:
            dominios_impactados.update(mapa_dominios[pk_lower])
        if pk_lower in mapa_rat:
            actividades_rat_impactadas.update(mapa_rat[pk_lower])
            
    revalidaciones_sugeridas = [
        f"Revisar controles del dominio {dom}" for dom in sorted(dominios_impactados)
    ] + [
        f"Actualizar evaluación de riesgo para actividad RAT: {act}" for act in sorted(actividades_rat_impactadas)
    ]
    
    return {
        "resolucion_origen": reforma.get("id_resolucion", "DESCONOCIDA"),
        "dominios_impactados": sorted(list(dominios_impactados)),
        "actividades_rat_impactadas": sorted(list(actividades_rat_impactadas)),
        "revalidaciones_sugeridas": revalidaciones_sugeridas,
        "nota": "Las auditorías pasadas permanecen inalteradas (Invariante Histórico)."
    }
