# ¤adpa
"""Capacidades de la sala Diagnóstico para otras salas."""


def catalogo_de_controles() -> list[dict]:
    from features.diagnostico import diagnostico_service

    return diagnostico_service.obtener_catalogo_controles_p1_p80()


def sanitizar_textos(textos: list[str]) -> list[str]:
    """Anonimiza con un solo sanitizador, de modo que un mismo nombre recibe el mismo sustituto."""
    from features.diagnostico import diagnostico_service

    sanitizador = diagnostico_service.NERSanitizer()
    return [sanitizador.sanitize(texto) for texto in textos]
