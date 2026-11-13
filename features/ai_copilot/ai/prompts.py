# ¤gemini-vertex ¤arbitro
"""Prompts versionados del copiloto de mitigación (IA-10, invariante 64). Las versiones anteriores no se borran."""
from app_core.pasillo import inferencia as pasillo_inferencia

PLAN_MITIGACION_V1 = pasillo_inferencia.prompt_versionado(
    "ai_copilot.plan_mitigacion",
    1,
    (
        "Actúa como Auditor GRC Senior. Tu misión es evaluar la normativa indicada y proponer un plan de "
        "mitigación estructurado. Debes reaccionar dinámicamente: si es LOPDP, enfócate en privacidad y "
        "protección de datos; si es NIIF 18, enfócate en presentación y revelación financiera. "
        "Severidad según el scoring global del diagnóstico."
    ),
    (
        "{contexto_doctrinal}"
        "Normativa: {normativa}\n"
        "Brechas identificadas: {brechas}\n"
        "Scoring Global: {scoring_global}"
    ),
)

VERSIONES = {1: PLAN_MITIGACION_V1}
VIGENTE = PLAN_MITIGACION_V1
