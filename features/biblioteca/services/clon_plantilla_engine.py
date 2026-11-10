# -*- coding: utf-8 -*-
# ¤adpa ¤demo ¤seguridad-tenant
# ¤¤developer-architect
"""Copia y siembra de la plantilla «Cooperativa Demo» en la sala biblioteca (DEMO-03d).

La biblioteca es multi-organización: el catálogo y las versiones editoriales son globales y no se copian.
Aquí solo se copian los documentos de la organización (`biblioteca_documentos`) y su historial inmutable
(`biblioteca_documentos_historial`) del tenant plantilla al tenant destino.

- Sin `commit`: la transacción es del orquestador (DEMO-02).
- Idempotente: los ids del destino se derivan (uuid5) del tenant destino y del id de origen, y cada
  inserción es `ON CONFLICT (id) DO NOTHING`; repetir la llamada no duplica ni cambia nada.
- La RLS se respeta: se lee con el contexto del tenant origen y se escribe con el del destino; al salir
  se restaura el contexto que traía la sesión.
"""
from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import date, datetime, timezone
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from features.biblioteca.domain.documentos import huella, sumar_meses

MapaIds = dict[str, str]

_JSON_PLANTILLA = Path(__file__).resolve().parents[3] / "data" / "demo" / "cooperativa_demo.json"
_FECHA_EMISION = date(2026, 1, 15)  # fija: la siembra repetida debe dejar el mismo estado
_ESTADOS_SEMBRABLES = ("borrador", "en_revision", "aprobado", "vencido")


# ¤adpa
def _id_destino(destino: str, id_origen: str) -> str:
    """Id estable en el tenant destino para una fila de origen; cabe en varchar(36)."""
    return str(uuid5(NAMESPACE_URL, f"biblioteca-demo/{destino}/{id_origen}"))


# ¤adpa ¤seguridad-tenant
async def _contexto_actual(session: AsyncSession) -> str:
    return (await session.execute(text("SELECT coalesce(current_setting('app.current_tenant_id', true), '')"))).scalar() or ""


# ¤adpa ¤seguridad-tenant
async def _fijar_tenant(session: AsyncSession, tenant_id: str) -> None:
    # Misma vía que app_core.db.session.fijar_contexto_rls: set_config local con parámetro enlazado.
    await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": tenant_id})


# ¤adpa
def _usuario(mapa_ids: Mapping[str, str], origen_id: str | None) -> str | None:
    return mapa_ids.get(origen_id) if origen_id else None


# ¤adpa ¤seguridad-tenant
async def clonar_desde_plantilla(session: AsyncSession, origen: str, destino: str, mapa_ids: MapaIds) -> MapaIds:
    """Copia los documentos de la organización de `origen` a `destino` y devuelve el mapa ampliado."""
    if origen == destino:
        raise ValueError("El tenant destino no puede ser el de la plantilla.")
    previo = await _contexto_actual(session)
    try:
        await _fijar_tenant(session, origen)
        documentos = (await session.execute(text(
            "SELECT id, codigo, nombre, origen, plantilla_id, plantilla_version, contenido_markdown, editado, "
            "estado, aprobado_por, aprobado_en, sha256, fecha_emision, proxima_revision, tarea_hoja_ruta_id, "
            "revision, creado_por, creado_en, actualizado_en FROM biblioteca_documentos "
            "WHERE tenant_id=:o ORDER BY creado_en, id"), {"o": origen})).mappings().all()
        historial = (await session.execute(text(
            "SELECT id, documento_id, revision, accion, contenido_markdown, sha256, actor_id, creado_en "
            "FROM biblioteca_documentos_historial WHERE tenant_id=:o ORDER BY documento_id, revision"),
            {"o": origen})).mappings().all()

        ampliado: MapaIds = dict(mapa_ids)
        await _fijar_tenant(session, destino)
        for fila in documentos:
            creador = _usuario(mapa_ids, fila["creado_por"])
            if creador is None:
                raise ValueError("El mapa de ids no traduce al autor del documento de la plantilla.")
            aprobador = _usuario(mapa_ids, fila["aprobado_por"])
            if fila["estado"] == "aprobado" and aprobador is None:
                aprobador = creador
            nuevo = _id_destino(destino, fila["id"])
            await session.execute(text(
                "INSERT INTO biblioteca_documentos(id, tenant_id, codigo, nombre, origen, plantilla_id, "
                "plantilla_version, contenido_markdown, editado, estado, aprobado_por, aprobado_en, sha256, "
                "fecha_emision, proxima_revision, tarea_hoja_ruta_id, revision, creado_por, creado_en, "
                "actualizado_en) VALUES (:id, :t, :codigo, :nombre, :origen, :pid, :pver, :c, :editado, :estado, "
                ":apr, :apr_en, :sha, :emision, :proxima, :tarea, :rev, :autor, :creado, :actualizado) "
                "ON CONFLICT (id) DO NOTHING"),
                {"id": nuevo, "t": destino, "codigo": fila["codigo"], "nombre": fila["nombre"],
                 "origen": fila["origen"], "pid": fila["plantilla_id"], "pver": fila["plantilla_version"],
                 "c": fila["contenido_markdown"], "editado": fila["editado"], "estado": fila["estado"],
                 "apr": aprobador if fila["estado"] == "aprobado" else None,
                 "apr_en": fila["aprobado_en"] if fila["estado"] == "aprobado" else None,
                 "sha": fila["sha256"], "emision": fila["fecha_emision"], "proxima": fila["proxima_revision"],
                 "tarea": _usuario(mapa_ids, fila["tarea_hoja_ruta_id"]), "rev": fila["revision"],
                 "autor": creador, "creado": fila["creado_en"], "actualizado": fila["actualizado_en"]})
            ampliado[fila["id"]] = nuevo
        for fila in historial:
            documento = ampliado.get(fila["documento_id"])
            actor = _usuario(mapa_ids, fila["actor_id"])
            if documento is None or actor is None:
                raise ValueError("El historial de la plantilla apunta a un documento o autor sin traducir.")
            await session.execute(text(
                "INSERT INTO biblioteca_documentos_historial(id, tenant_id, documento_id, revision, accion, "
                "contenido_markdown, sha256, actor_id, creado_en) VALUES (:id, :t, :d, :r, :a, :c, :h, :u, :creado) "
                "ON CONFLICT (id) DO NOTHING"),
                {"id": _id_destino(destino, fila["id"]), "t": destino, "d": documento, "r": fila["revision"],
                 "a": fila["accion"], "c": fila["contenido_markdown"], "h": fila["sha256"], "u": actor,
                 "creado": fila["creado_en"]})
        return ampliado
    finally:
        if previo:
            await _fijar_tenant(session, previo)


