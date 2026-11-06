# ¤adpa ¤rbac-tenant
# ¤¤developer-architect
"""Alta y edición de los documentos de la organización (BIB-107).

El estado, la aprobación y las transiciones son de BIB-301; las altas de documento propio y subido,
de BIB-106. Aquí solo se crea desde una plantilla publicada y se edita el borrador.
"""
import inspect
from datetime import date
from uuid import uuid4
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession
from app_core.errors import ErrorNegocio
from features.biblioteca.domain.documentos import (
    CambiarDocumento, CrearDocumento, Documento, PuertoRellenado, RellenadoLiteral, huella, meses_de_revision,
    sumar_meses,
)
from features.biblioteca.services.documentos_consulta import contexto, obtener_documento

_rellenador: PuertoRellenado = RellenadoLiteral()


# ¤adpa
def registrar_rellenador(rellenador: PuertoRellenado) -> None:
    """BIB-201 registra aquí su implementación; sin ella, todas las variables quedan como faltantes."""
    global _rellenador
    _rellenador = rellenador


# ¤adpa
async def _plantilla_publicada(session: AsyncSession, plantilla_id: str) -> dict:
    fila = (await session.execute(text(
        "SELECT v.id, v.codigo, v.version, v.cuerpo_md, c.nombre, c.metadatos FROM biblioteca_versiones v "
        "LEFT JOIN biblioteca_catalogo c ON c.codigo=v.codigo "
        "WHERE v.id=:id AND v.estado='publicada' AND v.formato='MD'"
    ), {"id": plantilla_id})).mappings().first()
    if fila is None:
        raise ErrorNegocio("BIB_PLANTILLA_NO_DISPONIBLE")
    return dict(fila)


# ¤adpa
async def _historial(session: AsyncSession, tenant_id: str, documento_id: str, revision: int, accion: str,
                     contenido: str, actor: str) -> None:
    await session.execute(text(
        "INSERT INTO biblioteca_documentos_historial(id, tenant_id, documento_id, revision, accion, "
        "contenido_markdown, sha256, actor_id) VALUES (:id, :t, :d, :r, :a, :c, :h, :u)"
    ), {"id": str(uuid4()), "t": tenant_id, "d": documento_id, "r": revision, "a": accion, "c": contenido,
        "h": huella(contenido), "u": actor})


# ¤adpa
async def crear_documento(session: AsyncSession, tenant_id: str, actor: str, entrada: CrearDocumento) -> Documento:
    """Borrador de la organización desde una plantilla publicada, con el rellenado registrado."""
    await contexto(session, tenant_id, actor)
    plantilla = await _plantilla_publicada(session, entrada.plantilla_id)
    resultado = _rellenador.rellenar(plantilla, {"tenant_id": tenant_id}, entrada.contexto)
    contenido, _ = await resultado if inspect.isawaitable(resultado) else resultado
    emision = entrada.fecha_emision or date.today()
    documento_id = str(uuid4())
    try:
        async with session.begin_nested():
            await session.execute(text(
                "INSERT INTO biblioteca_documentos(id, tenant_id, codigo, nombre, origen, plantilla_id, "
                "plantilla_version, contenido_markdown, sha256, fecha_emision, proxima_revision, "
                "tarea_hoja_ruta_id, creado_por) VALUES (:id, :t, :codigo, :nombre, 'plantilla', :pid, :ver, "
                ":c, :h, :emision, :proxima, :tarea, :u)"
            ), {"id": documento_id, "t": tenant_id, "codigo": plantilla["codigo"],
                "nombre": plantilla["nombre"] or plantilla["codigo"], "pid": plantilla["id"],
                "ver": plantilla["version"], "c": contenido, "h": huella(contenido), "emision": emision,
                "proxima": sumar_meses(emision, meses_de_revision(plantilla["metadatos"])),
                "tarea": entrada.tarea_hoja_ruta_id, "u": actor})
            await _historial(session, tenant_id, documento_id, 1, "creado", contenido, actor)
    except DBAPIError as error:
        if "BIB_TAREA_AJENA" in str(error.orig):
            raise ErrorNegocio("BIB_TAREA_AJENA") from None
        raise
    return await obtener_documento(session, tenant_id, actor, documento_id)


# ¤adpa
async def cambiar_documento(session: AsyncSession, tenant_id: str, actor: str, documento_id: str,
                            cambio: CambiarDocumento) -> Documento:
    """Edita el borrador si `revision` es la vigente; una revisión desfasada es un 409, no una pérdida silenciosa."""
    await contexto(session, tenant_id, actor)
    actualizado = (await session.execute(text(
        "UPDATE biblioteca_documentos SET contenido_markdown=:c, sha256=:h, editado=true, revision=revision+1, "
        "actualizado_en=now() WHERE id=:id AND tenant_id=:t AND revision=:r AND estado='borrador' RETURNING revision"
    ), {"c": cambio.contenido_markdown, "h": huella(cambio.contenido_markdown), "id": documento_id,
        "t": tenant_id, "r": cambio.revision})).scalar()
    if actualizado is None:
        actual = (await session.execute(text(
            "SELECT estado FROM biblioteca_documentos WHERE id=:id AND tenant_id=:t"
        ), {"id": documento_id, "t": tenant_id})).scalar()
        if actual is None:
            raise ErrorNegocio("BIB_DOCUMENTO_NO_ENCONTRADO")
        raise ErrorNegocio("BIB_DOCUMENTO_NO_EDITABLE" if actual != "borrador" else "BIB_DOCUMENTO_REVISION_DESFASADA")
    await _historial(session, tenant_id, documento_id, actualizado, "editado", cambio.contenido_markdown, actor)
    return await obtener_documento(session, tenant_id, actor, documento_id)
