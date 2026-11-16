"""Inventario de activos y sistemas, soportes y personas mínimas (sala ADPA: Organización). ¤rbac-tenant ¤inventario

ORG-17. Tres colecciones por organización, todas con RLS forzada: activos (sistemas y soportes físicos o
digitales), personas mínimas (nombre, cargo, área, correo; la cédula solo si se informa y siempre cifrada)
y el vínculo de un activo con tratamientos del RAT. La organización y la identidad llegan del contexto de
la sesión; los cuerpos no las admiten. Los tratamientos se validan por el pasillo de la sala rat, sin
importar su código. Nada se borra: los activos y las personas se archivan; los vínculos se reemplazan.
"""
from __future__ import annotations

import os
from typing import Any, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.audit import registrar_evento
from app_core.errors import ErrorNegocio
from app_core.pasillo.rat import listar_actividades_resumen
from features.organizacion.domain.errores import (
    INVENTARIO_CEDULA_INVALIDA,
    INVENTARIO_CIFRADO_NO_CONFIGURADO,
    INVENTARIO_DUPLICADO,
    INVENTARIO_NO_ENCONTRADO,
    INVENTARIO_REFERENCIA_INVALIDA,
)
from features.organizacion.services.contexto_tenant import fijar_tenant
from features.organizacion.services.datos_documentales_engine import es_cedula_valida

TipoActivo = Literal["sistema", "soporte_fisico", "soporte_digital"]
TIPOS_ACTIVO: tuple[str, ...] = ("sistema", "soporte_fisico", "soporte_digital")
VARIABLE_CLAVE_CIFRADO = "INVENTARIO_CLAVE_CIFRADO"


# ----------------------------------------------------------------------------------- modelos

