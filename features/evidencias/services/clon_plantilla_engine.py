# -*- coding: utf-8 -*-
# ¤demo ¤adpa ¤seguridad-tenant ¤evidencias
"""DEMO-03e: copia y siembra de la sala Evidencias para la demo «Cooperativa Demo».

Copia solo filas (`evidencias_documentos` y `evidencias_vinculos`) del tenant plantilla al destino, con
ids deterministas (uuid5 de destino e id de origen) traducidos con `mapa_ids`. No copia objetos de Cloud
Storage ni huellas de producción: cada documento clonado lleva una huella RECALCULADA sobre un contenido
ficticio propio del destino, y su `clave_almacen` es una clave sin objeto bajo un prefijo de la demo, que
no apunta a ningún bucket. Idempotente, sin commit, sin escribir en el origen.
"""
from __future__ import annotations

import hashlib
import uuid
from typing import Any

from sqlalchemy import column, select, table, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from features.evidencias.domain.models import NORMATIVA_POR_DEFECTO
from features.evidencias.domain.retencion import retencion_dias

MapaIds = dict[str, str]

_ESPACIO = uuid.UUID("8d2f4c1e-6b3a-4e0f-a1d5-7c9e0b2f4a03")
PREFIJO_SIN_OBJETO = "demo-sin-objeto"

_DOCUMENTOS = ("id", "codigo", "nombre_archivo", "tipo_mime", "tamano_bytes", "sha256", "normativa",
               "clave_almacen", "subido_por", "subido_en", "retencion_dias")
_VINCULOS = ("id", "documento_id", "control_id", "vinculado_por", "vinculado_en")
_TABLAS = {"evidencias_documentos": _DOCUMENTOS, "evidencias_vinculos": _VINCULOS}
_CON_DEFECTO = frozenset({"subido_en", "vinculado_en"})


def _id_nuevo(destino: str, id_origen: str) -> str:
    return str(uuid.uuid5(_ESPACIO, f"{destino}|{id_origen}"))


def contenido_ficticio(tenant_id: str, codigo: str) -> bytes:
    """Contenido ficticio, propio del tenant, del que sale la huella de cada documento de la demo."""
    return f"Documento ficticio de la demo · {tenant_id} · {codigo}".encode("utf-8")


def _tabla(nombre: str):
    return table(nombre, column("tenant_id"), *[column(c) for c in _TABLAS[nombre]])


async def _tenant(session: AsyncSession, tenant_id: str) -> None:
    await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": tenant_id})


async def _leer(session: AsyncSession, nombre: str, tenant_id: str) -> list[dict[str, Any]]:
    t = _tabla(nombre)
    consulta = select(*[t.c[c] for c in _TABLAS[nombre]]).where(t.c.tenant_id == tenant_id).order_by(t.c.id)
    return [dict(f) for f in (await session.execute(consulta)).mappings().all()]


async def _insertar(session: AsyncSession, nombre: str, tenant_id: str, fila: dict[str, Any]) -> None:
    cols = [c for c in _TABLAS[nombre] if not (c in _CON_DEFECTO and fila.get(c) is None)]
    valores = {c: fila[c] for c in cols}
    valores["tenant_id"] = tenant_id
    await session.execute(pg_insert(_tabla(nombre)).values(**valores).on_conflict_do_nothing())


async def _administrador(session: AsyncSession, tenant_id: str) -> str:
    fila = (await session.execute(
        text("SELECT user_id FROM user_tenant_roles WHERE tenant_id = :t AND role = 'admin_organizacion' "
             "AND (valid_to IS NULL OR valid_to > now()) ORDER BY user_id LIMIT 1"), {"t": tenant_id})).first()
    if fila is None:
        raise ValueError("El tenant no tiene administrador de la organización al que atribuir los documentos.")
    return fila[0]


def _documento_de_demo(tenant_id: str, id_doc: str, base: dict[str, Any], subido_por: str) -> dict[str, Any]:
    """Documento con huella y tamaño recalculados sobre contenido ficticio y clave sin objeto."""
    contenido = contenido_ficticio(tenant_id, base["codigo"])
    return {**base, "id": id_doc, "sha256": hashlib.sha256(contenido).hexdigest(), "tamano_bytes": len(contenido),
            "clave_almacen": f"{PREFIJO_SIN_OBJETO}/{tenant_id}/{id_doc}", "subido_por": subido_por}


async def clonar_desde_plantilla(session: AsyncSession, origen: str, destino: str, mapa_ids: MapaIds) -> MapaIds:
    """Copia las filas de la sala del tenant `origen` al `destino` y devuelve el mapa de ids ampliado."""
    if origen == destino:
        raise ValueError("El tenant destino de la copia debe ser distinto del de origen.")
    await _tenant(session, origen)
    documentos = await _leer(session, "evidencias_documentos", origen)
    vinculos = await _leer(session, "evidencias_vinculos", origen)

    mapa: MapaIds = dict(mapa_ids)
    for fila in documentos + vinculos:
        mapa[fila["id"]] = _id_nuevo(destino, fila["id"])

    await _tenant(session, destino)
    admin = await _administrador(session, destino) if documentos else None
    for d in documentos:
        await _insertar(session, "evidencias_documentos", destino, _documento_de_demo(
            destino, mapa[d["id"]], d, mapa_ids.get(d["subido_por"], admin)))
    for v in vinculos:
        await _insertar(session, "evidencias_vinculos", destino, {
            **v, "id": mapa[v["id"]], "documento_id": mapa[v["documento_id"]],
            "vinculado_por": mapa_ids.get(v["vinculado_por"], admin)})
    return mapa


async def sembrar_en_plantilla(session: AsyncSession, plantilla_id: str, datos: dict) -> None:
    """Siembra idempotente del bloque `evidencias` de la plantilla; no hace commit."""
    registros = (datos or {}).get("registros") or []
    if not registros:
        return
    await _tenant(session, plantilla_id)
    admin = await _administrador(session, plantilla_id)
    for i, r in enumerate(registros, start=1):
        base = {"codigo": f"EVD-DEMO-{i:04d}", "nombre_archivo": f"evidencia-ficticia-{i:02d}.pdf",
                "tipo_mime": "application/pdf", "normativa": NORMATIVA_POR_DEFECTO, "subido_en": None,
                "retencion_dias": retencion_dias(plantilla_id)}
        await _insertar(session, "evidencias_documentos", plantilla_id, _documento_de_demo(
            plantilla_id, _id_nuevo(plantilla_id, f"documento-{i}"), base, admin))
