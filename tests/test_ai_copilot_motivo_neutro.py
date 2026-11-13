"""IA-02: el estado del asistente no revela proveedor, modelo ni variables."""
import json

import pytest
from fastapi.testclient import TestClient

from features.ai_copilot.services import assistant_provider
from main import app

client = TestClient(app)
CABECERA = {"X-Tenant-ID": "tenant-corp-test"}
PROHIBIDOS = (
    "deepseek", "gemini", "vertex", "openai", "api_key", "_model", "deepseek-flash",
)


def _configurar(monkeypatch, tmp_path, habilitado: bool) -> None:
    from types import SimpleNamespace

    async def prohibido(*args, **kwargs):
        raise AssertionError("no debe llamarse a la compuerta")

    monkeypatch.setattr(assistant_provider, "pasillo_inferencia", SimpleNamespace(
        estado=lambda: SimpleNamespace(disponible=habilitado), generar_estructurado=prohibido,
    ))


@pytest.mark.parametrize("habilitado", [False, True])
def test_endpoint_estado_no_nombra_proveedor_modelo_ni_variables(monkeypatch, tmp_path, habilitado):
    _configurar(monkeypatch, tmp_path, habilitado)
    response = client.get("/api/v1/ai_copilot/estado", headers=CABECERA)
    assert response.status_code == 200
    texto = json.dumps(response.json(), ensure_ascii=False).lower()
    for prohibido in PROHIBIDOS + ("clave-simulada", "modelo-simulado"):
        assert prohibido not in texto, prohibido


@pytest.mark.parametrize("habilitado", [False, True])
def test_proveedor_y_modo_son_neutros_y_conservan_la_clave(monkeypatch, tmp_path, habilitado):
    _configurar(monkeypatch, tmp_path, habilitado)
    estado = assistant_provider.estado_proveedor_asistente()
    esperado = "externo" if habilitado else "local"
    assert estado["proveedor"] == esperado
    assert estado["modo"] == esperado
    assert estado["proveedor_configurado"] is habilitado
    assert estado["inferencia_externa_habilitada"] is habilitado


def test_proveedor_nunca_devuelve_deepseek(monkeypatch, tmp_path):
    for habilitado in (False, True):
        _configurar(monkeypatch, tmp_path, habilitado)
        assert assistant_provider.estado_proveedor_asistente()["proveedor"] != "deepseek"


def test_avisos_de_respaldo_son_neutros(monkeypatch, tmp_path):
    import asyncio
    _configurar(monkeypatch, tmp_path, False)
    _, modo, aviso = asyncio.run(assistant_provider.enriquecer_implementacion({}))
    assert modo == "local"
    assert aviso and "deepseek" not in aviso.lower()
