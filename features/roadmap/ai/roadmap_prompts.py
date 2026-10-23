# ¤roadmap ¤copiloto-ia
"""Prompts versionados para generación fiable con IA.

Incluye el esquema JSON estricto de RoadmapDocument en el prompt del sistema
para garantizar que el modelo produzca una estructura conforme a Pydantic (Aporte 94).
"""
import json
from features.roadmap.domain.models import RoadmapDocument

def get_roadmap_schema_str() -> str:
    """Devuelve la especificación del esquema JSON de RoadmapDocument formateada."""
    schema = RoadmapDocument.model_json_schema()
    return json.dumps(schema, ensure_ascii=False, indent=2)

SYSTEM_PROMPT = f"""Eres consultor senior de protección de datos LOPDP Ecuador/GDPR.
Recibes un assessment y variables de planeación.
Devuelve SOLO un objeto JSON estrictamente conforme al siguiente esquema JSON (RoadmapDocument):

ESQUEMA OBLIGATORIO:
{get_roadmap_schema_str()}

REGLAS CRÍTICAS DE NEGOCIO:
1. Prioriza brechas críticas estructurales.
2. Usa ÚNICAMENTE controles P1-P73, escritos SIN ceros a la izquierda (P1, P5, P73; nunca P01),
   y dimensiones D01-D10, escritas SIEMPRE con dos dígitos (D01, D05, D10).
3. Cada tarea debe tener entregable, evidencia y KPI verificables.
4. Respeta plazo, presupuesto, equipo, DPO e idioma.
5. No inventes controles ni agregues texto explicativo fuera del JSON."""

USER_PROMPT_TEMPLATE = """Genera una hoja de ruta personalizada.
assessment_json: {assessment_json}
variables_usuario_json: {variables_usuario_json}
Idioma: {idioma}. Devuelve únicamente JSON válido que cumpla el esquema."""


def build_roadmap_prompt(assessment: dict, variables: dict) -> str:
    return USER_PROMPT_TEMPLATE.format(
        assessment_json=json.dumps(assessment, ensure_ascii=False),
        variables_usuario_json=json.dumps(variables, ensure_ascii=False),
        idioma=variables.get("idioma", "ES"),
    )
