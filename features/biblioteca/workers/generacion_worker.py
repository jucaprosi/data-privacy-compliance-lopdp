# ¤adpa
# ¤¤developer-architect
# ¤rbac-tenant
"""Worker de los trabajos de generación de Biblioteca (BIB-207).

Cada paso va en su propia transacción, para que el estado sea visible y recuperable:
1. Reclamar (pendiente o vencido → generando) y confirmar: otros ven «Generando».
2. Generar y marcar «listo» y confirmar juntos; si falla, se revierte y se marca «fallido» en otra transacción.
Si el proceso cae entre 1 y 2, el trabajo queda «generando» hasta `TIEMPO_LIMITE` y luego se puede reclamar
o reintentar sin duplicar nada. La cola es la tabla `biblioteca_trabajos`; no hay servicio externo.
"""
import logging
from collections.abc import Callable
from sqlalchemy.ext.asyncio import AsyncSession
from features.biblioteca.services.borradores import FuentesDatos
from features.biblioteca.services.trabajos import Trabajo, ejecutar, obtener, reclamar

registro = logging.getLogger("biblioteca.trabajos")


# ¤adpa
async def procesar(fabrica: Callable[[], AsyncSession], fuentes: FuentesDatos, tenant_id: str, actor: str,
                   trabajo_id: str) -> Trabajo | None:
    """Procesa un trabajo con sesiones nuevas de `fabrica`. Devuelve su estado final, o None si no se pudo leer."""
    try:
        async with fabrica() as session:
            async with session.begin():
                tomado = await reclamar(session, tenant_id, actor, trabajo_id)
        async with fabrica() as session:
            async with session.begin():
                if not tomado:
                    return await obtener(session, tenant_id, actor, trabajo_id)
                return await ejecutar(session, fuentes, tenant_id, actor, trabajo_id)
    except Exception:  # noqa: BLE001  el trabajo queda reintentable al vencer; no se filtran detalles
        registro.exception("Trabajo de generación %s sin procesar", trabajo_id)
        return None


__all__ = ["procesar"]