# ¤adpa
def _bloque_de_la_sala(datos: Mapping | None) -> Mapping:
    """El bloque `biblioteca` de la plantilla; acepta el bloque suelto, el JSON entero o nada (lo lee del disco)."""
    if datos is None:
        datos = json.loads(_JSON_PLANTILLA.read_text(encoding="utf-8"))
    return datos.get("salas", {}).get("biblioteca", {}) if "salas" in datos else datos


# ¤adpa ¤seguridad-tenant
async def sembrar_en_plantilla(session: AsyncSession, plantilla_id: str, datos: Mapping | None = None) -> None:
    """Siembra los documentos ficticios de la plantilla; repetirla deja el mismo estado. No hace commit."""
    documentos = _bloque_de_la_sala(datos).get("documentos", [])
    if not documentos:
        return
    previo = await _contexto_actual(session)
    try:
        await _fijar_tenant(session, plantilla_id)
        autor = (await session.execute(text(
            "SELECT user_id FROM user_tenant_roles WHERE tenant_id=:t AND role='admin_organizacion' "
            "AND (valid_to IS NULL OR valid_to > now()) ORDER BY user_id LIMIT 1"), {"t": plantilla_id})).scalar()
        if autor is None:
            raise ValueError("La plantilla no tiene administrador: siembra primero la sala organización.")
        for posicion, doc in enumerate(documentos, start=1):
            estado = doc.get("estado", "borrador")
            if estado not in _ESTADOS_SEMBRABLES:
                raise ValueError(f"Estado de documento no sembrable: {estado}")
            codigo = f"DEMO-DOC-{posicion:02d}"
            contenido = f"# {doc['titulo']}\n\nDocumento ficticio de demostración. Sin datos reales.\n"
            identificador = _id_destino(plantilla_id, codigo)
            await session.execute(text(
                "INSERT INTO biblioteca_documentos(id, tenant_id, codigo, nombre, origen, contenido_markdown, "
                "estado, aprobado_por, aprobado_en, sha256, fecha_emision, proxima_revision, creado_por) "
                "VALUES (:id, :t, :codigo, :nombre, 'propio', :c, :estado, :apr, "
                ":apr_en, :h, :emision, :proxima, :u) "
                "ON CONFLICT (id) DO NOTHING"),
                {"id": identificador, "t": plantilla_id, "codigo": codigo, "nombre": doc["titulo"], "c": contenido,
                 "estado": estado, "apr": autor if estado == "aprobado" else None,
                 "apr_en": datetime(2026, 1, 15, tzinfo=timezone.utc) if estado == "aprobado" else None, "h": huella(contenido),
                 "emision": _FECHA_EMISION, "proxima": sumar_meses(_FECHA_EMISION, 12), "u": autor})
            await session.execute(text(
                "INSERT INTO biblioteca_documentos_historial(id, tenant_id, documento_id, revision, accion, "
                "contenido_markdown, sha256, actor_id) VALUES (:id, :t, :d, 1, 'creado', :c, :h, :u) "
                "ON CONFLICT (id) DO NOTHING"),
                {"id": _id_destino(plantilla_id, f"{codigo}/1"), "t": plantilla_id, "d": identificador,
                 "c": contenido, "h": huella(contenido), "u": autor})
    finally:
        if previo:
            await _fijar_tenant(session, previo)
