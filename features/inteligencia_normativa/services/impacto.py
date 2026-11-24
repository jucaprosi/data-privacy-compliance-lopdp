# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤inteligencia-normativa ¤copiloto-ia ¤vertex-cache ¤dpo-independencia ¤transcripcion-normativa ¤adpa
"""NORM-03: análisis de impacto de una resolución sobre una organización, validado por persona.

R1 · la propuesta de la IA no cambia nada: solo la aceptación del DPO genera hallazgos hacia el plan de acción.
R2 · cita cerrada: cada elemento cita artículos que el texto de la resolución contiene; sin sustento, la propuesta
queda vacía y `sin_base_normativa` es verdadero. R4 · un cambio de estado pide regenerar la caché de VTX-01.
Contrato: governance/especificaciones/NORM-03.md.
"""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime
from typing import Any, Awaitable, Callable, Optional, Protocol

from pydantic import BaseModel, Field
from sqlalchemy import text

from features.inteligencia_normativa.domain.errores import (
    DecisionInvalida,
    IaNoDisponible,
    ImpactoNoEncontrado,
    ImpactoYaDecidido,
    NotaDeDecisionObligatoria,
    ResolucionNoEncontrada,
    ResolucionSinTexto,
)
from features.inteligencia_normativa.services import extraccion, transcripcion_engine

logger = logging.getLogger(__name__)

TIPOS = ("pregunta", "tratamiento", "tarea", "plantilla")
ESTADOS_QUE_REGENERAN = ("vigente", "reformada", "derogada")
LARGO_MINIMO_NOTA = 10
DECISIONES = {"aceptar": "aceptada", "rechazar": "rechazada"}

_COLUMNAS = ("id::text AS id, resolucion_id::text AS resolucion_id, modelo, corpus_sha256, propuesta, "
             "sin_base_normativa, estado, solicitada_por, creada_en, decidida_por, decidida_en, nota, origen_texto")


class ElementoImpacto(BaseModel):
    tipo: str
    referencia_id: str
    motivo: str
    articulos_citados: list[str] = Field(default_factory=list)


class AnalisisImpacto(BaseModel):
    id: str
    resolucion_id: str
    modelo: str
    corpus_sha256: str
    propuesta: list[ElementoImpacto]
    sin_base_normativa: bool
    estado: str
    solicitada_por: str
    creada_en: datetime
    decidida_por: Optional[str] = None
    decidida_en: Optional[datetime] = None
    nota: Optional[str] = None
    origen_texto: str = "capa_texto"
    hallazgos_generados: int = 0


class RegeneracionCache(BaseModel):
    pedida: bool
    corpus_sha256: Optional[str] = None


class LectorOriginales(Protocol):
    def leer(self, clave: str) -> Optional[bytes]: ...


class CatalogoOrganizacion(Protocol):
    """Elementos de la organización que la resolución puede afectar: [{tipo, referencia_id, nombre}]."""

    async def elementos(self, sesion, tenant_id: str, user_id: str) -> list[dict]: ...


Analizador = Callable[[str, list, str], Awaitable[tuple[list[dict], Any]]]
RegistradorHallazgos = Callable[..., Awaitable[tuple[str, bool]]]


def _analisis(f, hallazgos: int = 0) -> AnalisisImpacto:
    return AnalisisImpacto(
        id=f.id, resolucion_id=f.resolucion_id, modelo=f.modelo, corpus_sha256=f.corpus_sha256,
        propuesta=[ElementoImpacto(**e) for e in (f.propuesta or [])], sin_base_normativa=f.sin_base_normativa,
        estado=f.estado, solicitada_por=f.solicitada_por, creada_en=f.creada_en, decidida_por=f.decidida_por,
        decidida_en=f.decidida_en, nota=f.nota, origen_texto=f.origen_texto, hallazgos_generados=hallazgos,
    )


