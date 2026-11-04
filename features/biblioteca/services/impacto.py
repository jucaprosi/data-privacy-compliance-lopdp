# ¤adpa ¤rbac-tenant
# ¤¤developer-architect
"""Análisis de impacto de versiones publicadas y decisiones de cada organización."""
from collections.abc import Callable
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.errores import ErrorNegocio
from features.biblioteca.services.autorizacion import autorizar
from features.biblioteca.domain.editorial import Capacidad


async def crear_analisis(session: AsyncSession, actor: str, version_id: str) -> dict:
    await autorizar(session, actor, Capacidad.PUBLICADOR)
    version = (await session.execute(text(
        "SELECT id,codigo,version,sustituye_id,estado FROM biblioteca_versiones WHERE id=:id"
    ), {"id": version_id})).mappings().first()
    if not version:
        raise ErrorNegocio("BIB_IMPACTO_VERSION_NO_ENCONTRADA")
    if version["estado"] != "publicada" or not version["sustituye_id"]:
        raise ErrorNegocio("BIB_IMPACTO_VERSION_NO_PUBLICADA")
    analisis_id = str(uuid4())
    await session.execute(text(
        "INSERT INTO biblioteca_impactos(id,version_id,version_anterior_id,codigo,creado_por) "
        "VALUES (:id,:version,:anterior,:codigo,:actor) ON CONFLICT(version_id) DO NOTHING"
    ), {"id": analisis_id, "version": version_id, "anterior": version["sustituye_id"],
        "codigo": version["codigo"], "actor": actor})
    analisis_id = (await session.execute(text(
        "SELECT id FROM biblioteca_impactos WHERE version_id=:version"
    ), {"version": version_id})).scalar_one()
    await session.execute(text(
        "INSERT INTO biblioteca_impactos_organizacion(id,impacto_id,tenant_id) "
        "SELECT gen_random_uuid()::text,:impacto,d.tenant_id FROM biblioteca_documentos d "
        "WHERE d.plantilla_id=:anterior GROUP BY d.tenant_id ON CONFLICT(impacto_id,tenant_id) DO NOTHING"
    ), {"impacto": analisis_id, "anterior": version["sustituye_id"]})
    return await obtener_analisis(session, analisis_id)


async def obtener_analisis(session: AsyncSession, analisis_id: str) -> dict:
    fila = (await session.execute(text(
        "SELECT i.id,i.version_id,i.version_anterior_id,i.codigo,i.creado_en,"
        "count(DISTINCT o.tenant_id) organizaciones_afectadas,count(DISTINCT d.id) documentos_afectados "
        "FROM biblioteca_impactos i LEFT JOIN biblioteca_impactos_organizacion o ON o.impacto_id=i.id "
        "LEFT JOIN biblioteca_documentos d ON d.tenant_id=o.tenant_id AND d.plantilla_id=i.version_anterior_id "
        "WHERE i.id=:id GROUP BY i.id"
    ), {"id": analisis_id})).mappings().first()
    if not fila:
        raise ErrorNegocio("BIB_IMPACTO_NO_ENCONTRADO")
    return dict(fila)


async def listar_organizacion(session: AsyncSession, tenant_id: str) -> list[dict]:
    filas = (await session.execute(text(
        "SELECT o.id,o.impacto_id,i.codigo,v.version,o.decision,o.motivo,o.decidente_id,o.decidido_en,"
        "count(d.id) documentos_afectados FROM biblioteca_impactos_organizacion o "
        "JOIN biblioteca_impactos i ON i.id=o.impacto_id JOIN biblioteca_versiones v ON v.id=i.version_id "
        "LEFT JOIN biblioteca_documentos d ON d.tenant_id=o.tenant_id AND d.plantilla_id=i.version_anterior_id "
        "WHERE o.tenant_id=:tenant GROUP BY o.id,i.codigo,v.version ORDER BY o.creado_en DESC"
    ), {"tenant": tenant_id})).mappings().all()
    return [dict(f) for f in filas]


async def decidir(session: AsyncSession, tenant_id: str, actor: str, expediente_id: str,
                  decision: str, motivo: str) -> dict:
    if decision not in {"actualizar", "no_aplica", "pendiente"} or not motivo.strip():
        raise ErrorNegocio("BIB_IMPACTO_DECISION_INVALIDA")
    fila = (await session.execute(text(
        "UPDATE biblioteca_impactos_organizacion SET decision=:decision,motivo=:motivo,"
        "decidente_id=:actor,decidido_en=now() WHERE id=:id AND tenant_id=:tenant RETURNING *"
    ), {"decision": decision, "motivo": motivo.strip(), "actor": actor,
        "id": expediente_id, "tenant": tenant_id})).mappings().first()
    if not fila:
        raise ErrorNegocio("BIB_IMPACTO_NO_ENCONTRADO")
    # Deliberadamente no se actualiza biblioteca_documentos: un aprobado permanece inmutable.
    return dict(fila)


async def preparar_avisos(
    session: AsyncSession, actor: str, analisis_id: str, app_base_url: str,
    construir_aviso: Callable[[str, str, str], dict[str, str]],
) -> list[dict]:
    """`construir_aviso` es el puerto de avisos: lo inyecta el router (adaptador en app_core)."""
    await autorizar(session, actor, Capacidad.PUBLICADOR)
    afectados = (await session.execute(text(
        "SELECT o.id,o.tenant_id FROM biblioteca_impactos_organizacion o WHERE o.impacto_id=:id"
    ), {"id": analisis_id})).mappings().all()
    salidas = []
    for afectado in afectados:
        aviso = construir_aviso(afectado["id"], afectado["tenant_id"], app_base_url)
        intento_id = str(uuid4())
        await session.execute(text(
            "INSERT INTO biblioteca_impactos_avisos(id,expediente_id,estado,intentos,ultimo_error) "
            "VALUES (:id,:expediente,'pendiente',0,NULL)"
        ), {"id": intento_id, "expediente": afectado["id"]})
        salidas.append({"id": intento_id, "estado": "pendiente", **aviso})
    return salidas


async def registrar_intento(session: AsyncSession, tenant_id: str, aviso_id: str,
                            recibido: bool, error: str | None) -> dict:
    fila = (await session.execute(text(
        "UPDATE biblioteca_impactos_avisos a SET intentos=intentos+1,ultimo_intento_en=now(),"
        "estado=CASE WHEN :recibido THEN 'recibido' ELSE 'fallido' END,"
        "recibido_en=CASE WHEN :recibido THEN now() ELSE recibido_en END,ultimo_error=:error "
        "FROM biblioteca_impactos_organizacion o WHERE a.expediente_id=o.id AND a.id=:id "
        "AND o.tenant_id=:tenant RETURNING a.*"
    ), {"recibido": recibido, "error": None if recibido else (error or "sin confirmación")[:500],
        "id": aviso_id, "tenant": tenant_id})).mappings().first()
    if not fila:
        raise ErrorNegocio("BIB_IMPACTO_NO_ENCONTRADO")
    return dict(fila)
