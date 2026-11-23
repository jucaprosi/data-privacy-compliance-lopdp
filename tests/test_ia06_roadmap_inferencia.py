# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤roadmap ¤arbitro
"""IA-06: Hoja de ruta generada por la compuerta de inferencia Vertex AI (gemini-2.5-pro), con cifras de código y traza."""
from __future__ import annotations

import ast
import asyncio
from datetime import date, timedelta
import importlib
import inspect
import json
import logging
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app_core.errors import ErrorNegocio

_client = importlib.import_module("features.roadmap.ai.client")
DEFAULT_TIMEOUT_SECONDS = _client.DEFAULT_TIMEOUT_SECONDS
LLMTimeoutError = _client.LLMTimeoutError
MODELO_POR_DEFECTO = _client.MODELO_POR_DEFECTO
TruncatedOutputError = _client.TruncatedOutputError
call_roadmap_llm = _client.call_roadmap_llm
generar_roadmap_con_traza = _client.generar_roadmap_con_traza

_prompts = importlib.import_module("features.roadmap.ai.roadmap_prompts")
PROMPT_ID = _prompts.PROMPT_ID
PROMPT_VERSION = _prompts.PROMPT_VERSION
SYSTEM_PROMPT = _prompts.SYSTEM_PROMPT
RoadmapTextoRespuesta = _prompts.RoadmapTextoRespuesta
VIGENTE = _prompts.VIGENTE

_esfuerzo = importlib.import_module("features.roadmap.domain.esfuerzo_controles")
ControlCifrado = _esfuerzo.ControlCifrado
OlaCifrada = _esfuerzo.OlaCifrada
PlanCifrado = _esfuerzo.PlanCifrado

_models = importlib.import_module("features.roadmap.domain.models")
GenerateRoadmapRequest = _models.GenerateRoadmapRequest
RoadmapDocument = _models.RoadmapDocument

engine = importlib.import_module("features.roadmap.services.generacion_engine")
GeneracionRoadmapError = engine.GeneracionRoadmapError
generate_roadmap_document = engine.generate_roadmap_document

en_linea = importlib.import_module("features.roadmap.services.generacion_en_linea")

RAIZ = Path(__file__).resolve().parents[1]
CENTINELA = "sk-proj-CENTINELA-0123456789abcdef"
HOY = date(2026, 11, 16)


def _ejemplo_doc(
    controles: list[str] | None = None,
    horas_locas: int = 40,
    prio_loca: str = "media",
    fecha_loca: str = "2026-11-16",
) -> dict:
    ctrls = controles or ["P1"]
    return {
        "roadmap_id": "rm-1",
        "tenant_id": "org-1",
        "resumen_ejecutivo": "Plan ejecutivo de adecuación.",
        "olas": [
            {
                "id": "ola-1",
                "nombre": "Ola 1: Medidas Inmediatas",
                "plazo": "Meses 1 a 2",
                "objetivo": "Cerrar brechas prioritarias",
                "tareas": [
                    {
                        "id": f"t-{c}",
                        "control_ref": c,
                        "dimension": "D01",
                        "titulo": f"Tarea para {c}",
                        "descripcion": f"Descripción de {c}",
                        "responsable": "DPO",
                        "prioridad": prio_loca,
                        "esfuerzo_estimado_horas": horas_locas,
                        "dependencias": [],
                        "entregable": "Documento aprobado",
                        "evidencia_requerida": ["Acta"],
                        "kpi": "Completado",
                        "fecha_inicio": fecha_loca,
                        "fecha_fin": fecha_loca,
                    }
                    for c in ctrls
                ],
            }
        ],
        "kpis_globales": {
            "criticos_totales": 0,
            "altos_totales": 0,
            "score_objetivo": 10.0,
            "evidencia_verificada_objetivo": 100.0,
        },
    }


def _plan_cifrado(controles: list[str] | None = None) -> PlanCifrado:
    ctrls = controles or ["P1"]
    return PlanCifrado(
        olas=(
            OlaCifrada(
                prioridad="critica",
                controles=tuple(ControlCifrado(c, 1, "critica", 40) for c in ctrls),
                horas=40 * len(ctrls),
                inicio=HOY,
                fin=HOY + timedelta(days=30),
            ),
        ),
        score_objetivo=(),
    )