async def huella_corpus_vigente(sesion, incluir: Optional[tuple[str, str]] = None) -> str:
    """SHA-256 del conjunto de resoluciones que hoy integran el corpus (vigentes o reformadas), por id y huella."""
    filas = (await sesion.execute(
        text("SELECT id::text AS id, archivo_sha256 FROM normativa_resoluciones "
             "WHERE estado IN ('vigente', 'reformada') ORDER BY id"),
    )).all()
    lineas = [f"{f.id}:{f.archivo_sha256}" for f in filas]
    if incluir is not None:
        lineas.append(f"{incluir[0]}:{incluir[1]}")
    return hashlib.sha256("\n".join(sorted(lineas)).encode("utf-8")).hexdigest()


def depurar_propuesta(elementos: list[dict], catalogo: list[dict], texto: str) -> list[dict]:
    """R2: solo elementos del catálogo (tipo y referencia exactos) con al menos un artículo presente en el texto."""
    validos = {(e["tipo"], e["referencia_id"]) for e in catalogo}
    presentes = extraccion.articulos_del_texto(texto)
    salida: list[dict] = []
    vistos: set[tuple[str, str]] = set()
    for e in elementos:
        clave = (e.get("tipo"), e.get("referencia_id"))
        if clave not in validos or clave in vistos:
            continue
        citas = []
        for c in dict.fromkeys(e.get("articulos_citados") or []):
            k = extraccion.normalizar_cita(c)
            if k is not None and k in presentes:
                citas.append(c)
        if not citas or not (e.get("motivo") or "").strip():
            continue
        vistos.add(clave)
        salida.append({"tipo": clave[0], "referencia_id": clave[1], "motivo": e["motivo"].strip(),
                       "articulos_citados": citas})
    return salida


async def _contexto(sesion, tenant_id: str, user_id: str) -> None:
    from app_core.db.session import fijar_contexto_rls

    await fijar_contexto_rls(sesion, tenant_id, user_id)


async def solicitar(
    sesion, tenant_id: str, user_id: str, resolucion_id: str, *, lector: LectorOriginales,
    catalogo: CatalogoOrganizacion, analizar: Analizador, modelo: str, indexador=None,
    registrar_traza: Optional[Callable[..., Awaitable[None]]] = None, transcribir=None,
) -> AnalisisImpacto:
    """Extrae el original, pide el análisis al modelo, depura las citas y guarda la propuesta (estado `propuesta`)."""
    await _contexto(sesion, tenant_id, user_id)
    fila = (await sesion.execute(
        text("SELECT archivo_sha256, ruta_original FROM normativa_resoluciones WHERE id = CAST(:i AS uuid)"),
        {"i": resolucion_id},
    )).first()
    if fila is None:
        raise ResolucionNoEncontrada()
    contenido = lector.leer(fila.ruta_original)
    if not contenido:
        raise ResolucionSinTexto()
    original = await transcripcion_engine.texto_de(sesion, contenido, fila.archivo_sha256, modelo=modelo,
                                                   transcribir=transcribir)
    texto = original.texto
    if not texto:
        raise ResolucionSinTexto()
    await extraccion.indexar(extraccion.fragmentar(texto), indexador)
    elementos_org = await catalogo.elementos(sesion, tenant_id, user_id)
    try:
        crudos, traza = await analizar(texto, elementos_org, tenant_id)
    except Exception as exc:  # noqa: BLE001 — falla cerrada; solo el tipo, nunca el mensaje
        logger.warning("Análisis de impacto sin IA: %s", type(exc).__name__)
        raise IaNoDisponible() from exc
    propuesta = depurar_propuesta(crudos, elementos_org, texto)
    corpus = await huella_corpus_vigente(sesion, (resolucion_id, fila.archivo_sha256))
    await _contexto(sesion, tenant_id, user_id)
    nuevo = (await sesion.execute(
        text("INSERT INTO normativa_analisis_impacto (tenant_id, resolucion_id, modelo, corpus_sha256, propuesta, "
             "sin_base_normativa, solicitada_por, origen_texto) "
             "VALUES (:t, CAST(:r AS uuid), :m, :c, CAST(:p AS jsonb), :s, :u, :o) "
             f"RETURNING {_COLUMNAS}"),
        {"t": tenant_id, "r": resolucion_id, "m": modelo, "c": corpus, "p": json.dumps(propuesta),
         "s": not propuesta, "u": user_id, "o": original.origen},
    )).one()
    if registrar_traza is not None and traza is not None:
        await registrar_traza(sesion, traza, "normativa_impacto", nuevo.id)
    await sesion.commit()
    return _analisis(nuevo)


