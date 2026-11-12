"""Sedes de la organización y clientes cuando actúa como encargada (sala ADPA: Organización). ¤rbac-tenant ¤inventario

ORG-18. Dos colecciones por organización con RLS forzada: sedes (una sola principal vigente, R1) y clientes
por encargo (solo si `tenants.rol_datos` es encargado o ambos, R2), con el contrato referenciado por su
huella SHA-256 en Evidencias (R3; aquí no se custodia). La organización y la identidad llegan del contexto
de la sesión; los cuerpos no las admiten. Nada se borra: las sedes y los clientes se retiran. La auditoría no
lleva datos personales: solo el tipo, el identificador y la acción.
"""
from __future__ import annotations

from datetime import date
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.audit import registrar_evento
from app_core.errors import ErrorNegocio
from app_core.pasillo import evidencias as _evidencias
from features.organizacion.domain.errores import (
    CLIENTE_DUPLICADO,
    CLIENTE_NO_ENCONTRADO,
    CONTRATO_NO_ENCONTRADO,
    NO_ES_ENCARGADA,
    SEDE_NO_ENCONTRADA,
    SEDE_PRINCIPAL_DUPLICADA,
)
from features.organizacion.services.contexto_tenant import fijar_tenant


# ----------------------------------------------------------------------------------- modelos

class SedeEntrada(BaseModel):
    """Alta y edición (PUT reemplaza los campos): la sede se describe completa."""
    model_config = ConfigDict(extra="forbid")
    nombre: str = Field(min_length=1, max_length=200)
    direccion: str = Field(min_length=1, max_length=300)
    ciudad: str = Field(min_length=1, max_length=120)
    provincia: str = Field(min_length=1, max_length=120)
    es_principal: bool = False
    contacto_spdp: Optional[str] = Field(default=None, max_length=500)
    contacto_titulares: Optional[str] = Field(default=None, max_length=500)
    medidas: Optional[str] = Field(default=None, max_length=2000)


class ClienteEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid")
    razon_social: str = Field(min_length=1, max_length=200)
    ruc: str = Field(pattern=r"^[0-9]{13}$")
    contrato_sha256: Optional[str] = Field(default=None, max_length=64)
    vigente_hasta: Optional[date] = None


# ----------------------------------------------------------------------------------- consultas

_SQL_SEDES = """
SELECT id, nombre, direccion, ciudad, provincia, es_principal, contacto_spdp, contacto_titulares, medidas,
       retirada_en, creado_en, actualizado_en
FROM sedes WHERE tenant_id = :t ORDER BY (retirada_en IS NOT NULL), NOT es_principal, lower(nombre)
"""
_SQL_SEDE = "SELECT id, es_principal, retirada_en FROM sedes WHERE id = :id AND tenant_id = :t"
_SQL_HAY_OTRA_PRINCIPAL = (
    "SELECT 1 FROM sedes WHERE tenant_id = :t AND es_principal AND retirada_en IS NULL AND id <> :id"
)
_SQL_CLIENTES = """
SELECT id, razon_social, ruc, contrato_sha256, vigente_hasta, retirado_en, creado_en, actualizado_en
FROM clientes_encargo WHERE tenant_id = :t ORDER BY (retirado_en IS NOT NULL), lower(razon_social)
"""
_SQL_CLIENTE = "SELECT id, retirado_en FROM clientes_encargo WHERE id = :id AND tenant_id = :t"


def _serializar(fila: Any) -> dict[str, Any]:
    salida = dict(fila)
    for campo, valor in salida.items():
        if hasattr(valor, "isoformat"):
            salida[campo] = valor.isoformat()
    return salida


async def _auditar(session: AsyncSession, tenant_id: str, user_id: str, tipo: str, entidad: str, accion: str) -> None:
    await registrar_evento(
        session=session, tenant_id=tenant_id, entity_type=tipo, entity_id=entidad,
        action=accion, user_id=user_id, payload=None,
    )


# ----------------------------------------------------------------------------------- sedes

async def listar_sedes(session: AsyncSession, tenant_id: str) -> list[dict[str, Any]]:
    await fijar_tenant(session, tenant_id)
    return [_serializar(f) for f in (await session.execute(text(_SQL_SEDES), {"t": tenant_id})).mappings().all()]