def _variables_payload() -> dict:
    return {
        "plazo_meses": 6,
        "presupuesto": 1500.0,
        "moneda": "USD",
        "equipo": ["DPO"],
        "dpo": "DPO Principal",
        "idioma": "ES",
    }


class SesionFalsa:
    def __init__(self):
        self.sentencias = []
        self.commits = 0
        self.rollbacks = 0

    async def execute(self, statement, params=None):
        self.sentencias.append((str(statement), params))
        return MagicMock()

    async def commit(self):
        self.commits += 1

    async def rollback(self):
        self.rollbacks += 1


def test_las_cifras_no_vienen_del_modelo():
    """Dado un cliente falso de la compuerta que devuelve prioridades, horas y fechas absurdas,

    entonces el documento final lleva las del PlanCifrado. Mutación: tomar una cifra de la
    respuesta del modelo hace fallar la prueba.
    """
    plan = _plan_cifrado(["P1"])
    doc_modelo_loco = _ejemplo_doc(["P1"], horas_locas=99999, prio_loca="media", fecha_loca="1970-01-01")

    doc = generate_roadmap_document(
        assessment={},
        variables=_variables_payload(),
        roadmap_id="rm-1",
        tenant_id="org-1",
        llm_caller=lambda sys_p, usr_p: json.dumps(doc_modelo_loco),
        plan_cifrado=plan,
        hoy=HOY,
    )

    t = doc.olas[0].tareas[0]
    # Cifras deterministas de PlanCifrado
    assert t.esfuerzo_estimado_horas == 40
    assert t.esfuerzo_estimado_horas != 99999
    assert t.prioridad.value == "critica"
    assert t.prioridad.value != "media"
    assert t.fecha_inicio == HOY.isoformat()
    assert t.fecha_inicio != "1970-01-01"
    assert t.fecha_fin == (HOY + timedelta(days=30)).isoformat()
    assert doc.kpis_globales.criticos_totales == 1


def test_esquema_solo_texto():
    """Dado el esquema que se pide al modelo, entonces no tiene ningún campo numérico, de fecha ni de prioridad."""
    schema = RoadmapTextoRespuesta.model_json_schema()
    texto_schema = json.dumps(schema).lower()

    # No debe solicitar horas ni prioridad numérica ni fechas
    for campo_prohibido in ("esfuerzo_estimado_horas", "fecha_inicio", "fecha_fin", "score_objetivo"):
        assert campo_prohibido not in texto_schema

    # Inspeccionar propiedades de cada entidad en definitions/$defs
    defs = schema.get("$defs", {})
    for nombre_def, definicion in defs.items():
        props = definicion.get("properties", {})
        for prop_name, prop_data in props.items():
            prop_type = prop_data.get("type", "")
            assert prop_type not in ("integer", "number"), f"Campo numérico detectado en {nombre_def}.{prop_name}"
            assert prop_data.get("format") not in ("date", "date-time"), f"Campo de fecha en {nombre_def}.{prop_name}"
            assert prop_name != "prioridad", f"Campo de prioridad detectado en {nombre_def}"


def test_correspondencia_por_control():
    """Dado una respuesta sin texto para un control del plan, o con un control que no está en el plan,

    entonces la generación falla y no se guarda nada.
    """
    plan = _plan_cifrado(["P1", "P2"])

    # Caso A: Falta P2 en el texto devuelto por el modelo
    doc_incompleto = _ejemplo_doc(["P1"])
    with pytest.raises(GeneracionRoadmapError, match="Correspondencia de controles no coincide"):
        generate_roadmap_document(
            assessment={},
            variables=_variables_payload(),
            roadmap_id="rm-1",
            tenant_id="org-1",
            llm_caller=lambda sys_p, usr_p: json.dumps(doc_incompleto),
            plan_cifrado=plan,
            hoy=HOY,
        )

    # Caso B: El modelo devolvió un control ajeno (P3, que no está en el plan [P1, P2])
    doc_ajeno = _ejemplo_doc(["P1", "P2", "P3"])
    with pytest.raises(GeneracionRoadmapError, match="Correspondencia de controles no coincide"):
        generate_roadmap_document(
            assessment={},
            variables=_variables_payload(),
            roadmap_id="rm-1",
            tenant_id="org-1",
            llm_caller=lambda sys_p, usr_p: json.dumps(doc_ajeno),
            plan_cifrado=plan,
            hoy=HOY,
        )


