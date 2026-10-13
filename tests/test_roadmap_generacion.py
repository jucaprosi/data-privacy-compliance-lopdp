# ¤roadmap ¤copiloto-ia
"""Suite de pruebas unitarias para la generación fiable con IA (RM-12).

Prueba de forma aislada y determinista con un modelo de IA simulado:
1. Verificación de que el prompt del sistema contiene el esquema completo de RoadmapDocument (Aporte 94).
2. Generación exitosa de un RoadmapDocument en el primer intento.
3. Detección y manejo de salida truncada (TruncatedOutputError con finish_reason == 'length').
4. Reintento correctivo exitoso reenviando el error de validación cuando el primer intento falla.
5. Fallo controlado (GeneracionRoadmapError) cuando se agotan los reintentos permitidos.
6. Manejo de tiempo límite explícito (timeout / LLMTimeoutError).
"""
import json
from datetime import date, timedelta
from typing import Any
from unittest.mock import MagicMock

import pytest

from features.roadmap.roadmap_service import (
    GeneracionRoadmapError,
    LLMTimeoutError,
    RoadmapDocument,
    SYSTEM_PROMPT,
    TruncatedOutputError,
    build_roadmap_prompt,
    call_roadmap_llm,
    generate_roadmap_document,
    get_roadmap_schema_str,
)


def _datos_ejemplo_documento(roadmap_id: str = "rm-123", tenant_id: str = "tenant-abc") -> dict:
    """Genera un diccionario que cumple con la validación de RoadmapDocument."""
    today = date.today()
    return {
        "roadmap_id": roadmap_id,
        "tenant_id": tenant_id,
        "resumen_ejecutivo": "Plan de implementación LOPDP para adecuación organizativa y técnica.",
        "olas": [
            {
                "id": "ola-1",
                "nombre": "Ola 1: Medidas Inmediatas y Gobernanza",
                "plazo": "Meses 1 a 2",
                "objetivo": "Cerrar brechas prioritarias de gobernanza y nombramiento del DPO",
                "tareas": [
                    {
                        "id": "tarea-1",
                        "control_ref": "P1",
                        "dimension": "D01",
                        "titulo": "Formalizar designación y funciones del DPO",
                        "descripcion": "Establecer la estructura de supervisión de datos personales.",
                        "responsable": "Dirección General",
                        "prioridad": "critica",
                        "esfuerzo_estimado_horas": 40,
                        "dependencias": [],
                        "entregable": "Resolución de designación de DPO inscrita",
                        "evidencia_requerida": ["Acta de designación", "Contrato de servicios"],
                        "kpi": "DPO nombrado y notificado",
                        "fecha_inicio": today.isoformat(),
                        "fecha_fin": (today + timedelta(days=30)).isoformat(),
                    }
                ],
            }
        ],
        "kpis_globales": {
            "criticos_totales": 1,
            "altos_totales": 0,
            "score_objetivo": 85.5,
            "evidencia_verificada_objetivo": 90.0,
        },
    }


def test_prompt_sistema_incluye_esquema_roadmap_document():
    """Valida el Aporte 94: el prompt del sistema debe contener el esquema JSON de RoadmapDocument."""
    assert "RoadmapDocument" in SYSTEM_PROMPT
    schema_str = get_roadmap_schema_str()
    # Debe contener las propiedades esenciales del esquema
    assert "resumen_ejecutivo" in SYSTEM_PROMPT
    assert "olas" in SYSTEM_PROMPT
    assert "kpis_globales" in SYSTEM_PROMPT
    assert "control_ref" in SYSTEM_PROMPT
    assert "P1-P73" in SYSTEM_PROMPT
    assert "D01-D10" in SYSTEM_PROMPT


def test_generacion_exitosa_primer_intento():
    """El modelo devuelve un JSON válido a la primera llamada y se valida como RoadmapDocument."""
    ejemplo = _datos_ejemplo_documento("rm-test-1", "tenant-test-1")
    prompt_recibido = {}

    def mock_caller(sys_p: str, user_p: str) -> str:
        prompt_recibido["sys"] = sys_p
        prompt_recibido["user"] = user_p
        return json.dumps(ejemplo)

    doc = generate_roadmap_document(
        assessment={"brechas": ["P01"]},
        variables={"plazo_meses": 6, "idioma": "ES"},
        roadmap_id="rm-test-1",
        tenant_id="tenant-test-1",
        llm_caller=mock_caller,
    )

    assert isinstance(doc, RoadmapDocument)
    assert str(doc.roadmap_id) == "rm-test-1"
    assert doc.tenant_id == "tenant-test-1"
    assert len(doc.olas) == 1
    assert doc.olas[0].tareas[0].control_ref == "P1"
    assert "assessment_json" in prompt_recibido["user"]


