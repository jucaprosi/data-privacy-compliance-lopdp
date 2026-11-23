# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
"""Prueba de comportamiento: La API no inventa datos ni oculta fallos reales."""
from fastapi.testclient import TestClient
from main import app


def test_api_no_inventa_datos_en_recurso_inexistente():
    """Un recurso inexistente responde con 404 Not Found y nunca genera datos inventados."""
    client = TestClient(app)
    resp = client.get("/api/v1/recurso-inexistente-sin-inventar")
    assert resp.status_code == 404
    assert "detail" in resp.json()
