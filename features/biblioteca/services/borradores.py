# ¤adpa
# ¤¤developer-architect
"""Borradores de la organización: guardado de las respuestas `contexto.*` y vista rellenada (BIB-201).

Biblioteca no importa otras salas: los datos de la organización, el DPD y el RAT llegan por `FuentesDatos`,
que arma el router con las compuertas de ORG-14, Organización y RAT. Todo se lee; nada se escribe fuera
de `biblioteca_borradores`. La organización sale siempre de la sesión autenticada, nunca del cuerpo.
"""
import json
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from datetime import date
from uuid import uuid4
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app_core.errors import ErrorNegocio
from features.biblioteca.domain.esquemas import (
    GENERADAS, Borrador, EntradaBorrador, GuardarBorrador, Plantilla, avisos_activos, leer_plantilla,
)
from features.biblioteca.domain.plantillas_md import validar_plantilla_md
from features.biblioteca.services.rellenado import (
    datos_de_tratamiento, datos_del_documento, fichas_de_actividades, rellenar,
)
from features.biblioteca.services.validacion import es_revisable, validar_contexto
import features.biblioteca.domain.errores  # noqa: F401  registra los códigos de Biblioteca al importarse

LEER = ("SELECT b.id, b.version_id, b.contexto, b.fecha_emision, b.revision, b.plantilla_md, b.creado_en, "
        "b.actualizado_en FROM biblioteca_borradores b WHERE b.id=:id")
LEER_BLOQUEANDO = LEER + " FOR UPDATE"


# ¤adpa
@dataclass(frozen=True)
class FuentesDatos:
    """Lecturas de otras salas, ya resueltas por su compuerta y con el tenant de la sesión."""
    organizacion: Callable[[AsyncSession, str], Awaitable[Mapping[str, object]]]  # ORG-14: variable → valor
    dpd_vigente: Callable[[AsyncSession, str], Awaitable[Mapping[str, object] | None]]  # nombre, correo, fecha
    actividades: Callable[[AsyncSession, str], Awaitable[list[Mapping]]]  # RAT-01, solo lectura


# ¤adpa
async def _fijar_contexto(session: AsyncSession, tenant_id: str, actor: str) -> None:
    await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true), "
                               "set_config('app.current_user_id', :u, true)"), {"t": tenant_id, "u": actor})


# ¤adpa
async def _armar(session: AsyncSession, fuentes: FuentesDatos, tenant_id: str, plantilla: Plantilla,
                 fecha: date, guardado: dict) -> tuple[str, list[str], list]:
    organizacion: dict[str, object] = dict(await fuentes.organizacion(session, tenant_id))
    organizacion.update(datos_del_documento(plantilla, fecha))
    dpd = await fuentes.dpd_vigente(session, tenant_id)
    organizacion["dpo.designado"] = dpd is not None
    if dpd is not None:
        organizacion.update({"dpo.nombre": dpd.get("nombre"), "dpo.correo": dpd.get("correo"),
                             "dpo.fecha_designacion": dpd.get("fecha_designacion")})
    contexto: dict = dict(guardado)
    if "tratamiento." in plantilla.cuerpo or any(c.origen == "rat" for c in plantilla.campos):
        actividades = await fuentes.actividades(session, tenant_id)
        organizacion.update(datos_de_tratamiento(actividades))
        if actividades and any(c.origen == "rat" for c in plantilla.campos):
            for clave in GENERADAS:
                contexto[clave] = fichas_de_actividades(actividades)
    contenido, faltantes = rellenar(plantilla, organizacion, contexto)
    return contenido, faltantes, avisos_activos(plantilla, contexto, dpd is not None)


# ¤adpa
async def _vista(session: AsyncSession, fuentes: FuentesDatos, tenant_id: str, fila: Mapping) -> Borrador:
    plantilla = leer_plantilla(fila["plantilla_md"])
    guardado = fila["contexto"] if isinstance(fila["contexto"], dict) else json.loads(fila["contexto"])
    contenido, faltantes, avisos = await _armar(session, fuentes, tenant_id, plantilla, fila["fecha_emision"], guardado)
    return Borrador(
        id=fila["id"], version_id=fila["version_id"], codigo=plantilla.codigo, plantilla_version=plantilla.version,
        fecha_emision=fila["fecha_emision"], contexto=guardado, campos=plantilla.campos, contenido_markdown=contenido,
        variables_faltantes=faltantes, avisos=avisos, revisable=es_revisable(faltantes), revision=fila["revision"],
        creado_en=fila["creado_en"], actualizado_en=fila["actualizado_en"])