async def listar(sesion, tenant_id: str, user_id: str, resolucion_id: Optional[str] = None) -> list[AnalisisImpacto]:
    await _contexto(sesion, tenant_id, user_id)
    filas = (await sesion.execute(
        text(f"SELECT {_COLUMNAS} FROM normativa_analisis_impacto "
             "WHERE tenant_id = :t AND (CAST(:r AS text) IS NULL OR resolucion_id = CAST(:r AS uuid)) "
             "ORDER BY creada_en DESC, id"),
        {"t": tenant_id, "r": resolucion_id},
    )).all()
    return [_analisis(f) for f in filas]


async def decidir(
    sesion, tenant_id: str, user_id: str, analisis_id: str, decision: str, nota: str, *,
    registrar_hallazgo: RegistradorHallazgos,
) -> AnalisisImpacto:
    """Solo el DPO (lo exige el router). Aceptar genera un hallazgo por elemento; rechazar no genera nada (R1, R3)."""
    nuevo_estado = DECISIONES.get(decision)
    if nuevo_estado is None:
        raise DecisionInvalida()
    nota_limpia = (nota or "").strip()
    if len(nota_limpia) < LARGO_MINIMO_NOTA:
        raise NotaDeDecisionObligatoria()
    await _contexto(sesion, tenant_id, user_id)
    existe = (await sesion.execute(
        text("SELECT 1 FROM normativa_analisis_impacto WHERE id = CAST(:i AS uuid) AND tenant_id = :t"),
        {"i": analisis_id, "t": tenant_id},
    )).first()
    if existe is None:
        raise ImpactoNoEncontrado()
    actualizado = (await sesion.execute(
        text("UPDATE normativa_analisis_impacto SET estado = :e, decidida_por = :u, decidida_en = now(), nota = :n "
             f"WHERE id = CAST(:i AS uuid) AND tenant_id = :t AND estado = 'propuesta' RETURNING {_COLUMNAS}"),
        {"e": nuevo_estado, "u": user_id, "n": nota_limpia, "i": analisis_id, "t": tenant_id},
    )).first()
    if actualizado is None:
        raise ImpactoYaDecidido()
    generados = 0
    if nuevo_estado == "aceptada":
        numero = (await sesion.execute(
            text("SELECT numero_resolucion || '/' || anio_emision AS n FROM normativa_resoluciones "
                 "WHERE id = CAST(:r AS uuid)"), {"r": actualizado.resolucion_id},
        )).scalar() or ""
        for i, e in enumerate(actualizado.propuesta or []):
            titulo = f"Resolución {numero}: revisar {e['tipo']} {e['referencia_id']}"
            _, creado = await registrar_hallazgo(sesion, tenant_id, user_id, f"norm03:{analisis_id}:{i}", titulo)
            generados += 1 if creado else 0
    await sesion.commit()
    return _analisis(actualizado, generados)


async def pedir_regeneracion_de_cache(
    sesion, estado_nuevo: str, solicitar_cache: Callable[[str], None]
) -> RegeneracionCache:
    """R4: tras pasar a vigente, reformada o derogada, pide a VTX-01 regenerar la caché con el nuevo `corpus_sha256`.

    El cambio de estado ya está confirmado; si el pedido falla no se deshace, solo se informa `pedida=False`.
    """
    if estado_nuevo not in ESTADOS_QUE_REGENERAN:
        return RegeneracionCache(pedida=False)
    corpus = await huella_corpus_vigente(sesion)
    try:
        solicitar_cache(corpus)
    except Exception as exc:  # noqa: BLE001
        logger.warning("No se pudo pedir la regeneración de la caché: %s", type(exc).__name__)
        return RegeneracionCache(pedida=False, corpus_sha256=corpus)
    return RegeneracionCache(pedida=True, corpus_sha256=corpus)
