# ¤adpa ¤rbac-tenant
# ¤¤developer-architect
"""Documentos externos del cliente (BIB-106): reserva, archivo, análisis, finalización y descarga.

La organización y el usuario salen de la sesión verificada. La reserva es de quien la pidió: otro usuario
o tenant recibe 404. El archivo no se interpreta; se conserva tal cual con su huella calculada en el
servidor. Solo una carga con análisis `limpio` se finaliza (como Borrador) o se descarga.
"""
import hashlib
from datetime import date, datetime, timedelta, timezone
from typing import Literal
from uuid import uuid4
from pydantic import Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app_core.errors import ErrorNegocio
from features.biblioteca.domain.documentos import Contrato, Documento, MESES_REVISION, huella, sumar_meses
from features.biblioteca.services import analisis_archivos as analisis
from features.biblioteca.services.archivos import limpiar_nombre, tipo_mime
from features.biblioteca.services.documentos_consulta import contexto, obtener_documento

MINUTOS_RESERVA = 15
EstadoAnalisis = Literal["sin_archivo", "pendiente", "limpio", "infectado", "error", "rechazado"]


# ¤adpa
class ReservarCarga(Contrato):
    titulo: str = Field(min_length=1, max_length=200)
    codigo: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,39}$")
    version_propia: str = Field(min_length=1, max_length=40)
    formato: Literal["DOCX", "XLSX"]
    nombre_archivo: str = Field(min_length=1, max_length=160)
    tamano_bytes: int = Field(ge=1, le=analisis.TAMANO_MAXIMO)
    version_maestra_id: str | None = Field(default=None, min_length=1, max_length=36)
    documento_id: str | None = Field(default=None, min_length=1, max_length=36)


# ¤adpa
class VersionMaestra(Contrato):
    id: str
    codigo: str
    version: str


# ¤adpa
class Carga(Contrato):
    id: str
    titulo: str
    codigo: str
    version_propia: str
    version_maestra: VersionMaestra | None
    formato: Literal["DOCX", "XLSX"]
    nombre_archivo: str
    tamano_bytes: int | None
    sha256: str | None
    estado_analisis: EstadoAnalisis
    descargable: bool
    documento_id: str | None
    revision_externa: int | None
    finalizada: bool
    creado_en: datetime
    expira_en: datetime




# ¤adpa
def _carga(fila) -> Carga:
    maestra = (VersionMaestra(id=fila["version_maestra_id"], codigo=fila["maestra_codigo"], version=fila["maestra_version"])
               if fila["version_maestra_id"] else None)
    return Carga(
        id=fila["id"], titulo=fila["titulo"], codigo=fila["codigo"], version_propia=fila["version_propia"],
        version_maestra=maestra, formato=fila["formato"], nombre_archivo=fila["nombre_archivo"],
        tamano_bytes=fila["tamano_bytes"], sha256=fila["sha256"], estado_analisis=fila["estado_analisis"],
        descargable=fila["estado_analisis"] == "limpio", documento_id=fila["documento_id"],
        revision_externa=fila["revision_externa"], finalizada=fila["finalizada_en"] is not None,
        creado_en=fila["creado_en"], expira_en=fila["expira_en"])


# ¤adpa
async def _fila(session: AsyncSession, tenant_id: str, actor: str, carga_id: str, *, propia: bool):
    """Propia: solo quien reservó. Si no, también las finalizadas de la organización. Lo demás es 404."""
    fila = (await session.execute(text(
        "SELECT c.id, c.titulo, c.codigo, c.version_propia, c.version_maestra_id, v.codigo AS maestra_codigo, "
        "v.version AS maestra_version, c.formato, c.nombre_archivo, c.tamano_bytes, c.sha256, c.estado_analisis, "
        "c.documento_id, c.revision_externa, c.finalizada_en, c.creado_en, c.expira_en, c.usuario_id "
        "FROM biblioteca_cargas c LEFT JOIN biblioteca_versiones v ON v.id = c.version_maestra_id "
        "WHERE c.id=:id AND c.tenant_id=:t AND (c.usuario_id=:u "
        "OR (CAST(:todas AS boolean) AND c.finalizada_en IS NOT NULL))"
    ), {"id": carga_id, "t": tenant_id, "u": actor, "todas": not propia})).mappings().first()
    if fila is None:
        raise ErrorNegocio("BIB_CARGA_NO_ENCONTRADA")
    return fila


