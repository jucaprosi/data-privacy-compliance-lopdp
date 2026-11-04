# ¤adpa ¤rbac-tenant
# ¤¤developer-architect
"""Servicio de aplicabilidad determinista y explicable de plantillas (BIB-204).

Cruza las compuertas de Organización (ORG-14), RAT (RAT-01) y Riesgos MTGE (MTGE-01).
No importa modelos ni servicios internos de otras salas.
"""
from __future__ import annotations

import json
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.errors import ErrorNegocio
from features.biblioteca.domain import errores  # noqa: F401
from features.biblioteca.domain.reglas import (
    EvaluacionPlantilla,
    HechosOrganizacion,
    ModificacionHumana,
    NaturalezaPlantilla,
    ReglaEvaluada,
    ResultadoAplicabilidad,
    evaluar_ap01_datos_personales,
    evaluar_ap02_trabajadores_100,
    evaluar_ap03_gran_escala,
    evaluar_ap04_interes_legitimo,
    evaluar_ap05_datos_sensibles,
    evaluar_ap06_alto_riesgo_eipd,
    evaluar_ap07_biometria,
    evaluar_ap08_encargados,
    evaluar_ap09_transferencias,
    evaluar_ap10_sector_publico,
    evaluar_ap11_consentimiento,
    evaluar_ap13_ia,
)

_ROOT = Path(__file__).resolve().parents[3]
_ESPECIFICACION_PATH = _ROOT / "data/biblioteca/kit_v1/especificacion/especificacion_biblioteca.json"


# ¤adpa
@dataclass(frozen=True)
class FuentesAplicabilidad:
    """Inyección de compuertas para aislamiento y pruebas."""
    obtener_organizacion: Callable[[AsyncSession, str], Awaitable[Mapping[str, Any]]]
    listar_actividades: Callable[[AsyncSession, str], Awaitable[list[Any]]]
    obtener_gran_escala: Callable[[AsyncSession, str], Awaitable[tuple[bool, int]]]


# ¤adpa
async def _empty_org(_session: AsyncSession, _tenant_id: str) -> Mapping[str, Any]:
    return {}


# ¤adpa
async def _empty_actividades(_session: AsyncSession, _tenant_id: str) -> list[Any]:
    return []


# ¤adpa
async def _empty_gran_escala(_session: AsyncSession, _tenant_id: str) -> tuple[bool, int]:
    return (False, 0)


FUENTES_DEFECTO = FuentesAplicabilidad(
    obtener_organizacion=_empty_org,
    listar_actividades=_empty_actividades,
    obtener_gran_escala=_empty_gran_escala,
)

_PLANTILLAS_CACHE: list[dict[str, Any]] | None = None


# ¤adpa
def cargar_catalogo_plantillas() -> list[dict[str, Any]]:
    """Carga metadatos canónicos de plantillas de la especificación oficial."""
    global _PLANTILLAS_CACHE
    if _PLANTILLAS_CACHE is not None:
        return _PLANTILLAS_CACHE
    if _ESPECIFICACION_PATH.exists():
        with open(_ESPECIFICACION_PATH, encoding="utf-8") as f:
            data = json.load(f)
            _PLANTILLAS_CACHE = data.get("templates", [])
            return _PLANTILLAS_CACHE
    return []


