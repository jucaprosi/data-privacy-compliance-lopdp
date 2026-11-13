# ¤adpa
"""Capacidades de la sala Inferencia para otras salas (solo reexporta; la sala se importa al usarla)."""


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
    from features.inferencia.domain.prompts import PromptVersionado

    return PromptVersionado(id=id, version=version, sistema=sistema, plantilla=plantilla)


async def generar_trazado(prompt, valores, esquema, *, modelo, org_id, corpus_sha256=None):
    from features.inferencia import inferencia_service

    return await inferencia_service.generar_trazado(
        prompt, valores, esquema, modelo=modelo, org_id=org_id, corpus_sha256=corpus_sha256
    )


async def registrar_traza(session, traza, entidad, entidad_id):
    from features.inferencia import inferencia_service

    return await inferencia_service.registrar_traza(session, traza, entidad, entidad_id)
