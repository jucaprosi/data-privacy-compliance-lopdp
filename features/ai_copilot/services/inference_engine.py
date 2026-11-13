"""Motor del copiloto de mitigación: genera el plan solo por la compuerta de inferencia (IA-03), sin clave ni plan simulado."""
import logging

from features.ai_copilot.domain.models import AnalisisDiagnosticoRequest, PlanMitigacionResponse
from features.ai_copilot.domain.sanitizer import LLMDataSanitizer
from app_core.pasillo import niif18
from app_core.pasillo import inferencia as pasillo_inferencia

logger = logging.getLogger("jubys_lopdp_json_logger")

MODELO = "gemini-2.5-flash"


async def _invocar_compuerta(sistema: str, usuario: str, org_id: str) -> PlanMitigacionResponse:
    """Única llamada a la compuerta. Sin traza IA-10: pendiente de ampliación de propiedad (cambiar a generar_trazado aquí)."""
    return await pasillo_inferencia.generar_estructurado(
        sistema, usuario, PlanMitigacionResponse, modelo=MODELO, org_id=org_id,
    )


async def generar_plan_mitigacion(
    request: AnalisisDiagnosticoRequest, org_id: str | None = None,
) -> PlanMitigacionResponse:
    """Genera el plan estructurado. Sin organización o sin Vertex lanza InferenciaNoDisponible; nunca inventa un plan."""
    no_disponible, _ = pasillo_inferencia.errores()
    if not org_id:
        raise no_disponible()

    # K-Anonimato (Data Sanitizer): pre-inferencia
    brechas_seguras = LLMDataSanitizer().sanitize_dict({"brechas": request.brechas_identificadas})["brechas"]

    system_prompt = (
        f"Actúa como Auditor GRC Senior. "
        f"Tu misión es evaluar la normativa {request.normativa} "
        f"y proponer un plan de mitigación estructurado. "
        f"Debes reaccionar dinámicamente: si es LOPDP, enfócate en privacidad y protección de datos; "
        f"si es NIIF 18, enfócate en presentación y revelación financiera. "
        f"Severidad según el scoring global del diagnóstico."
    )
    if "NIIF" in request.normativa.upper():
        system_prompt += (
            f"\n\n--- INICIO CONTEXTO DOCTRINAL NIIF 18 ---\n"
            f"{niif18.contexto_doctrinal()}\n"
            f"--- FIN CONTEXTO DOCTRINAL NIIF 18 ---\n"
            f"Actúa estrictamente como un Auditor Especialista en NIIF 18."
        )
    user_prompt = (
        f"Normativa: {request.normativa}\n"
        f"Brechas identificadas: {brechas_seguras}\n"
        f"Scoring Global: {request.scoring_global}"
    )
    try:
        return await _invocar_compuerta(system_prompt, user_prompt, org_id)
    except no_disponible:
        raise
    except Exception as exc:  # noqa: BLE001 — falla cerrada; solo el tipo, nunca el mensaje
        logger.error("Fallo de la inferencia del copiloto: %s", type(exc).__name__)
        raise no_disponible() from exc