# ¤adpa
async def extraer_hechos(
    session: AsyncSession,
    tenant_id: str,
    fuentes: FuentesAplicabilidad = FUENTES_DEFECTO,
) -> HechosOrganizacion:
    """Extrae hechos consumiendo exclusivamente las compuertas de Organización, RAT y MTGE."""
    # 1. Organización (ORG-14)
    org_datos: Mapping[str, Any] = {}
    try:
        org_datos = await fuentes.obtener_organizacion(session, tenant_id)
    except Exception:
        org_datos = {}

    tamano = org_datos.get("tamano") if org_datos else None
    sector = org_datos.get("sector") if org_datos else None
    num_trabajadores = None

    # 2. RAT (RAT-01)
    actividades_dict: list[dict[str, Any]] | None = None
    rat_cargado = False
    try:
        acts = await fuentes.listar_actividades(session, tenant_id)
        actividades_dict = []
        for a in acts:
            if isinstance(a, dict):
                actividades_dict.append(a)
            elif hasattr(a, "__dict__"):
                actividades_dict.append(vars(a))
            else:
                actividades_dict.append({
                    "id": getattr(a, "id", ""),
                    "nombre": getattr(a, "nombre", ""),
                    "base_legal": str(getattr(a, "base_legal", "")),
                    "datos_sensibles": getattr(a, "datos_sensibles", False),
                    "requiere_eipd": getattr(a, "requiere_eipd", False),
                    "es_gran_escala": getattr(a, "es_gran_escala", False),
                    "encargados": getattr(a, "encargados", []),
                    "transferencia_internacional": getattr(a, "transferencia_internacional", False),
                    "pais_transferencia": getattr(a, "pais_transferencia", ""),
                    "decisiones_automatizadas": getattr(a, "decisiones_automatizadas", False),
                    "categorias_datos": getattr(a, "categorias_datos", []),
                    "nivel_riesgo": getattr(a, "nivel_riesgo", ""),
                    "origen": getattr(a, "origen", ""),
                })
        rat_cargado = True
    except Exception:
        rat_cargado = False
        actividades_dict = None

    # 3. Mitigación Gran Escala (MTGE-01)
    tiene_gran_escala: bool | None = None
    total_gran_escala: int | None = None
    mtge_cargado = False
    try:
        escala, total = await fuentes.obtener_gran_escala(session, tenant_id)
        tiene_gran_escala = escala
        total_gran_escala = total
        mtge_cargado = True
    except Exception:
        mtge_cargado = False
        tiene_gran_escala = None
        total_gran_escala = None

    return HechosOrganizacion(
        tenant_id=tenant_id,
        tamano=tamano,
        num_trabajadores=num_trabajadores,
        sector=sector,
        datos_documentales=org_datos or {},
        rat_cargado=rat_cargado,
        actividades_rat=actividades_dict,
        mtge_cargado=mtge_cargado,
        tiene_gran_escala=tiene_gran_escala,
        total_gran_escala=total_gran_escala,
    )


