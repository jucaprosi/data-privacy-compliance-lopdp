# ¤adpa
# ¤¤developer-architect
"""Persistencia editorial transaccional. La dependencia de sesión confirma o revierte."""
import json
from uuid import uuid4
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from api.errores import ErrorNegocio
from features.biblioteca.domain.editorial import (
    ArchivoMaestro, Capacidad, CrearVersion, Dictamen, EditarFicha, Transicion,
    exigir_publicable, exigir_separacion, exigir_sustitucion, validar_archivo,
)
from features.biblioteca.services.autorizacion import autorizar

COLUMNAS = "id, codigo, version, formato, ficha, responsable_id, autores, estado, generacion, nombre_archivo, sha256, sustituye_id, creada_en"


# ¤adpa
async def _version(session: AsyncSession, identificador: str, generacion: int | None = None) -> dict:
    fila = (await session.execute(text(
        f"SELECT {COLUMNAS} FROM biblioteca_versiones WHERE id=:id FOR UPDATE"
    ), {"id": identificador})).mappings().first()
    if not fila:
        raise ErrorNegocio("BIB_NO_ENCONTRADA")
    version = dict(fila)
    if generacion is not None and version["generacion"] != generacion:
        raise ErrorNegocio("BIB_CONFLICTO_VERSION")
    return version


# ¤adpa
async def _guardar(session: AsyncSession, sql: str, parametros: dict) -> None:
    try:
        async with session.begin_nested():
            await session.execute(text(sql), parametros)
    except IntegrityError:
        raise ErrorNegocio("BIB_CONFLICTO_VERSION") from None


# ¤adpa
async def _publicada_vigente(session: AsyncSession, codigo: str, excluir: str | None = None) -> str | None:
    return (await session.execute(text(
        "SELECT id FROM biblioteca_versiones WHERE codigo=:codigo AND estado='publicada' "
        "AND id IS DISTINCT FROM :excluir"
    ), {"codigo": codigo, "excluir": excluir})).scalar()


# ¤adpa
async def listar(session: AsyncSession, actor: str) -> dict:
    permisos = await autorizar(session, actor)
    versiones = (await session.execute(text(
        f"SELECT {COLUMNAS} FROM biblioteca_versiones ORDER BY creada_en DESC LIMIT 200"
    ))).mappings().all()
    revisiones = (await session.execute(text(
        "SELECT version_id, generacion, tipo, aprobado, revisor_id, comentario, creada_en "
        "FROM biblioteca_revisiones ORDER BY creada_en"
    ))).mappings().all()
    return {"actor_id": actor, "capacidades": permisos, "versiones": [dict(v) for v in versiones],
            "revisiones": [dict(r) for r in revisiones]}


# ¤adpa
async def crear(session: AsyncSession, actor: str, entrada: CrearVersion) -> dict:
    await autorizar(session, actor, Capacidad.EDITOR)
    # Serializa versiones/sustituciones del mismo código, incluso sin fila de catálogo.
    await session.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:codigo, 0))"), {"codigo": entrada.codigo})
    exigir_sustitucion(await _publicada_vigente(session, entrada.codigo), entrada.sustituye_id)
    if entrada.sustituye_id:
        anterior = await _version(session, entrada.sustituye_id)
        if anterior["codigo"] != entrada.codigo or anterior["estado"] != "publicada":
            raise ErrorNegocio("BIB_CONFLICTO_VERSION")
    identificador = str(uuid4())
    async with session.begin_nested():
        await session.execute(text(
            "INSERT INTO biblioteca_catalogo(codigo) VALUES (:codigo) ON CONFLICT DO NOTHING"
        ), {"codigo": entrada.codigo})
        await _guardar(session,
            "INSERT INTO biblioteca_versiones(id,codigo,version,formato,ficha,responsable_id,autores,sustituye_id) "
            "VALUES (:id,:codigo,:version,:formato,CAST(:ficha AS jsonb),:actor,CAST(:autores AS jsonb),:sustituye)",
            {"id": identificador, "codigo": entrada.codigo, "version": entrada.version, "formato": entrada.formato,
             "ficha": entrada.ficha.model_dump_json() if entrada.ficha else None,
             "actor": actor, "autores": json.dumps([actor]), "sustituye": entrada.sustituye_id})
    return await _version(session, identificador)


