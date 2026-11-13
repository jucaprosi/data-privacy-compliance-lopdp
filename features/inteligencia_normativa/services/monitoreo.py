# ¤vigilancia-spdp ¤inteligencia-normativa
"""Corrida de monitoreo de la SPDP (NORM-01): descarga, valida, guarda el original y registra la corrida.

Invocable a mano. Se programa a las 05:00 en `America/Guayaquil` con Cloud Scheduler tras GCP-01 (brief del
propietario). El original se guarda intacto, antes de registrar nada, con el hash como nombre; va a Cloud
Storage (`gs://evydentia-corpus-normativo/spdp/`) con las credenciales por defecto, sin claves, y nunca a R2.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Callable, Protocol

from sqlalchemy import text

from features.inteligencia_normativa.domain.errores import (
    AlmacenNoDisponible,
    ErrorNormativo,
    FuenteBloqueada,
)
from features.inteligencia_normativa.schemas import ResumenCorrida
from features.inteligencia_normativa.services import deduplicacion
from features.inteligencia_normativa.services.conector_spdp import SECCIONES, ConectorSpdp

VARIABLE_BUCKET = "GCP_STORAGE_BUCKET_NORMATIVO"
TIPO_PDF = "application/pdf"


class AlmacenOriginales(Protocol):
    def guardar(self, clave: str, contenido: bytes) -> bool:
        """Guarda con escritura única. True si lo creó; False si ya existía (mismo hash, mismo nombre)."""
        ...


class AlmacenGcsNormativo:
    """Escritura única en el bucket del corpus: `if_generation_match=0`, sin borrar nunca."""

    def __init__(self, bucket: Any) -> None:
        self._bucket = bucket

    def guardar(self, clave: str, contenido: bytes) -> bool:
        from google.api_core.exceptions import PreconditionFailed  # type: ignore[import-not-found]

        try:
            self._bucket.blob(clave).upload_from_string(contenido, content_type=TIPO_PDF, if_generation_match=0)
        except PreconditionFailed:
            return False
        return True


def almacen_por_defecto() -> AlmacenOriginales:
    """Almacén real; fuera de Cloud Run o sin bucket falla cerrado y no intenta conectar."""
    from app_core.config import corre_en_cloud_run

    bucket = os.environ.get(VARIABLE_BUCKET, "").strip()
    if not corre_en_cloud_run() or not bucket:
        raise AlmacenNoDisponible(VARIABLE_BUCKET)
    import google.auth  # type: ignore[import-not-found]
    from google.cloud import storage  # type: ignore[import-not-found]

    credenciales, proyecto = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    return AlmacenGcsNormativo(storage.Client(project=proyecto, credentials=credenciales).bucket(bucket))


def _sesion_por_defecto():
    from app_core.db.session import async_session_factory

    return async_session_factory()


async def _abrir_corrida(session, origen: str, inicio: datetime) -> str:
    return (await session.execute(
        text("INSERT INTO normativa_monitoreo_logs (inicio, origen, estado) VALUES (:i, :o, 'fallida') RETURNING id::text"),
        {"i": inicio, "o": origen},
    )).scalar_one()


async def _cerrar_corrida(session, id_: str, fin: datetime, resumen: dict, estado: str) -> None:
    await session.execute(
        text("UPDATE normativa_monitoreo_logs SET fin = :f, documentos_vistos = :v, nuevos = :n, "
             "versiones_nuevas = :vn, errores = :e, estado = :s, codigos_error = CAST(:c AS jsonb) "
             "WHERE id = CAST(:id AS uuid)"),
        {"f": fin, "v": resumen["vistos"], "n": resumen["nuevos"], "vn": resumen["versiones"],
         "e": len(resumen["codigos"]), "s": estado, "c": _json(resumen["codigos"]), "id": id_},
    )


def _json(valor: list[str]) -> str:
    import json

    return json.dumps(valor)


async def ejecutar(
    origen: str,
    *,
    conector: ConectorSpdp,
    almacen: AlmacenOriginales | None = None,
    sesion_factory: Callable[[], Any] = _sesion_por_defecto,
    ahora: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
) -> ResumenCorrida:
    """Una corrida: secciones en serie, documento por documento. Cada corrida queda registrada."""
    inicio = ahora()
    almacen = almacen or almacen_por_defecto()
    resumen = {"vistos": 0, "nuevos": 0, "versiones": 0, "codigos": []}
    bloqueada = False

    async with sesion_factory() as sesion:
        id_corrida = await _abrir_corrida(sesion, origen, inicio)
        await sesion.commit()  # la corrida existe aunque el proceso se caiga después

        async with conector:
            for seccion in SECCIONES:
                if bloqueada:
                    break
                try:
                    enlaces = await conector.listar(seccion)
                except FuenteBloqueada as exc:
                    resumen["codigos"].append(exc.codigo)
                    bloqueada = True
                    break
                except ErrorNormativo as exc:
                    resumen["codigos"].append(exc.codigo)
                    continue
                for enlace in enlaces:
                    resumen["vistos"] += 1
                    try:
                        await _procesar(sesion, conector, almacen, enlace, resumen)
                        await sesion.commit()
                    except FuenteBloqueada as exc:
                        await sesion.rollback()
                        resumen["codigos"].append(exc.codigo)
                        bloqueada = True
                        break
                    except ErrorNormativo as exc:
                        await sesion.rollback()
                        resumen["codigos"].append(exc.codigo)

        estado = "fallida" if bloqueada else ("parcial" if resumen["codigos"] else "ok")
        fin = ahora()
        await _cerrar_corrida(sesion, id_corrida, fin, resumen, estado)
        await sesion.commit()

    return ResumenCorrida(
        id=id_corrida, origen=origen, estado=estado, inicio=inicio, fin=fin,
        documentos_vistos=resumen["vistos"], nuevos=resumen["nuevos"], versiones_nuevas=resumen["versiones"],
        errores=len(resumen["codigos"]), codigos_error=list(resumen["codigos"]),
    )


async def _procesar(sesion, conector, almacen, enlace, resumen) -> None:
    nombre_archivo = enlace.url.rsplit("/", 1)[-1]
    numero, anio = deduplicacion.reconocer_numero(enlace.titulo, nombre_archivo)
    descarga = await conector.descargar(enlace.url)
    clave = deduplicacion.ruta_original(descarga.sha256)
    # R1: el original queda guardado, intacto, antes de registrar o extraer nada.
    almacen.guardar(clave, descarga.contenido)
    decision = await deduplicacion.aplicar(sesion, deduplicacion.DocumentoDescargado(
        numero_resolucion=numero, anio_emision=anio, titulo=enlace.titulo or numero, url_fuente=enlace.url,
        seccion_fuente=enlace.seccion, sha256=descarga.sha256, ruta_original=clave, tamano_bytes=descarga.tamano,
    ))
    if decision is deduplicacion.Decision.NUEVA:
        resumen["nuevos"] += 1
    elif decision is deduplicacion.Decision.VERSION:
        resumen["versiones"] += 1