async def _sede_vigente(session: AsyncSession, tenant_id: str, sede_id: str) -> Any:
    fila = (await session.execute(text(_SQL_SEDE), {"id": sede_id, "t": tenant_id})).mappings().first()
    if fila is None or fila["retirada_en"] is not None:
        raise ErrorNegocio(SEDE_NO_ENCONTRADA)
    return fila


async def _exigir_principal_libre(session: AsyncSession, tenant_id: str, sede_id: str) -> None:
    if (await session.execute(text(_SQL_HAY_OTRA_PRINCIPAL), {"t": tenant_id, "id": sede_id})).first():
        raise ErrorNegocio(SEDE_PRINCIPAL_DUPLICADA)


async def crear_sede(session: AsyncSession, tenant_id: str, user_id: str, datos: SedeEntrada) -> dict[str, Any]:
    await fijar_tenant(session, tenant_id, user_id)
    sede_id = str(uuid4())
    if datos.es_principal:
        await _exigir_principal_libre(session, tenant_id, sede_id)
    try:
        async with session.begin_nested():
            await session.execute(
                text(
                    "INSERT INTO sedes (id, tenant_id, nombre, direccion, ciudad, provincia, es_principal, "
                    "contacto_spdp, contacto_titulares, medidas, creado_por) "
                    "VALUES (:id, :t, :nombre, :direccion, :ciudad, :provincia, :principal, :spdp, :titulares, "
                    ":medidas, :user)"
                ),
                {
                    "id": sede_id, "t": tenant_id, "nombre": datos.nombre.strip(), "direccion": datos.direccion.strip(),
                    "ciudad": datos.ciudad.strip(), "provincia": datos.provincia.strip(), "principal": datos.es_principal,
                    "spdp": datos.contacto_spdp, "titulares": datos.contacto_titulares, "medidas": datos.medidas,
                    "user": user_id,
                },
            )
    except IntegrityError as exc:  # carrera con otra sede principal: el índice parcial manda
        raise ErrorNegocio(SEDE_PRINCIPAL_DUPLICADA) from exc
    await _auditar(session, tenant_id, user_id, "sede", sede_id, "crear")
    return {"id": sede_id}


async def editar_sede(
    session: AsyncSession, tenant_id: str, user_id: str, sede_id: str, datos: SedeEntrada,
) -> dict[str, Any]:
    await fijar_tenant(session, tenant_id, user_id)
    await _sede_vigente(session, tenant_id, sede_id)
    if datos.es_principal:
        await _exigir_principal_libre(session, tenant_id, sede_id)
    try:
        async with session.begin_nested():
            await session.execute(
                text(
                    "UPDATE sedes SET nombre = :nombre, direccion = :direccion, ciudad = :ciudad, "
                    "provincia = :provincia, es_principal = :principal, contacto_spdp = :spdp, "
                    "contacto_titulares = :titulares, medidas = :medidas, actualizado_en = now() "
                    "WHERE id = :id AND tenant_id = :t"
                ),
                {
                    "id": sede_id, "t": tenant_id, "nombre": datos.nombre.strip(), "direccion": datos.direccion.strip(),
                    "ciudad": datos.ciudad.strip(), "provincia": datos.provincia.strip(), "principal": datos.es_principal,
                    "spdp": datos.contacto_spdp, "titulares": datos.contacto_titulares, "medidas": datos.medidas,
                },
            )
    except IntegrityError as exc:
        raise ErrorNegocio(SEDE_PRINCIPAL_DUPLICADA) from exc
    await _auditar(session, tenant_id, user_id, "sede", sede_id, "editar")
    return {"id": sede_id}


async def retirar_sede(session: AsyncSession, tenant_id: str, user_id: str, sede_id: str) -> dict[str, Any]:
    await fijar_tenant(session, tenant_id, user_id)
    await _sede_vigente(session, tenant_id, sede_id)
    await session.execute(
        text("UPDATE sedes SET retirada_en = now(), actualizado_en = now() WHERE id = :id AND tenant_id = :t"),
        {"id": sede_id, "t": tenant_id},
    )
    await _auditar(session, tenant_id, user_id, "sede", sede_id, "retirar")
    return {"id": sede_id}


# ----------------------------------------------------------------------------------- clientes

async def _exigir_encargada(session: AsyncSession, tenant_id: str) -> None:
    """R2: solo una organización encargada (o ambos) tiene clientes por encargo."""
    rol = (await session.execute(text("SELECT rol_datos FROM tenants WHERE id = :t"), {"t": tenant_id})).scalar()
    if rol not in ("encargado", "ambos"):
        raise ErrorNegocio(NO_ES_ENCARGADA)


