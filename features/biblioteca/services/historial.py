# ¤adpa ¤rbac-tenant
# ¤¤developer-architect
"""Cronología autorizada y restauración append-only de documentos de la organización."""
from datetime import datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.errors import ErrorNegocio
from features.biblioteca.domain.documentos import huella
from features.biblioteca.services.documentos_consulta import contexto, obtener_documento

TipoEvento = Literal["cambio", "descarga", "generacion", "aprobacion", "notificacion", "reapertura", "restauracion"]


class ContratoHistorial(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EventoCronologia(ContratoHistorial):
    id: str
    tipo: TipoEvento
    revision: int | None
    actor_id: str
    detalle: dict[str, Any]
    creado_en: datetime


class RegistrarEvento(ContratoHistorial):
    tipo: Literal["descarga", "generacion", "aprobacion", "notificacion", "reapertura", "restauracion"]
    revision: int | None = Field(default=None, ge=1)
    detalle: dict[str, Any] = Field(default_factory=dict)


class RestaurarRevision(ContratoHistorial):
    revision_origen: int = Field(ge=1)
    motivo: str = Field(min_length=1, max_length=1000)


async def registrar_evento(
    session: AsyncSession, tenant_id: str, actor: str, documento_id: str, entrada: RegistrarEvento,
) -> EventoCronologia:
    await contexto(session, tenant_id, actor)
    documento = await obtener_documento(session, tenant_id, actor, documento_id)
    revision = entrada.revision or documento.revision
    fila = (await session.execute(text(
        "INSERT INTO biblioteca_eventos_documento(id,tenant_id,documento_id,tipo,revision,actor_id,detalle) "
        "VALUES (:id,:t,:d,:tipo,:r,:u,CAST(:detalle AS jsonb)) "
        "RETURNING id,tipo,revision,actor_id,detalle,creado_en"
    ), {"id": str(uuid4()), "t": tenant_id, "d": documento_id, "tipo": entrada.tipo,
        "r": revision, "u": actor, "detalle": __import__('json').dumps(entrada.detalle)})).mappings().one()
    return EventoCronologia(**fila)


async def cronologia(
    session: AsyncSession, tenant_id: str, actor: str, documento_id: str,
) -> list[EventoCronologia]:
    await contexto(session, tenant_id, actor)
    await obtener_documento(session, tenant_id, actor, documento_id)
    filas = (await session.execute(text(
        "SELECT id, CASE WHEN accion='creado' THEN 'cambio' ELSE 'cambio' END AS tipo, revision, actor_id, "
        "jsonb_build_object('accion',accion,'sha256',sha256) AS detalle, creado_en "
        "FROM biblioteca_documentos_historial WHERE tenant_id=:t AND documento_id=:d "
        "UNION ALL SELECT id,tipo,revision,actor_id,detalle,creado_en FROM biblioteca_eventos_documento "
        "WHERE tenant_id=:t AND documento_id=:d ORDER BY creado_en,id"
    ), {"t": tenant_id, "d": documento_id})).mappings().all()
    return [EventoCronologia(**fila) for fila in filas]


async def restaurar_revision(
    session: AsyncSession, tenant_id: str, actor: str, documento_id: str, entrada: RestaurarRevision,
):
    await contexto(session, tenant_id, actor)
    actual = await obtener_documento(session, tenant_id, actor, documento_id)
    origen = (await session.execute(text(
        "SELECT contenido_markdown FROM biblioteca_documentos_historial "
        "WHERE tenant_id=:t AND documento_id=:d AND revision=:r"
    ), {"t": tenant_id, "d": documento_id, "r": entrada.revision_origen})).scalar()
    if origen is None:
        raise ErrorNegocio("BIB_REVISION_NO_ENCONTRADA")
    nueva = actual.revision + 1
    actualizado = (await session.execute(text(
        "UPDATE biblioteca_documentos SET contenido_markdown=:c,sha256=:h,editado=true,revision=:n,"
        "actualizado_en=now() WHERE tenant_id=:t AND id=:d AND revision=:actual RETURNING revision"
    ), {"c": origen, "h": huella(origen), "n": nueva, "t": tenant_id, "d": documento_id,
        "actual": actual.revision})).scalar()
    if actualizado is None:
        raise ErrorNegocio("BIB_DOCUMENTO_REVISION_DESFASADA")
    await session.execute(text(
        "INSERT INTO biblioteca_documentos_historial(id,tenant_id,documento_id,revision,accion,contenido_markdown,"
        "sha256,actor_id) VALUES (:id,:t,:d,:r,'editado',:c,:h,:u)"
    ), {"id": str(uuid4()), "t": tenant_id, "d": documento_id, "r": nueva, "c": origen,
        "h": huella(origen), "u": actor})
    await registrar_evento(session, tenant_id, actor, documento_id, RegistrarEvento(
        tipo="restauracion", revision=nueva,
        detalle={"revision_origen": entrada.revision_origen, "motivo": entrada.motivo},
    ))
    return await obtener_documento(session, tenant_id, actor, documento_id)
