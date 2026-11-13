# ¤evidencias ¤evidencias-vigencia
"""Paquete para inspección de la SPDP, ordenado por requisito (EVI-02).

Un ZIP con `indice.csv` (requisito, documento, huella SHA-256, fecha de registro y vencimiento), `LEEME.txt` y los
archivos en `documentos/`. Solo entran los documentos vigentes y visibles para quien lo pide; cada archivo se
descarga del almacén y se comprueba contra la huella que el servidor registró al subirlo.
"""
from __future__ import annotations

import csv
import hashlib
import io
import re
import zipfile
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app_core.errors import ErrorNegocio
from app_core.storage import gcs
from features.evidencias.domain import errores as _e
from features.evidencias.domain.vigencia import AtributosDocumento
from features.evidencias.services.vigencia_engine import listar_atributos

TAMANO_MAXIMO_PAQUETE_BYTES = 100 * 1024 * 1024
TAMANO_MAXIMO_ARCHIVO_BYTES = 10 * 1024 * 1024
SIN_REQUISITO = "Sin requisito vinculado"
ENCABEZADO = ["requisito", "control", "codigo", "archivo", "sha256", "tamano_bytes", "registrado_en", "vence_en"]


def _nombre_seguro(nombre: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", nombre).strip("._") or "documento"


def _ruta_en_paquete(documento: AtributosDocumento) -> str:
    return f"documentos/{documento.codigo}_{_nombre_seguro(documento.nombre_archivo)}"


def filas_del_indice(
    documentos: list[AtributosDocumento], nombres_controles: dict[int, str]
) -> list[list[str]]:
    """Filas del índice ordenadas por requisito (control) y por código; los sin vincular, al final."""
    filas: list[tuple[int, str, list[str]]] = []
    for d in documentos:
        destinos = sorted(d.controles) or [0]
        for control in destinos:
            requisito = f"P{control} · {nombres_controles.get(control, '')}".rstrip(" ·") if control else SIN_REQUISITO
            filas.append(
                (
                    control or 10_000,
                    d.codigo,
                    [
                        requisito, str(control) if control else "", d.codigo, _ruta_en_paquete(d), d.sha256,
                        str(d.tamano_bytes), d.subido_en.isoformat(), d.vence_en.isoformat() if d.vence_en else "",
                    ],
                )
            )
    return [f for _, _, f in sorted(filas, key=lambda x: (x[0], x[1]))]


async def armar_paquete(
    session: AsyncSession,
    almacen: gcs.Almacen,
    tenant_id: str,
    user_id: str,
    rol: str,
    hoy: date,
    nombres_controles: dict[int, str],
) -> bytes:
    candidatos = await listar_atributos(session, tenant_id, user_id, rol)
    documentos = [d for d in candidatos if d.vigente(hoy)]
    if not documentos:
        raise ErrorNegocio(_e.PAQUETE_VACIO)
    contenidos: dict[str, bytes] = {}
    total = 0
    for d in documentos:
        contenido = almacen.descargar(d.clave_almacen, TAMANO_MAXIMO_ARCHIVO_BYTES)
        if contenido is None or hashlib.sha256(contenido).hexdigest() != d.sha256:
            raise ErrorNegocio(_e.PAQUETE_INTEGRIDAD)
        total += len(contenido)
        if total > TAMANO_MAXIMO_PAQUETE_BYTES:
            raise ErrorNegocio(_e.PAQUETE_DEMASIADO_GRANDE)
        contenidos[d.documento_id] = contenido

    indice = io.StringIO()
    escritor = csv.writer(indice, lineterminator="\n")
    escritor.writerow(ENCABEZADO)
    escritor.writerows(filas_del_indice(documentos, nombres_controles))
    salida = io.BytesIO()
    with zipfile.ZipFile(salida, "w", zipfile.ZIP_DEFLATED) as paquete:
        paquete.writestr("indice.csv", indice.getvalue())
        paquete.writestr(
            "LEEME.txt",
            f"Paquete para inspección generado el {hoy.isoformat()}.\n"
            "Incluye solo documentos vigentes. Cada archivo se corresponde con la huella SHA-256 del índice.\n",
        )
        for d in documentos:
            paquete.writestr(_ruta_en_paquete(d), contenidos[d.documento_id])
    return salida.getvalue()
