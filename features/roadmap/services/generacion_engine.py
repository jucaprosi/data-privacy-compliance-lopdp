# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤roadmap ¤copiloto-ia
"""Motor de generación con IA de hojas de ruta (sala ADPA: Hoja de Ruta).

Implementa la generación síncrona fiable con IA (generate_roadmap_document):
- Inclusión obligatoria del esquema de RoadmapDocument en el prompt.
- Detección de salida truncada (finish_reason = 'length').
- Reintento correctivo enviando el esquema y el error específico de validación de Pydantic.
- Límite de tiempo explícito en la llamada.
- Falla cerrado ante indisponibilidad de la compuerta (InferenciaNoDisponible).
- Integración determinista con PlanCifrado (RM-26 / IA-06): las cifras, horas y prioridades no vienen del modelo.
"""
from __future__ import annotations

from datetime import date
import json
import logging
from typing import Callable, Optional

from pydantic import ValidationError

from app_core.pasillo import inferencia as pasillo_inferencia
from features.roadmap.ai.client import (
    DEFAULT_MAX_TOKENS,
    DEFAULT_TIMEOUT_SECONDS,
    LLMTimeoutError,
    TruncatedOutputError,
    call_roadmap_llm,
)
from features.roadmap.ai.roadmap_prompts import (
    SYSTEM_PROMPT,
    build_roadmap_prompt,
    get_roadmap_schema_str,
)
from features.roadmap.domain.esfuerzo_controles import PlanCifrado
from features.roadmap.domain.models import RoadmapDocument, TaskPriority
from features.roadmap.services.cifras_engine import cifrar_plan

logger = logging.getLogger(__name__)


class GeneracionRoadmapError(Exception):
    """Fallo en el proceso de generación con IA."""
    pass


def ensamblar_plan_cifrado_con_texto(
    plan_cifrado: PlanCifrado,
    doc: RoadmapDocument,
) -> RoadmapDocument:
    """Une las cifras deterministas de PlanCifrado con el texto redactado por el modelo (IA-06).

    R2: El modelo no decide cifras. Prioridad, horas y fechas salen del PlanCifrado.
    R3: Correspondencia exacta por control_ref.
    """
    controles_plan = {c.control_ref: c for ola in plan_cifrado.olas for c in ola.controles}
    tareas_doc = {t.control_ref: t for ola in doc.olas for t in ola.tareas}

    if set(controles_plan.keys()) != set(tareas_doc.keys()):
        faltantes = set(controles_plan.keys()) - set(tareas_doc.keys())
        sobrantes = set(tareas_doc.keys()) - set(controles_plan.keys())
        raise GeneracionRoadmapError(
            f"Correspondencia de controles no coincide entre el plan cifrado y el modelo. "
            f"Faltantes en modelo: {faltantes}, Sobrantes en modelo: {sobrantes}"
        )

    # Sobrescribir cifras, prioridades y fechas desde el PlanCifrado
    for ola_cifrada in plan_cifrado.olas:
        for c in ola_cifrada.controles:
            t = tareas_doc[c.control_ref]
            t.prioridad = TaskPriority(c.prioridad)
            t.esfuerzo_estimado_horas = c.horas
            t.fecha_inicio = ola_cifrada.inicio.isoformat()
            t.fecha_fin = ola_cifrada.fin.isoformat()

    criticos = sum(1 for c in controles_plan.values() if c.prioridad == "critica")
    altos = sum(1 for c in controles_plan.values() if c.prioridad == "alta")
    doc.kpis_globales.criticos_totales = criticos
    doc.kpis_globales.altos_totales = altos

    return doc


def generate_roadmap_document(
    assessment: dict,
    variables: dict,
    roadmap_id: str,
    tenant_id: str,
    *,
    llm_caller: Optional[Callable[[str, str], str]] = None,
    max_retries: int = 2,
    plan_cifrado: Optional[PlanCifrado] = None,
    hoy: Optional[date] = None,
) -> RoadmapDocument:
    """Genera y valida un RoadmapDocument utilizando IA y reintentos correctivos.

    Si la respuesta es inválida sintáctica o esquemáticamente, reintenta enviando
    el error exacto y el esquema para que el modelo corrija su salida.
    """
    InferenciaNoDisponible, _ = pasillo_inferencia.errores()

    if plan_cifrado is None and assessment.get("respuestas_diagnostico"):
        try:
            class _VarsAdapter:
                def __init__(self, d: dict):
                    self.plazo_meses = int(d.get("plazo_meses", 6))

            plan_cifrado = cifrar_plan(assessment, _VarsAdapter(variables), hoy or date.today())
        except Exception as exc:
            logger.warning("No se pudo cifrar el plan desde el contexto: %s", exc)
            plan_cifrado = None

    initial_user_prompt = build_roadmap_prompt(assessment, variables)
    current_user_prompt = initial_user_prompt
    last_error: Optional[Exception] = None

    for intento in range(max_retries):
        try:
            if llm_caller is not None:
                raw_response = llm_caller(SYSTEM_PROMPT, current_user_prompt)
            else:
                raw_response = call_roadmap_llm(
                    system_prompt=SYSTEM_PROMPT,
                    user_prompt=current_user_prompt,
                    max_tokens=DEFAULT_MAX_TOKENS,
                    timeout=DEFAULT_TIMEOUT_SECONDS,
                    org_id=tenant_id,
                )

            data = json.loads(raw_response)
            data["roadmap_id"] = roadmap_id
            data["tenant_id"] = tenant_id

            doc = RoadmapDocument.model_validate(data)

            if plan_cifrado is not None and plan_cifrado.olas:
                doc = ensamblar_plan_cifrado_con_texto(plan_cifrado, doc)

            return doc

        except InferenciaNoDisponible:
            # Falla cerrado: si la compuerta no está disponible, no se reintenta ni se devuelve plan simulado
            raise

        except LLMTimeoutError:
            # IA-18 R8: el único reintento ante un fallo de Vertex es el de la compuerta (R2 y R3)
            raise

        except TruncatedOutputError as exc:
            logger.warning(
                "Intento %d de generación de roadmap truncado por tokens: %s",
                intento + 1,
                exc,
            )
            last_error = exc
            current_user_prompt = (
                initial_user_prompt
                + "\n\nERROR PREVIO: La respuesta anterior fue truncada por límite de longitud."
                + f"\nPor favor genera un documento conciso manteniendo las olas prioritarias y cumpliendo estrictamente el esquema:\n{get_roadmap_schema_str()}"
            )

        except (json.JSONDecodeError, ValidationError, Exception) as exc:
            logger.warning(
                "Intento %d de generación de roadmap falló con error: %s",
                intento + 1,
                exc,
            )
            last_error = exc
            error_msg = str(exc)
            current_user_prompt = (
                initial_user_prompt
                + "\n\nCORRECCIÓN REQUERIDA (Intento previo fallido):"
                + "\nLa salida anterior NO cumplió con las especificaciones y produjo el siguiente error:"
                + f"\n{error_msg}"
                + f"\n\nAsegúrate de devolver ÚNICAMENTE un JSON válido que cumpla estrictamente este esquema:\n{get_roadmap_schema_str()}"
            )

    raise GeneracionRoadmapError(
        f"No se pudo generar un RoadmapDocument válido tras {max_retries} intentos. Último error: {last_error}"
    )
