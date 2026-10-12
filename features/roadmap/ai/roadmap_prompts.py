"""Prompts versionados: la salida del modelo siempre se valida con Pydantic."""
SYSTEM_PROMPT = """Eres consultor senior de protección de datos LOPDP Ecuador/GDPR. Recibes un assessment y variables de planeación. Devuelve SOLO JSON conforme al esquema RoadmapDocument. Prioriza brechas críticas estructurales, usa únicamente controles P1-P73 y dimensiones D01-D10; cada tarea debe tener entregable, evidencia y KPI verificables. Respeta plazo, presupuesto, equipo, DPO e idioma. No inventes controles ni texto fuera del JSON."""
USER_PROMPT_TEMPLATE = """Genera una hoja de ruta personalizada.
assessment_json: {assessment_json}
variables_usuario_json: {variables_usuario_json}
Idioma: {idioma}. Devuelve únicamente JSON válido."""

def build_roadmap_prompt(assessment: dict, variables: dict) -> str:
    import json
    return USER_PROMPT_TEMPLATE.format(assessment_json=json.dumps(assessment, ensure_ascii=False), variables_usuario_json=json.dumps(variables, ensure_ascii=False), idioma=variables.get("idioma", "ES"))
