# -*- coding: utf-8 -*-
# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤adpa ¤demo ¤seguridad-tenant
# ¤¤developer-architect-adpa
"""Copia y siembra de la plantilla «Cooperativa Demo» en la sala videovigilancia (DEMO-03f).

La videovigilancia copia únicamente el inventario técnico y perfil de conformidad de cámaras
(`cctv_camaras_inventario`) del tenant plantilla al tenant destino.
Los clips de grabaciones (`cctv_clips_boveda`) y los objetos de la bóveda no se copian (regla R3).

- Sin `commit`: la transacción es del orquestador (DEMO-02).
- Idempotente: los ids del destino se derivan de forma estable (uuid5 con NAMESPACE_URL)
  y cada inserción es `ON CONFLICT (id) DO NOTHING`. Repetir la llamada no duplica nada.
- La RLS se respeta: se lee con el contexto del tenant origen y se escribe con el del destino;
  al salir se restaura el contexto que traía la sesión.
- Ortogonalidad ZERAG: no importa otras salas.
"""
from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

MapaIds = dict[str, str]

_JSON_PLANTILLA = Path(__file__).resolve().parents[3] / "data" / "demo" / "cooperativa_demo.json"
_FECHA_SEMBRADA = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
_CODECS_VALIDOS = ("H265", "H265_PLUS")


# ¤adpa
def _id_destino(destino: str, id_origen: str) -> str:
    """Id estable en el tenant destino para una fila de origen; cabe en UUID."""
    return str(uuid5(NAMESPACE_URL, f"videovigilancia-demo/{destino}/{id_origen}"))


# ¤adpa
def _id_plantilla(plantilla_id: str, clave: str) -> str:
    """Id estable en el tenant plantilla para una cámara de la plantilla; cabe en UUID."""
    return str(uuid5(NAMESPACE_URL, f"videovigilancia-demo/{plantilla_id}/{clave}"))


# ¤adpa ¤seguridad-tenant
async def _contexto_actual(session: AsyncSession) -> str:
    return (await session.execute(text("SELECT coalesce(current_setting('app.current_tenant_id', true), '')"))).scalar() or ""


# ¤adpa ¤seguridad-tenant
async def _fijar_tenant(session: AsyncSession, tenant_id: str) -> None:
    await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": tenant_id})


# ¤adpa
def _bloque_de_la_sala(datos: Mapping | None) -> Mapping:
    """El bloque `videovigilancia` de la plantilla; acepta el bloque suelto, el JSON entero o nada (lo lee del disco)."""
    if datos is None:
        datos = json.loads(_JSON_PLANTILLA.read_text(encoding="utf-8"))
    if "salas" in datos:
        return datos.get("salas", {}).get("videovigilancia", {})
    if "videovigilancia" in datos:
        return datos.get("videovigilancia", {})
    return datos


