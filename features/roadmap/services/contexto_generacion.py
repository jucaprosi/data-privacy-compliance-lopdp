# ¤roadmap ¤copiloto-ia ¤adpa
"""Armado del contexto real en el servidor para la generación de la hoja de ruta (RM-19).

Decisión del propietario (2026-10-25):
- El catálogo P1-P80 son las 80 preguntas del banco de la plataforma.
- El servidor es la fuente de verdad: el contexto de generación se arma exclusivamente
  desde la base de datos de la organización del usuario (respuestas del diagnóstico DIAG-01,
  matriz de madurez por dimensión, brechas críticas, sector y tamaño del tenant, y actividades
  del RAT con datos sensibles o a gran escala RAT-01).
- Minimización estricta: a la IA solo van códigos, estados y nombres de actividad,
  pasados por ner_sanitizer.py; nunca datos de titulares ni de otra organización.
- Si no hay diagnóstico guardado para la organización, se levanta SinDiagnosticoError:
  «complete el diagnóstico antes de generar».
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from features.diagnostico import diagnostico_service
from features.rat import rat_service

logger = logging.getLogger(__name__)


class SinDiagnosticoError(Exception):
    """Error cuando la organización no ha completado el diagnóstico previo a generar la hoja de ruta."""
    pass


async def armar_contexto_generacion(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
) -> dict[str, Any]:
    """Recupera y estructura el contexto real del tenant para la generación de la hoja de ruta.

    Levanta SinDiagnosticoError si la organización no tiene respuestas de diagnóstico registradas.
    """
    # 1. Obtener respuestas guardadas del diagnóstico (DIAG-01)
    respuestas_db = await diagnostico_service.listar_respuestas(session, tenant_id, user_id)
    if not respuestas_db:
        raise SinDiagnosticoError("complete el diagnóstico antes de generar")

    # Mapeo del catálogo P1-P80 para enriquecer
    catalogo = diagnostico_service.obtener_catalogo_controles_p1_p80()
    catalogo_por_id = {c["pregunta_id"]: c for c in catalogo}

    # 2. Convertir a RespuestaControl para evaluar agregación y dimensiones
    respuestas_control: list[diagnostico_service.RespuestaControl] = []
    respuestas_por_control: list[dict[str, Any]] = []

    # Mapeo de estados de texto a EstadoCumplimiento
    estado_map = {
        "conforme": diagnostico_service.EstadoCumplimiento.CONFORME,
        "parcial": diagnostico_service.EstadoCumplimiento.PARCIAL,
        "no conforme": diagnostico_service.EstadoCumplimiento.NO_CONFORME,
        "no_conforme": diagnostico_service.EstadoCumplimiento.NO_CONFORME,
        "pendiente": diagnostico_service.EstadoCumplimiento.PENDIENTE,
    }

    sanitizer = diagnostico_service.NERSanitizer()

    for r in respuestas_db:
        pid = r["pregunta_id"]
        info_cat = catalogo_por_id.get(pid, {})
        control_nombre = r.get("control") or info_cat.get("control") or f"Control {pid}"
        dimension_id = r.get("dimension") or info_cat.get("dimension") or "D01"
        codigo_p = f"P{pid}"
        estado_raw = str(r.get("estado", "")).strip().lower()
        cumple = estado_map.get(estado_raw, diagnostico_service.EstadoCumplimiento.PENDIENTE)

        evidencia_val = r.get("nivel_evidencia", 0)
        if isinstance(evidencia_val, str) and evidencia_val.upper().startswith("E"):
            try:
                evidencia_nivel = int(evidencia_val[1:])
            except ValueError:
                evidencia_nivel = 0
        else:
            try:
                evidencia_nivel = int(evidencia_val or 0)
            except (ValueError, TypeError):
                evidencia_nivel = 0

        criticidad = int(r.get("criticidad") or 3)
        es_critica = bool(r.get("es_critica", False))

        resp_ctrl = diagnostico_service.RespuestaControl(
            pregunta_id=pid,
            cumple=cumple,
            evidencia_nivel=evidencia_nivel,
            criticidad=criticidad,
            es_critica=es_critica,
            dimension_id=dimension_id,
            control=control_nombre,
        )
        respuestas_control.append(resp_ctrl)

        respuestas_por_control.append({
            "codigo": codigo_p,
            "pregunta_id": pid,
            "control": control_nombre,
            "dimension": dimension_id,
            "estado": r.get("estado", "Pendiente"),
            "nivel_evidencia": evidencia_nivel,
            "criticidad": criticidad,
            "es_critica": es_critica,
        })

    # 3. Calcular madurez por dimensión y brechas
    resultado_assessment = diagnostico_service.evaluar_assessment_por_dimension(respuestas_control)

    madurez_por_dimension = [
        {
            "id": d.id,
            "nombre": d.nombre,
            "score": round(d.score, 1),
            "nivel": d.nivel,
            "nivel_etiqueta": d.nivel_etiqueta,
            "brechas_criticas": d.brechas_criticas,
            "brechas_altas": d.brechas_altas,
        }
        for d in resultado_assessment.dimensiones
    ]

    brechas_criticas = [
        {
            "codigo": f"P{b.pregunta_id}",
            "control": b.control,
            "dimension": b.dimension_id,
            "severidad": b.severidad.value if hasattr(b.severidad, "value") else str(b.severidad),
            "es_estructural": b.es_estructural,
            "riesgo": round(b.riesgo, 1),
        }
        for b in resultado_assessment.brechas
        if (b.severidad.value if hasattr(b.severidad, "value") else str(b.severidad)) in ("Crítico", "Alto") or b.es_estructural
    ]

    # 4. Ficha organizacional (sector y tamaño del tenant)
    res_tenant = await session.execute(
        text("SELECT sector, tamano, razon_social, nombre_comercial FROM tenants WHERE id = :tid"),
        {"tid": tenant_id},
    )
    tenant_row = res_tenant.mappings().first()
    sector = tenant_row["sector"] if tenant_row and tenant_row["sector"] else "No configurado"
    tamano = tenant_row["tamano"] if tenant_row and tenant_row["tamano"] else "No configurado"

    # 5. Actividades del RAT con datos sensibles o a gran escala (RAT-01)
    actividades_rat = await rat_service.listar_actividades_rat(session, tenant_id)
    rat_relevantes: list[dict[str, Any]] = []

    for act in actividades_rat:
        if act.datos_sensibles or act.es_gran_escala or act.requiere_eipd:
            # Sanitizar nombre de actividad por si contiene PII
            nombre_saneado = sanitizer.sanitize(act.nombre)
            rat_relevantes.append({
                "codigo": act.codigo or f"RAT-{act.id[:8]}",
                "nombre": nombre_saneado,
                "datos_sensibles": act.datos_sensibles,
                "es_gran_escala": act.es_gran_escala,
                "requiere_eipd": act.requiere_eipd,
            })

    return {
        "tenant_id": tenant_id,
        "ficha_organizacion": {
            "sector": sector,
            "tamano": tamano,
        },
        "score_global": round(resultado_assessment.score_ponderado, 1),
        "nivel_madurez": resultado_assessment.nivel_ajustado,
        "nivel_madurez_etiqueta": resultado_assessment.nivel_ajustado_etiqueta,
        "madurez_por_dimension": madurez_por_dimension,
        "brechas_criticas": brechas_criticas,
        "respuestas_diagnostico": respuestas_por_control,
        "actividades_rat_criticas": rat_relevantes,
    }
