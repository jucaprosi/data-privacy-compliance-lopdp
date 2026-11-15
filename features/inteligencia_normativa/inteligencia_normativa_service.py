# ¤inteligencia-normativa ¤vigilancia-spdp ¤adpa
"""Compuerta de la sala Inteligencia Normativa (NORM-01): monitoreo de la SPDP y lectura del corpus."""
from __future__ import annotations

from typing import Any, Callable

from sqlalchemy import text

from features.inteligencia_normativa.domain import errores
from features.inteligencia_normativa.domain.errores import ErrorNormativo, ResolucionNoEncontrada
from features.inteligencia_normativa.schemas import (
    FiltrosResoluciones,
    ResolucionDetalle,
    ResolucionResumen,
    ResumenCorrida,
    VersionResolucion,
)
from features.inteligencia_normativa.services import monitoreo
from features.inteligencia_normativa.services.conector_spdp import ConectorSpdp

__all__ = [
    "ErrorNormativo",
    "FiltrosResoluciones",
    "ejecutar_monitoreo",
    "errores",
    "inyectar_dependencias_de_prueba",
    "listar_resoluciones",
    "obtener_resolucion",
]

_conector_de_prueba: ConectorSpdp | None = None
_almacen_de_prueba: Any = None
_sesion_de_prueba: Callable[[], Any] | None = None


def inyectar_dependencias_de_prueba(*, conector=None, almacen=None, sesion_factory=None) -> None:
    """SOLO PARA PRUEBAS: conector con servidor simulado, almacén en memoria y fábrica de sesiones."""
    global _conector_de_prueba, _almacen_de_prueba, _sesion_de_prueba
    _conector_de_prueba, _almacen_de_prueba, _sesion_de_prueba = conector, almacen, sesion_factory


def _sesion():
    if _sesion_de_prueba is not None:
        return _sesion_de_prueba()
    from app_core.db.session import async_session_factory

    return async_session_factory()


async def ejecutar_monitoreo(origen: str = "manual") -> ResumenCorrida:
    """Una corrida de monitoreo (la lanza Cloud Scheduler a las 05:00 de Guayaquil o una persona a mano)."""
    kwargs: dict[str, Any] = {"conector": _conector_de_prueba or ConectorSpdp()}
    if _almacen_de_prueba is not None:
        kwargs["almacen"] = _almacen_de_prueba
    if _sesion_de_prueba is not None:
        kwargs["sesion_factory"] = _sesion_de_prueba
    return await monitoreo.ejecutar(origen, **kwargs)


def _resumen(f) -> ResolucionResumen:
    return ResolucionResumen(
        id=f.id, numero_resolucion=f.numero_resolucion, anio_emision=f.anio_emision, titulo=f.titulo,
        seccion_fuente=f.seccion_fuente, estado=f.estado, archivo_sha256=f.archivo_sha256,
        detectada_en=f.detectada_en,
    )


async def listar_resoluciones(filtros: FiltrosResoluciones | None = None) -> list[ResolucionResumen]:
    filtros = filtros or FiltrosResoluciones()
    async with _sesion() as sesion:
        filas = (await sesion.execute(
            text("SELECT id::text AS id, numero_resolucion, anio_emision, titulo, seccion_fuente, estado, "
                 "archivo_sha256, detectada_en FROM normativa_resoluciones "
                 "WHERE (CAST(:e AS text) IS NULL OR estado = :e) "
                 "AND (CAST(:s AS text) IS NULL OR seccion_fuente = :s) "
                 "AND (CAST(:a AS integer) IS NULL OR anio_emision = :a) "
                 "ORDER BY detectada_en DESC, numero_resolucion LIMIT :l"),
            {"e": filtros.estado, "s": filtros.seccion, "a": filtros.anio, "l": filtros.limite},
        )).all()
    return [_resumen(f) for f in filas]


