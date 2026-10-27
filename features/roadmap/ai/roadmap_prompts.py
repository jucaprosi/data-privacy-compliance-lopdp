# ¤roadmap ¤copiloto-ia
"""Prompts versionados para generación fiable con IA.

Incluye el esquema JSON estricto de RoadmapDocument en el prompt del sistema
para garantizar que el modelo produzca una estructura conforme a Pydantic (Aporte 94).
RM-19: Incluye el catálogo P1-P80 del banco de la plataforma con el nombre de cada control
y la regla de citar la brecha que atiende cada tarea.
"""
import json
from features.roadmap.domain.models import RoadmapDocument
from features.diagnostico import diagnostico_service


def get_roadmap_schema_str() -> str:
    """Devuelve la especificación del esquema JSON de RoadmapDocument formateada."""
    schema = RoadmapDocument.model_json_schema()
    return json.dumps(schema, ensure_ascii=False, indent=2)


def get_catalogo_formateado_str() -> str:
    """Formatea el catálogo canónico P1-P80 para el prompt de la IA."""
    try:
        controles = diagnostico_service.obtener_catalogo_controles_p1_p80()
        lineas = [f"- {c['codigo']} ({c['dimension']}): {c['control']}" for c in controles]
        return "\n".join(lineas)
    except Exception:
        return "- P1 a P80: Controles del SGPDP (D01-D10)"


SYSTEM_PROMPT = f"""Eres consultor senior de protección de datos LOPDP Ecuador/GDPR.
Recibes un assessment y variables de planeación.
Devuelve SOLO un objeto JSON estrictamente conforme al siguiente esquema JSON (RoadmapDocument):

ESQUEMA OBLIGATORIO:
{get_roadmap_schema_str()}

CATÁLOGO CANÓNICO DE CONTROLES P1-P80:
{get_catalogo_formateado_str()}

REGLAS CRÍTICAS DE NEGOCIO:
1. Prioriza brechas críticas estructurales.
2. Usa ÚNICAMENTE controles P1-P80, escritos SIN ceros a la izquierda (P1, P5, P80; nunca P01),
   y dimensiones D01-D10, escritas SIEMPRE con dos dígitos (D01, D05, D10).
3. Cada tarea debe citar la brecha o control que atiende (usando su código P y nombre del catálogo).
4. Cada tarea debe tener entregable, evidencia y KPI verificables.
5. Respeta plazo, presupuesto, equipo, DPO e idioma.
6. No inventes controles ni agregues texto explicativo fuera del JSON."""

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