# ¤adpa ¤seguridad-tenant
async def clonar_desde_plantilla(
    session: AsyncSession, origen: str, destino: str, mapa_ids: MapaIds
) -> MapaIds:
    """Copia las cámaras técnicas de `origen` a `destino` y devuelve el mapa ampliado (R1..R5)."""
    if origen == destino:
        raise ValueError("El tenant destino no puede ser el de la plantilla.")
    previo = await _contexto_actual(session)
    try:
        await _fijar_tenant(session, origen)
        camaras = (
            await session.execute(
                text(
                    "SELECT id, nombre_ubicacion, codec, modo_grabacion, audio_ambiental_activo, "
                    "mascara_privacidad_activa, plazo_retencion_dias, estado_conformidad, "
                    "actividad_rat_id, creado_por, creado_en FROM cctv_camaras_inventario "
                    "WHERE tenant_id=:o ORDER BY creado_en, id"
                ),
                {"o": origen},
            )
        ).mappings().all()

        for fila in camaras:
            if mapa_ids.get(fila["creado_por"]) is None:
                raise ValueError("El mapa de ids no traduce al autor de la cámara de la plantilla.")

        ampliado: MapaIds = dict(mapa_ids)
        await _fijar_tenant(session, destino)
        for fila in camaras:
            creador = mapa_ids.get(fila["creado_por"])
            if creador is None:
                raise ValueError("El mapa de ids no traduce al autor de la cámara de la plantilla.")
            id_origen_str = str(fila["id"])
            nuevo = _id_destino(destino, id_origen_str)
            rat_id = mapa_ids.get(fila["actividad_rat_id"]) if fila["actividad_rat_id"] else None
            await session.execute(
                text(
                    "INSERT INTO cctv_camaras_inventario ("
                    "id, tenant_id, nombre_ubicacion, codec, modo_grabacion, audio_ambiental_activo, "
                    "mascara_privacidad_activa, plazo_retencion_dias, estado_conformidad, "
                    "actividad_rat_id, creado_por, creado_en) "
                    "VALUES (:id, :t, :nombre, :codec, :modo, :audio, :mascara, :retencion, :conformidad, :rat, :creador, :creado) "
                    "ON CONFLICT (id) DO NOTHING"
                ),
                {
                    "id": nuevo,
                    "t": destino,
                    "nombre": fila["nombre_ubicacion"],
                    "codec": fila["codec"],
                    "modo": fila["modo_grabacion"],
                    "audio": fila["audio_ambiental_activo"],
                    "mascara": fila["mascara_privacidad_activa"],
                    "retencion": fila["plazo_retencion_dias"],
                    "conformidad": fila["estado_conformidad"],
                    "rat": rat_id,
                    "creador": creador,
                    "creado": fila["creado_en"],
                },
            )
            ampliado[id_origen_str] = nuevo
        return ampliado
    finally:
        if previo:
            await _fijar_tenant(session, previo)


# ¤adpa ¤seguridad-tenant
async def sembrar_en_plantilla(session: AsyncSession, plantilla_id: str, datos: Mapping | None = None) -> None:
    """Siembra las cámaras conformes ficticias de la plantilla; repetirla deja el mismo estado. No hace commit."""
    bloque = _bloque_de_la_sala(datos)
    camaras = bloque.get("camaras", [])
    if not camaras:
        return
    previo = await _contexto_actual(session)
    try:
        await _fijar_tenant(session, plantilla_id)
        autor = (
            await session.execute(
                text(
                    "SELECT user_id FROM user_tenant_roles WHERE tenant_id=:t AND role='admin_organizacion' "
                    "AND (valid_to IS NULL OR valid_to > now()) ORDER BY user_id LIMIT 1"
                ),
                {"t": plantilla_id},
            )
        ).scalar()
        if autor is None:
            raise ValueError("La plantilla no tiene administrador: siembra primero la sala organización.")

        for cam in camaras:
            clave = cam.get("clave") or cam.get("id") or cam.get("nombre_ubicacion")
            codec = cam.get("codec", "H265_PLUS")
            if codec not in _CODECS_VALIDOS:
                raise ValueError(f"Codec no optimizado para videovigilancia demo: {codec}")
            id_cam = _id_plantilla(plantilla_id, str(clave))
            nombre = cam.get("nombre_ubicacion", "Cámara (ficticia)")
            await session.execute(
                text(
                    "INSERT INTO cctv_camaras_inventario ("
                    "id, tenant_id, nombre_ubicacion, codec, modo_grabacion, audio_ambiental_activo, "
                    "mascara_privacidad_activa, plazo_retencion_dias, estado_conformidad, "
                    "actividad_rat_id, creado_por, creado_en) "
                    "VALUES (:id, :t, :nombre, :codec, 'EVENTO_MOVIMIENTO', false, true, 15, 'CONFORME', NULL, :creador, :creado) "
                    "ON CONFLICT (id) DO NOTHING"
                ),
                {
                    "id": id_cam,
                    "t": plantilla_id,
                    "nombre": nombre,
                    "codec": codec,
                    "creador": autor,
                    "creado": _FECHA_SEMBRADA,
                },
            )
    finally:
        if previo:
            await _fijar_tenant(session, previo)