class ActivoCrear(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tipo: TipoActivo
    nombre: str = Field(min_length=1, max_length=200)
    descripcion: Optional[str] = Field(default=None, max_length=1000)
    ubicacion: Optional[str] = Field(default=None, max_length=200)
    area_id: Optional[str] = None
    responsable_id: Optional[str] = None


class ActivoEditar(BaseModel):
    """Solo cambian los campos enviados; `tipo` no se edita."""
    model_config = ConfigDict(extra="forbid")
    nombre: Optional[str] = Field(default=None, min_length=1, max_length=200)
    descripcion: Optional[str] = Field(default=None, max_length=1000)
    ubicacion: Optional[str] = Field(default=None, max_length=200)
    area_id: Optional[str] = None
    responsable_id: Optional[str] = None
    archivado: Optional[bool] = None


class PersonaCrear(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nombre: str = Field(min_length=1, max_length=200)
    cargo: str = Field(min_length=1, max_length=150)
    area_id: Optional[str] = None
    email: str = Field(min_length=3, max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    cedula: Optional[str] = Field(default=None, max_length=13)


class PersonaEditar(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nombre: Optional[str] = Field(default=None, min_length=1, max_length=200)
    cargo: Optional[str] = Field(default=None, min_length=1, max_length=150)
    area_id: Optional[str] = None
    email: Optional[str] = Field(default=None, min_length=3, max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    cedula: Optional[str] = Field(default=None, max_length=13)
    archivada: Optional[bool] = None


class VinculosTratamientos(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tratamiento_ids: list[str] = Field(max_length=200)


# ----------------------------------------------------------------------------------- cifrado

def _cifrador():
    """Cifrador de la cédula. Sin clave configurada, la cédula no se guarda (nunca en claro)."""
    clave = os.environ.get(VARIABLE_CLAVE_CIFRADO, "").strip()
    if not clave:
        raise ErrorNegocio(INVENTARIO_CIFRADO_NO_CONFIGURADO)
    from cryptography.fernet import Fernet

    try:
        return Fernet(clave.encode("ascii"))
    except (ValueError, UnicodeEncodeError) as exc:
        raise ErrorNegocio(INVENTARIO_CIFRADO_NO_CONFIGURADO) from exc


def _cifrar_cedula(cedula: str) -> str:
    if not es_cedula_valida(cedula):
        raise ErrorNegocio(INVENTARIO_CEDULA_INVALIDA)
    return _cifrador().encrypt(cedula.encode("ascii")).decode("ascii")


# ----------------------------------------------------------------------------------- consultas

_SQL_ACTIVOS = """
SELECT a.id, a.tipo, a.nombre, a.descripcion, a.ubicacion, a.area_id, a.responsable_id, a.archivado,
       a.created_at, a.updated_at,
       COALESCE((SELECT array_agg(v.rat_id ORDER BY v.rat_id)
                 FROM inventario_activos_tratamientos v WHERE v.activo_id = a.id), ARRAY[]::text[]) AS tratamiento_ids
FROM inventario_activos a
WHERE a.tenant_id = :t AND (CAST(:tipo AS text) IS NULL OR a.tipo = :tipo)
ORDER BY a.archivado, lower(a.nombre)
"""

_SQL_ACTIVO = """
SELECT id, tipo, nombre, descripcion, ubicacion, area_id, responsable_id, archivado
FROM inventario_activos WHERE id = :id AND tenant_id = :t
"""

_SQL_PERSONAS = """
SELECT id, nombre, cargo, area_id, email, (cedula_cifrada IS NOT NULL) AS tiene_cedula, archivada,
       created_at, updated_at
FROM inventario_personas WHERE tenant_id = :t ORDER BY archivada, lower(nombre)
"""

_SQL_PERSONA = """
SELECT id, nombre, cargo, area_id, email, cedula_cifrada, archivada
FROM inventario_personas WHERE id = :id AND tenant_id = :t
"""


def _serializar(fila: Any) -> dict[str, Any]:
    salida = dict(fila)
    for campo in ("created_at", "updated_at"):
        if salida.get(campo) is not None:
            salida[campo] = salida[campo].isoformat()
    return salida


async def _existe_area(session: AsyncSession, tenant_id: str, area_id: Optional[str]) -> None:
    if area_id is None:
        return
    fila = (await session.execute(
        text("SELECT 1 FROM areas WHERE id = :id AND tenant_id = :t AND deleted_at IS NULL"),
        {"id": area_id, "t": tenant_id},
    )).first()
    if fila is None:
        raise ErrorNegocio(INVENTARIO_REFERENCIA_INVALIDA)


async def _existe_persona(session: AsyncSession, tenant_id: str, persona_id: Optional[str]) -> None:
    if persona_id is None:
        return
    fila = (await session.execute(
        text("SELECT 1 FROM inventario_personas WHERE id = :id AND tenant_id = :t AND NOT archivada"),
        {"id": persona_id, "t": tenant_id},
    )).first()
    if fila is None:
        raise ErrorNegocio(INVENTARIO_REFERENCIA_INVALIDA)


async def _auditar(session: AsyncSession, tenant_id: str, user_id: str, tipo: str, entidad: str, accion: str) -> None:
    await registrar_evento(
        session=session, tenant_id=tenant_id, entity_type=tipo, entity_id=entidad,
        action=accion, user_id=user_id, payload=None,
    )


# ----------------------------------------------------------------------------------- activos

async def listar_activos(session: AsyncSession, tenant_id: str, tipo: Optional[str] = None) -> list[dict[str, Any]]:
    if tipo is not None and tipo not in TIPOS_ACTIVO:
        raise ErrorNegocio(INVENTARIO_REFERENCIA_INVALIDA, "El tipo de activo no existe.")
    await fijar_tenant(session, tenant_id)
    filas = (await session.execute(text(_SQL_ACTIVOS), {"t": tenant_id, "tipo": tipo})).mappings().all()
    return [_serializar(f) for f in filas]


async def crear_activo(session: AsyncSession, tenant_id: str, user_id: str, datos: ActivoCrear) -> dict[str, Any]:
    await fijar_tenant(session, tenant_id, user_id)
    await _existe_area(session, tenant_id, datos.area_id)
    await _existe_persona(session, tenant_id, datos.responsable_id)
    activo_id = str(uuid4())
    try:
        async with session.begin_nested():
            await session.execute(
                text(
                    "INSERT INTO inventario_activos "
                    "(id, tenant_id, tipo, nombre, descripcion, ubicacion, area_id, responsable_id, created_by) "
                    "VALUES (:id, :t, :tipo, :nombre, :descripcion, :ubicacion, :area, :resp, :user)"
                ),
                {
                    "id": activo_id, "t": tenant_id, "tipo": datos.tipo, "nombre": datos.nombre.strip(),
                    "descripcion": datos.descripcion, "ubicacion": datos.ubicacion, "area": datos.area_id,
                    "resp": datos.responsable_id, "user": user_id,
                },
            )
    except IntegrityError as exc:
        raise ErrorNegocio(INVENTARIO_DUPLICADO) from exc
    await _auditar(session, tenant_id, user_id, "inventario_activo", activo_id, "crear")
    return {"id": activo_id}


async def editar_activo(
    session: AsyncSession, tenant_id: str, user_id: str, activo_id: str, datos: ActivoEditar,
) -> dict[str, Any]:
    await fijar_tenant(session, tenant_id, user_id)
    actual = (await session.execute(text(_SQL_ACTIVO), {"id": activo_id, "t": tenant_id})).mappings().first()
    if actual is None:
        raise ErrorNegocio(INVENTARIO_NO_ENCONTRADO)
    nuevo = {**actual, **{c: getattr(datos, c) for c in datos.model_fields_set}}
    if "area_id" in datos.model_fields_set:
        await _existe_area(session, tenant_id, nuevo["area_id"])
    if "responsable_id" in datos.model_fields_set:
        await _existe_persona(session, tenant_id, nuevo["responsable_id"])
    if nuevo["nombre"] is None or nuevo["archivado"] is None:
        raise ErrorNegocio(INVENTARIO_REFERENCIA_INVALIDA, "El nombre y el estado no pueden quedar vacíos.")
    try:
        async with session.begin_nested():
            await session.execute(
                text(
                    "UPDATE inventario_activos SET nombre = :nombre, descripcion = :descripcion, "
                    "ubicacion = :ubicacion, area_id = :area, responsable_id = :resp, archivado = :arch, "
                    "updated_at = now() WHERE id = :id AND tenant_id = :t"
                ),
                {
                    "id": activo_id, "t": tenant_id, "nombre": str(nuevo["nombre"]).strip(),
                    "descripcion": nuevo["descripcion"], "ubicacion": nuevo["ubicacion"],
                    "area": nuevo["area_id"], "resp": nuevo["responsable_id"], "arch": nuevo["archivado"],
                },
            )
    except IntegrityError as exc:
        raise ErrorNegocio(INVENTARIO_DUPLICADO) from exc
    await _auditar(session, tenant_id, user_id, "inventario_activo", activo_id, "editar")
    return {"id": activo_id}


async def reemplazar_vinculos_tratamientos(
    session: AsyncSession, tenant_id: str, user_id: str, activo_id: str, datos: VinculosTratamientos,
) -> dict[str, Any]:
    """Deja exactamente los tratamientos indicados; cada uno debe existir en el RAT de la organización."""
    await fijar_tenant(session, tenant_id, user_id)
    actual = (await session.execute(text(_SQL_ACTIVO), {"id": activo_id, "t": tenant_id})).mappings().first()
    if actual is None:
        raise ErrorNegocio(INVENTARIO_NO_ENCONTRADO)
    pedidos = sorted(set(datos.tratamiento_ids))
    if pedidos:
        validos = {a.id for a in await listar_actividades_resumen(session, tenant_id)}
        if not set(pedidos) <= validos:
            raise ErrorNegocio(INVENTARIO_REFERENCIA_INVALIDA)
    await session.execute(
        text("DELETE FROM inventario_activos_tratamientos WHERE activo_id = :a AND tenant_id = :t"),
        {"a": activo_id, "t": tenant_id},
    )
    for rat_id in pedidos:
        await session.execute(
            text(
                "INSERT INTO inventario_activos_tratamientos (activo_id, rat_id, tenant_id) "
                "VALUES (:a, :r, :t)"
            ),
            {"a": activo_id, "r": rat_id, "t": tenant_id},
        )
    await _auditar(session, tenant_id, user_id, "inventario_activo", activo_id, "vincular_tratamientos")
    return {"id": activo_id, "tratamiento_ids": pedidos}


async def tratamientos_disponibles(session: AsyncSession, tenant_id: str) -> list[dict[str, Any]]:
    """Tratamientos del RAT que se pueden vincular (por el pasillo de rat)."""
    await fijar_tenant(session, tenant_id)
    return [
        {"id": a.id, "codigo": a.codigo, "nombre": a.nombre}
        for a in await listar_actividades_resumen(session, tenant_id)
    ]


# ----------------------------------------------------------------------------------- personas

async def listar_personas(session: AsyncSession, tenant_id: str) -> list[dict[str, Any]]:
    await fijar_tenant(session, tenant_id)
    filas = (await session.execute(text(_SQL_PERSONAS), {"t": tenant_id})).mappings().all()
    return [_serializar(f) for f in filas]


async def crear_persona(session: AsyncSession, tenant_id: str, user_id: str, datos: PersonaCrear) -> dict[str, Any]:
    await fijar_tenant(session, tenant_id, user_id)
    await _existe_area(session, tenant_id, datos.area_id)
    cedula = _cifrar_cedula(datos.cedula) if datos.cedula else None
    persona_id = str(uuid4())
    try:
        async with session.begin_nested():
            await session.execute(
                text(
                    "INSERT INTO inventario_personas "
                    "(id, tenant_id, nombre, cargo, area_id, email, cedula_cifrada, created_by) "
                    "VALUES (:id, :t, :nombre, :cargo, :area, :email, :cedula, :user)"
                ),
                {
                    "id": persona_id, "t": tenant_id, "nombre": datos.nombre.strip(), "cargo": datos.cargo.strip(),
                    "area": datos.area_id, "email": datos.email.strip(), "cedula": cedula, "user": user_id,
                },
            )
    except IntegrityError as exc:
        raise ErrorNegocio(INVENTARIO_DUPLICADO) from exc
    await _auditar(session, tenant_id, user_id, "inventario_persona", persona_id, "crear")
    return {"id": persona_id}


async def editar_persona(
    session: AsyncSession, tenant_id: str, user_id: str, persona_id: str, datos: PersonaEditar,
) -> dict[str, Any]:
    await fijar_tenant(session, tenant_id, user_id)
    actual = (await session.execute(text(_SQL_PERSONA), {"id": persona_id, "t": tenant_id})).mappings().first()
    if actual is None:
        raise ErrorNegocio(INVENTARIO_NO_ENCONTRADO)
    nuevo = {**actual, **{c: getattr(datos, c) for c in datos.model_fields_set if c != "cedula"}}
    if "cedula" in datos.model_fields_set:
        nuevo["cedula_cifrada"] = _cifrar_cedula(datos.cedula) if datos.cedula else None
    if "area_id" in datos.model_fields_set:
        await _existe_area(session, tenant_id, nuevo["area_id"])
    if nuevo["nombre"] is None or nuevo["cargo"] is None or nuevo["email"] is None or nuevo["archivada"] is None:
        raise ErrorNegocio(INVENTARIO_REFERENCIA_INVALIDA, "Nombre, cargo, correo y estado no pueden quedar vacíos.")
    try:
        async with session.begin_nested():
            await session.execute(
                text(
                    "UPDATE inventario_personas SET nombre = :nombre, cargo = :cargo, area_id = :area, "
                    "email = :email, cedula_cifrada = :cedula, archivada = :arch, updated_at = now() "
                    "WHERE id = :id AND tenant_id = :t"
                ),
                {
                    "id": persona_id, "t": tenant_id, "nombre": str(nuevo["nombre"]).strip(),
                    "cargo": str(nuevo["cargo"]).strip(), "area": nuevo["area_id"],
                    "email": str(nuevo["email"]).strip(), "cedula": nuevo["cedula_cifrada"],
                    "arch": nuevo["archivada"],
                },
            )
    except IntegrityError as exc:
        raise ErrorNegocio(INVENTARIO_DUPLICADO) from exc
    await _auditar(session, tenant_id, user_id, "inventario_persona", persona_id, "editar")
    return {"id": persona_id}