# ¤adpa
def _editable(version: dict) -> None:
    if version["estado"] != "en_revision":
        raise ErrorNegocio("BIB_VERSION_INMUTABLE")


# ¤adpa
async def editar(session: AsyncSession, actor: str, identificador: str, entrada: EditarFicha) -> dict:
    await autorizar(session, actor, Capacidad.EDITOR)
    version = await _version(session, identificador, entrada.generacion)
    _editable(version)
    await session.execute(text(
        "UPDATE biblioteca_versiones SET ficha=CAST(:ficha AS jsonb), generacion=generacion+1, "
        "autores=CAST(:autores AS jsonb) WHERE id=:id"
    ), {"id": identificador, "ficha": entrada.ficha.model_dump_json(),
        "autores": json.dumps(sorted(set(version["autores"] + [actor])))})
    return await _version(session, identificador)


# ¤adpa
async def cargar(session: AsyncSession, actor: str, identificador: str, entrada: ArchivoMaestro) -> dict:
    await autorizar(session, actor, Capacidad.EDITOR)
    version = await _version(session, identificador, entrada.generacion)
    _editable(version)
    datos, checksum = validar_archivo(entrada, version["formato"])
    await session.execute(text(
        "UPDATE biblioteca_versiones SET archivo=:archivo,nombre_archivo=:nombre,sha256=:sha, "
        "generacion=generacion+1,autores=CAST(:autores AS jsonb) WHERE id=:id"
    ), {"id": identificador, "archivo": datos, "nombre": entrada.nombre, "sha": checksum,
        "autores": json.dumps(sorted(set(version["autores"] + [actor])))})
    return await _version(session, identificador)


# ¤adpa
async def revisar(session: AsyncSession, actor: str, identificador: str, entrada: Dictamen) -> dict:
    capacidad = Capacidad.TECNICO if entrada.tipo == "tecnica" else Capacidad.JURIDICO
    await autorizar(session, actor, capacidad)
    version = await _version(session, identificador, entrada.generacion)
    _editable(version)
    exigir_separacion(actor, version["autores"])
    if not entrada.comentario.strip():
        raise ErrorNegocio("BIB_REVISION_PENDIENTE")
    await _guardar(session,
        "INSERT INTO biblioteca_revisiones(id,version_id,generacion,tipo,aprobado,revisor_id,comentario) "
        "VALUES (:id,:version_id,:generacion,:tipo,:aprobado,:actor,:comentario)",
        {"id": str(uuid4()), "version_id": identificador, "actor": actor, **entrada.model_dump()})
    return version


# ¤adpa
async def publicar(session: AsyncSession, actor: str, identificador: str, entrada: Transicion) -> dict:
    await autorizar(session, actor, Capacidad.PUBLICADOR)
    # Mismo orden de bloqueo que crear, evitando interbloqueos al sustituir.
    codigo = (await session.execute(text("SELECT codigo FROM biblioteca_versiones WHERE id=:id"), {"id": identificador})).scalar()
    if not codigo:
        raise ErrorNegocio("BIB_NO_ENCONTRADA")
    await session.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:codigo, 0))"), {"codigo": codigo})
    version = await _version(session, identificador, entrada.generacion)
    revisiones = (await session.execute(text(
        "SELECT tipo, aprobado, generacion, revisor_id FROM biblioteca_revisiones WHERE version_id=:id"
    ), {"id": identificador})).mappings().all()
    exigir_publicable(version, [dict(r) for r in revisiones], actor)
    exigir_sustitucion(await _publicada_vigente(session, codigo, identificador), version["sustituye_id"])
    if version["sustituye_id"]:
        anterior = await _version(session, version["sustituye_id"])
        if anterior["estado"] != "publicada":
            raise ErrorNegocio("BIB_CONFLICTO_VERSION")
        await session.execute(text(
            "UPDATE biblioteca_versiones SET estado='sustituida', motivo=:motivo WHERE id=:id"
        ), {"id": anterior["id"], "motivo": entrada.motivo})
    await session.execute(text(
        "UPDATE biblioteca_versiones SET estado='publicada', motivo=:motivo WHERE id=:id"
    ), {"id": identificador, "motivo": entrada.motivo})
    return await _version(session, identificador)


