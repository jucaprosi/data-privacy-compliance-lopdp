# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤gemini-vertex ¤vertex-cache
"""Listas cerradas de modelos permitidos: Gemini para generación y caché; vectores para embeddings (IA-12)."""

MODELOS_PERMITIDOS: frozenset[str] = frozenset({"gemini-2.5-flash", "gemini-2.5-pro"})

MODELOS_EMBEDDING: tuple[str, ...] = ("text-embedding-005",)
