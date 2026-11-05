# ¤adpa ¤rbac-tenant
# ¤¤developer-architect
"""Reutilización con procedencia (BIB-202): leer fuentes canónicas, emitir instantáneas y avisar cambios.

Biblioteca no importa otras salas: Organización, DPD, RAT y Diagnóstico llegan por `PuertoFuentes`,
que arma el router con sus compuertas. El puerto solo lee; aquí no existe ninguna vía para escribir en
una fuente. La instantánea emitida se guarda como evento append-only del documento (BIB-306) y nunca se
reescribe: si la fuente cambia, se avisa comparando con ella. Una corrección del consultor queda como
propuesta registrada, no como cambio del dato canónico.
"""
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app_core.errors import ErrorNegocio
from features.biblioteca.domain.procedencia import (
    MARCA_INSTANTANEA, MARCA_PROPUESTA, AvisoCambios, EntradaPropuesta, Instantanea, OrigenCampo,
    PropuestaCorreccion, RegistroFuente, comparar, instantanea, origenes,
)
from features.biblioteca.services.documentos_consulta import contexto, obtener_documento
from features.biblioteca.services.historial import RegistrarEvento, registrar_evento
import features.biblioteca.domain.errores  # noqa: F401  registra los códigos de Biblioteca al importarse

LEER_EMITIDA = ("SELECT detalle, revision, creado_en FROM biblioteca_eventos_documento WHERE documento_id=:d "
                "AND tenant_id=:t "
                "AND tipo='generacion' AND detalle->>'marca'=:m ORDER BY creado_en DESC, id DESC LIMIT 1")


# ¤adpa
@dataclass(frozen=True)
class PuertoFuentes:
    """Lectura de las fuentes canónicas ya autorizadas por su compuerta, con el tenant de la sesión."""
    registros: Callable[[AsyncSession, str], Awaitable[list[RegistroFuente]]]


# ¤adpa
async def procedencia_actual(session: AsyncSession, puerto: PuertoFuentes, tenant_id: str,
                             actor: str) -> Instantanea:
    """Valores reutilizables hoy, cada uno con su origen; sin documento asociado."""
    await contexto(session, tenant_id, actor)
    return instantanea(origenes(await puerto.registros(session, tenant_id)),
                       tomada_en=datetime.now(timezone.utc))


# ¤adpa
async def emitir_instantanea(session: AsyncSession, puerto: PuertoFuentes, tenant_id: str, actor: str,
                             documento_id: str) -> Instantanea:
    """Congela la procedencia de la revisión actual del documento en un evento inmutable."""
    await contexto(session, tenant_id, actor)
    documento = await obtener_documento(session, tenant_id, actor, documento_id)
    campos = origenes(await puerto.registros(session, tenant_id))
    foto = instantanea(campos, documento_id, documento.revision)
    evento = await registrar_evento(session, tenant_id, actor, documento_id, RegistrarEvento(
        tipo="generacion", revision=documento.revision,
        detalle={"marca": MARCA_INSTANTANEA, "sha256": foto.sha256,
                 "campos": [c.model_dump() for c in campos]}))
    return foto.model_copy(update={"tomada_en": evento.creado_en})


# ¤adpa
async def instantanea_emitida(session: AsyncSession, tenant_id: str, actor: str, documento_id: str) -> Instantanea:
    """La última instantánea emitida tal como se guardó (la RLS oculta las de otra organización)."""
    await contexto(session, tenant_id, actor)
    documento = await obtener_documento(session, tenant_id, actor, documento_id)
    fila = (await session.execute(text(LEER_EMITIDA), {"d": documento.id, "t": tenant_id, "m": MARCA_INSTANTANEA})).mappings().first()
    if fila is None:
        raise ErrorNegocio("BIB_PROCEDENCIA_SIN_INSTANTANEA")
    detalle = fila["detalle"]
    campos = [OrigenCampo(**c) for c in detalle["campos"]]
    return Instantanea(documento_id=documento.id, revision_documento=fila["revision"], campos=campos,
                       sha256=detalle["sha256"], tomada_en=fila["creado_en"])


# ¤adpa
async def cambios_de_fuente(session: AsyncSession, puerto: PuertoFuentes, tenant_id: str, actor: str,
                            documento_id: str) -> AvisoCambios:
    """Compara la instantánea emitida con la fuente de hoy; avisa sin reescribir lo emitido."""
    emitida = await instantanea_emitida(session, tenant_id, actor, documento_id)
    actuales = origenes(await puerto.registros(session, tenant_id))
    cambios = comparar(emitida, actuales)
    actual = instantanea(actuales, documento_id, tomada_en=datetime.now(timezone.utc))
    return AvisoCambios(documento_id=documento_id, cambiado=bool(cambios), cambios=cambios,
                        emitida=emitida, actual=actual)


# ¤adpa
async def proponer_correccion(session: AsyncSession, puerto: PuertoFuentes, tenant_id: str, actor: str,
                              documento_id: str, entrada: EntradaPropuesta) -> PropuestaCorreccion:
    """Registra la corrección propuesta junto al documento; el dato canónico sigue igual."""
    await contexto(session, tenant_id, actor)
    documento = await obtener_documento(session, tenant_id, actor, documento_id)
    actual = {c.clave: c for c in origenes(await puerto.registros(session, tenant_id))}
    canonico = actual.get(entrada.clave)
    if canonico is None:
        raise ErrorNegocio("BIB_PROCEDENCIA_CAMPO_DESCONOCIDO")
    propuesta = PropuestaCorreccion(
        documento_id=documento.id, clave=entrada.clave, valor_canonico=canonico.valor,
        valor_propuesto=entrada.valor_propuesto, motivo=entrada.motivo,
        fuente=canonico.fuente, fuente_id=canonico.fuente_id)
    await registrar_evento(session, tenant_id, actor, documento_id, RegistrarEvento(
        tipo="notificacion", revision=documento.revision,
        detalle={"marca": MARCA_PROPUESTA, **propuesta.model_dump()}))
    return propuesta