# ¤adpa
async def retirar(session: AsyncSession, actor: str, identificador: str, entrada: Transicion) -> dict:
    await autorizar(session, actor, Capacidad.PUBLICADOR)
    version = await _version(session, identificador, entrada.generacion)
    exigir_separacion(actor, version["autores"])
    if version["estado"] != "publicada":
        raise ErrorNegocio("BIB_VERSION_INMUTABLE")
    await session.execute(text(
        "UPDATE biblioteca_versiones SET estado='retirada',motivo=:motivo WHERE id=:id"
    ), {"id": identificador, "motivo": entrada.motivo})
    return await _version(session, identificador)


# ¤adpa
async def historial(session: AsyncSession, actor: str, identificador: str) -> list[dict]:
    await autorizar(session, actor)
    await _version(session, identificador)
    filas = (await session.execute(text(
        "SELECT actor_id, alcance, accion, generacion, motivo, creada_en FROM biblioteca_auditoria "
        "WHERE version_id=:id ORDER BY creada_en,id"
    ), {"id": identificador})).mappings().all()
    return [dict(f) for f in filas]


# === BIB-109 ===
# ¤adpa
async def crear_version_md(session: AsyncSession, actor: str, codigo: str, version: str,
                           cuerpo: str | None, sustituye_id: str | None = None) -> dict:
    """Crea una versión MD en revisión con los mismos controles que `crear`; nunca la publica."""
    import hashlib
    from features.biblioteca.domain.editorial import CrearVersionMd
    entrada = CrearVersionMd(codigo=codigo, version=version, cuerpo=cuerpo, sustituye_id=sustituye_id)
    await autorizar(session, actor, Capacidad.EDITOR)
    await session.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:codigo, 0))"), {"codigo": entrada.codigo})
    exigir_sustitucion(await _publicada_vigente(session, entrada.codigo), entrada.sustituye_id)
    if entrada.sustituye_id:
        anterior = await _version(session, entrada.sustituye_id)
        if anterior["codigo"] != entrada.codigo or anterior["estado"] != "publicada":
            raise ErrorNegocio("BIB_CONFLICTO_VERSION")
    identificador = str(uuid4())
    huella = hashlib.sha256(entrada.cuerpo.encode("utf-8")).hexdigest() if entrada.cuerpo else None
    async with session.begin_nested():
        await session.execute(text(
            "INSERT INTO biblioteca_catalogo(codigo) VALUES (:codigo) ON CONFLICT DO NOTHING"
        ), {"codigo": entrada.codigo})
        await _guardar(session,
            "INSERT INTO biblioteca_versiones(id,codigo,version,formato,responsable_id,autores,sustituye_id,cuerpo_md,sha256) "
            "VALUES (:id,:codigo,:version,'MD',:actor,CAST(:autores AS jsonb),:sustituye,:cuerpo,:sha)",
            {"id": identificador, "codigo": entrada.codigo, "version": entrada.version, "actor": actor,
             "autores": json.dumps([actor]), "sustituye": entrada.sustituye_id, "cuerpo": entrada.cuerpo,
             "sha": huella})
    return await _version(session, identificador)
# === fin BIB-109 ===