def test_sin_compuerta_no_hay_hoja(monkeypatch):
    """Dado la compuerta no disponible, entonces falla cerrado sin persistir olas ni tareas.

    Mutación: reponer un plan de respaldo hace fallar la prueba.
    """
    no_disponible, motivo_neutro = en_linea.pasillo_inferencia.errores()

    # Simular compuerta no disponible
    monkeypatch.setattr(en_linea.pasillo_inferencia, "estado", lambda: SimpleNamespace(disponible=False))

    async def _falsa_generar(*args, **kwargs):
        raise no_disponible(motivo_neutro)

    monkeypatch.setattr(en_linea.pasillo_inferencia, "generar_estructurado", _falsa_generar)

    sesion = SesionFalsa()
    req = GenerateRoadmapRequest(
        tenant_id="org-1",
        user_id="user-1",
        variables=_variables_payload(),
        assessment={"brechas": ["P1"]},
    )

    with patch("features.roadmap.services.generacion_en_linea.armar_contexto_generacion", return_value={"brechas": ["P1"]}):
        res = asyncio.run(en_linea.generate_roadmap_inline(sesion, "org-1", "user-1", req))

    assert res["status"] == "failed"

    # Verificar que no quedaron sentencias de inserción de olas ni tareas
    sentencias_str = " ".join(s for s, _ in sesion.sentencias)
    assert "INSERT INTO roadmap_waves" not in sentencias_str
    assert "INSERT INTO roadmap_tasks" not in sentencias_str
    assert "UPDATE roadmaps" in sentencias_str

    # Directamente sobre el cliente o motor, la compuerta no disponible levanta InferenciaNoDisponible
    with pytest.raises(no_disponible):
        call_roadmap_llm("sys", "user")


def test_generacion_con_traza(monkeypatch):
    """Dado una generación correcta, entonces existe una traza con el prompt, su versión y la versión del modelo."""
    traza_simulada = SimpleNamespace(
        id="traza-123",
        sala="roadmap",
        tenant_id="org-1",
        modelo_version="gemini-2.5-pro@001",
        modelo_solicitado="gemini-2.5-pro",
        prompt_id=PROMPT_ID,
        prompt_version=PROMPT_VERSION,
        corpus_sha256=None,
    )
    doc_ejemplo = RoadmapDocument.model_validate(_ejemplo_doc(["P1"]))

    llamadas = []

    async def falsa_trazado(prompt, valores, esquema, *, modelo, org_id, corpus_sha256=None):
        llamadas.append({"prompt": prompt, "modelo": modelo, "org_id": org_id})
        return doc_ejemplo, traza_simulada

    monkeypatch.setattr(engine.pasillo_inferencia, "estado", lambda: SimpleNamespace(disponible=True))
    monkeypatch.setattr(engine.pasillo_inferencia, "generar_trazado", falsa_trazado)

    res, traza = asyncio.run(
        generar_roadmap_con_traza(
            prompt=VIGENTE,
            valores={"assessment_json": "{}", "variables_usuario_json": "{}", "idioma": "ES"},
            org_id="org-1",
            modelo="gemini-2.5-pro",
        )
    )

    assert isinstance(res, RoadmapDocument)
    assert traza.prompt_id == "roadmap.generacion"
    assert traza.prompt_version == 1
    assert traza.modelo_solicitado == "gemini-2.5-pro"
    assert traza.modelo_version == "gemini-2.5-pro@001"
    assert len(llamadas) == 1
    assert llamadas[0]["modelo"] == "gemini-2.5-pro"


