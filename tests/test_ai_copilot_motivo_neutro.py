# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
"""IA-02: el estado del asistente no revela proveedor, modelo ni variables de entorno."""
import asyncio
import json
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from features.ai_copilot.services import assistant_provider
from main import app

client = TestClient(app)
CABECERA = {"X-Tenant-ID": "tenant-corp-test"}
PROHIBIDOS = (
    "gemini",
    "vertex",
    "google_cloud_project",
    "vertex_location",
    "us-central1",
    "api_key",
    "_model",
    "proyecto-simulado",
)


def _configurar(monkeypatch, habilitado: bool) -> None:
    if habilitado:
        monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "proyecto-simulado")
        monkeypatch.setenv("VERTEX_LOCATION", "us-central1")
    else:
        monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
        monkeypatch.delenv("VERTEX_LOCATION", raising=False)

    async def prohibido(*args, **kwargs):
        raise AssertionError("no debe llamarse a la compuerta")

    monkeypatch.setattr(
        assistant_provider,
        "pasillo_inferencia",
        SimpleNamespace(
            estado=lambda: SimpleNamespace(disponible=habilitado),
            generar_estructurado=prohibido,
        ),
    )


@pytest.mark.parametrize("habilitado", [False, True])
def test_endpoint_estado_no_nombra_proveedor_modelo_ni_variables(monkeypatch, habilitado):
    _configurar(monkeypatch, habilitado)
    response = client.get("/api/v1/ai_copilot/estado", headers=CABECERA)
    assert response.status_code == 200
    texto = json.dumps(response.json(), ensure_ascii=False).lower()
    for prohibido in PROHIBIDOS:
        assert prohibido not in texto, prohibido


@pytest.mark.parametrize("habilitado", [False, True])
def test_estado_real_con_entorno_vertex_es_neutro(monkeypatch, habilitado):
    if habilitado:
        monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "proyecto-simulado")
        monkeypatch.setenv("VERTEX_LOCATION", "us-central1")
    else:
        monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
        monkeypatch.delenv("VERTEX_LOCATION", raising=False)
    response = client.get("/api/v1/ai_copilot/estado", headers=CABECERA)
    assert response.status_code == 200
    cuerpo = response.json()
    esperado = "externo" if habilitado else "local"
    assert cuerpo["modo"] == esperado
    assert cuerpo["proveedor"] == esperado
    texto = json.dumps(cuerpo, ensure_ascii=False).lower()
    for prohibido in PROHIBIDOS:
        assert prohibido not in texto, prohibido


@pytest.mark.parametrize("habilitado", [False, True])
def test_proveedor_y_modo_son_neutros_y_conservan_la_clave(monkeypatch, habilitado):
    _configurar(monkeypatch, habilitado)
    estado = assistant_provider.estado_proveedor_asistente()
    esperado = "externo" if habilitado else "local"
    assert estado["proveedor"] == esperado
    assert estado["modo"] == esperado
    assert estado["proveedor_configurado"] is habilitado
    assert estado["inferencia_externa_habilitada"] is habilitado


def test_proveedor_solo_devuelve_modos_neutros(monkeypatch):
    for habilitado in (False, True):
        _configurar(monkeypatch, habilitado)
        assert assistant_provider.estado_proveedor_asistente()["proveedor"] in ("local", "externo")


def test_avisos_de_respaldo_son_neutros(monkeypatch):
    _configurar(monkeypatch, False)
    _, modo, aviso = asyncio.run(assistant_provider.enriquecer_implementacion({}))
    assert modo == "local"
    assert aviso
    for palabra in ("vertex", "gemini", "google", "proyecto", "modelo", "proveedor"):
        assert palabra not in aviso.lower(), palabra
