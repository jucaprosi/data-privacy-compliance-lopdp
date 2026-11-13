# ¤inteligencia-normativa ¤vigilancia-spdp
"""Deduplicación en tres capas y persistencia del corpus (NORM-01, R3 y R5).

1. Mismo número y año con el mismo hash: no hace nada.
2. Mismo número y año con otro hash: crea una versión inmutable; el original anterior queda intacto.
3. Número nuevo: crea la resolución en `pendiente_revision`. Nunca se asigna `vigente`, `reformada` ni
   `derogada`: eso lo hace una persona (R5).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from sqlalchemy import text

from features.inteligencia_normativa.domain.errores import NumeroNoReconocido

_NUMERO = re.compile(r"\b(SPDP-[A-Z0-9]+-(\d{4})-\d{3,5}(?:-[A-Z]{1,3})?)\b", re.I)


class Decision(str, Enum):
    NADA = "nada"
    VERSION = "version"
    NUEVA = "nueva"


@dataclass(frozen=True)
class DocumentoDescargado:
    numero_resolucion: str
    anio_emision: int
    titulo: str
    url_fuente: str
    seccion_fuente: str
    sha256: str
    ruta_original: str
    tamano_bytes: int


def reconocer_numero(*textos: str) -> tuple[str, int]:
    """(número, año) de la primera pista que lo traiga: título del enlace o nombre del archivo."""
    for texto in textos:
        coincidencia = _NUMERO.search(texto or "")
        if coincidencia:
            return coincidencia.group(1).upper(), int(coincidencia.group(2))
    raise NumeroNoReconocido()


def ruta_original(sha256: str) -> str:
    """Clave del original en el almacén: el hash es el nombre, así que dos subidas iguales coinciden."""
    return f"spdp/{sha256}.pdf"


def decidir(hash_existente: str | None, hash_nuevo: str) -> Decision:
    if hash_existente is None:
        return Decision.NUEVA
    return Decision.NADA if hash_existente == hash_nuevo else Decision.VERSION


async def hash_registrado(session, numero: str, anio: int) -> tuple[str, str] | None:
    """(id de la resolución, hash vigente) o None; el hash vigente es el de la última versión, si la hay."""
    fila = (await session.execute(
        text("SELECT id::text, archivo_sha256 FROM normativa_resoluciones "
             "WHERE numero_resolucion = :n AND anio_emision = :a"),
        {"n": numero, "a": anio},
    )).first()
    if fila is None:
        return None
    ultima = (await session.execute(
        text("SELECT archivo_sha256 FROM normativa_versiones WHERE resolucion_id = CAST(:r AS uuid) "
             "ORDER BY detectada_en DESC, id DESC LIMIT 1"),
        {"r": fila[0]},
    )).first()
    return fila[0], (ultima[0] if ultima else fila[1])


async def aplicar(session, doc: DocumentoDescargado) -> Decision:
    """Aplica las tres capas; escribe en la sesión del llamador y no hace commit."""
    registrado = await hash_registrado(session, doc.numero_resolucion, doc.anio_emision)
    decision = decidir(registrado[1] if registrado else None, doc.sha256)
    if decision is Decision.NUEVA:
        await session.execute(
            text("INSERT INTO normativa_resoluciones (numero_resolucion, anio_emision, titulo, url_fuente, "
                 "seccion_fuente, archivo_sha256, ruta_original, tamano_bytes, estado) "
                 "VALUES (:n, :a, :t, :u, :s, :h, :r, :b, 'pendiente_revision')"),
            {"n": doc.numero_resolucion, "a": doc.anio_emision, "t": doc.titulo[:500], "u": doc.url_fuente[:1000],
             "s": doc.seccion_fuente, "h": doc.sha256, "r": doc.ruta_original, "b": doc.tamano_bytes},
        )
    elif decision is Decision.VERSION:
        await session.execute(
            text("INSERT INTO normativa_versiones (resolucion_id, archivo_sha256, ruta_original, motivo) "
                 "VALUES (CAST(:r AS uuid), :h, :ruta, 'cambio_en_fuente')"),
            {"r": registrado[0], "h": doc.sha256, "ruta": doc.ruta_original},
        )
    return decision
