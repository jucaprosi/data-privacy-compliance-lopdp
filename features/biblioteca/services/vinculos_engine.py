# ¤adpa ¤rbac-tenant ¤rat ¤hallazgos
# ¤¤developer-architect
"""Vínculos de un documento de la organización con tratamientos, controles y tareas (BIB-402).

Contrato: governance/especificaciones/BIB-402.md. Biblioteca no conoce a RAT ni a Hoja de Ruta:
este motor define sus puertos y el router (o el pasillo `app_core/pasillo/biblioteca.py`) inyecta
los adaptadores. Reglas: R1 aprobar adjunta evidencia a la tarea sin cerrarla; R2 cambiar o dar de
baja un tratamiento marca sus documentos «revisar» con un hallazgo `rat` por documento; R3 toda
referencia se valida antes de escribir.
"""
import re
from datetime import datetime
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.errores import ErrorNegocio
from app_core.audit import registrar_evento
from features.biblioteca.services.documentos_consulta import contexto

TipoVinculo = Literal["tratamiento", "control", "tarea"]
_CONTROL = re.compile(r"^P([1-9]|[1-7][0-9]|80)$")


class EntradaVinculos(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tratamientos: list[str] = Field(default_factory=list, max_length=200)
    controles: list[str] = Field(default_factory=list, max_length=80)
    tareas: list[str] = Field(default_factory=list, max_length=200)


class Vinculo(BaseModel):
    id: str
    documento_id: str
    tipo: TipoVinculo
    ref: str
    estado: Literal["vigente", "revisar"]
    creado_por: str
    creado_en: datetime


class VinculosDocumento(BaseModel):
    vinculos: list[Vinculo]


class DocumentoVinculado(BaseModel):
    documento_id: str
    codigo: str
    nombre: str
    estado_documento: str
    estado: Literal["vigente", "revisar"]


class PuertoReferencias(Protocol):
    async def tratamiento_existe(self, session: AsyncSession, tenant_id: str, ref: str) -> bool: ...
    async def tarea_existe(self, session: AsyncSession, tenant_id: str, ref: str) -> bool: ...


class PuertoHallazgos(Protocol):
    async def registrar(self, session: AsyncSession, tenant_id: str, actor: str, origen_ref: str,
                        titulo: str) -> None: ...


class PuertoEvidencias(Protocol):
    async def adjuntar(self, session: AsyncSession, tenant_id: str, actor: str, tarea_id: str,
                       documento_id: str, sha256: str) -> None: ...


def es_control(ref: str) -> bool:
    """Catálogo canónico P1–P80, sin ceros a la izquierda."""
    return bool(_CONTROL.match(ref))


def _sin_repetir(valores: list[str]) -> list[str]:
    return list(dict.fromkeys(v.strip() for v in valores if v.strip()))


async def _exigir_documento(session: AsyncSession, tenant_id: str, documento_id: str) -> None:
    existe = (await session.execute(text(
        "SELECT 1 FROM biblioteca_documentos WHERE id=:d AND tenant_id=:t"
    ), {"d": documento_id, "t": tenant_id})).scalar()
    if existe is None:
        raise ErrorNegocio("BIB_DOCUMENTO_NO_ENCONTRADO")


async def listar_vinculos(session: AsyncSession, tenant_id: str, actor: str, documento_id: str) -> VinculosDocumento:
    await contexto(session, tenant_id, actor)
    await _exigir_documento(session, tenant_id, documento_id)
    filas = (await session.execute(text(
        "SELECT id,documento_id,tipo,ref,estado,creado_por,creado_en FROM biblioteca_vinculos "
        "WHERE tenant_id=:t AND documento_id=:d ORDER BY tipo,ref"
    ), {"t": tenant_id, "d": documento_id})).mappings().all()
    return VinculosDocumento(vinculos=[Vinculo(**dict(f)) for f in filas])


async def _validar(session: AsyncSession, tenant_id: str, entrada: EntradaVinculos,
                   referencias: PuertoReferencias) -> list[tuple[str, str]]:
    """R3: devuelve los pares (tipo, ref) o falla con 422 antes de cualquier escritura."""
    pares: list[tuple[str, str]] = []
    for ref in _sin_repetir(entrada.controles):
        if not es_control(ref):
            raise ErrorNegocio("VINCULO_REF_INEXISTENTE")
        pares.append(("control", ref))
    for ref in _sin_repetir(entrada.tratamientos):
        if len(ref) > 120 or not await referencias.tratamiento_existe(session, tenant_id, ref):
            raise ErrorNegocio("VINCULO_REF_INEXISTENTE")
        pares.append(("tratamiento", ref))
    for ref in _sin_repetir(entrada.tareas):
        if len(ref) > 120 or not await referencias.tarea_existe(session, tenant_id, ref):
            raise ErrorNegocio("VINCULO_REF_INEXISTENTE")
        pares.append(("tarea", ref))
    return pares


async def reemplazar_vinculos(
    session: AsyncSession, tenant_id: str, actor: str, documento_id: str, entrada: EntradaVinculos,
    referencias: PuertoReferencias,
) -> VinculosDocumento:
    """PUT: el conjunto enviado sustituye al anterior; un vínculo que se conserva mantiene su estado."""
    await contexto(session, tenant_id, actor)
    await _exigir_documento(session, tenant_id, documento_id)
    pares = await _validar(session, tenant_id, entrada, referencias)
    actuales = {(f["tipo"], f["ref"]) for f in (await session.execute(text(
        "SELECT tipo,ref FROM biblioteca_vinculos WHERE tenant_id=:t AND documento_id=:d"
    ), {"t": tenant_id, "d": documento_id})).mappings().all()}
    nuevos = set(pares)
    for tipo, ref in sorted(actuales - nuevos):
        await session.execute(text(
            "DELETE FROM biblioteca_vinculos WHERE tenant_id=:t AND documento_id=:d AND tipo=:k AND ref=:r"
        ), {"t": tenant_id, "d": documento_id, "k": tipo, "r": ref})
    for tipo, ref in pares:
        if (tipo, ref) in actuales:
            continue
        await session.execute(text(
            "INSERT INTO biblioteca_vinculos(id,tenant_id,documento_id,tipo,ref,estado,creado_por) "
            "VALUES (:id,:t,:d,:k,:r,'vigente',:u) ON CONFLICT (tenant_id,documento_id,tipo,ref) DO NOTHING"
        ), {"id": f"{documento_id}:{tipo}:{ref}", "t": tenant_id, "d": documento_id, "k": tipo, "r": ref,
            "u": actor})
    if actuales != nuevos:
        await registrar_evento(session, tenant_id, "biblioteca_documento", documento_id, "vinculos_actualizados",
                               actor, {"vinculos": [f"{k}:{r}" for k, r in pares]})
    return await listar_vinculos(session, tenant_id, actor, documento_id)


async def documentos_de_tratamiento(
    session: AsyncSession, tenant_id: str, actor: str, tratamiento_id: str,
) -> list[DocumentoVinculado]:
    """Vista inversa para la pestaña «Documentos que lo usan» del RAT."""
    await contexto(session, tenant_id, actor)
    filas = (await session.execute(text(
        "SELECT v.documento_id,d.codigo,d.nombre,d.estado estado_documento,v.estado "
        "FROM biblioteca_vinculos v JOIN biblioteca_documentos d ON d.id=v.documento_id AND d.tenant_id=v.tenant_id "
        "WHERE v.tenant_id=:t AND v.tipo='tratamiento' AND v.ref=:r ORDER BY d.nombre,v.documento_id"
    ), {"t": tenant_id, "r": tratamiento_id})).mappings().all()
    return [DocumentoVinculado(**dict(f)) for f in filas]


async def al_aprobar_documento(
    session: AsyncSession, tenant_id: str, actor: str, documento_id: str, evidencias: PuertoEvidencias,
) -> int:
    """R1: el documento aprobado queda como evidencia de cada tarea vinculada; la tarea no cambia de estado
    (cuatro ojos: la valida quien corresponda en Hoja de Ruta)."""
    await contexto(session, tenant_id, actor)
    sha = (await session.execute(text(
        "SELECT sha256 FROM biblioteca_documentos WHERE id=:d AND tenant_id=:t AND estado='aprobado'"
    ), {"d": documento_id, "t": tenant_id})).scalar()
    if not sha:
        return 0
    tareas = (await session.execute(text(
        "SELECT ref FROM biblioteca_vinculos WHERE tenant_id=:t AND documento_id=:d AND tipo='tarea' ORDER BY ref"
    ), {"t": tenant_id, "d": documento_id})).scalars().all()
    for tarea in tareas:
        await evidencias.adjuntar(session, tenant_id, actor, tarea, documento_id, sha)
    return len(tareas)


async def al_cambiar_tratamiento(
    session: AsyncSession, tenant_id: str, actor: str, tratamiento_id: str, hallazgos: PuertoHallazgos,
) -> list[str]:
    """R2: versión nueva o baja del tratamiento ⇒ sus documentos pasan a «revisar» y un hallazgo `rat` cada uno."""
    await contexto(session, tenant_id, actor)
    documentos = (await session.execute(text(
        "UPDATE biblioteca_vinculos SET estado='revisar' WHERE tenant_id=:t AND tipo='tratamiento' AND ref=:r "
        "RETURNING documento_id"
    ), {"t": tenant_id, "r": tratamiento_id})).scalars().all()
    afectados = sorted(set(documentos))
    for documento_id in afectados:
        await hallazgos.registrar(
            session, tenant_id, actor, f"{tratamiento_id}:documento:{documento_id}",
            "Revisar el documento: cambió un tratamiento que usa",
        )
    return afectados