async def obtener_resolucion(id_resolucion: str) -> ResolucionDetalle:
    async with _sesion() as sesion:
        f = (await sesion.execute(
            text("SELECT id::text AS id, numero_resolucion, anio_emision, titulo, seccion_fuente, estado, "
                 "archivo_sha256, detectada_en, organo_emisor, materia, fecha_publicacion, url_fuente, "
                 "ruta_original, tamano_bytes, revisada_por, revisada_en FROM normativa_resoluciones "
                 "WHERE id = CAST(:i AS uuid)"),
            {"i": id_resolucion},
        )).first()
        if f is None:
            raise ResolucionNoEncontrada()
        versiones = (await sesion.execute(
            text("SELECT id::text AS id, archivo_sha256, ruta_original, detectada_en, motivo "
                 "FROM normativa_versiones WHERE resolucion_id = CAST(:i AS uuid) ORDER BY detectada_en, id"),
            {"i": id_resolucion},
        )).all()
    return ResolucionDetalle(
        **_resumen(f).model_dump(), organo_emisor=f.organo_emisor, materia=f.materia,
        fecha_publicacion=f.fecha_publicacion, url_fuente=f.url_fuente, ruta_original=f.ruta_original,
        tamano_bytes=f.tamano_bytes, revisada_por=f.revisada_por, revisada_en=f.revisada_en,
        versiones=[VersionResolucion(id=v.id, archivo_sha256=v.archivo_sha256, ruta_original=v.ruta_original,
                                     detectada_en=v.detectada_en, motivo=v.motivo) for v in versiones],
    )


# === NORM-02 ===
import os  # noqa: E402

from features.inteligencia_normativa.domain.errores import (  # noqa: E402
    EstadoNoPermitido,
    NotaObligatoria,
    OriginalNoDisponible,
)
from features.inteligencia_normativa.services import revision  # noqa: E402
from features.inteligencia_normativa.services.revision import (  # noqa: E402
    CorridaBitacora,
    FiltrosCatalogo,
    LectorOriginales,
    PaginaResoluciones,
    ResolucionConNota,
)

__all__.extend([
    "CorridaBitacora", "EstadoNoPermitido", "FiltrosCatalogo", "NotaObligatoria", "OriginalNoDisponible",
    "PaginaResoluciones", "ResolucionConNota", "bitacora", "catalogo", "detalle_con_nota",
    "disparar_monitoreo", "inyectar_lector_de_prueba", "leer_original_de", "revisar_estado",
])

_lector_de_prueba: LectorOriginales | None = None
_avisador_de_prueba: Callable[..., Any] | None = None


def inyectar_lector_de_prueba(lector: LectorOriginales | None = None, avisador: Callable[..., Any] | None = None) -> None:
    """SOLO PARA PRUEBAS: doble del lector de originales y del aviso al operador."""
    global _lector_de_prueba, _avisador_de_prueba
    _lector_de_prueba, _avisador_de_prueba = lector, avisador


def _lector() -> LectorOriginales:
    # El adaptador real (envoltorio de app_core.storage.descargar) llega con EVI-04; mientras, falla cerrado.
    return _lector_de_prueba or revision.LectorOriginalesCerrado()


async def catalogo(filtros: FiltrosCatalogo) -> PaginaResoluciones:
    async with _sesion() as sesion:
        return await revision.listar_catalogo(sesion, filtros)


async def detalle_con_nota(id_resolucion: str) -> ResolucionConNota:
    async with _sesion() as sesion:
        return await revision.nota_de_revision(sesion, id_resolucion)


async def bitacora(limite: int = 50) -> list[CorridaBitacora]:
    async with _sesion() as sesion:
        return await revision.listar_bitacora(sesion, limite)


async def revisar_estado(id_resolucion: str, estado: str, nota: str, usuario_id: str) -> ResolucionConNota:
    async with _sesion() as sesion:
        return await revision.registrar_revision(sesion, id_resolucion, estado, nota, usuario_id)