# ¤adpa
def _determinar_reglas_plantilla(
    codigo: str, hechos: HechosOrganizacion,
) -> tuple[ResultadoAplicabilidad, bool, list[ReglaEvaluada], str]:
    """Evalúa deterministamente las reglas de una plantilla concreta."""
    ap01 = evaluar_ap01_datos_personales(hechos)
    ap02 = evaluar_ap02_trabajadores_100(hechos)
    ap03 = evaluar_ap03_gran_escala(hechos)
    ap04 = evaluar_ap04_interes_legitimo(hechos)
    ap05 = evaluar_ap05_datos_sensibles(hechos)
    ap06 = evaluar_ap06_alto_riesgo_eipd(hechos)
    ap07 = evaluar_ap07_biometria(hechos)
    ap08 = evaluar_ap08_encargados(hechos)
    ap09 = evaluar_ap09_transferencias(hechos)
    ap10 = evaluar_ap10_sector_publico(hechos)
    ap11 = evaluar_ap11_consentimiento(hechos)
    ap13 = evaluar_ap13_ia(hechos)

    # 1. RAT-01
    if codigo == "RAT-01":
        reglas = [ap02, ap03]
        if ap02.resultado == ResultadoAplicabilidad.APLICA:
            return (ResultadoAplicabilidad.APLICA, True, reglas,
                    "Obligación legal expresa: responsable con 100 o más trabajadores (art. 38 RGLOPDP).")
        if ap03.resultado == ResultadoAplicabilidad.APLICA:
            return (ResultadoAplicabilidad.APLICA, True, reglas,
                    "Obligación legal expresa: tratamiento calificado a gran escala (N09 art. 6).")
        if (ap02.resultado == ResultadoAplicabilidad.INFORMACION_INSUFICIENTE or
                ap03.resultado == ResultadoAplicabilidad.INFORMACION_INSUFICIENTE):
            return (ResultadoAplicabilidad.INFORMACION_INSUFICIENTE, False, reglas,
                    "Falta información de trabajadores o evaluación MTGE para determinar obligatoriedad de RAT.")
        return (ResultadoAplicabilidad.NO_APLICA, False, reglas,
                "No concurren los supuestos de obligación legal de RAT (puede adoptarse voluntariamente).")

    # 2. LIA-01
    if codigo == "LIA-01":
        reglas = [ap04]
        if ap04.resultado == ResultadoAplicabilidad.APLICA:
            return (ResultadoAplicabilidad.APLICA, True, reglas,
                    "Aplica ponderación de interés legítimo para los tratamientos propuestos bajo esta base.")
        if ap04.resultado == ResultadoAplicabilidad.INFORMACION_INSUFICIENTE:
            return (ResultadoAplicabilidad.INFORMACION_INSUFICIENTE, False, reglas,
                    "Información insuficiente sobre bases de legitimación de tratamientos.")
        return (ResultadoAplicabilidad.NO_APLICA, False, reglas,
                "No aplica: ningún tratamiento registrado se fundamenta en interés legítimo.")

    # 3. ESC-01
    if codigo == "ESC-01":
        reglas = [ap03]
        if ap03.resultado == ResultadoAplicabilidad.APLICA:
            return (ResultadoAplicabilidad.APLICA, True, reglas,
                    "Aplica evaluación y reporte formal de tratamientos calificados a gran escala.")
        if ap03.resultado == ResultadoAplicabilidad.INFORMACION_INSUFICIENTE:
            return (ResultadoAplicabilidad.INFORMACION_INSUFICIENTE, False, reglas,
                    "Información insuficiente sobre calificación a gran escala.")
        return (ResultadoAplicabilidad.NO_APLICA, False, reglas,
                "No aplica: tratamientos no superan el umbral de gran escala.")

    # 4. EIPD-00 y EIPD-01
    if codigo in ("EIPD-00", "EIPD-01"):
        reglas = [ap06, ap07, ap03, ap13]
        if any(r.resultado == ResultadoAplicabilidad.APLICA for r in reglas):
            return (ResultadoAplicabilidad.APLICA, True, reglas,
                    "Aplica evaluación de impacto (EIPD) por alto riesgo, biometría, IA o gran escala.")
        if any(r.resultado == ResultadoAplicabilidad.INFORMACION_INSUFICIENTE for r in reglas):
            return (ResultadoAplicabilidad.INFORMACION_INSUFICIENTE, False, reglas,
                    "Información insuficiente para evaluar si los tratamientos requieren EIPD.")
        return (ResultadoAplicabilidad.NO_APLICA, False, reglas,
                "No aplica: ningún tratamiento registrado califica para EIPD obligatoria.")

    # 5. GOB-01 y GOB-02 (DPD / Delegado)
    if codigo in ("GOB-01", "GOB-02"):
        reglas = [ap10, ap03]
        if ap10.resultado == ResultadoAplicabilidad.APLICA:
            return (ResultadoAplicabilidad.APLICA, True, reglas,
                    "Obligación legal expresa de nombramiento de DPD para entidades del sector público.")
        if ap03.resultado == ResultadoAplicabilidad.APLICA:
            return (ResultadoAplicabilidad.APLICA, True, reglas,
                    "Obligación de DPD por tratamientos a gran escala conforme a la Res. 0005-R.")
        if ap10.resultado == ResultadoAplicabilidad.INFORMACION_INSUFICIENTE:
            return (ResultadoAplicabilidad.INFORMACION_INSUFICIENTE, False, reglas,
                    "Información insuficiente sobre el sector o actividad de la entidad para designación de DPD.")
        return (ResultadoAplicabilidad.NO_APLICA, False, reglas,
                "No concurren supuestos de obligación directa de DPD (puede nombrarse voluntariamente).")

    # 6. Variantes y contratos específicos
    if codigo == "VAR-BIO":
        return (ap07.resultado, ap07.resultado == ResultadoAplicabilidad.APLICA, [ap07], ap07.explicacion)
    if codigo == "VAR-IA":
        return (ap13.resultado, ap13.resultado == ResultadoAplicabilidad.APLICA, [ap13], ap13.explicacion)
    if codigo in ("PRV-01", "CON-01"):
        return (ap08.resultado, ap08.resultado == ResultadoAplicabilidad.APLICA, [ap08], ap08.explicacion)
    if codigo in ("TRA-01", "TRA-02"):
        return (ap09.resultado, ap09.resultado == ResultadoAplicabilidad.APLICA, [ap09], ap09.explicacion)
    if codigo in ("CNS-01", "CNS-02"):
        return (ap11.resultado, ap11.resultado == ResultadoAplicabilidad.APLICA, [ap11], ap11.explicacion)

    # 7. Plantillas base aplicables a todo tratamiento de datos
    reglas_base = [ap01]
    if ap01.resultado == ResultadoAplicabilidad.APLICA:
        return (ResultadoAplicabilidad.APLICA, False, reglas_base,
                "Aplica como instrumento de cumplimiento para organizaciones que tratan datos personales.")
    if ap01.resultado == ResultadoAplicabilidad.INFORMACION_INSUFICIENTE:
        return (ResultadoAplicabilidad.INFORMACION_INSUFICIENTE, False, reglas_base,
                "Información insuficiente: inventario de actividades de tratamiento pendiente.")
    return (ResultadoAplicabilidad.NO_APLICA, False, reglas_base,
            "No aplica: organización no trata datos personales.")


