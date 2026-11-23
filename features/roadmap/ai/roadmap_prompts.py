# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤roadmap ¤copiloto-ia
"""Prompts versionados para generación fiable con IA.

Incluye el esquema JSON estricto de RoadmapDocument en el prompt del sistema
para garantizar que el modelo produzca una estructura conforme a Pydantic (Aporte 94).
RM-19: Incluye el catálogo P1-P80 del banco de la plataforma con el nombre de cada control
y la regla de citar la brecha que atiende cada tarea.
IA-06: Esquema de solo texto para el modelo (las cifras las calcula cifrar_plan).
"""
import json
from typing import Any
from pydantic import BaseModel, Field

# --- INICIO ADPA-04 ---
from app_core.pasillo import diagnostico as pasillo_diagnostico
# --- FIN ADPA-04 ---
from app_core.pasillo import inferencia as pasillo_inferencia
from features.roadmap.domain.models import RoadmapDocument


# === Esquema de solo texto (IA-06) ===
class TareaTextoRoadmap(BaseModel):
    control_ref: str
    titulo: str
    descripcion: str
    entregable: str
    evidencia_requerida: list[str] = Field(default_factory=list)
    kpi: str = ""


class OlaTextoRoadmap(BaseModel):
    nombre: str
    objetivo: str
    tareas: list[TareaTextoRoadmap] = Field(default_factory=list)


class RoadmapTextoRespuesta(BaseModel):
    resumen_ejecutivo: str
    olas: list[OlaTextoRoadmap] = Field(default_factory=list)


def get_roadmap_schema_str() -> str:
    """Devuelve la especificación del esquema JSON de RoadmapDocument formateada."""
    schema = RoadmapDocument.model_json_schema()
    return json.dumps(schema, ensure_ascii=False, indent=2)


def get_roadmap_texto_schema_str() -> str:
    """Devuelve la especificación del esquema de solo texto formateada (IA-06)."""
    schema = RoadmapTextoRespuesta.model_json_schema()
    return json.dumps(schema, ensure_ascii=False, indent=2)


def get_catalogo_formateado_str() -> str:
    """Formatea el catálogo canónico P1-P80 para el prompt de la IA."""
    try:
        controles = pasillo_diagnostico.catalogo_de_controles()
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


PROMPT_ID = "roadmap.generacion"
PROMPT_VERSION = 1

try:
    VIGENTE = pasillo_inferencia.prompt_versionado(
        id=PROMPT_ID,
        version=PROMPT_VERSION,
        sistema=SYSTEM_PROMPT,
        plantilla=USER_PROMPT_TEMPLATE,
    )
except Exception:
    VIGENTE = None
