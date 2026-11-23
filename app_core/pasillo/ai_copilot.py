# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤adpa ¤copiloto-ia
"""Capacidades de la sala AI Copilot para otras salas (solo reexporta; la sala se importa al usarla)."""

# === NORM-03 ===
# ¤vertex-cache Análisis de impacto de una resolución con Gemini; devuelve datos propios, no tipos de la sala.
async def analizar_impacto_normativo(texto_resolucion: str, catalogo: list[dict], org_id: str):
    """(lista de dicts {tipo, referencia_id, motivo, articulos_citados}, traza). `ErrorNegocio` si la IA no responde."""
    from features.ai_copilot import ai_copilot_service

    return await ai_copilot_service.analizar_impacto_normativo(texto_resolucion, catalogo, org_id)


def modelo_de_impacto() -> str:
    from features.ai_copilot import ai_copilot_service

    return ai_copilot_service.MODELO_IMPACTO


def errores_de_negocio():
    """(ErrorNegocio, código de «IA no disponible») para que el llamador los capture sin importar la sala."""
    from features.ai_copilot import ai_copilot_service

    return ai_copilot_service.ErrorNegocio, ai_copilot_service.INFERENCIA_NO_DISPONIBLE
# === fin NORM-03 ===
