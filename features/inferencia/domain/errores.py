# ¤gemini-vertex
"""Errores de dominio de la sala inferencia."""

MOTIVO_NEUTRO = (
    "La inferencia con IA no está disponible en este momento. "
    "Contacte a la persona administradora de la plataforma."
)


class InferenciaNoDisponible(Exception):
    """Vertex no responde, falta permiso o configuración, o la respuesta no es válida (falla cerrada)."""

    def __init__(self, motivo: str = MOTIVO_NEUTRO) -> None:
        super().__init__(motivo)
        self.motivo = motivo
