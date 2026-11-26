# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
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


async def revisar_estado(id_resolucion: str, estado: str, nota: str, usuario_id: str,
                         fecha_vigencia=None) -> ResolucionConNota:
    async with _sesion() as sesion:
        return await revision.registrar_revision(sesion, id_resolucion, estado, nota, usuario_id, fecha_vigencia)


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


async def revisar_estado(id_resolucion: str, estado: str, nota: str, usuario_id: str,
                         fecha_vigencia=None) -> ResolucionConNota:
    """Revisión de NORM-02 y, ya confirmada, pedido a VTX-01 de regenerar la caché si el estado la afecta (R4).

    NORM-07 R2: antes de revisar lee el estado previo y, ya confirmada, pide la propuesta a la biblioteca.
    """
    async with _sesion() as sesion:
        anterior = revision.estado_anterior_de(await revision.estado_guardado(sesion, id_resolucion))
    resultado = await _revisar_estado_norm02(id_resolucion, estado, nota, usuario_id, fecha_vigencia)
    global _ultima_regeneracion
    async with _sesion() as sesion:
        _ultima_regeneracion = await impacto.pedir_regeneracion_de_cache(
            sesion, resultado.estado, await _dependencia("solicitar_cache", _pedir_cache_por_pasillo)
        )
    await _pedir_propuesta_a_la_biblioteca(id_resolucion, resultado.estado, anterior, usuario_id)
    return resultado


async def _pedir_propuesta_a_la_biblioteca(id_resolucion: str, estado: str, anterior, actor: str) -> None:
    """NORM-07 R2: la revisión ya está confirmada; si la propuesta falla solo se registra el tipo del fallo."""
    if not revision.debe_pedir_propuesta(estado, anterior):
        return
    from app_core.pasillo import biblioteca as pasillo_biblioteca

    try:
        async with _sesion() as sesion:
            await pasillo_biblioteca.proponer_por_resolucion(sesion, id_resolucion, estado, anterior, actor)
    except Exception as exc:  # noqa: BLE001 — la revisión no se deshace
        logging.getLogger("normativa.propuestas").warning(
            "NORM-07: la propuesta de la biblioteca falló (%s)", type(exc).__name__)


async def fecha_vigencia_de(id_resolucion: str):
    """NORM-07 R3: fecha de entrada en vigencia de una resolución, o None."""
    async with _sesion() as sesion:
        return await revision.fecha_vigencia_de(sesion, id_resolucion)


async def fecha_vigencia_por_url(url: str):
    """NORM-07 R3: fecha de vigencia de la única resolución con esa URL oficial, o None."""
    async with _sesion() as sesion:
        return await revision.fecha_vigencia_por_url(sesion, url)
# === fin NORM-03 ===


# === NORM-02b ===
# ¤seguridad-tenant Aviso a las organizaciones de resoluciones nuevas o con versión nueva, al final de una corrida.
import logging  # noqa: E402

_registro_norm02b = logging.getLogger(__name__)
_disparar_monitoreo_norm02 = disparar_monitoreo
_sesion_destinatarios_de_prueba: Callable[[], Any] | None = None

__all__.extend(["inyectar_destinatarios_de_prueba"])


def inyectar_destinatarios_de_prueba(sesion_factory: Callable[[], Any] | None = None) -> None:
    """SOLO PARA PRUEBAS: fábrica de sesiones (con `lopdp_app`) para leer los destinatarios por el pasillo."""
    global _sesion_destinatarios_de_prueba
    _sesion_destinatarios_de_prueba = sesion_factory


async def _conocidas(sesion) -> tuple[list[str], list[str]]:
    """Identificadores de resoluciones y versiones ya registradas antes de la corrida (R5)."""
    resoluciones = (await sesion.execute(text("SELECT id::text FROM normativa_resoluciones"))).scalars().all()
    versiones = (await sesion.execute(text("SELECT id::text FROM normativa_versiones"))).scalars().all()
    return list(resoluciones), list(versiones)


async def _novedades_de_la_corrida(sesion, conocidas: tuple[list[str], list[str]]) -> list[dict]:
    """Resoluciones nuevas o con versión nueva desde la foto previa: número, título e id. Corpus público."""
    resoluciones, versiones = conocidas
    filas = (await sesion.execute(
        text("SELECT r.id::text AS id, r.numero_resolucion, r.titulo FROM normativa_resoluciones r "
             "WHERE NOT (r.id = ANY(CAST(:r AS uuid[]))) "
             "OR EXISTS (SELECT 1 FROM normativa_versiones v WHERE v.resolucion_id = r.id "
             "AND NOT (v.id = ANY(CAST(:v AS uuid[])))) "
             "ORDER BY r.anio_emision, r.numero_resolucion, r.id"),
        {"r": resoluciones, "v": versiones},
    )).all()
    return [{"id": f.id, "numero_resolucion": f.numero_resolucion, "titulo": f.titulo} for f in filas]


def _sesion_destinatarios():
    return _sesion_destinatarios_de_prueba() if _sesion_destinatarios_de_prueba is not None else _sesion()


