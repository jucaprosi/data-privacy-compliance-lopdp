# ¤adpa ¤inteligencia-normativa
"""Capacidades de la sala Inteligencia Normativa para otras salas (solo reexporta; se importa al usarla)."""


async def ejecutar_monitoreo(origen="manual"):
    from features.inteligencia_normativa import inteligencia_normativa_service as svc

    return await svc.ejecutar_monitoreo(origen)


async def listar_resoluciones(filtros=None):
    from features.inteligencia_normativa import inteligencia_normativa_service as svc

    return await svc.listar_resoluciones(filtros)


async def obtener_resolucion(id_resolucion):
    from features.inteligencia_normativa import inteligencia_normativa_service as svc

    return await svc.obtener_resolucion(id_resolucion)


def filtros(**campos):
    """Filtros de `listar_resoluciones` (estado, seccion, anio, limite)."""
    from features.inteligencia_normativa import inteligencia_normativa_service as svc

    return svc.FiltrosResoluciones(**campos)


def error_normativo():
    """La clase base de los errores de la sala, para que el llamador la capture sin importarla."""
    from features.inteligencia_normativa import inteligencia_normativa_service as svc

    return svc.ErrorNormativo
