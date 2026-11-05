# ¤adpa ¤rbac-tenant
"""Flujo de cuatro ojos para documentos de la organización."""
from uuid import uuid4
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app_core.errors import ErrorNegocio
from features.biblioteca.domain.documentos import faltantes_de
from features.biblioteca.domain.revisiones import (
    AprobarRevision, DelegarAutoridad, DictamenRevision, EnviarRevision, RevisionDocumental,
)
from features.biblioteca.services.documentos_consulta import contexto


async def delegar_autoridad(session: AsyncSession, tenant_id: str, actor: str,
                            entrada: DelegarAutoridad) -> str:
    await contexto(session, tenant_id, actor)
    if entrada.vigente_hasta is not None and entrada.vigente_hasta <= entrada.vigente_desde:
        raise ErrorNegocio("BIB_AUTORIDAD_NO_VIGENTE")
    autoridad_id = str(uuid4())
    await session.execute(text(
        "INSERT INTO biblioteca_autoridades_aprobacion(id,tenant_id,usuario_id,criterio,vigente_desde,"
        "vigente_hasta,delegada_por) VALUES (:id,:t,:u,:c,:desde,:hasta,:actor)"
    ), {"id": autoridad_id, "t": tenant_id, "u": entrada.usuario_id, "c": entrada.criterio,
        "desde": entrada.vigente_desde, "hasta": entrada.vigente_hasta, "actor": actor})
    return autoridad_id


async def enviar_a_revision(session: AsyncSession, tenant_id: str, actor: str, documento_id: str,
                            entrada: EnviarRevision) -> RevisionDocumental:
    await contexto(session, tenant_id, actor)
    fila = (await session.execute(text(
        "SELECT revision,sha256,contenido_markdown,creado_por FROM biblioteca_documentos "
        "WHERE id=:id AND tenant_id=:t AND estado='borrador' FOR UPDATE"
    ), {"id": documento_id, "t": tenant_id})).mappings().first()
    if fila is None:
        raise ErrorNegocio("BIB_DOCUMENTO_NO_REVISABLE")
    if faltantes_de(fila["contenido_markdown"]):
        raise ErrorNegocio("BIB_DOCUMENTO_INCOMPLETO")
    if entrada.revisor_id == actor:
        raise ErrorNegocio("BIB_SEPARACION_FUNCIONES")
    rid = str(uuid4())
    await session.execute(text(
        "INSERT INTO biblioteca_revisiones_documento(id,tenant_id,documento_id,revision,sha256,revisor_id,"
        "tipo_participacion,asignado_por) VALUES (:id,:t,:d,:r,:h,:revisor,:tipo,:actor)"
    ), {"id": rid, "t": tenant_id, "d": documento_id, "r": fila["revision"], "h": fila["sha256"],
        "revisor": entrada.revisor_id, "tipo": entrada.tipo_participacion, "actor": actor})
    enviados = (await session.execute(text("SELECT biblioteca_enviar_documento_a_revision(:id,:t)"),
                                      {"id": documento_id, "t": tenant_id})).scalar()
    if enviados != 1:
        raise ErrorNegocio("BIB_REVISION_DOCUMENTAL_DESFASADA")
    return await obtener_revision(session, tenant_id, rid)


async def obtener_revision(session: AsyncSession, tenant_id: str, revision_id: str) -> RevisionDocumental:
    fila = (await session.execute(text(
        "SELECT id,documento_id,revision,sha256,revisor_id,tipo_participacion,estado,observaciones,"
        "asignado_por,asignado_en,decidido_por,decidido_en,criterio_aprobacion,autoridad_id "
        "FROM biblioteca_revisiones_documento WHERE id=:id AND tenant_id=:t"
    ), {"id": revision_id, "t": tenant_id})).mappings().first()
    if fila is None:
        raise ErrorNegocio("BIB_REVISION_NO_ENCONTRADA")
    return RevisionDocumental(**fila)


