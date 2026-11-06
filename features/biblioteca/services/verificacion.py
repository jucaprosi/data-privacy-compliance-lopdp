# ¤adpa ¤rbac-tenant
# ¤¤developer-architect
"""Evidencias y verificación de cierre de acciones canónicas (BIB-303).

- La evidencia guarda versión, hash, clasificación, permisos, fecha y su relación con una acción
  (y, si aplica, un control y una revisión documental). Tener hash no la vuelve legible ni revisada.
- Una verificación es un registro inmutable: criterio, evidencia legible, revisor, resultado, fecha y,
  cuando corresponde, eficacia. Una verificación no conforme no borra la anterior y mantiene o reabre
  la acción. Un documento aprobado o enlazado no cierra la acción por sí solo.
- `VerificadorEvidencia` implementa el puerto `VerificadorDeCierre` de Roadmap (RM-24). Roadmap lo
  prepara de forma asíncrona antes del cierre y luego le pregunta de forma síncrona.
"""
from __future__ import annotations

import contextvars
import uuid
from collections.abc import Awaitable, Callable
from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.errors import ErrorNegocio
from app_core.audit import registrar_evento
from features.biblioteca.services.documentos_consulta import contexto

ObtenerAccion = Callable[[AsyncSession, str, str], Awaitable[Any]]
ReabrirAccion = Callable[[AsyncSession, str, str, str], Awaitable[None]]

Clasificacion = Literal["publica", "interna", "confidencial", "restringida"]
Resultado = Literal["conforme", "no_conforme"]
Veredicto = Literal["conforme", "no_conforme", "pendiente", "sin_requisito"]
ROLES_VALIDOS = {"responsable_area", "coordinador", "dpo", "implementador", "admin_organizacion"}


class RegistrarEvidencia(BaseModel):
    model_config = ConfigDict(extra="forbid")
    titulo: str = Field(min_length=3, max_length=200)
    version: str = Field(min_length=1, max_length=40)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    clasificacion: Clasificacion
    permisos: list[str] = Field(min_length=1, max_length=5)
    fecha: date
    control_ref: str | None = Field(default=None, max_length=64)
    documento_id: str | None = Field(default=None, max_length=36)
    documento_revision: int | None = Field(default=None, ge=1)


class RegistrarVerificacion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    evidencia_id: str = Field(min_length=1, max_length=36)
    criterio: str = Field(min_length=5, max_length=1000)
    evidencia_legible: bool
    resultado: Resultado
    eficacia_requerida: bool = False
    eficacia_conforme: bool | None = None
    fecha: date
    observaciones: str | None = Field(default=None, max_length=2000)


class Evidencia(BaseModel):
    id: str
    accion_id: str
    titulo: str
    version: str
    sha256: str
    clasificacion: str
    permisos: list[str]
    fecha: date
    control_ref: str | None
    documento_id: str | None
    documento_revision: int | None
    creado_por: str
    creado_en: datetime


class Verificacion(BaseModel):
    id: str
    accion_id: str
    evidencia_id: str
    criterio: str
    evidencia_legible: bool
    resultado: str
    eficacia_requerida: bool
    eficacia_conforme: bool | None
    revisor: str
    fecha: date
    observaciones: str | None
    creado_en: datetime


class ExpedienteVerificacion(BaseModel):
    accion_id: str
    veredicto: Veredicto
    evidencias: list[Evidencia]
    verificaciones: list[Verificacion]


# ¤adpa
def validar_verificacion(entrada: RegistrarVerificacion, hoy: date | None = None) -> None:
    """Reglas de cierre: un 'conforme' exige evidencia legible y, si corresponde, eficacia conforme."""
    if entrada.fecha > (hoy or date.today()):
        raise ErrorNegocio("BIB_VERIF_FECHA_FUTURA")
    if entrada.resultado == "conforme" and not entrada.evidencia_legible:
        raise ErrorNegocio("BIB_VERIF_EVIDENCIA_ILEGIBLE")
    if entrada.resultado == "conforme" and entrada.eficacia_requerida and entrada.eficacia_conforme is not True:
        raise ErrorNegocio("BIB_VERIF_EFICACIA_PENDIENTE")


