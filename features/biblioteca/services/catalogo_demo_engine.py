# -*- coding: utf-8 -*-
# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤adpa ¤demo ¤arbitro ¤plantillas-demo
# ¤¤developer-architect
"""BIB-404: catálogo ficticio de la demo (seis plantillas BIB-091 a BIB-096).

Solo en la base de la demo (`APP_ENV=demo`). Todo pasa por el flujo editorial de BIB-105 y BIB-403, nunca
por un INSERT directo en `biblioteca_versiones` ni en `biblioteca_revisiones`:

- `admin@cooperativa-demo.invalid` concede las capacidades;
- `implementacion@cooperativa-demo.invalid` carga cada versión con su ficha (`editor`);
- `coordinacion@cooperativa-demo.invalid` registra la revisión técnica y publica.

Idempotente por huella: una versión publicada igual no se toca; una distinta con el mismo código es
`BIB_CONFLICTO_VERSION` y la transacción del orquestador revierte toda la siembra. Sin `commit`.
"""
from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.entorno.guardias import entorno_actual
from app_core.errors import ErrorNegocio
from features.biblioteca.domain.editorial import Capacidad, Dictamen, Transicion
from features.biblioteca.domain.plantillas_md import huella, metadatos_de
from features.biblioteca.services import capacidades_admin
from features.biblioteca.services.editorial import publicar, revisar
from features.biblioteca.services.plantillas_md import cargar_plantilla_md

CARPETA = Path(__file__).resolve().parents[3] / "data" / "demo" / "biblioteca_catalogo"
ADMIN = "admin@cooperativa-demo.invalid"
IMPLEMENTACION = "implementacion@cooperativa-demo.invalid"
COORDINACION = "coordinacion@cooperativa-demo.invalid"
MOTIVO_CAPACIDAD = "Siembra de la demo (ficticio)"
COMENTARIO_REVISION = "Revisión ficticia de demostración"
CAPACIDADES = ((IMPLEMENTACION, Capacidad.EDITOR), (COORDINACION, Capacidad.TECNICO),
               (COORDINACION, Capacidad.PUBLICADOR))


# ¤adpa
async def _usuario(session: AsyncSession, mapa_ids: Mapping[str, str], correo: str) -> str:
    """Id de la persona ficticia: el del mapa si lo trae, y si no el de `users` por su correo `.invalid`."""
    if mapa_ids.get(correo):
        return mapa_ids[correo]
    uid = (await session.execute(text("SELECT id FROM users WHERE email=:e"), {"e": correo})).scalar()
    if uid is None:
        raise ValueError("Falta una persona ficticia de la demo: siembra primero la sala organización.")
    return uid


# ¤adpa
def _leer_catalogo() -> tuple[dict[str, str], dict[str, dict]]:
    textos = {r.stem: r.read_bytes().decode("utf-8") for r in sorted(CARPETA.glob("BIB-*.md"))}
    fichas = json.loads((CARPETA / "catalogo.json").read_bytes().decode("utf-8"))
    if set(textos) != set(fichas):
        raise ValueError("catalogo.json y las plantillas ficticias no tienen los mismos códigos.")
    return textos, fichas


# ¤adpa
async def sembrar_catalogo_demo(session: AsyncSession, mapa_ids: Mapping[str, str] | None = None) -> dict:
    """Siembra y publica las seis plantillas ficticias; repetirla no cambia nada. No hace commit."""
    if entorno_actual() != "demo":
        raise ValueError("El catálogo ficticio solo se siembra con APP_ENV=demo.")
    mapa_ids = mapa_ids or {}
    textos, fichas = _leer_catalogo()
    admin = await _usuario(session, mapa_ids, ADMIN)
    editor = await _usuario(session, mapa_ids, IMPLEMENTACION)
    revisor = await _usuario(session, mapa_ids, COORDINACION)
    por_correo = {ADMIN: admin, IMPLEMENTACION: editor, COORDINACION: revisor}
    for correo, capacidad in CAPACIDADES:
        await capacidades_admin.conceder(session, por_correo[correo], capacidad.value, admin, MOTIVO_CAPACIDAD)
    publicadas = 0
    for codigo, texto in textos.items():
        meta = metadatos_de(texto)
        vigente = (await session.execute(text(
            "SELECT sha256, version FROM biblioteca_versiones WHERE codigo=:c AND estado='publicada'"),
            {"c": codigo})).first()
        if vigente is not None:
            if vigente[0] != huella(texto):  # otra versión publicada con el mismo código: no se reemplaza en silencio
                raise ErrorNegocio("BIB_CONFLICTO_VERSION")
            continue
        await cargar_plantilla_md(session, editor, texto, codigo, fichas[codigo])
        version = (await session.execute(text(
            "SELECT id, generacion FROM biblioteca_versiones WHERE codigo=:c AND version=:v"),
            {"c": codigo, "v": meta["version"]})).first()
        await revisar(session, revisor, version[0], Dictamen(
            tipo="tecnica", aprobado=True, comentario=COMENTARIO_REVISION, generacion=version[1]))
        await publicar(session, revisor, version[0], Transicion(
            generacion=version[1], motivo="Publicación de la demo (ficticio)"))
        publicadas += 1
    return {"publicadas": publicadas}
