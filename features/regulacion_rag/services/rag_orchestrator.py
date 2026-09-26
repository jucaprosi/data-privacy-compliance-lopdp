# -*- coding: utf-8 -*-
"""
RAG Orchestrator
================
Orquestador RAG para consultas normativas.
Aplica sanitización DLP, búsqueda en corpus legal cerrado y síntesis con citación estricta.
"""

from typing import Dict, Any, List
from app_core.dlp_sanitizer import sanitizar_texto_pii

# Simulación de un Corpus Legal Cerrado en Memoria
# En la vida real, se leería de data/corpus_normativo/
CORPUS_LEGAL = [
    {
        "id": "ART_12_LOPDP",
        "texto": "El consentimiento para el tratamiento de datos personales debe ser libre, específico, informado e inequívoco.",
        "citacion": "Art. 12, LOPDP (Vigente desde 26/05/2021)"
    },
    {
        "id": "RES_001_SPDP",
        "texto": "Las transferencias internacionales requieren la verificación de niveles adecuados de protección en el país de destino.",
        "citacion": "Resolución 001-SPDP-2024 (Vigente desde 15/01/2024)"
    }
]

def buscar_en_corpus(query: str) -> List[Dict[str, str]]:
    """Simula una búsqueda vectorial / BM25 en el corpus cerrado."""
    resultados = []
    query_lower = query.lower()
    for doc in CORPUS_LEGAL:
        if any(palabra in doc["texto"].lower() for palabra in query_lower.split()):
            resultados.append(doc)
    return resultados

def procesar_consulta_rag(consulta_usuario: str) -> Dict[str, Any]:
    """
    Procesa una consulta mediante el pipeline RAG estricto.
    
    Paso 1: Sanitización DLP.
    Paso 2: Búsqueda en corpus cerrado.
    Paso 3: Síntesis con citación formal.
    """
    # Paso 1: Sanitización
    consulta_segura = sanitizar_texto_pii(consulta_usuario)
    
    # Paso 2: Búsqueda
    documentos_recuperados = buscar_en_corpus(consulta_segura)
    
    # Paso 3: Síntesis
    if not documentos_recuperados:
        respuesta_sintetizada = (
            "INCERTIDUMBRE EXPLÍCITA: No se encontró norma vinculante aplicable "
            "en el corpus normativo cerrado para la consulta realizada."
        )
        citaciones = []
    else:
        # Generar una síntesis (simulada aquí conectando los textos recuperados)
        textos = [doc["texto"] for doc in documentos_recuperados]
        respuesta_sintetizada = "De acuerdo a la normativa vigente: " + " ".join(textos)
        citaciones = [doc["citacion"] for doc in documentos_recuperados]
        
    return {
        "consulta_original_sanitizada": consulta_segura,
        "respuesta": respuesta_sintetizada,
        "citaciones_formales": citaciones
    }
