# ¤¤llm_privacy_tests
import pytest
import os
import logging
from features.ai_copilot.domain.sanitizer import LLMDataSanitizer
from features.ai_copilot.domain.models import AnalisisDiagnosticoRequest
from features.ai_copilot.services.inference_engine import generar_plan_mitigacion, APILoggerFilter

# ¤test-sanitizer-removes-llm-pii
def test_sanitizer_removes_llm_pii():
    """Valida que el sanitizador reemplaza correos, IPs, empresas y nombres por tokens genéricos."""
    sanitizer = LLMDataSanitizer()
    texto_crudo = "La empresa Acme Corp sufrió una brecha. Juan Perez desde la IP 192.168.1.1 reportó el incidente a juan@acme.com."
    
    texto_seguro = sanitizer.sanitize_text(texto_crudo)
    
    # Nombres
    assert "Juan Perez" not in texto_seguro
    assert "[PERSONA_1]" in texto_seguro
    
    # Empresa
    assert "Acme Corp" not in texto_seguro
    assert "[EMPRESA_1]" in texto_seguro
    
    # IPs
    assert "192.168.1.1" not in texto_seguro
    assert "[IP_1]" in texto_seguro
    
    # Correos
    assert "juan@acme.com" not in texto_seguro
    assert "[EMAIL_1]" in texto_seguro

# ¤test-sanitizer-dict-recursive
def test_sanitizer_dict_recursive():
    """Valida que la sanitización recursiva de diccionarios funciona correctamente."""
    sanitizer = LLMDataSanitizer()
    data = {
        "user": "Carlos Slim",
        "company": {"name": "America Movil S.A."},
        "emails": ["carlos@telmex.com", "admin@telmex.com"]
    }
    
    safe_data = sanitizer.sanitize_dict(data)
    assert safe_data["user"] == "[PERSONA_1]"
    assert safe_data["company"]["name"] == "[EMPRESA_1]"
    assert safe_data["emails"][0] == "[EMAIL_1]"
    assert safe_data["emails"][1] == "[EMAIL_2]"

@pytest.mark.asyncio
# ¤test-generar-plan-mitigacion-anonymizes-data
async def test_generar_plan_mitigacion_anonymizes_data(monkeypatch):
    """Valida que el request al motor de inferencia es interceptado y anonimizado."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    request = AnalisisDiagnosticoRequest(
        id_diagnostico="test-123",
        normativa="LOPDP",
        brechas_identificadas=["Base de datos de empleados de Globex Corp expuesta por Homero Simpson en 10.0.0.5"],
        scoring_global=2.5,
        tenant_id="test"
    )
    
    response = await generar_plan_mitigacion(request)
    
    # Validamos en la respuesta (mock) que las tareas contengan el texto sanitizado
    tarea = response.tareas_propuestas[0]
    assert "Globex Corp" not in tarea.descripcion
    assert "Homero Simpson" not in tarea.descripcion
    assert "10.0.0.5" not in tarea.descripcion
    assert "[EMPRESA_1]" in tarea.descripcion
    assert "[PERSONA_1]" in tarea.descripcion
    assert "[IP_1]" in tarea.descripcion

# ¤mock-log-record
class MockLogRecord:
    def __init__(self, msg):
        self.msg = msg

# ¤test-api-logger-filter
def test_api_logger_filter(monkeypatch):
    """Valida que el filtro de log elimina la API key."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-12345secret")
    
    filtro = APILoggerFilter()
    record = MockLogRecord("Intentando invocar LLM con API KEY sk-12345secret")
    
    filtro.filter(record)
    assert "sk-12345secret" not in record.msg
    assert "[REDACTED_API_KEY]" in record.msg


# ¤test-sanitizer-nested-lists-dicts-and-tuples-are-sanitized-without-mutation
def test_sanitizer_nested_lists_dicts_and_tuples_are_sanitized_without_mutation():
    sanitizer = LLMDataSanitizer()
    source = {
        "hallazgos": [
            {"evidencias": [[{"contacto": "ana@example.test", "telefono": "+593 99 123 4567"}]]},
            ("1710034065", {"responsable": "Juan Perez"}),
        ],
        "score": 2.5,
        "activo": False,
        "extra": None,
    }
    safe = sanitizer.sanitize_dict(source)
    assert safe["hallazgos"][0]["evidencias"][0][0] == {
        "contacto": "[EMAIL_1]", "telefono": "[DATO_SANITIZADO_POR_DLP]",
    }
    assert safe["hallazgos"][1] == (
        "[DATO_SANITIZADO_POR_DLP]", {"responsable": "[PERSONA_1]"},
    )
    assert safe["score"] == 2.5
    assert safe["activo"] is False
    assert safe["extra"] is None
    assert source["hallazgos"][0]["evidencias"][0][0]["contacto"] == "ana@example.test"


# ¤test-sanitizer-preserves-legal-names-and-article-references
def test_sanitizer_preserves_legal_names_and_article_references():
    text = (
        "Ley Orgánica de Protección de Datos Personales, Art. 8: consentimiento. "
        "Reglamento General. Registro Oficial 459. Evaluación de Impacto."
    )
    assert LLMDataSanitizer().sanitize_text(text) == text


# ¤test-sanitizer-uses-stable-tokens-and-common-dlp
def test_sanitizer_uses_stable_tokens_and_common_dlp():
    sanitizer = LLMDataSanitizer()
    safe = sanitizer.sanitize_dict({
        "pregunta": "Contactar a ana@example.test, CI 1710034065",
        "historial": [{"respuesta": "ana@example.test y 0991234567"}],
    })
    assert "[EMAIL_1]" in safe["pregunta"]
    assert "[EMAIL_1]" in safe["historial"][0]["respuesta"]
    assert "[DATO_SANITIZADO_POR_DLP]" in safe["pregunta"]
    assert "[DATO_SANITIZADO_POR_DLP]" in safe["historial"][0]["respuesta"]


# ¤test-compuerta-dlp-mantiene-conteo-compatible
def test_compuerta_dlp_mantiene_conteo_compatible():
    from app_core.app_service import filtrar_datos_sensibles_dlp
    safe, count = filtrar_datos_sensibles_dlp("CI 1710034065 y ana@example.test")
    assert count == 2
    assert safe.count("[DATO_SANITIZADO_POR_DLP]") == 2
    assert filtrar_datos_sensibles_dlp(safe) == (safe, 0)