# ¤adpa
def calcular_veredicto(hay_requisito: bool, ultimo_resultado: str | None) -> Veredicto:
    """Solo la última verificación cuenta; sin evidencia ni enlaces no hay requisito documental."""
    if ultimo_resultado == "conforme":
        return "conforme"
    if ultimo_resultado == "no_conforme":
        return "no_conforme"
    return "pendiente" if hay_requisito else "sin_requisito"


async def _exigir_accion(session: AsyncSession, tenant_id: str, accion_id: str,
                         obtener_accion: ObtenerAccion) -> Any:
    accion = await obtener_accion(session, tenant_id, accion_id)
    if accion is None:
        raise ErrorNegocio("BIB_VERIF_ACCION_AJENA")
    return accion


async def veredicto_de_accion(session: AsyncSession, tenant_id: str, accion_id: str) -> Veredicto:
    fila = (await session.execute(text(
        "SELECT (SELECT v.resultado FROM biblioteca_verificaciones v WHERE v.tenant_id=:t AND v.accion_id=:a "
        "ORDER BY v.creado_en DESC, v.secuencia DESC LIMIT 1) ultimo, "
        "EXISTS (SELECT 1 FROM biblioteca_evidencias e WHERE e.tenant_id=:t AND e.accion_id=:a) "
        "OR EXISTS (SELECT 1 FROM biblioteca_revision_acciones r WHERE r.tenant_id=:t AND r.accion_id=:a) requisito"
    ), {"t": tenant_id, "a": accion_id})).mappings().first()
    return calcular_veredicto(bool(fila and fila["requisito"]), fila["ultimo"] if fila else None)


async def obtener_expediente(
    session: AsyncSession, tenant_id: str, actor: str, accion_id: str, obtener_accion: ObtenerAccion
) -> ExpedienteVerificacion:
    await contexto(session, tenant_id, actor)
    await _exigir_accion(session, tenant_id, accion_id, obtener_accion)
    evidencias = (await session.execute(text(
        "SELECT id,accion_id,titulo,version,sha256,clasificacion,permisos,fecha,control_ref,documento_id,"
        "documento_revision,creado_por,creado_en FROM biblioteca_evidencias "
        "WHERE tenant_id=:t AND accion_id=:a ORDER BY creado_en,id"
    ), {"t": tenant_id, "a": accion_id})).mappings().all()
    verificaciones = (await session.execute(text(
        "SELECT id,accion_id,evidencia_id,criterio,evidencia_legible,resultado,eficacia_requerida,"
        "eficacia_conforme,revisor,fecha,observaciones,creado_en FROM biblioteca_verificaciones "
        "WHERE tenant_id=:t AND accion_id=:a ORDER BY creado_en,secuencia"
    ), {"t": tenant_id, "a": accion_id})).mappings().all()
    return ExpedienteVerificacion(
        accion_id=accion_id, veredicto=await veredicto_de_accion(session, tenant_id, accion_id),
        evidencias=[Evidencia(**dict(f)) for f in evidencias],
        verificaciones=[Verificacion(**dict(f)) for f in verificaciones],
    )


async def registrar_evidencia(
    session: AsyncSession, tenant_id: str, actor: str, accion_id: str, entrada: RegistrarEvidencia,
    obtener_accion: ObtenerAccion,
) -> Evidencia:
    await contexto(session, tenant_id, actor)
    if not set(entrada.permisos) <= ROLES_VALIDOS:
        raise ErrorNegocio("BIB_EVIDENCIA_PERMISOS_INVALIDOS")
    if (entrada.documento_id is None) != (entrada.documento_revision is None):
        raise ErrorNegocio("BIB_EVIDENCIA_REVISION_INCOMPLETA")
    accion = await _exigir_accion(session, tenant_id, accion_id, obtener_accion)
    evidencia_id = str(uuid.uuid4())
    fila = (await session.execute(text(
        "INSERT INTO biblioteca_evidencias(id,tenant_id,accion_id,titulo,version,sha256,clasificacion,permisos,"
        "fecha,control_ref,documento_id,documento_revision,creado_por) VALUES (:id,:t,:a,:titulo,:version,"
        ":sha,:clas,:permisos,:fecha,:control,:doc,:rev,:u) RETURNING id,accion_id,titulo,version,sha256,"
        "clasificacion,permisos,fecha,control_ref,documento_id,documento_revision,creado_por,creado_en"
    ), {"id": evidencia_id, "t": tenant_id, "a": accion_id, "titulo": entrada.titulo,
        "version": entrada.version, "sha": entrada.sha256, "clas": entrada.clasificacion,
        "permisos": sorted(set(entrada.permisos)), "fecha": entrada.fecha,
        "control": entrada.control_ref or accion.get("control_ref"),
        "doc": entrada.documento_id, "rev": entrada.documento_revision, "u": actor})).mappings().first()
    await registrar_evento(session, tenant_id, "biblioteca_evidencia", evidencia_id, "evidencia_registrada",
                           actor, {"accion_id": accion_id, "sha256": entrada.sha256, "version": entrada.version})
    return Evidencia(**dict(fila))


