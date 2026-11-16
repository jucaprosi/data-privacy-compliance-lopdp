"""Motor del copiloto de mitigación: genera el plan solo por la compuerta de inferencia (IA-03), sin clave ni plan simulado."""
import logging

from features.ai_copilot.domain.models import AnalisisDiagnosticoRequest, PlanMitigacionResponse
from features.ai_copilot.domain.sanitizer import LLMDataSanitizer
from app_core.pasillo import niif18
from features.ai_copilot.ai.prompts import VIGENTE
from app_core.pasillo import inferencia as pasillo_inferencia

logger = logging.getLogger("jubys_lopdp_json_logger")

MODELO = "gemini-2.5-flash"


async def _invocar_compuerta(valores: dict, org_id: str):
    """Única llamada a la compuerta, con traza IA-10: devuelve (plan, traza)."""
    return await pasillo_inferencia.generar_trazado(
        VIGENTE, valores, PlanMitigacionResponse, modelo=MODELO, org_id=org_id,
    )


async def generar_plan_mitigacion(
    request: AnalisisDiagnosticoRequest, org_id: str | None = None,
):
    """Devuelve (plan, traza). Sin organización o sin Vertex lanza InferenciaNoDisponible; nunca inventa un plan."""
    no_disponible, _ = pasillo_inferencia.errores()
    if not org_id:
        raise no_disponible()

    # K-Anonimato (Data Sanitizer): pre-inferencia
    brechas_seguras = LLMDataSanitizer().sanitize_dict({"brechas": request.brechas_identificadas})["brechas"]
    contexto = ""
    if "NIIF" in request.normativa.upper():
        contexto = (
            "--- INICIO CONTEXTO DOCTRINAL NIIF 18 ---\n"
            f"{niif18.contexto_doctrinal()}\n"
            "--- FIN CONTEXTO DOCTRINAL NIIF 18 ---\n"
            "Actúa estrictamente como un Auditor Especialista en NIIF 18.\n\n"
        )
    valores = {
        "contexto_doctrinal": contexto,
        "normativa": request.normativa,
        "brechas": brechas_seguras,
        "scoring_global": request.scoring_global,
    }
    try:
        return await _invocar_compuerta(valores, org_id)
    except no_disponible:
        raise
    except Exception as exc:  # noqa: BLE001 — falla cerrada; solo el tipo, nunca el mensaje
        logger.error("Fallo de la inferencia del copiloto: %s", type(exc).__name__)
        raise no_disponible() from exc