# ¤adpa
async def reservar_carga(session: AsyncSession, tenant_id: str, actor: str, entrada: ReservarCarga) -> Carga:
    await contexto(session, tenant_id, actor)
    analisis.exigir_extension(entrada.nombre_archivo, entrada.formato)
    if entrada.version_maestra_id and (await session.execute(text(
            "SELECT 1 FROM biblioteca_versiones WHERE id=:id AND estado='publicada'"),
            {"id": entrada.version_maestra_id})).first() is None:
        raise ErrorNegocio("BIB_CARGA_VERSION_MAESTRA_INVALIDA")
    if entrada.documento_id:
        origen = (await session.execute(text(
            "SELECT origen FROM biblioteca_documentos WHERE id=:id AND tenant_id=:t"),
            {"id": entrada.documento_id, "t": tenant_id})).scalar()
        if origen is None:
            raise ErrorNegocio("BIB_DOCUMENTO_NO_ENCONTRADO")
        if origen != "subido":
            raise ErrorNegocio("BIB_CARGA_DOCUMENTO_NO_SUBIDO")
    carga_id = str(uuid4())
    await session.execute(text(
        "INSERT INTO biblioteca_cargas(id, tenant_id, usuario_id, titulo, codigo, version_propia, version_maestra_id, "
        "formato, nombre_archivo, tamano_declarado, documento_id, expira_en) VALUES (:id, :t, :u, :titulo, :codigo, "
        ":vp, :vm, :f, :n, :tam, :doc, :exp)"
    ), {"id": carga_id, "t": tenant_id, "u": actor, "titulo": entrada.titulo, "codigo": entrada.codigo,
        "vp": entrada.version_propia, "vm": entrada.version_maestra_id, "f": entrada.formato,
        "n": limpiar_nombre(entrada.nombre_archivo), "tam": entrada.tamano_bytes, "doc": entrada.documento_id,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=MINUTOS_RESERVA)})
    return _carga(await _fila(session, tenant_id, actor, carga_id, propia=True))


# ¤adpa
async def subir_archivo(session: AsyncSession, tenant_id: str, actor: str, carga_id: str, contenido: bytes) -> Carga:
    """Verifica el objeto real (tamaño, formato, ZIP, macros, enlaces) y lo analiza; nunca reemplaza un archivo."""
    await contexto(session, tenant_id, actor)
    fila = await _fila(session, tenant_id, actor, carga_id, propia=True)
    if fila["estado_analisis"] != "sin_archivo":
        raise ErrorNegocio("BIB_CARGA_ESTADO_INVALIDO")
    if fila["expira_en"] < datetime.now(timezone.utc):
        raise ErrorNegocio("BIB_CARGA_RESERVA_CADUCADA")
    reserva = (await session.execute(text("SELECT tamano_declarado FROM biblioteca_cargas WHERE id=:id"),
                                     {"id": carga_id})).scalar()
    if len(contenido) != reserva:
        raise ErrorNegocio("BIB_CARGA_TAMANO_INVALIDO")
    analisis.inspeccionar(contenido, fila["formato"])
    estado = analisis.analizar(contenido, fila["nombre_archivo"])
    await session.execute(text(
        "UPDATE biblioteca_cargas SET archivo=:a, sha256=:h, tamano_bytes=:n, estado_analisis=:e "
        "WHERE id=:id AND tenant_id=:t AND estado_analisis='sin_archivo'"
    ), {"a": contenido, "h": hashlib.sha256(contenido).hexdigest(), "n": len(contenido), "e": estado, "id": carga_id, "t": tenant_id})
    return _carga(await _fila(session, tenant_id, actor, carga_id, propia=True))


# ¤adpa
def _procedencia(fila, revision: int) -> str:
    """Ficha de procedencia en texto; el contenido del archivo no se interpreta."""
    maestra = (f"{fila['maestra_codigo']} v{fila['maestra_version']}" if fila["version_maestra_id"]
               else "Origen no vinculado")
    return (f"# {fila['titulo']}\n\nDocumento externo de la organización.\n\n"
            f"- Código: {fila['codigo']}\n- Versión propia: {fila['version_propia']}\n- Versión maestra: {maestra}\n"
            f"- Archivo: {fila['nombre_archivo']} ({fila['tamano_bytes']} bytes)\n- SHA-256: {fila['sha256']}\n"
            f"- Revisión externa: {revision}\n")