async def registrar_verificacion(
    session: AsyncSession, tenant_id: str, actor: str, accion_id: str, entrada: RegistrarVerificacion,
    obtener_accion: ObtenerAccion, reabrir_accion: ReabrirAccion,
) -> ExpedienteVerificacion:
    """Añade una verificación; nunca modifica ni borra las anteriores."""
    await contexto(session, tenant_id, actor)
    validar_verificacion(entrada)
    await _exigir_accion(session, tenant_id, accion_id, obtener_accion)
    autor = (await session.execute(text(
        "SELECT creado_por FROM biblioteca_evidencias WHERE id=:e AND tenant_id=:t AND accion_id=:a"
    ), {"e": entrada.evidencia_id, "t": tenant_id, "a": accion_id})).scalar()
    if autor is None:
        raise ErrorNegocio("BIB_EVIDENCIA_NO_ENCONTRADA")
    if autor == actor:
        raise ErrorNegocio("BIB_VERIF_REVISOR_AUTOR")
    verificacion_id = str(uuid.uuid4())
    await session.execute(text(
        "INSERT INTO biblioteca_verificaciones(id,tenant_id,accion_id,evidencia_id,criterio,evidencia_legible,"
        "resultado,eficacia_requerida,eficacia_conforme,revisor,fecha,observaciones) VALUES (:id,:t,:a,:e,"
        ":criterio,:legible,:resultado,:requerida,:eficacia,:u,:fecha,:obs)"
    ), {"id": verificacion_id, "t": tenant_id, "a": accion_id, "e": entrada.evidencia_id,
        "criterio": entrada.criterio, "legible": entrada.evidencia_legible, "resultado": entrada.resultado,
        "requerida": entrada.eficacia_requerida, "eficacia": entrada.eficacia_conforme, "u": actor,
        "fecha": entrada.fecha, "obs": entrada.observaciones})
    await registrar_evento(session, tenant_id, "biblioteca_verificacion", verificacion_id,
                           "verificacion_registrada", actor,
                           {"accion_id": accion_id, "evidencia_id": entrada.evidencia_id,
                            "resultado": entrada.resultado})
    if entrada.resultado == "no_conforme":
        await reabrir_accion(session, tenant_id, actor, accion_id)
    return await obtener_expediente(session, tenant_id, actor, accion_id, _accion_ya_validada)


async def _accion_ya_validada(_session: AsyncSession, _tenant_id: str, accion_id: str) -> dict:
    return {"id": accion_id}


# --- Puerto VerificadorDeCierre (RM-24) --------------------------------------------------------------

_veredicto_preparado: contextvars.ContextVar[tuple[str, str, Veredicto] | None] = contextvars.ContextVar(
    "bib303_veredicto_preparado", default=None)


class VerificadorEvidencia:
    """True: última verificación conforme. False: hay requisito y no está conforme. None: sin requisito
    o sin veredicto preparado para esa misma acción y organización."""

    async def preparar(self, session: AsyncSession, tenant_id: str, actor: str, tarea_id: str) -> None:
        await contexto(session, tenant_id, actor)
        _veredicto_preparado.set((tenant_id, tarea_id, await veredicto_de_accion(session, tenant_id, tarea_id)))

    def evidencia_conforme(self, tenant_id: str, tarea_id: str) -> bool | None:
        preparado = _veredicto_preparado.get()
        if preparado is None or preparado[:2] != (tenant_id, tarea_id):
            return None
        veredicto = preparado[2]
        if veredicto == "sin_requisito":
            return None
        return veredicto == "conforme"
