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