def _contrato_normalizado(tenant_id: str, sha256: Optional[str]) -> Optional[str]:
    """R3: la huella debe existir en Evidencias de la propia organización."""
    if sha256 is None or not sha256.strip():
        return None
    huella = _evidencias.huella_registrada(tenant_id, sha256.strip())
    if huella is None:
        raise ErrorNegocio(CONTRATO_NO_ENCONTRADO)
    return huella


async def listar_clientes(session: AsyncSession, tenant_id: str) -> list[dict[str, Any]]:
    await fijar_tenant(session, tenant_id)
    await _exigir_encargada(session, tenant_id)
    return [_serializar(f) for f in (await session.execute(text(_SQL_CLIENTES), {"t": tenant_id})).mappings().all()]


async def crear_cliente(session: AsyncSession, tenant_id: str, user_id: str, datos: ClienteEntrada) -> dict[str, Any]:
    await fijar_tenant(session, tenant_id, user_id)
    await _exigir_encargada(session, tenant_id)
    contrato = _contrato_normalizado(tenant_id, datos.contrato_sha256)
    cliente_id = str(uuid4())
    try:
        async with session.begin_nested():
            await session.execute(
                text(
                    "INSERT INTO clientes_encargo (id, tenant_id, razon_social, ruc, contrato_sha256, vigente_hasta, "
                    "creado_por) VALUES (:id, :t, :razon, :ruc, :contrato, :vigente, :user)"
                ),
                {
                    "id": cliente_id, "t": tenant_id, "razon": datos.razon_social.strip(), "ruc": datos.ruc,
                    "contrato": contrato, "vigente": datos.vigente_hasta, "user": user_id,
                },
            )
    except IntegrityError as exc:
        raise ErrorNegocio(CLIENTE_DUPLICADO) from exc
    await _auditar(session, tenant_id, user_id, "cliente_encargo", cliente_id, "crear")
    return {"id": cliente_id}


async def _cliente_vigente(session: AsyncSession, tenant_id: str, cliente_id: str) -> None:
    fila = (await session.execute(text(_SQL_CLIENTE), {"id": cliente_id, "t": tenant_id})).mappings().first()
    if fila is None or fila["retirado_en"] is not None:
        raise ErrorNegocio(CLIENTE_NO_ENCONTRADO)


async def editar_cliente(
    session: AsyncSession, tenant_id: str, user_id: str, cliente_id: str, datos: ClienteEntrada,
) -> dict[str, Any]:
    await fijar_tenant(session, tenant_id, user_id)
    await _exigir_encargada(session, tenant_id)
    await _cliente_vigente(session, tenant_id, cliente_id)
    contrato = _contrato_normalizado(tenant_id, datos.contrato_sha256)
    try:
        async with session.begin_nested():
            await session.execute(
                text(
                    "UPDATE clientes_encargo SET razon_social = :razon, ruc = :ruc, contrato_sha256 = :contrato, "
                    "vigente_hasta = :vigente, actualizado_en = now() WHERE id = :id AND tenant_id = :t"
                ),
                {
                    "id": cliente_id, "t": tenant_id, "razon": datos.razon_social.strip(), "ruc": datos.ruc,
                    "contrato": contrato, "vigente": datos.vigente_hasta,
                },
            )
    except IntegrityError as exc:
        raise ErrorNegocio(CLIENTE_DUPLICADO) from exc
    await _auditar(session, tenant_id, user_id, "cliente_encargo", cliente_id, "editar")
    return {"id": cliente_id}


async def retirar_cliente(session: AsyncSession, tenant_id: str, user_id: str, cliente_id: str) -> dict[str, Any]:
    await fijar_tenant(session, tenant_id, user_id)
    await _exigir_encargada(session, tenant_id)
    await _cliente_vigente(session, tenant_id, cliente_id)
    await session.execute(
        text("UPDATE clientes_encargo SET retirado_en = now(), actualizado_en = now() WHERE id = :id AND tenant_id = :t"),
        {"id": cliente_id, "t": tenant_id},
    )
    await _auditar(session, tenant_id, user_id, "cliente_encargo", cliente_id, "retirar")
    return {"id": cliente_id}