def test_reintento_correctivo_con_error_de_validacion():
    """Si el primer intento devuelve un JSON con datos inválidos, el reintento incluye el error y el esquema."""
    intentos = []
    ejemplo_invalido = _datos_ejemplo_documento("rm-test-2", "tenant-test-2")
    # Inyectar control fuera del rango P1-P73 para forzar ValidationError
    ejemplo_invalido["olas"][0]["tareas"][0]["control_ref"] = "P999"

    ejemplo_valido = _datos_ejemplo_documento("rm-test-2", "tenant-test-2")

    def mock_caller_con_reintento(sys_p: str, user_p: str) -> str:
        intentos.append(user_p)
        if len(intentos) == 1:
            return json.dumps(ejemplo_invalido)
        return json.dumps(ejemplo_valido)

    doc = generate_roadmap_document(
        assessment={"brechas": ["P01"]},
        variables={"plazo_meses": 6},
        roadmap_id="rm-test-2",
        tenant_id="tenant-test-2",
        llm_caller=mock_caller_con_reintento,
        max_retries=2,
    )

    assert len(intentos) == 2
    # El segundo intento debe contener el aviso de corrección y el detalle del error
    assert "CORRECCIÓN REQUERIDA" in intentos[1]
    assert "control_ref no pertenece al catálogo P1-P73" in intentos[1]
    assert "resumen_ejecutivo" in intentos[1]  # Esquema reenviado
    assert doc.olas[0].tareas[0].control_ref == "P1"


def test_deteccion_salida_truncada_en_cliente():
    """Valida que finish_reason == 'length' levante TruncatedOutputError con límite de tokens."""
    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.finish_reason = "length"
    mock_choice.message.content = '{"resumen_ejecutivo": "Incompleto...'
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response

    with pytest.raises(TruncatedOutputError, match="truncada por límite de tokens"):
        call_roadmap_llm(
            system_prompt="sys",
            user_prompt="user",
            client=mock_client,
            max_tokens=4096,
        )


def test_reintento_ante_salida_truncada():
    """Si el primer intento es truncado, el reintento solicita concisión respetando el esquema."""
    intentos = []
    ejemplo_valido = _datos_ejemplo_documento("rm-test-3", "tenant-test-3")

    def mock_caller_truncado(sys_p: str, user_p: str) -> str:
        intentos.append(user_p)
        if len(intentos) == 1:
            raise TruncatedOutputError("Salida truncada")
        return json.dumps(ejemplo_valido)

    doc = generate_roadmap_document(
        assessment={},
        variables={},
        roadmap_id="rm-test-3",
        tenant_id="tenant-test-3",
        llm_caller=mock_caller_truncado,
        max_retries=2,
    )

    assert len(intentos) == 2
    assert "ERROR PREVIO: La respuesta anterior fue truncada" in intentos[1]
    assert isinstance(doc, RoadmapDocument)


def test_fallo_tras_agotar_reintentos():
    """Si todos los reintentos devuelven datos inválidos, se lanza GeneracionRoadmapError."""
    def mock_caller_siempre_invalido(sys_p: str, user_p: str) -> str:
        return '{"invalido": true}'

    with pytest.raises(GeneracionRoadmapError, match="No se pudo generar un RoadmapDocument válido tras 2 intentos"):
        generate_roadmap_document(
            assessment={},
            variables={},
            roadmap_id="rm-fail",
            tenant_id="tenant-fail",
            llm_caller=mock_caller_siempre_invalido,
            max_retries=2,
        )


def test_tiempo_limite_explicito_en_cliente():
    """Valida el manejo de timeouts explícitos en el cliente LLM."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = Exception("Request timed out after 5.0 seconds")

    with pytest.raises(LLMTimeoutError, match="Tiempo límite agotado en llamada al LLM"):
        call_roadmap_llm(
            system_prompt="sys",
            user_prompt="user",
            client=mock_client,
            timeout=5.0,
        )
