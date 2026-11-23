# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤gemini-vertex ¤vertex-cache
"""Única fuente de los modelos (IA-13 R1): Gemini para generación y caché; vectores para embeddings (IA-12).

Ninguna otra sala escribe el nombre de un modelo: lo toma del pasillo de inferencia.
"""

MODELO_GENERACION: str = "gemini-3.8-flash"

MODELOS_PERMITIDOS: frozenset[str] = frozenset({MODELO_GENERACION})

MODELO_EMBEDDING: str = "text-embedding-005"

MODELOS_EMBEDDING: tuple[str, ...] = (MODELO_EMBEDDING,)
