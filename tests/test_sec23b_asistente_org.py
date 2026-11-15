# ¤seguridad-tenant ¤arbitro
"""SEC-23b: el asistente pasa la organización autenticada al tope de inferencia.

Sin base de datos, sin red y sin `import yaml`: la compuerta de inferencia y el consumidor del tope son dobles
en memoria; la identidad sale de la dependencia `obtener_tenant_id_actual` (SEC-23), sustituida por el doble.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from types import SimpleNamespace

from api.dependencies import obtener_tenant_id_actual
from features.ai_copilot.services import assistant_provider
from main import app

RUTA = "/api/v1/ai_copilot/consulta"


class TopeAgotado(Exception):
    pass


class Compuerta:
    """Doble de la compuerta: cuenta una generación del tope de la organización que recibe."""

    def __init__(self, topes: dict[str, int]):
        self.topes, self.llamadas = dict(topes), []

    def estado(self):
        return SimpleNamespace(disponible=True)

    async def generar_estructurado(self, sistema, usuario, esquema, *, modelo, org_id):
        self.llamadas.append(org_id)
        if self.topes.get(org_id, 0) <= 0:
            raise TopeAgotado()
        self.topes[org_id] -= 1
        raise RuntimeError("salida no verificable")  # el consumo ya ocurrió; la respuesta cae al respaldo local


CUERPO = {
    "pregunta": "¿Cómo implemento esta brecha?", "estado": "Implementación", "historial": [],
    "brechas": [{"pregunta_id": 21, "control": "Gestión del consentimiento",
                 "dimension_id": "D03", "severidad": "Alto"}],
}


@pytest.fixture
def consultar(monkeypatch):
    def _consultar(compuerta, org, cuerpo=None):
        monkeypatch.setattr(assistant_provider, "pasillo_inferencia", compuerta)
        app.dependency_overrides[obtener_tenant_id_actual] = lambda: org
        try:
            return TestClient(app).post(RUTA, json=cuerpo or CUERPO)
        finally:
            app.dependency_overrides.pop(obtener_tenant_id_actual, None)
    return _consultar


def test_consulta_consume_el_tope_de_su_organizacion(consultar):
    """Mutación: pasar org_id=None desde el router con un tenant autenticado hace fallar esta prueba."""
    compuerta = Compuerta({"org-A": 3})
    r = consultar(compuerta, "org-A")
    assert r.status_code == 200
    assert compuerta.llamadas == ["org-A"]
    assert compuerta.topes["org-A"] == 2


def test_topes_separados_por_organizacion(consultar):
    compuerta = Compuerta({"org-A": 3, "org-B": 5})
    consultar(compuerta, "org-A")
    consultar(compuerta, "org-B")
    consultar(compuerta, "org-B")
    assert compuerta.topes == {"org-A": 2, "org-B": 3}


def test_org_no_sale_del_cuerpo(consultar):
    """Mutación: tomar la organización del cuerpo hace fallar esta prueba (llegaría 'org-AJENA' a la compuerta)."""
    compuerta = Compuerta({"org-A": 3, "org-AJENA": 3})
    r = consultar(compuerta, "org-A", {**CUERPO, "org_id": "org-AJENA", "tenant_id": "org-AJENA"})
    assert "org-AJENA" not in compuerta.llamadas
    assert compuerta.topes["org-AJENA"] == 3
    # El contrato del cuerpo es cerrado: el campo ajeno se rechaza antes de llegar a la compuerta.
    assert r.status_code == 422 and compuerta.llamadas == []
    r = consultar(compuerta, "org-A")
    assert r.status_code == 200 and compuerta.llamadas == ["org-A"]


def test_tope_agotado_respaldo_local(consultar):
    compuerta = Compuerta({"org-A": 0, "org-B": 2})
    r = consultar(compuerta, "org-A")
    assert r.status_code == 200
    datos = r.json()
    assert datos["modo"] == "local"
    assert assistant_provider.AVISO_NO_VERIFICABLE in datos["advertencias"]
    assert compuerta.topes["org-B"] == 2
    texto = " ".join(datos["advertencias"]).lower()
    assert "gemini" not in texto and "vertex" not in texto and "tope" not in texto