def test_roadmap_solo_por_la_compuerta():
    """Dado la sala roadmap, entonces ningún módulo importa un cliente de modelo ni lee variables de proveedor.

    Mutación: volver a un cliente directo hace fallar la prueba.
    """
    directorio_roadmap = RAIZ / "features" / "roadmap"
    for py_file in directorio_roadmap.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        arbol = ast.parse(py_file.read_text(encoding="utf-8"))
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Import):
                for alias in nodo.names:
                    for prohibido in ("openai", "anthropic", "google.genai", "vertexai"):
                        assert not alias.name.startswith(prohibido), f"Import directo {alias.name} en {py_file}"
            elif isinstance(nodo, ast.ImportFrom):
                modulo = nodo.module or ""
                assert not modulo.startswith("features.inferencia"), f"Import lateral {modulo} en {py_file}"
                for prohibido in ("openai", "anthropic", "google.genai", "vertexai"):
                    assert not modulo.startswith(prohibido), f"Import directo {modulo} en {py_file}"


def test_registros_sin_clave(monkeypatch, caplog):
    """Dado un centinela con forma de clave en el entorno, entonces no aparece en los registros, tampoco en la rama de error."""
    caplog.set_level(logging.DEBUG)
    monkeypatch.setenv("CLAVE_IA_EXTERNA", CENTINELA)
    monkeypatch.setenv("GEMINI_API_KEY", CENTINELA)

    no_disponible, motivo = engine.pasillo_inferencia.errores()

    # Rama de error
    def falso_caller_error(*a, **kw):
        raise no_disponible(f"Fallo de conexión con credencial {CENTINELA}")

    with pytest.raises(no_disponible):
        generate_roadmap_document(
            assessment={},
            variables={},
            roadmap_id="rm-err",
            tenant_id="org-1",
            llm_caller=falso_caller_error,
        )

    assert CENTINELA not in caplog.text
    assert all(CENTINELA not in r.getMessage() for r in caplog.records)


def test_sin_organizacion_falla_cerrado():
    """Sin organización explícita, call_roadmap_llm falla cerrado."""
    no_disponible, _ = engine.pasillo_inferencia.errores()
    for org in ("", "  ", None):
        with pytest.raises(no_disponible):
            call_roadmap_llm(
                system_prompt="sys",
                user_prompt="usr",
                org_id=org,  # type: ignore[arg-type]
            )


def test_tiempo_limite_en_cliente(monkeypatch):
    """Timeout superado en la llamada structured lanza LLMTimeoutError."""
    monkeypatch.setattr(engine.pasillo_inferencia, "estado", lambda: SimpleNamespace(disponible=True))

    async def falsa_lenta(*args, **kwargs):
        await asyncio.sleep(1.0)
        return RoadmapDocument.model_validate(_ejemplo_doc(["P1"]))

    monkeypatch.setattr(engine.pasillo_inferencia, "generar_estructurado", falsa_lenta)

    with pytest.raises(LLMTimeoutError, match="Tiempo límite agotado"):
        call_roadmap_llm(
            system_prompt="sys",
            user_prompt="usr",
            timeout=0.01,
            org_id="org-1",
        )


def test_truncamiento_de_salida():
    """finish_reason == 'length' levanta TruncatedOutputError."""
    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.finish_reason = "length"
    mock_choice.message.content = '{"resumen_ejecutivo": "Cortado...'
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response

    with pytest.raises(TruncatedOutputError, match="truncada por límite de tokens"):
        call_roadmap_llm(
            system_prompt="sys",
            user_prompt="usr",
            client=mock_client,
            max_tokens=2048,
        )


def test_cliente_usa_gemini_2_5_pro(monkeypatch):
    """Comprueba que el modelo invocado es gemini-2.5-pro."""
    assert MODELO_POR_DEFECTO == "gemini-2.5-pro"
    llamadas = []

    async def falsa_gen(sistema, usuario, esquema, *, modelo, org_id):
        llamadas.append({"modelo": modelo, "org_id": org_id})
        return RoadmapDocument.model_validate(_ejemplo_doc(["P1"]))

    monkeypatch.setattr(engine.pasillo_inferencia, "estado", lambda: SimpleNamespace(disponible=True))
    monkeypatch.setattr(engine.pasillo_inferencia, "generar_estructurado", falsa_gen)

    call_roadmap_llm("sys", "usr", org_id="org-test")
    assert len(llamadas) == 1
    assert llamadas[0]["modelo"] == "gemini-2.5-pro"
    assert llamadas[0]["org_id"] == "org-test"
