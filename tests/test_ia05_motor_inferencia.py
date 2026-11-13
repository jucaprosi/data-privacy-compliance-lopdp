"""IA-05: el motor del copiloto genera el plan solo por la compuerta de inferencia (sin OpenAI, sin clave, sin plan simulado)."""
import asyncio
import inspect
import logging
from types import SimpleNamespace

import pytest

from app_core.errors import ErrorNegocio
from features.ai_copilot import ai_copilot_service as servicio
from features.ai_copilot.domain.models import (
    AnalisisDiagnosticoRequest, PlanMitigacionResponse, TareaMitigacionIA,
)
from features.ai_copilot.services import inference_engine as motor

CENTINELA = "sk-proj-CENTINELA-0123456789abcdef"
PLAN = PlanMitigacionResponse(
    analisis_general="ok", tareas_propuestas=[TareaMitigacionIA(descripcion="x", impacto_riesgo="ALTO")]
)


def _request(normativa="LOPDP") -> AnalisisDiagnosticoRequest:
    return AnalisisDiagnosticoRequest(
        id_diagnostico="d1", normativa=normativa, brechas_identificadas=["Sin retención"], scoring_global=2.0,
    )


class SesionFalsa:
    def __init__(self):
        self.agregadas = []
        self.commits = 0

    def add(self, obj):
        self.agregadas.append(obj)

    async def commit(self):
        self.commits += 1


def _compuerta(monkeypatch, *, resultado=PLAN, error=None):
    llamadas = []

    async def falsa(sistema, usuario, esquema, *, modelo, org_id):
        llamadas.append({"sistema": sistema, "usuario": usuario, "esquema": esquema, "modelo": modelo, "org_id": org_id})
        if error:
            raise error
        return resultado

    monkeypatch.setattr(motor.pasillo_inferencia, "generar_estructurado", falsa)
    return llamadas


def test_el_motor_llama_a_la_compuerta_con_esquema_modelo_y_org(monkeypatch):
    llamadas = _compuerta(monkeypatch)
    assert asyncio.run(motor.generar_plan_mitigacion(_request(), "org-1")) == PLAN
    assert len(llamadas) == 1
    assert llamadas[0]["esquema"] is PlanMitigacionResponse
    assert llamadas[0]["modelo"] == "gemini-2.5-flash"
    assert llamadas[0]["org_id"] == "org-1"


def test_niif_agrega_contexto_doctrinal(monkeypatch):
    llamadas = _compuerta(monkeypatch)
    asyncio.run(motor.generar_plan_mitigacion(_request("NIIF 18"), "org-1"))
    assert "CONTEXTO DOCTRINAL NIIF 18" in llamadas[0]["sistema"]


def test_sin_organizacion_falla_cerrado_sin_llamar_a_la_compuerta(monkeypatch):
    llamadas = _compuerta(monkeypatch)
    no_disponible, _ = motor.pasillo_inferencia.errores()
    for org in (None, ""):
        with pytest.raises(no_disponible):
            asyncio.run(motor.generar_plan_mitigacion(_request(), org))
    assert llamadas == []


def test_compuerta_fallando_no_devuelve_plan_ni_guarda_tareas(monkeypatch):
    no_disponible, _ = motor.pasillo_inferencia.errores()
    _compuerta(monkeypatch, error=no_disponible())
    sesion = SesionFalsa()
    with pytest.raises(ErrorNegocio) as exc:
        asyncio.run(servicio.ejecutar_diagnostico_y_crear_tareas(_request(), "org-1", sesion))
    assert exc.value.status_code == 503
    assert sesion.agregadas == [] and sesion.commits == 0
    texto = str(exc.value.detail if hasattr(exc.value, "detail") else exc.value).lower()
    for prohibido in ("vertex", "gemini", "openai", "google"):
        assert prohibido not in texto


def test_exito_guarda_las_tareas_con_el_tenant(monkeypatch):
    _compuerta(monkeypatch)
    sesion = SesionFalsa()
    asyncio.run(servicio.ejecutar_diagnostico_y_crear_tareas(_request(), "org-1", sesion))
    assert len(sesion.agregadas) == 1 and sesion.agregadas[0].tenant_id == "org-1" and sesion.commits == 1


@pytest.mark.parametrize("ruta_excepcion", [False, True])
def test_el_log_no_contiene_una_clave(monkeypatch, caplog, ruta_excepcion):
    caplog.set_level(logging.DEBUG)
    monkeypatch.setenv("OPENAI_API_KEY", CENTINELA)
    error = RuntimeError(f"401 credencial rechazada: {CENTINELA}") if ruta_excepcion else None
    _compuerta(monkeypatch, error=error)
    if ruta_excepcion:
        no_disponible, _ = motor.pasillo_inferencia.errores()
        with pytest.raises(no_disponible):
            asyncio.run(motor.generar_plan_mitigacion(_request(), "org-1"))
    else:
        asyncio.run(motor.generar_plan_mitigacion(_request(), "org-1"))
    assert CENTINELA not in caplog.text
    assert all(CENTINELA not in str(r.args) + r.getMessage() + str(r.exc_text) for r in caplog.records)


def test_el_motor_no_usa_proveedor_directo_ni_plan_simulado():
    """Mutación: reponer OpenAI, la lectura de la clave o el plan simulado pone esta prueba en rojo."""
    fuente = inspect.getsource(motor).lower()
    for prohibido in ("openai", "api_key", "os.getenv", "mock", "tareas_mock", "api key"):
        assert prohibido not in fuente, prohibido
    assert "pasillo_inferencia.generar_estructurado" in fuente
    assert not hasattr(motor, "AsyncOpenAI")
