# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤adpa
"""Capacidades de la sala Inferencia para otras salas (solo reexporta; la sala se importa al usarla)."""

_CONSTANTES_DE_MODELO = frozenset({"MODELO_GENERACION", "MODELO_EMBEDDING"})


def __getattr__(nombre):
    """`MODELO_GENERACION` y `MODELO_EMBEDDING` (IA-13 R1): la única fuente es la sala, resuelta al pedirlos."""
    if nombre in _CONSTANTES_DE_MODELO:
        from features.inferencia import inferencia_service

        return getattr(inferencia_service, nombre)
    raise AttributeError(f"module {__name__!r} has no attribute {nombre!r}")


async def generar_estructurado(sistema, usuario, esquema, *, modelo, org_id):
    from features.inferencia import inferencia_service

    return await inferencia_service.generar_estructurado(sistema, usuario, esquema, modelo=modelo, org_id=org_id)


def estado():
    from features.inferencia import inferencia_service

    return inferencia_service.estado()


def errores():
    """(InferenciaNoDisponible, MOTIVO_NEUTRO) para que el llamador capture el error de dominio."""
    from features.inferencia import inferencia_service

    return inferencia_service.InferenciaNoDisponible, inferencia_service.MOTIVO_NEUTRO


def prompt_versionado(id, version, sistema, plantilla):
    """Declara un prompt versionado (`<sala>.<nombre>`); las salas lo usan en `features/<sala>/ai/prompts.py`."""
    from features.inferencia.inferencia_service import PromptVersionado

    return PromptVersionado(id=id, version=version, sistema=sistema, plantilla=plantilla)


async def generar_trazado(prompt, valores, esquema, *, modelo, org_id, corpus_sha256=None):
    from features.inferencia import inferencia_service

    return await inferencia_service.generar_trazado(
        prompt, valores, esquema, modelo=modelo, org_id=org_id, corpus_sha256=corpus_sha256
    )


async def registrar_traza(session, traza, entidad, entidad_id):
    from features.inferencia import inferencia_service

    return await inferencia_service.registrar_traza(session, traza, entidad, entidad_id)


async def vectorizar(textos, modelo):
    from features.inferencia import inferencia_service

    return await inferencia_service.vectorizar(textos, modelo)


def crear_cache_contenido(modelo, contenido, ttl_segundos):
    from features.inferencia import inferencia_service

    return inferencia_service.crear_cache_contenido(modelo, contenido, ttl_segundos)


async def transcribir_pdf(pdf, prompt, *, modelo):
    """NORM-06: texto de un PDF escaneado y su traza; no consume tope."""
    from features.inferencia import inferencia_service

    return await inferencia_service.transcribir_pdf(pdf, prompt, modelo=modelo)
