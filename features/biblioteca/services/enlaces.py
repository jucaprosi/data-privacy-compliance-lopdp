# ¤adpa ¤rbac-tenant
# ¤¤developer-architect
"""Enlaces entre una revisión documental concreta y acciones canónicas de Roadmap (BIB-302)."""
from datetime import datetime
from collections.abc import Awaitable, Callable
from typing import Any
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.errores import ErrorNegocio
from app_core.audit import registrar_evento
from features.biblioteca.services.documentos_consulta import contexto

ObtenerAccion = Callable[[AsyncSession, str, str], Awaitable[Any]]


class CrearEnlace(BaseModel):
    model_config = ConfigDict(extra="forbid")
    accion_id: str = Field(min_length=1, max_length=64)
    revision: int = Field(ge=1)


class EnlaceDocumento(BaseModel):
    id: str
    documento_id: str
    documento_revision: int
    accion_id: str
    accion_titulo: str
    accion_estado: str
    requisito: str
    hallazgo_id: str | None
    hallazgo_titulo: str | None
    hallazgo_origen: str | None
    hallazgo_origen_ref: str | None
    pregunta: str | None
    assessment_version: int | None
    creado_por: str
    creado_en: datetime


async def listar_enlaces(
    session: AsyncSession, tenant_id: str, actor: str, documento_id: str
) -> list[EnlaceDocumento]:
    await contexto(session, tenant_id, actor)
    existe = (await session.execute(text(
        "SELECT 1 FROM biblioteca_documentos WHERE id=:d AND tenant_id=:t"
    ), {"d": documento_id, "t": tenant_id})).scalar()
    if existe is None:
        raise ErrorNegocio("BIB_DOCUMENTO_NO_ENCONTRADO")
    filas = await session.execute(text(
        "SELECT e.id,e.documento_id,e.documento_revision,e.accion_id,e.creado_por,e.creado_en,"
        "t.title accion_titulo,t.status accion_estado,t.control_ref requisito,h.id hallazgo_id,"
        "h.titulo hallazgo_titulo,h.origen hallazgo_origen,h.origen_ref hallazgo_origen_ref,"
        "CASE WHEN h.origen='diagnostico' THEN t.control_ref END pregunta,dr.secuencia assessment_version "
        "FROM biblioteca_revision_acciones e "
        "JOIN roadmap_tasks t ON t.id=e.accion_id AND t.tenant_id=e.tenant_id "
        "LEFT JOIN hallazgos h ON h.id=t.hallazgo_id AND h.tenant_id=e.tenant_id "
        "LEFT JOIN diagnostico_resultados dr ON h.origen='diagnostico' AND dr.tenant_id=e.tenant_id "
        "AND dr.id=split_part(h.origen_ref,':',1) "
        "WHERE e.tenant_id=:t AND e.documento_id=:d ORDER BY e.creado_en,e.id"
    ), {"t": tenant_id, "d": documento_id})
    return [EnlaceDocumento(**dict(f)) for f in filas.mappings().all()]


async def listar_documentos_de_accion(
    session: AsyncSession, tenant_id: str, actor: str, accion_id: str, obtener_accion: ObtenerAccion
) -> list[EnlaceDocumento]:
    """Vista inversa N:M; una acción ajena se trata como inexistente para este tenant."""
    await contexto(session, tenant_id, actor)
    if await obtener_accion(session, tenant_id, accion_id) is None:
        raise ErrorNegocio("BIB_ENLACE_ACCION_AJENA")
    documentos = (await session.execute(text(
        "SELECT DISTINCT documento_id FROM biblioteca_revision_acciones "
        "WHERE tenant_id=:t AND accion_id=:a ORDER BY documento_id"
    ), {"t": tenant_id, "a": accion_id})).scalars().all()
    resultado: list[EnlaceDocumento] = []
    for documento_id in documentos:
        resultado.extend(e for e in await listar_enlaces(session, tenant_id, actor, documento_id)
                         if e.accion_id == accion_id)
    return resultado


async def crear_enlace(
    session: AsyncSession, tenant_id: str, actor: str, documento_id: str, entrada: CrearEnlace,
    obtener_accion: ObtenerAccion,
) -> EnlaceDocumento:
    await contexto(session, tenant_id, actor)
    documento = (await session.execute(text(
        "SELECT revision FROM biblioteca_documentos WHERE id=:d AND tenant_id=:t"
    ), {"d": documento_id, "t": tenant_id})).scalar()
    if documento is None:
        raise ErrorNegocio("BIB_DOCUMENTO_NO_ENCONTRADO")
    if int(documento) < entrada.revision:
        raise ErrorNegocio("BIB_ENLACE_REVISION_INVALIDA")
    accion = await obtener_accion(session, tenant_id, entrada.accion_id)
    if accion is None:
        raise ErrorNegocio("BIB_ENLACE_ACCION_AJENA")
    enlace_id = f"{documento_id}:{entrada.revision}:{entrada.accion_id}"
    insertado = (await session.execute(text(
        "INSERT INTO biblioteca_revision_acciones(id,tenant_id,documento_id,documento_revision,accion_id,creado_por) "
        "VALUES (:id,:t,:d,:r,:a,:u) ON CONFLICT (tenant_id,documento_id,documento_revision,accion_id) "
        "DO NOTHING RETURNING id"
    ), {"id": enlace_id, "t": tenant_id, "d": documento_id, "r": entrada.revision,
        "a": entrada.accion_id, "u": actor})).scalar()
    if insertado is not None:
        await registrar_evento(session, tenant_id, "biblioteca_revision_accion", enlace_id,
                                "enlace_documental_creado", actor,
                                {"documento_id": documento_id, "revision": entrada.revision,
                                 "accion_id": entrada.accion_id})
    enlaces = await listar_enlaces(session, tenant_id, actor, documento_id)
    return next(e for e in enlaces if e.accion_id == entrada.accion_id and e.documento_revision == entrada.revision)


async def eliminar_enlace(
    session: AsyncSession, tenant_id: str, actor: str, documento_id: str, enlace_id: str
) -> None:
    await contexto(session, tenant_id, actor)
    fila = (await session.execute(text(
        "DELETE FROM biblioteca_revision_acciones WHERE id=:id AND documento_id=:d AND tenant_id=:t "
        "RETURNING documento_revision,accion_id"
    ), {"id": enlace_id, "d": documento_id, "t": tenant_id})).mappings().first()
    if fila is None:
        raise ErrorNegocio("BIB_ENLACE_NO_ENCONTRADO")
    await registrar_evento(session, tenant_id, "biblioteca_revision_accion", enlace_id,
                            "enlace_documental_eliminado", actor,
                            {"documento_id": documento_id, "revision": fila["documento_revision"],
                             "accion_id": fila["accion_id"]})