# ¤adpa
async def finalizar_carga(session: AsyncSession, tenant_id: str, actor: str, carga_id: str) -> Documento:
    """Solo un archivo limpio entra como Borrador; una revisión nueva se añade sin sobrescribir la anterior."""
    await contexto(session, tenant_id, actor)
    fila = await _fila(session, tenant_id, actor, carga_id, propia=True)
    if fila["finalizada_en"] is not None or fila["estado_analisis"] != "limpio":
        raise ErrorNegocio("BIB_CARGA_ESTADO_INVALIDO")
    documento_id = fila["documento_id"]
    if documento_id is None:
        documento_id, revision = str(uuid4()), 1
        contenido = _procedencia(fila, revision)
        hoy = date.today()
        await session.execute(text(
            "INSERT INTO biblioteca_documentos(id, tenant_id, codigo, nombre, origen, contenido_markdown, sha256, "
            "fecha_emision, proxima_revision, creado_por) VALUES (:id, :t, :codigo, :nombre, 'subido', :c, :h, :hoy, "
            ":proxima, :u)"
        ), {"id": documento_id, "t": tenant_id, "codigo": fila["codigo"], "nombre": fila["titulo"], "c": contenido,
            "h": huella(contenido), "hoy": hoy, "proxima": sumar_meses(hoy, MESES_REVISION), "u": actor})
        version_doc, accion = 1, "creado"
    else:
        revision = 1 + ((await session.execute(text(
            "SELECT max(revision_externa) FROM biblioteca_cargas WHERE documento_id=:d AND tenant_id=:t "
            "AND finalizada_en IS NOT NULL"), {"d": documento_id, "t": tenant_id})).scalar() or 0)
        contenido = _procedencia(fila, revision)
        version_doc = (await session.execute(text(
            "UPDATE biblioteca_documentos SET contenido_markdown=:c, sha256=:h, editado=true, revision=revision+1, "
            "actualizado_en=now() WHERE id=:id AND tenant_id=:t AND estado='borrador' RETURNING revision"
        ), {"c": contenido, "h": huella(contenido), "id": documento_id, "t": tenant_id})).scalar()
        if version_doc is None:
            raise ErrorNegocio("BIB_DOCUMENTO_NO_EDITABLE")
        accion = "editado"
    await session.execute(text(
        "INSERT INTO biblioteca_documentos_historial(id, tenant_id, documento_id, revision, accion, "
        "contenido_markdown, sha256, actor_id) VALUES (:id, :t, :d, :r, :a, :c, :h, :u)"
    ), {"id": str(uuid4()), "t": tenant_id, "d": documento_id, "r": version_doc, "a": accion, "c": contenido,
        "h": huella(contenido), "u": actor})
    await session.execute(text(
        "UPDATE biblioteca_cargas SET documento_id=:d, revision_externa=:r, finalizada_en=now() "
        "WHERE id=:id AND tenant_id=:t AND estado_analisis='limpio' AND finalizada_en IS NULL"
    ), {"d": documento_id, "r": revision, "id": carga_id, "t": tenant_id})
    return await obtener_documento(session, tenant_id, actor, documento_id)


# ¤adpa
async def obtener_carga(session: AsyncSession, tenant_id: str, actor: str, carga_id: str) -> Carga:
    await contexto(session, tenant_id, actor)
    return _carga(await _fila(session, tenant_id, actor, carga_id, propia=False))


# ¤adpa
async def listar_cargas(session: AsyncSession, tenant_id: str, actor: str, documento_id: str) -> list[Carga]:
    """Revisiones finalizadas de un documento externo, de la más antigua a la más reciente."""
    await contexto(session, tenant_id, actor)
    filas = (await session.execute(text(
        "SELECT c.id, c.titulo, c.codigo, c.version_propia, c.version_maestra_id, v.codigo AS maestra_codigo, "
        "v.version AS maestra_version, c.formato, c.nombre_archivo, c.tamano_bytes, c.sha256, c.estado_analisis, "
        "c.documento_id, c.revision_externa, c.finalizada_en, c.creado_en, c.expira_en, c.usuario_id "
        "FROM biblioteca_cargas c LEFT JOIN biblioteca_versiones v ON v.id = c.version_maestra_id "
        "WHERE c.tenant_id=:t AND c.documento_id=:d AND c.finalizada_en IS NOT NULL "
        "ORDER BY c.revision_externa"), {"t": tenant_id, "d": documento_id})).mappings().all()
    return [_carga(f) for f in filas]


# ¤adpa
async def descargar_carga(session: AsyncSession, tenant_id: str, actor: str, carga_id: str) -> tuple[bytes, str, str]:
    """Cuarentena: pendiente, error, infectado o rechazado nunca se entregan."""
    await contexto(session, tenant_id, actor)
    fila = await _fila(session, tenant_id, actor, carga_id, propia=False)
    if fila["estado_analisis"] != "limpio":
        raise ErrorNegocio("BIB_CARGA_EN_CUARENTENA")
    archivo = (await session.execute(text(
        "SELECT archivo FROM biblioteca_cargas WHERE id=:id AND tenant_id=:t"),
        {"id": carga_id, "t": tenant_id})).scalar()
    return bytes(archivo), fila["nombre_archivo"], tipo_mime(fila["formato"])
