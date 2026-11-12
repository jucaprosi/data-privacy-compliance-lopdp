"""MARCA-01: la plataforma se llama solo EVYDENTIA en /health, OpenAPI y configuración."""
from fastapi.testclient import TestClient

from app_core.config import config
from main import app


def test_health_devuelve_platform_evydentia():
    respuesta = TestClient(app).get("/health")
    assert respuesta.json()["platform"] == "EVYDENTIA"


def test_titulo_openapi_dice_evydentia():
    titulo = app.openapi()["info"]["title"]
    assert "EVYDENTIA" in titulo
    assert "JUBYS" not in titulo


def test_nombre_de_configuracion_es_evydentia():
    assert config.app_name == "EVYDENTIA"
