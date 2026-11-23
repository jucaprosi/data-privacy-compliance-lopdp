# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤arbitro
"""IA-07: el asistente usa solo la compuerta de inferencia Vertex AI y emite avisos sin jerga."""
from __future__ import annotations

import ast
import asyncio
import json
import re
from pathlib import Path
from types import SimpleNamespace

from features.ai_copilot.domain.assistant_models import ConsultaAsistente
from features.ai_copilot.services import assistant_provider
from features.ai_copilot.services.implementation_assistant import responder_implementacion
from features.inferencia import inferencia_service
from features.regulacion_rag.domain.corpus import CORPUS_VERSION
from features.regulacion_rag.services.implementation_guides import obtener_guia_brecha
from app_core.pasillo.inferencia import MODELO_GENERACION

RAIZ = Path(__file__).resolve().parents[1]
PROVEEDOR = RAIZ / "features/ai_copilot/services/assistant_provider.py"
ASISTENTE = RAIZ / "features/ai_copilot/services/implementation_assistant.py"


class Compuerta:
    def __init__(self, disponible=True, error=None):
        self.disponible, self.error, self.llamadas = disponible, error, []

    def estado(self):
        return SimpleNamespace(disponible=self.disponible)

    async def generar_estructurado(self, sistema, usuario, esquema, *, modelo, org_id):
        self.llamadas.append(org_id)
        raise self.error or RuntimeError("compuerta caída")


def _consulta(n=1):
    brechas = [
        {
            "pregunta_id": 21 + i,
            "control": "Gestión del consentimiento",
            "dimension_id": "D03",
            "severidad": "Alto",
        }
        for i in range(n)
    ]
    return ConsultaAsistente.model_validate({
        "pregunta": "¿Cómo implemento esta brecha?",
        "brechas": brechas,
        "historial": [],
        "estado": "Implementación",
    })


def _responder(monkeypatch, compuerta, org_id="org-1", n=1):
    monkeypatch.setattr(assistant_provider, "pasillo_inferencia", compuerta)
    guia = obtener_guia_brecha(21, "Gestión del consentimiento", "D03")
    guias = {21 + i: guia for i in range(n)}
    return asyncio.run(responder_implementacion(
        _consulta(n), guias, guia["fundamento"], CORPUS_VERSION, org_id=org_id,
    ))


def test_proveedor_solo_delega_en_compuerta_sin_leer_entorno():
    """El proveedor del asistente expone funciones tipadas y delega en el pasillo."""
    assert callable(assistant_provider.esquema_asistente)
    assert callable(assistant_provider.validar_salida_asistente)


def test_solo_importa_la_compuerta_desde_el_pasillo():
    arbol = ast.parse(PROVEEDOR.read_text(encoding="utf-8"))
    modulos = {n.module for n in ast.walk(arbol) if isinstance(n, ast.ImportFrom)}
    modulos |= {a.name for n in ast.walk(arbol) if isinstance(n, ast.Import) for a in n.names}
    assert "app_core.pasillo" in modulos
    assert not any(m and m.startswith("features.inferencia") for m in modulos)
    assert assistant_provider.MODELO == MODELO_GENERACION


def test_enriquecer_implementacion_vertex_exitoso(monkeypatch):
    """El asistente enruta la inferencia por Vertex AI a través de `app_core/pasillo/inferencia.py`."""
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "proyecto-asistente-test")
    monkeypatch.setenv("VERTEX_LOCATION", "us-central1")
    consumos: list[str] = []

    async def _consumir(org_id: str) -> None:
        consumos.append(org_id)

    payload = {
        "respuesta": "Plan alineado con LOPDP.",
        "enfoque": "plan",
        "planes": [
            {
                "pregunta_id": 21,
                "pasos": ["Revisar cláusula de consentimiento"],
                "responsable_sugerido": "DPD",
                "evidencias": ["Registro de consentimiento"],
                "criterio_cierre": "Aprobación formal",
                "seguimiento": "Trimestral",
            }
        ],
    }

    class _Models:
        async def generate_content(self, **kwargs):
            assert kwargs["model"] == assistant_provider.MODELO
            return SimpleNamespace(text=json.dumps(payload, ensure_ascii=False))

    cliente_falso = SimpleNamespace(aio=SimpleNamespace(models=_Models()))
    inferencia_service.inyectar_cliente_de_prueba(cliente_falso)
    inferencia_service.inyectar_consumidor_de_prueba(_consumir)
    try:
        guia = obtener_guia_brecha(21, "Gestión del consentimiento", "D03")
        respuesta = asyncio.run(responder_implementacion(
            _consulta(1), {21: guia}, guia["fundamento"], CORPUS_VERSION, org_id="org-vertex-1",
        ))
    finally:
        inferencia_service.inyectar_cliente_de_prueba(None)
        inferencia_service.inyectar_consumidor_de_prueba(None)

    assert consumos == ["org-vertex-1"]
    assert respuesta.modo == "externo"


def test_compuerta_fallando_da_motivo_neutro(monkeypatch):
    compuerta = Compuerta()
    respuesta = _responder(monkeypatch, compuerta)
    assert compuerta.llamadas == ["org-1"]
    assert respuesta.modo == "local"
    assert assistant_provider.AVISO_NO_VERIFICABLE in respuesta.advertencias


def test_sin_org_id_nunca_se_llama_a_la_compuerta(monkeypatch):
    """Llamar sin `org_id` falla cerrado sin invocar `generar_estructurado`."""
    compuerta = Compuerta()
    respuesta = _responder(monkeypatch, compuerta, org_id=None)
    assert compuerta.llamadas == []
    assert respuesta.modo == "local"
    assert assistant_provider.AVISO_NO_DISPONIBLE in respuesta.advertencias


def test_avisos_al_cliente_sin_jerga_ni_proveedor(monkeypatch):
    """Los avisos al usuario final permanecen libres de tecnicismos o nombres de proveedor."""
    avisos = set()
    for compuerta, org in ((Compuerta(), "org-1"), (Compuerta(), None), (Compuerta(disponible=False), "org-1")):
        avisos |= set(_responder(monkeypatch, compuerta, org_id=org, n=13).advertencias)
    assert any("priorizó" in a for a in avisos)
    assert assistant_provider.AVISO_NO_DISPONIBLE in avisos
    assert assistant_provider.AVISO_NO_VERIFICABLE in avisos
    for aviso in avisos:
        bajo = aviso.lower()
        assert "apoyo con ia" not in bajo or "respaldo local" in bajo, aviso
        for palabra in ("inferencia", "gemini", "vertex", "google", "modelo", "proveedor"):
            assert palabra not in bajo, (palabra, aviso)
