# ¤adpa ¤rbac-tenant
# ¤¤developer-architect
"""Lectura de los documentos de la organización. El tenant sale de la sesión y se filtra siempre,
además de la RLS forzada: un id de otra organización es un 404, nunca un 403 que confirme su existencia."""
from datetime import date, datetime, timedelta
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app_core.errors import ErrorNegocio
from app_core.zona_negocio import ZONA_NEGOCIO_NOMBRE, hoy_negocio
from features.biblioteca.domain.documentos import (
    DIAS_POR_VENCER, Documento, DocumentoResumen, EventoHistorial, Pendientes, faltantes_de,
)

# ¤adpa
async def contexto(session: AsyncSession, tenant_id: str, actor: str) -> None:
    """Fija la organización y el usuario ya verificados en la transacción, para la RLS."""
    from app_core.db.session import fijar_contexto_rls  # tarde: importar la compuerta no exige DATABASE_URL
    await fijar_contexto_rls(session, tenant_id, actor)


# ¤adpa
async def obtener_documento(
    session: AsyncSession, tenant_id: str, actor: str, documento_id: str, *, ahora: datetime | None = None,
) -> Documento:
    """`ahora` inyecta el reloj (BIB-120); «vencido» se decide con el día de negocio en Guayaquil."""
    await contexto(session, tenant_id, actor)
    fila = (await session.execute(
        text("SELECT id, codigo, nombre, origen, plantilla_version, "
             "CASE WHEN estado='aprobado' AND proxima_revision < :hoy THEN 'vencido' ELSE estado END AS estado, "
             "editado, proxima_revision, revision, creado_por, creado_en, actualizado_en, plantilla_id, "
             "contenido_markdown, aprobado_por, aprobado_en, sha256, fecha_emision, tarea_hoja_ruta_id "
             "FROM biblioteca_documentos WHERE id=:id AND tenant_id=:t"),
        {"id": documento_id, "t": tenant_id, "hoy": hoy_negocio(ahora)},
    )).mappings().first()
    if fila is None:
        raise ErrorNegocio("BIB_DOCUMENTO_NO_ENCONTRADO")
    return Documento(**fila, variables_faltantes=faltantes_de(fila["contenido_markdown"]))


# ¤adpa
async def listar_documentos(
    session: AsyncSession, tenant_id: str, actor: str, *, estado: str | None = None, origen: str | None = None,
    codigo: str | None = None, autor: str | None = None, desde: date | None = None, hasta: date | None = None,
    ahora: datetime | None = None,
) -> list[DocumentoResumen]:
    """`desde`/`hasta` y «vencido» se comparan en el día de negocio de Guayaquil, no en la zona de la sesión."""
    await contexto(session, tenant_id, actor)
    filas = (await session.execute(text(
        "SELECT id, codigo, nombre, origen, plantilla_version, "
        "CASE WHEN estado='aprobado' AND proxima_revision < :hoy THEN 'vencido' ELSE estado END AS estado, "
        "editado, proxima_revision, revision, creado_por, creado_en, actualizado_en FROM biblioteca_documentos "
        "WHERE tenant_id=:t "
        "AND (CAST(:estado AS text) IS NULL OR CASE WHEN estado='aprobado' AND proxima_revision < :hoy "
        "THEN 'vencido' ELSE estado END = :estado) "
        "AND (CAST(:origen AS text) IS NULL OR origen=:origen) "
        "AND (CAST(:codigo AS text) IS NULL OR codigo=:codigo) "
        "AND (CAST(:autor AS text) IS NULL OR creado_por=:autor) "
        "AND (CAST(:desde AS date) IS NULL OR (creado_en AT TIME ZONE :zona)::date >= :desde) "
        "AND (CAST(:hasta AS date) IS NULL OR (creado_en AT TIME ZONE :zona)::date <= :hasta) "
        "ORDER BY actualizado_en DESC, id LIMIT 500"
    ), {"t": tenant_id, "hoy": hoy_negocio(ahora), "zona": ZONA_NEGOCIO_NOMBRE, "estado": estado, "origen": origen,
        "codigo": codigo, "autor": autor, "desde": desde, "hasta": hasta})).mappings().all()
    return [DocumentoResumen(**f) for f in filas]


# ¤adpa
async def pendientes(session: AsyncSession, tenant_id: str, actor: str, *, ahora: datetime | None = None) -> Pendientes:
    """Contador del botón: lo que necesita atención. `total` suma las cuatro cifras, sin doble conteo."""
    await contexto(session, tenant_id, actor)
    hoy = hoy_negocio(ahora)
    fila = (await session.execute(text(
        "SELECT count(*) FILTER (WHERE estado='borrador') AS borrador, "
        "count(*) FILTER (WHERE estado='en_revision') AS en_revision, "
        "count(*) FILTER (WHERE estado='aprobado' AND proxima_revision >= :hoy AND proxima_revision <= :limite) "
        "AS por_vencer, "
        "count(*) FILTER (WHERE estado='aprobado' AND proxima_revision < :hoy) AS vencidos "
        "FROM biblioteca_documentos WHERE tenant_id=:t"
    ), {"t": tenant_id, "hoy": hoy, "limite": hoy + timedelta(days=DIAS_POR_VENCER)})).mappings().one()
    return Pendientes(**fila, total=sum(fila.values()))


# ¤adpa
async def historial_documento(session: AsyncSession, tenant_id: str, actor: str, documento_id: str) -> list[EventoHistorial]:
    await obtener_documento(session, tenant_id, actor, documento_id)  # 404 si no es de esta organización
    filas = (await session.execute(text(
        "SELECT revision, accion, sha256, actor_id, creado_en FROM biblioteca_documentos_historial "
        "WHERE documento_id=:id AND tenant_id=:t ORDER BY revision"
    ), {"id": documento_id, "t": tenant_id})).mappings().all()
    return [EventoHistorial(**f) for f in filas]