async def leer_original_de(id_resolucion: str) -> bytes:
    async with _sesion() as sesion:
        clave = await revision.clave_original(sesion, id_resolucion)
    return revision.leer_original(_lector(), clave)


async def disparar_monitoreo(origen: str = "manual") -> ResumenCorrida:
    """Corrida de monitoreo y, si falla, aviso técnico al operador por el pasillo de notificaciones."""
    resumen = await ejecutar_monitoreo(origen)
    if resumen.estado == "fallida":
        correos = [c.strip() for c in os.environ.get("NORMATIVA_AVISO_OPERADOR_EMAIL", "").split(",") if c.strip()]
        if correos:
            if _avisador_de_prueba is not None:
                avisar = _avisador_de_prueba
            else:
                from app_core.pasillo.notificaciones import avisar_corrida_normativa_fallida as avisar
            try:
                await avisar(correos=correos, origen=origen, codigos=list(resumen.codigos_error),
                             app_base_url=os.environ.get("APP_BASE_URL", ""))
            except Exception:  # el aviso nunca tumba la corrida ya registrada
                pass
    return resumen
# === fin NORM-02 ===


# === NORM-03 ===
# ¤copiloto-ia ¤vertex-cache ¤dpo-independencia Análisis de impacto validado por el DPO y caché de contexto al día.
from features.inteligencia_normativa.domain.errores import (  # noqa: E402
    DecisionInvalida,
    IaNoDisponible,
    ImpactoNoEncontrado,
    ImpactoYaDecidido,
    NotaDeDecisionObligatoria,
    ResolucionSinTexto,
)
from features.inteligencia_normativa.services import impacto  # noqa: E402
from features.inteligencia_normativa.services.impacto import (  # noqa: E402
    AnalisisImpacto,
    RegeneracionCache,
)

__all__.extend([
    "AnalisisImpacto", "DecisionInvalida", "IaNoDisponible", "ImpactoNoEncontrado", "ImpactoYaDecidido",
    "NotaDeDecisionObligatoria", "RegeneracionCache", "ResolucionSinTexto", "analizar_impacto",
    "decidir_impacto", "inyectar_dependencias_de_impacto_de_prueba", "listar_impactos",
    "ultima_regeneracion_de_cache",
])

_impacto_de_prueba: dict[str, Any] = {}
_ultima_regeneracion: RegeneracionCache | None = None


def inyectar_dependencias_de_impacto_de_prueba(*, analizar=None, catalogo=None, registrar_hallazgo=None,
                                               solicitar_cache=None, indexador=None) -> None:
    """SOLO PARA PRUEBAS: modelo simulado, catálogo, registro de hallazgos, pedido de caché e indexador."""
    global _ultima_regeneracion
    _impacto_de_prueba.clear()
    _ultima_regeneracion = None
    for nombre, valor in (("analizar", analizar), ("catalogo", catalogo), ("registrar_hallazgo", registrar_hallazgo),
                          ("solicitar_cache", solicitar_cache), ("indexador", indexador)):
        if valor is not None:
            _impacto_de_prueba[nombre] = valor


class _CatalogoPorPasillos:
    """Preguntas del assessment (P1-P80) y tratamientos del RAT de la organización, por los pasillos de cada sala."""

    async def elementos(self, sesion, tenant_id: str, user_id: str) -> list[dict]:
        from app_core.pasillo import diagnostico as pasillo_diagnostico
        from app_core.pasillo import rat as pasillo_rat

        preguntas = [{"tipo": "pregunta", "referencia_id": c["codigo"], "nombre": c.get("control", "")}
                     for c in pasillo_diagnostico.catalogo_de_controles()]
        tratamientos = [{"tipo": "tratamiento", "referencia_id": a.id, "nombre": f"{a.codigo} {a.nombre}"}
                        for a in await pasillo_rat.listar_actividades_resumen(sesion, tenant_id)]
        return preguntas + tratamientos