async def devolver_revision(session: AsyncSession, tenant_id: str, actor: str, revision_id: str,
                            entrada: DictamenRevision) -> RevisionDocumental:
    await contexto(session, tenant_id, actor)
    revision = await obtener_revision(session, tenant_id, revision_id)
    if revision.estado != "asignada" or revision.revisor_id != actor:
        raise ErrorNegocio("BIB_REVISION_NO_AUTORIZADA")
    await session.execute(text(
        "UPDATE biblioteca_revisiones_documento SET estado='devuelta',observaciones=:o,decidido_por=:u,decidido_en=now() "
        "WHERE id=:id AND tenant_id=:t"
    ), {"o": entrada.motivo, "u": actor, "id": revision_id, "t": tenant_id})
    devueltos = (await session.execute(text(
        "SELECT biblioteca_devolver_documento(:d,:t,:r,:h)"
    ), {"d": revision.documento_id, "t": tenant_id, "r": revision.revision, "h": revision.sha256})).scalar()
    if devueltos != 1:
        raise ErrorNegocio("BIB_REVISION_DOCUMENTAL_DESFASADA")
    return await obtener_revision(session, tenant_id, revision_id)


async def aprobar_revision(session: AsyncSession, tenant_id: str, actor: str, revision_id: str,
                           entrada: AprobarRevision) -> RevisionDocumental:
    await contexto(session, tenant_id, actor)
    revision = await obtener_revision(session, tenant_id, revision_id)
    if revision.estado != "asignada" or revision.revisor_id != actor or revision.tipo_participacion != "revision":
        raise ErrorNegocio("BIB_REVISION_NO_AUTORIZADA")
    autor = (await session.execute(text(
        "SELECT creado_por FROM biblioteca_documentos WHERE id=:d AND tenant_id=:t AND estado='en_revision' "
        "AND revision=:r AND sha256=:h FOR UPDATE"
    ), {"d": revision.documento_id, "t": tenant_id, "r": revision.revision, "h": revision.sha256})).scalar()
    if autor is None:
        raise ErrorNegocio("BIB_REVISION_DOCUMENTAL_DESFASADA")
    if autor == actor or revision.asignado_por == actor:
        raise ErrorNegocio("BIB_SEPARACION_FUNCIONES")
    autoridad = (await session.execute(text(
        "SELECT id FROM biblioteca_autoridades_aprobacion WHERE tenant_id=:t AND usuario_id=:u "
        "AND revocada_en IS NULL AND vigente_desde<=now() AND (vigente_hasta IS NULL OR vigente_hasta>now()) "
        "ORDER BY vigente_desde DESC LIMIT 1"
    ), {"t": tenant_id, "u": actor})).scalar()
    if autoridad is None:
        raise ErrorNegocio("BIB_AUTORIDAD_NO_VIGENTE")
    await session.execute(text(
        "UPDATE biblioteca_revisiones_documento SET estado='aprobada',decidido_por=:u,decidido_en=now(),"
        "criterio_aprobacion=:c,autoridad_id=:a WHERE id=:id AND tenant_id=:t"
    ), {"u": actor, "c": entrada.criterio, "a": autoridad, "id": revision_id, "t": tenant_id})
    filas = (await session.execute(text(
        "SELECT biblioteca_aprobar_documento(:d,:t,:u,:r,:h)"
    ), {"u": actor, "d": revision.documento_id, "t": tenant_id, "r": revision.revision, "h": revision.sha256})).scalar()
    if filas != 1:
        raise ErrorNegocio("BIB_REVISION_DOCUMENTAL_DESFASADA")
    return await obtener_revision(session, tenant_id, revision_id)


async def abrir_nueva_revision(session: AsyncSession, tenant_id: str, actor: str, documento_id: str) -> int:
    """Un aprobado no se sobrescribe: abre otro borrador y conserva su dictamen/hash en revisiones."""
    await contexto(session, tenant_id, actor)
    nueva = (await session.execute(text(
        "SELECT biblioteca_reabrir_documento(:id,:t)"
    ), {"id": documento_id, "t": tenant_id})).scalar()
    if nueva is None:
        raise ErrorNegocio("BIB_DOCUMENTO_NO_REVISABLE")
    return nueva

