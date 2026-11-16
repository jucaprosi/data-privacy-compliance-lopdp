# -*- coding: utf-8 -*-
# ¤demo ¤adpa ¤seguridad-tenant
"""DEMO-03a: siembra de la plantilla y clonado de la sala `organizacion` (PRD EVYDENTIA §5.6.8).

- `sembrar_en_plantilla`: asegura, sin duplicar, el tenant plantilla (`es_demo`), sus unidades y
  sus personas ficticias con un solo rol cada una.
- `clonar_desde_plantilla`: copia esas filas al tenant destino con ids nuevos y devuelve el mapa
  ampliado (id en la plantilla → id en el destino). No hace commit y puede repetirse dentro de la
  misma transacción sin duplicar.

Personas del clon: cada clon tiene sus propios usuarios (nunca los de la plantilla ni los de otro
clon), con correo `.invalid` y su única relación con el tenant en `user_tenant_roles`; así la purga
de usuarios (DEMO-05b) borra solo los del clon.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from features.organizacion.domain.models import RoleGrant
from features.organizacion.domain.roles import Role
from features.organizacion.services.contexto_tenant import fijar_tenant
from features.organizacion.services.estructura_engine import AreaEstructuraCreate, crear_area_estructura
from features.organizacion.services.roles_engine import grant_role

_RAIZ = Path(__file__).resolve().parents[3]
_JSON_PLANTILLA = _RAIZ / "data" / "demo" / "cooperativa_demo.json"
_SUFIJO_FICTICIO = ".invalid"
_ROL_ADMIN = "admin_organizacion"


def _huella(*partes: str, largo: int = 16) -> str:
    return hashlib.sha256("|".join(partes).encode("utf-8")).hexdigest()[:largo]


def _id_usuario_plantilla(correo: str) -> str:
    """Mismo esquema que `scripts/datos_sinteticos`: la siembra del script y esta encuentran al mismo usuario."""
    return "usr-ep-" + _huella(correo.strip().lower())


def _id_usuario_clon(destino: str, origen_uid: str) -> str:
    return "usr-demo-" + _huella(destino, origen_uid)


def _correo_clon(correo_origen: str, destino: str) -> str:
    local, _, dominio = correo_origen.strip().lower().partition("@")
    if not dominio.endswith(_SUFIJO_FICTICIO):
        raise ValueError("la persona de la plantilla no tiene correo ficticio (.invalid)")
    return f"{local}.{_huella(destino, correo_origen, largo=8)}@{dominio}"


def _ruc_clon(destino: str) -> str:
    return "9999" + str(int(_huella(destino, largo=12), 16) % 10**9).zfill(9)


async def _usuario(session: AsyncSession, uid: str, correo: str, nombre: str) -> str:
    existente = (await session.execute(
        text("SELECT id FROM users WHERE id = :id OR lower(email) = :e"), {"id": uid, "e": correo}
    )).first()
    if existente:
        return existente[0]
    await session.execute(
        text("INSERT INTO users (id, email, nombre, activo) VALUES (:id, :e, :n, TRUE)"),
        {"id": uid, "e": correo, "n": nombre},
    )
    return uid


async def _area(session: AsyncSession, tenant_id: str, codigo: str, nombre: str, nivel: str,
                padre: str | None, admin_uid: str) -> str:
    fila = (await session.execute(
        text("SELECT id FROM areas WHERE tenant_id = :t AND codigo = :c AND deleted_at IS NULL"),
        {"t": tenant_id, "c": codigo},
    )).first()
    if fila:
        return fila[0]
    area = await crear_area_estructura(
        session=session, tenant_id=tenant_id, user_id=admin_uid,
        payload=AreaEstructuraCreate(nombre=nombre, codigo=codigo, nivel=nivel, parent_area_id=padre),
    )
    return area["id"]


async def _rol(session: AsyncSession, tenant_id: str, uid: str, rol: str, area_id: str | None,
               admin_uid: str) -> None:
    fila = (await session.execute(
        text(
            "SELECT 1 FROM user_tenant_roles WHERE user_id = :u AND tenant_id = :t AND role = :r "
            "AND area_id IS NOT DISTINCT FROM CAST(:a AS TEXT) AND (valid_to IS NULL OR valid_to > now())"
        ),
        {"u": uid, "t": tenant_id, "r": rol, "a": area_id},
    )).first()
    if fila:
        return
    await grant_role(session=session, tenant_id=tenant_id, granted_by=admin_uid,
                     payload=RoleGrant(user_id=uid, role=Role(rol), area_id=area_id))


def _ordenar_padres_primero(unidades: list[dict]) -> list[dict]:
    pendientes, vistos, salida = list(unidades), set(), []
    while pendientes:
        avance = [u for u in pendientes if u["padre"] is None or u["padre"] in vistos]
        if not avance:
            raise ValueError("las unidades de la plantilla tienen un ciclo o un padre inexistente")
        for u in avance:
            vistos.add(u["codigo"])
            salida.append(u)
        pendientes = [u for u in pendientes if u not in avance]
    return salida


async def _materializar(session: AsyncSession, tenant_id: str, tenant: dict, unidades: list[dict],
                        personas: list[dict]) -> tuple[dict[str, str], dict[str, str]]:
    """Asegura tenant, personas, unidades y roles. `personas` lleva `uid` ya resuelto.

    Devuelve (ids de unidades por código, ids de personas por clave de origen).
    """
    await session.execute(
        text(
            "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, sector, tamano, "
            "activo, es_demo) VALUES (:id, :n, :r, :ruc, :sec, :tam, TRUE, TRUE) ON CONFLICT (id) DO NOTHING"
        ),
        {"id": tenant_id, "n": tenant["nombre_comercial"], "r": tenant["razon_social"], "ruc": tenant["ruc"],
         "sec": tenant["sector"], "tam": tenant["tamano"]},
    )
    await fijar_tenant(session, tenant_id)
    uids = {}
    for p in personas:
        uids[p["clave"]] = await _usuario(session, p["uid"], p["correo"], p["nombre"])
    admin = next(p for p in personas if p["rol"] == _ROL_ADMIN)
    admin_uid = uids[admin["clave"]]
    await fijar_tenant(session, tenant_id, admin_uid)
    await _rol(session, tenant_id, admin_uid, _ROL_ADMIN, None, admin_uid)
    areas: dict[str, str] = {}
    for u in _ordenar_padres_primero(unidades):
        areas[u["codigo"]] = await _area(
            session, tenant_id, u["codigo"], u["nombre"], u["nivel"],
            areas[u["padre"]] if u["padre"] else None, admin_uid)
    for p in personas:
        if p["rol"] == _ROL_ADMIN:
            continue
        area = areas[p["unidad"]] if p.get("unidad") else None
        await _rol(session, tenant_id, uids[p["clave"]], p["rol"], area, admin_uid)
    return areas, uids


async def sembrar_en_plantilla(session: AsyncSession, plantilla_id: str, datos: dict[str, Any]) -> None:
    """Asegura la parte de organización de la plantilla. Idempotente; no hace commit.

    `datos` es el bloque de la sala; si no trae `tenant`, `unidades` y `personas`, se leen del nivel
    superior de `data/demo/cooperativa_demo.json`.
    """
    if not all(k in datos for k in ("tenant", "unidades", "personas")):
        datos = {**json.loads(_JSON_PLANTILLA.read_text(encoding="utf-8")), **datos}
    personas = [
        {**p, "clave": p["correo"], "uid": _id_usuario_plantilla(p["correo"]), "correo": p["correo"].strip().lower()}
        for p in datos["personas"]
    ]
    await _materializar(session, plantilla_id, datos["tenant"], datos["unidades"], personas)


async def clonar_desde_plantilla(session: AsyncSession, origen: str, destino: str,
                                 mapa_ids: dict[str, str]) -> dict[str, str]:
    """Copia tenant, unidades, personas y roles de `origen` a `destino`; devuelve el mapa ampliado.

    Nunca escribe en `origen`. No hace commit. Repetirlo con el mismo destino no duplica nada.
    """
    await fijar_tenant(session, origen)
    t = (await session.execute(
        text("SELECT nombre_comercial, razon_social, sector, tamano FROM tenants WHERE id = :t"), {"t": origen}
    )).mappings().first()
    if t is None:
        raise ValueError("la plantilla no está sembrada")
    areas_o = (await session.execute(
        text("SELECT id, codigo, nombre, nivel, parent_area_id FROM areas "
             "WHERE tenant_id = :t AND deleted_at IS NULL"), {"t": origen}
    )).mappings().all()
    roles_o = (await session.execute(
        text("SELECT r.user_id, r.role, r.area_id, u.email, u.nombre FROM user_tenant_roles r "
             "JOIN users u ON u.id = r.user_id WHERE r.tenant_id = :t "
             "AND (r.valid_to IS NULL OR r.valid_to > now()) ORDER BY r.user_id, r.role"), {"t": origen}
    )).mappings().all()

    cod_de_area = {a["id"]: a["codigo"] for a in areas_o}
    unidades = [
        {"codigo": a["codigo"], "nombre": a["nombre"], "nivel": a["nivel"],
         "padre": cod_de_area.get(a["parent_area_id"])}
        for a in areas_o
    ]
    personas = [
        {"clave": r["user_id"], "uid": _id_usuario_clon(destino, r["user_id"]),
         "correo": _correo_clon(r["email"], destino), "nombre": r["nombre"], "rol": r["role"],
         "unidad": cod_de_area.get(r["area_id"])}
        for r in roles_o
    ]
    tenant = {"nombre_comercial": t["nombre_comercial"], "razon_social": t["razon_social"],
              "ruc": _ruc_clon(destino), "sector": t["sector"], "tamano": t["tamano"]}
    areas_d, uids_d = await _materializar(session, destino, tenant, unidades, personas)

    ampliado = dict(mapa_ids)
    ampliado[origen] = destino
    for a in areas_o:
        ampliado[a["id"]] = areas_d[a["codigo"]]
    for clave, uid in uids_d.items():
        ampliado[clave] = uid
    return ampliado