async def _analizar_por_pasillo(texto: str, catalogo: list, org_id: str):
    from app_core.pasillo import ai_copilot as pasillo_ai

    try:
        return await pasillo_ai.analizar_impacto_normativo(texto, catalogo, org_id)
    except pasillo_ai.errores_de_negocio()[0] as exc:
        raise IaNoDisponible() from exc


async def _registrar_hallazgo_por_pasillo(sesion, tenant_id: str, user_id: str, origen_ref: str, titulo: str):
    """Hallazgo hacia el plan de acción único por el pasillo de la hoja de ruta (origen `rat`, el único genérico)."""
    from app_core.pasillo import roadmap as pasillo_roadmap

    return await pasillo_roadmap.registrar_hallazgo_rat(
        sesion, tenant_id, user_id, origen_ref, "media", titulo, None, None
    )


def _pedir_cache_por_pasillo(corpus_sha256: str) -> None:
    from app_core.pasillo import regulacion_rag as pasillo_rag

    pasillo_rag.pedir_regeneracion_cache(corpus_sha256)


async def _indexar_por_pasillo_adaptador():
    from app_core.pasillo import regulacion_rag as pasillo_rag

    class _Indexador:
        async def vectorizar(self, textos, modelo):
            return await pasillo_rag.vectorizar_fragmentos(textos, modelo)

    return _Indexador()


async def _dependencia(nombre: str, por_defecto):
    return _impacto_de_prueba.get(nombre, por_defecto)


async def analizar_impacto(sesion, tenant_id: str, user_id: str, id_resolucion: str) -> AnalisisImpacto:
    """Pide el análisis (202 en la API). Queda `propuesta`: no cambia nada de la organización hasta que decida el DPO."""
    from app_core.pasillo import ai_copilot as pasillo_ai
    from app_core.pasillo import inferencia as pasillo_inferencia

    return await impacto.solicitar(
        sesion, tenant_id, user_id, id_resolucion, lector=_lector(),
        catalogo=await _dependencia("catalogo", _CatalogoPorPasillos()),
        analizar=await _dependencia("analizar", _analizar_por_pasillo),
        modelo=pasillo_ai.modelo_de_impacto(),
        indexador=await _dependencia("indexador", await _indexar_por_pasillo_adaptador()),
        registrar_traza=pasillo_inferencia.registrar_traza,
    )


async def listar_impactos(sesion, tenant_id: str, user_id: str, id_resolucion: str | None = None) -> list[AnalisisImpacto]:
    return await impacto.listar(sesion, tenant_id, user_id, id_resolucion)


async def decidir_impacto(sesion, tenant_id: str, user_id: str, id_analisis: str, decision: str, nota: str) -> AnalisisImpacto:
    """El router exige el rol DPO (R3). Aceptar genera hallazgos hacia el plan de acción; rechazar solo registra."""
    return await impacto.decidir(
        sesion, tenant_id, user_id, id_analisis, decision, nota,
        registrar_hallazgo=await _dependencia("registrar_hallazgo", _registrar_hallazgo_por_pasillo),
    )


def ultima_regeneracion_de_cache() -> RegeneracionCache | None:
    return _ultima_regeneracion


_revisar_estado_norm02 = revisar_estado


async def revisar_estado(id_resolucion: str, estado: str, nota: str, usuario_id: str) -> ResolucionConNota:
    """Revisión de NORM-02 y, ya confirmada, pedido a VTX-01 de regenerar la caché si el estado la afecta (R4)."""
    resultado = await _revisar_estado_norm02(id_resolucion, estado, nota, usuario_id)
    global _ultima_regeneracion
    async with _sesion() as sesion:
        _ultima_regeneracion = await impacto.pedir_regeneracion_de_cache(
            sesion, resultado.estado, await _dependencia("solicitar_cache", _pedir_cache_por_pasillo)
        )
    return resultado
# === fin NORM-03 ===