async def _anotar_avisos(id_corrida: str, cuentas: dict) -> None:
    """Cuentas de avisos en la bitácora de la corrida, sin correos (R6, R7, R8)."""
    from features.inteligencia_normativa.services.monitoreo import _como_normativa

    codigos = [f"NORMATIVA_AVISOS_ENVIADOS={cuentas['enviados']}",
               f"NORMATIVA_AVISOS_FALLIDOS={cuentas['fallidos']}",
               f"NORMATIVA_ORGANIZACIONES_SIN_DESTINATARIOS={cuentas['sin_destinatarios']}"]
    async with _sesion() as sesion:
        await _como_normativa(sesion)
        await sesion.execute(
            text("UPDATE normativa_monitoreo_logs SET codigos_error = codigos_error || CAST(:c AS jsonb) "
                 "WHERE id = CAST(:i AS uuid)"),
            {"c": _json_lista(codigos), "i": id_corrida},
        )
        await sesion.commit()


def _json_lista(valor: list[str]) -> str:
    import json

    return json.dumps(valor)


async def _avisar_organizaciones(resumen: ResumenCorrida, conocidas: tuple[list[str], list[str]]) -> dict:
    from app_core.pasillo import notificaciones as pasillo_notificaciones
    from app_core.pasillo import plataforma as pasillo_plataforma

    async with _sesion() as sesion:
        novedades = await _novedades_de_la_corrida(sesion, conocidas)
    if not novedades:
        return {"enviados": 0, "fallidos": 0, "sin_destinatarios": 0}
    async with _sesion_destinatarios() as sesion:
        destinatarios = await pasillo_plataforma.destinatarios_normativos(sesion)
        activas = await pasillo_plataforma.contar_organizaciones_activas(sesion)
    cuentas = await pasillo_notificaciones.avisar_novedades_normativas(
        destinatarios=destinatarios, novedades=novedades, app_base_url=os.environ.get("APP_BASE_URL", ""),
    )
    cuentas["sin_destinatarios"] = max(activas - len(destinatarios), 0)
    await _anotar_avisos(resumen.id, cuentas)
    return cuentas


async def disparar_monitoreo(origen: str = "manual") -> ResumenCorrida:
    """Corrida y aviso al operador de NORM-02; si la corrida no falló y trajo novedades, aviso a cada organización (R4).

    El aviso nunca tumba la corrida ya registrada (R6) y el registro no lleva correos (R8).
    """
    try:
        async with _sesion() as sesion:
            conocidas = await _conocidas(sesion)
    except Exception:  # sin la foto previa no se sabe qué es nuevo: no se avisa antes que repetir (R5)
        _registro_norm02b.warning("NORM-02b: sin foto previa del corpus; la corrida no avisará a las organizaciones")
        conocidas = None
    resumen = await _disparar_monitoreo_norm02(origen)
    if conocidas is not None and resumen.estado != "fallida" and (resumen.nuevos or resumen.versiones_nuevas):
        try:
            await _avisar_organizaciones(resumen, conocidas)
        except Exception as exc:  # el aviso nunca tumba la corrida ya registrada (R6)
            _registro_norm02b.warning("NORM-02b: el aviso a las organizaciones falló (%s)", type(exc).__name__)
    return resumen
# === fin NORM-02b ===


# === NORM-05 ===
# ¤vigilancia-spdp ¤seguridad Disparo manual que lanza el Job del monitoreo en lugar de correrlo en el backend (NORM-05 R3).
from features.inteligencia_normativa.services import lanzador_trabajo  # noqa: E402

_envio_del_trabajo_de_prueba: Callable[[str], Any] | None = None
_registro_norm05 = logging.getLogger("normativa.lanzador")


def inyectar_envio_del_trabajo_de_prueba(envio: Callable[[str], Any] | None = None) -> None:
    global _envio_del_trabajo_de_prueba
    _envio_del_trabajo_de_prueba = envio


async def lanzar_monitoreo(quien: str) -> None:
    """Lanza el Job; la ejecución corre con origen `programado`. Se anota quién la pidió, sin datos personales."""
    await lanzador_trabajo.lanzar(_envio_del_trabajo_de_prueba)
    _registro_norm05.info("NORM-05: monitoreo lanzado por el operador %s", quien)
# === fin NORM-05 ===


# === NORM-04 ===
# ¤vigilancia-spdp ¤inteligencia-normativa ¤seguridad Lector real de originales, de solo lectura, en el backend (NORM-04 R2).


def _lector() -> LectorOriginales:  # noqa: F811 - redefine el de NORM-02 como NORM-02b redefine disparar_monitoreo
    """Lector real sobre el bucket normativo (`K_SERVICE` y `GCP_STORAGE_BUCKET_NORMATIVO`); si falta alguno, el cerrado."""
    if _lector_de_prueba is not None:
        return _lector_de_prueba
    from features.inteligencia_normativa.services import almacen_normativo

    return almacen_normativo.lector_normativo_por_defecto()
# === fin NORM-04 ===