# ¤adpa
async def _publicada(session: AsyncSession, version_id: str) -> tuple[str, str]:
    """Versión publicada en Markdown y legible por la RLS de miembro; su texto íntegro y su huella."""
    fila = (await session.execute(text(
        "SELECT codigo, cuerpo_md, sha256 FROM biblioteca_versiones "
        "WHERE id=:id AND estado='publicada' AND formato='MD'"), {"id": version_id})).mappings().first()
    if fila is None or validar_plantilla_md(fila["cuerpo_md"], fila["codigo"]):
        raise ErrorNegocio("BIB_PLANTILLA_NO_DISPONIBLE")
    return fila["cuerpo_md"], fila["sha256"]


# ¤adpa
async def _leer(session: AsyncSession, identificador: str, bloquear: bool = False) -> Mapping:
    fila = (await session.execute(text(LEER_BLOQUEANDO if bloquear else LEER), {"id": identificador})).mappings().first()
    if fila is None:  # la RLS oculta los de otra organización: se ve igual que uno inexistente
        raise ErrorNegocio("BIB_BORRADOR_NO_ENCONTRADO")
    return fila


# ¤adpa
async def crear_borrador(session: AsyncSession, fuentes: FuentesDatos, tenant_id: str, actor: str,
                         entrada: EntradaBorrador) -> Borrador:
    await _fijar_contexto(session, tenant_id, actor)
    texto, huella = await _publicada(session, entrada.version_id)
    plantilla = leer_plantilla(texto)
    contexto = validar_contexto(plantilla.campos, entrada.contexto)
    identificador = str(uuid4())
    await session.execute(text(
        "INSERT INTO biblioteca_borradores(id, tenant_id, version_id, plantilla_md, plantilla_sha256, contexto, "
        "fecha_emision, creado_por, actualizado_por) VALUES (:id, :t, :v, :md, :sha, CAST(:ctx AS jsonb), "
        ":fecha, :u, :u)"),
        {"id": identificador, "t": tenant_id, "v": entrada.version_id, "md": texto, "sha": huella,
         "ctx": json.dumps(contexto, ensure_ascii=False), "fecha": entrada.fecha_emision or date.today(), "u": actor})
    return await _vista(session, fuentes, tenant_id, await _leer(session, identificador))


# ¤adpa
async def obtener_borrador(session: AsyncSession, fuentes: FuentesDatos, tenant_id: str, actor: str,
                           identificador: str) -> Borrador:
    await _fijar_contexto(session, tenant_id, actor)
    return await _vista(session, fuentes, tenant_id, await _leer(session, identificador))


# ¤adpa
async def guardar_borrador(session: AsyncSession, fuentes: FuentesDatos, tenant_id: str, actor: str,
                           identificador: str, entrada: GuardarBorrador) -> Borrador:
    """Guarda incompleto: lo que falte se devuelve como faltante, no como error. Revisión desfasada: 409."""
    await _fijar_contexto(session, tenant_id, actor)
    fila = await _leer(session, identificador, bloquear=True)
    if fila["revision"] != entrada.revision:
        raise ErrorNegocio("BIB_REVISION_DESFASADA")
    contexto = validar_contexto(leer_plantilla(fila["plantilla_md"]).campos, entrada.contexto)
    await session.execute(text(
        "UPDATE biblioteca_borradores SET contexto=CAST(:ctx AS jsonb), fecha_emision=:fecha, "
        "revision=revision+1, actualizado_por=:u, actualizado_en=now() WHERE id=:id AND revision=:rev"),
        {"ctx": json.dumps(contexto, ensure_ascii=False), "fecha": entrada.fecha_emision or fila["fecha_emision"],
         "u": actor, "id": identificador, "rev": entrada.revision})
    return await _vista(session, fuentes, tenant_id, await _leer(session, identificador))
