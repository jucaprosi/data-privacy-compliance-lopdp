# ¤arbitro
"""IA-07: el asistente usa solo la compuerta de inferencia, sin DeepSeek, sin .env y con avisos sin jerga."""
from __future__ import annotations

import ast
import asyncio
import re
from pathlib import Path
from types import SimpleNamespace

from features.ai_copilot.domain.assistant_models import ConsultaAsistente
from features.ai_copilot.services import assistant_provider
from features.ai_copilot.services.implementation_assistant import responder_implementacion
from features.regulacion_rag.domain.corpus import CORPUS_VERSION
from features.regulacion_rag.services.implementation_guides import obtener_guia_brecha

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
    brechas = [{"pregunta_id": 21 + i, "control": "Gestión del consentimiento",
                "dimension_id": "D03", "severidad": "Alto"} for i in range(n)]
    return ConsultaAsistente.model_validate({
        "pregunta": "¿Cómo implemento esta brecha?", "brechas": brechas,
        "historial": [], "estado": "Implementación",
    })


def _responder(monkeypatch, compuerta, org_id="org-1", n=1):
    monkeypatch.setattr(assistant_provider, "pasillo_inferencia", compuerta)
    guia = obtener_guia_brecha(21, "Gestión del consentimiento", "D03")
    guias = {21 + i: guia for i in range(n)}
    return asyncio.run(responder_implementacion(
        _consulta(n), guias, guia["fundamento"], CORPUS_VERSION, org_id=org_id,
    ))


def test_sin_deepseek_ni_env_en_el_codigo():
    """Mutación: reponer la lectura de DEEPSEEK_API_KEY o del .env hace fallar esta prueba."""
    texto = PROVEEDOR.read_text(encoding="utf-8")
    for prohibido in ("DEEPSEEK", "dotenv", ".env", "os.environ", "httpx", "api.deepseek.com"):
        assert prohibido not in texto, prohibido


def test_solo_importa_la_compuerta_desde_el_pasillo():
    arbol = ast.parse(PROVEEDOR.read_text(encoding="utf-8"))
    modulos = {n.module for n in ast.walk(arbol) if isinstance(n, ast.ImportFrom)}
    modulos |= {a.name for n in ast.walk(arbol) if isinstance(n, ast.Import) for a in n.names}
    assert "app_core.pasillo" in modulos
    assert not any(m and m.startswith("features.inferencia") for m in modulos)
    assert assistant_provider.MODELO == "gemini-2.5-pro"


def test_compuerta_fallando_da_motivo_neutro(monkeypatch):
    compuerta = Compuerta()
    respuesta = _responder(monkeypatch, compuerta)
    assert compuerta.llamadas == ["org-1"]
    assert respuesta.modo == "local"
    assert assistant_provider.AVISO_NO_VERIFICABLE in respuesta.advertencias


def test_sin_org_id_nunca_se_llama_a_la_compuerta(monkeypatch):
    """Mutación: llamar a generar_estructurado con org_id=None hace fallar esta prueba."""
    compuerta = Compuerta()
    respuesta = _responder(monkeypatch, compuerta, org_id=None)
    assert compuerta.llamadas == []
    assert respuesta.modo == "local"
    assert assistant_provider.AVISO_NO_DISPONIBLE in respuesta.advertencias


def test_avisos_al_cliente_sin_jerga_ni_proveedor(monkeypatch):
    """Mutación: reponer «inferencia» en cualquier aviso hace fallar esta prueba."""
    avisos = set()
    for compuerta, org in ((Compuerta(), "org-1"), (Compuerta(), None), (Compuerta(disponible=False), "org-1")):
        avisos |= set(_responder(monkeypatch, compuerta, org_id=org, n=13).advertencias)
    assert any("priorizó" in a for a in avisos)
    assert assistant_provider.AVISO_NO_DISPONIBLE in avisos
    assert assistant_provider.AVISO_NO_VERIFICABLE in avisos
    for aviso in avisos:
        bajo = aviso.lower()
        for palabra in ("inferencia", "deepseek", "gemini", "vertex", "modelo"):
            assert palabra not in bajo, (palabra, aviso)


def test_literales_de_aviso_del_codigo_sin_inferencia():
    for ruta in (PROVEEDOR, ASISTENTE):
        arbol = ast.parse(ruta.read_text(encoding="utf-8"))
        cadenas = [n.value for n in ast.walk(arbol) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
        cadenas += [p.value for n in ast.walk(arbol) if isinstance(n, ast.JoinedStr)
                    for p in n.values if isinstance(p, ast.Constant)]
        avisos = [c for c in cadenas if re.search(r"(?i)respaldo|priorizó", c)]
        assert avisos, ruta
        assert not any("inferencia" in c.lower() for c in avisos)


def test_modo_externo_en_contrato_y_cliente():
    """Mutación: dejar "deepseek" en copilotClient.ts hace fallar esta prueba."""
    for rel in ("frontend/src/lib/copilotClient.ts", "frontend/src/types/copilot.ts",
                "frontend/src/components/copilot/CopilotWorkspace.tsx",
                "features/ai_copilot/domain/assistant_models.py"):
        texto = (RAIZ / rel).read_text(encoding="utf-8")
        assert "deepseek" not in texto.lower(), rel
        assert '"externo"' in texto, rel