# ¤adpa
async def listar_modificaciones_humanas(
    session: AsyncSession, tenant_id: str,
) -> dict[str, ModificacionHumana]:
    """Carga todas las correcciones manuales persistidas para el tenant."""
    query = text("""
        SELECT plantilla_codigo, resultado_original, resultado_modificado, motivo,
               evidencia, autor_id, es_obligacion_confirmada, revisor_juridico_id, fecha
        FROM biblioteca_aplicabilidad_modificaciones
        WHERE tenant_id = :tenant_id
    """)
    res = await session.execute(query, {"tenant_id": tenant_id})
    filas = res.mappings().all()
    modificaciones: dict[str, ModificacionHumana] = {}
    for f in filas:
        modificaciones[f["plantilla_codigo"]] = ModificacionHumana(
            resultado_original=ResultadoAplicabilidad(f["resultado_original"]),
            resultado_modificado=ResultadoAplicabilidad(f["resultado_modificado"]),
            motivo=f["motivo"],
            evidencia=f["evidencia"],
            autor_id=f["autor_id"],
            fecha=f["fecha"],
            es_obligacion_confirmada=f["es_obligacion_confirmada"],
            revisor_juridico_id=f["revisor_juridico_id"],
        )
    return modificaciones


# ¤adpa
async def evaluar_aplicabilidad_organizacion(
    session: AsyncSession,
    tenant_id: str,
    fuentes: FuentesAplicabilidad = FUENTES_DEFECTO,
) -> list[EvaluacionPlantilla]:
    """Evalúa la aplicabilidad de todas las plantillas del catálogo de forma determinista y explicable."""
    hechos = await extraer_hechos(session, tenant_id, fuentes)
    modificaciones = await listar_modificaciones_humanas(session, tenant_id)
    catalogo = cargar_catalogo_plantillas()

    evaluaciones: list[EvaluacionPlantilla] = []
    for item in catalogo:
        codigo = item.get("codigo") or item.get("template_id") or ""
        if not codigo:
            continue
        nombre = item.get("nombre") or codigo
        tipo = item.get("tipo") or "Documento"
        familia = item.get("familia") or "General"
        formato = item.get("formato") or "MD"
        naturaleza = item.get("naturaleza") or "Obligación legal"
        fuentes_lista = [f.strip() for f in str(item.get("fuentes", "")).split(";") if f.strip()]
        version = str(item.get("version") or "1.0")

        res_calc, es_ob, reglas_eval, motivo = _determinar_reglas_plantilla(codigo, hechos)

        faltantes: list[str] = []
        for r in reglas_eval:
            faltantes.extend(r.hechos_faltantes)
        faltantes = sorted(list(set(faltantes)))

        hechos_rel: dict[str, Any] = {}
        for r in reglas_eval:
            hechos_rel.update(r.hechos_analizados)

        mod = modificaciones.get(codigo)
        resultado_final = mod.resultado_modificado if mod else res_calc

        evaluaciones.append(EvaluacionPlantilla(
            codigo=codigo,
            nombre=nombre,
            resultado=resultado_final,
            resultado_calculado=res_calc,
            tipo=tipo,
            familia=familia,
            formato=formato,
            naturaleza=naturaleza,
            es_obligacion=es_ob,
            fuentes_normativas=fuentes_lista,
            version_regla=version,
            motivo_recomendacion=motivo,
            hechos_relevantes=hechos_rel,
            hechos_faltantes=faltantes,
            reglas_evaluadas=reglas_eval,
            modificacion_humana=mod,
        ))

    return evaluaciones


