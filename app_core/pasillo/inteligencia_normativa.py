# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
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


async def fecha_vigencia_de(id_resolucion):
    """Fecha de entrada en vigencia de la resolución, o None (NORM-07 R3)."""
    from features.inteligencia_normativa import inteligencia_normativa_service as svc

    return await svc.fecha_vigencia_de(id_resolucion)


async def fecha_vigencia_por_url(url):
    """Fecha de vigencia de la resolución con esa URL oficial (la usa BIB-407), o None (NORM-07 R3)."""
    from features.inteligencia_normativa import inteligencia_normativa_service as svc

    return await svc.fecha_vigencia_por_url(url)
