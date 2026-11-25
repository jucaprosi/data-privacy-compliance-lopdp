# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤adpa ¤cita-verificada
# ¤¤developer-architect
"""BIB-407: lectura de la comparación de una versión con la publicada del mismo código. Solo lee (R4)."""
import inspect
from datetime import date

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.errors import ErrorNegocio
from features.biblioteca.domain.comparacion import Comparacion, comparar, elegir_base
from features.biblioteca.domain.editorial import Capacidad
from features.biblioteca.services.autorizacion import autorizar
from features.biblioteca.services.catalogo import leer_citas

_VERSION = text(
    "SELECT id, codigo, estado, cuerpo_md, redactada_por, cambios_ia FROM biblioteca_versiones WHERE id=:id"
)
_DEL_CODIGO = text(
    "SELECT id, estado, cuerpo_md FROM biblioteca_versiones WHERE codigo=:codigo AND formato='MD'"
)
_CAPACIDADES = {Capacidad.EDITOR.value, Capacidad.TECNICO.value, Capacidad.PUBLICADOR.value}


# ¤adpa
async def _vigencias(urls: set[str]) -> dict[str, date | None]:
    """R3: la fecha de vigencia sale del pasillo normativo (NORM-07) si ya la ofrece; si no, va nula."""
    from app_core.pasillo import inteligencia_normativa as pasillo_normativa

    leer = getattr(pasillo_normativa, "fecha_vigencia_de", None)
    if leer is None:
        return {}
    fechas = {}
    for url in urls:
        valor = leer(url)
        fechas[url] = await valor if inspect.isawaitable(valor) else valor
    return fechas


# ¤adpa
async def comparar_version(session: AsyncSession, actor: str, identificador: str,
                           vigencias: dict[str, date | None] | None = None) -> Comparacion:
    """La versión `identificador` frente a la publicada de su código. `vigencias` se inyecta en pruebas."""
    permisos = await autorizar(session, actor)
    if not _CAPACIDADES & set(permisos):
        raise ErrorNegocio("BIB_SIN_CAPACIDAD")
    version = (await session.execute(_VERSION, {"id": identificador})).mappings().first()
    if not version:
        raise ErrorNegocio("BIB_NO_ENCONTRADA")
    del_codigo = [dict(f) for f in (await session.execute(_DEL_CODIGO, {"codigo": version["codigo"]})).mappings().all()]
    base = elegir_base(del_codigo, identificador)
    citas = leer_citas() or {}
    cambios_ia = version["cambios_ia"] if version["redactada_por"] == "ia" else None
    if vigencias is None:
        urls = {citas.get("fuentes", {}).get(citas.get("fuente_de", {}).get(c.get("cita")), {}).get("url")
                for c in (cambios_ia or [])}
        vigencias = await _vigencias({u for u in urls if u})
    return comparar(base["cuerpo_md"] if base else None, version["cuerpo_md"] or "", cambios_ia, citas,
                    lambda url: vigencias.get(url))