# ¤adpa
async def registrar_modificacion_aplicabilidad(
    session: AsyncSession,
    tenant_id: str,
    actor_id: str,
    plantilla_codigo: str,
    resultado_modificado: ResultadoAplicabilidad,
    motivo: str,
    evidencia: str,
    es_juridico: bool = False,
    revisor_juridico_id: str | None = None,
    fuentes: FuentesAplicabilidad = FUENTES_DEFECTO,
) -> ModificacionHumana:
    """Registra una corrección humana exigiendo revisión jurídica si es obligación confirmada."""
    if resultado_modificado not in (ResultadoAplicabilidad.APLICA, ResultadoAplicabilidad.NO_APLICA):
        raise ErrorNegocio("BIB_MODIFICACION_INVALIDA", "El resultado modificado solo puede ser 'Aplica' o 'No aplica'.")
    if not motivo or len(motivo.strip()) < 3:
        raise ErrorNegocio("BIB_MODIFICACION_INVALIDA", "El motivo debe tener al menos 3 caracteres.")
    if not evidencia or len(evidencia.strip()) < 1:
        raise ErrorNegocio("BIB_MODIFICACION_INVALIDA", "Debe adjuntar una evidencia justificativa.")

    # Calcular resultado original
    hechos = await extraer_hechos(session, tenant_id, fuentes)
    res_orig, es_obligacion, _, _ = _determinar_reglas_plantilla(plantilla_codigo, hechos)

    # Invariante 3: exclusión de obligación confirmada exige revisión jurídica
    if es_obligacion and res_orig == ResultadoAplicabilidad.APLICA and resultado_modificado == ResultadoAplicabilidad.NO_APLICA:
        if not (es_juridico or revisor_juridico_id):
            raise ErrorNegocio(
                "BIB_EXCLUSION_EXIGE_JURIDICO",
                "Una obligación legal confirmada exige revisión jurídica para ser excluida.",
            )

    ahora = datetime.now(timezone.utc)
    rev_id = revisor_juridico_id or (actor_id if es_juridico else None)
    id_mod = str(uuid4())

    query = text("""
        INSERT INTO biblioteca_aplicabilidad_modificaciones
            (id, tenant_id, plantilla_codigo, resultado_original, resultado_modificado,
             motivo, evidencia, autor_id, es_obligacion_confirmada, revisor_juridico_id, fecha, creado_en, actualizado_en)
        VALUES
            (:id, :tenant_id, :plantilla_codigo, :resultado_original, :resultado_modificado,
             :motivo, :evidencia, :autor_id, :es_obligacion_confirmada, :revisor_juridico_id, :fecha, :ahora, :ahora)
        ON CONFLICT (tenant_id, plantilla_codigo) DO UPDATE
        SET resultado_modificado = EXCLUDED.resultado_modificado,
            motivo = EXCLUDED.motivo,
            evidencia = EXCLUDED.evidencia,
            autor_id = EXCLUDED.autor_id,
            es_obligacion_confirmada = EXCLUDED.es_obligacion_confirmada,
            revisor_juridico_id = EXCLUDED.revisor_juridico_id,
            fecha = EXCLUDED.fecha,
            actualizado_en = EXCLUDED.actualizado_en
    """)

    await session.execute(query, {
        "id": id_mod,
        "tenant_id": tenant_id,
        "plantilla_codigo": plantilla_codigo,
        "resultado_original": res_orig.value,
        "resultado_modificado": resultado_modificado.value,
        "motivo": motivo.strip(),
        "evidencia": evidencia.strip(),
        "autor_id": actor_id,
        "es_obligacion_confirmada": es_obligacion,
        "revisor_juridico_id": rev_id,
        "fecha": ahora,
        "ahora": ahora,
    })
    await session.commit()

    return ModificacionHumana(
        resultado_original=res_orig,
        resultado_modificado=resultado_modificado,
        motivo=motivo.strip(),
        evidencia=evidencia.strip(),
        autor_id=actor_id,
        fecha=ahora,
        es_obligacion_confirmada=es_obligacion,
        revisor_juridico_id=rev_id,
    )
