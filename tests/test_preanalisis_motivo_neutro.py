"""IA-01: el estado del preanálisis y sus errores de proveedor nunca nombran variables ni proyectos. Sin red."""
from __future__ import annotations

import asyncio
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from features.inferencia import inferencia_service
from features.inferencia.domain.modelos_permitidos import MODELOS_PERMITIDOS
from features.preanalisis.domain.models import ControlContexto, Fragmento, ProveedorFallo, ProveedorNoDisponible
from features.preanalisis.preanalisis_service import (
    analizar_control,
    inyectar_proveedor_de_prueba,
    restablecer_proveedor_entorno,
)
from features.preanalisis.services import proveedor as mod_proveedor
from main import app

URL = "/api/v1/preanalisis"
HDR = {"X-Tenant-ID": "tenant-pre-neutro"}
MODELO = "modelo-simulado-ia01"
PROYECTO = "proyecto-simulado-ia01-no-real"
PROHIBIDOS = ("GOOGLE_CLOUD_PROJECT", "VERTEX_LOCATION", "API_KEY", "BASE_URL")
VARIABLES = ("GOOGLE_CLOUD_PROJECT", "VERTEX_LOCATION")
CUERPO = {
    "control_id": 5,
    "control": "Delegado de Protección de Datos",
    "enunciado": "Se ha designado un Delegado de Protección de Datos",
    "evidencia_esperada": "Resolución de designación",
    "referencia_normativa": "LOPDP art. 48",
    "fragmentos": [{"texto": "La organización designó formalmente a un Delegado.", "origen": "p. 1"}],
}


def _sin_nombres(texto: str, extras: tuple[str, ...] = ()) -> None:
    bajo = texto.lower()
    for t in (*PROHIBIDOS, PROYECTO, *extras, mod_proveedor.MODELO_POR_DEFECTO):
        assert t not in texto and t.lower() not in bajo, f"{t!r} aparece en: {texto}"


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    for v in VARIABLES:
        monkeypatch.delenv(v, raising=False)
    inferencia_service.inyectar_cliente_de_prueba(None)
    inferencia_service.inyectar_consumidor_de_prueba(None)
    restablecer_proveedor_entorno()
    with TestClient(app) as c:
        yield c
    inferencia_service.inyectar_cliente_de_prueba(None)
    inferencia_service.inyectar_consumidor_de_prueba(None)
    restablecer_proveedor_entorno()


def _configurar(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", PROYECTO)
    monkeypatch.setenv("VERTEX_LOCATION", "us-central1")


def test_estado_sin_proveedor_es_neutro(client: TestClient) -> None:
    r = client.get(f"{URL}/estado", headers=HDR)
    assert r.status_code == 200
    assert r.json()["disponible"] is False
    _sin_nombres(r.text, ("vertex", "gemini"))


def test_propuesta_sin_proveedor_503_es_neutra(client: TestClient) -> None:
    r = client.post(f"{URL}/analizar", json=CUERPO, headers=HDR)
    assert r.status_code == 503
    _sin_nombres(r.text, ("vertex", "gemini"))


def test_estado_con_proveedor_no_filtra_variables_en_el_motivo(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _configurar(monkeypatch)
    r = client.get(f"{URL}/estado", headers=HDR)
    cuerpo = r.json()
    assert r.status_code == 200 and cuerpo["disponible"] is True
    assert cuerpo["modelo"] in MODELOS_PERMITIDOS
    assert cuerpo["motivo"] is None
    for t in (*PROHIBIDOS, PROYECTO, "us-central1"):
        assert t not in r.text, f"{t!r} aparece en: {r.text}"


def test_propuesta_con_proveedor_que_falla_502_es_neutra(client: TestClient) -> None:
    class ProveedorRoto:
        nombre = "roto"
        modelo = MODELO

        async def proponer(self, sistema: str, usuario: str):
            raise ProveedorFallo(
                f"fallo con {PROYECTO} {MODELO} GOOGLE_CLOUD_PROJECT VERTEX_LOCATION"
            )

    inyectar_proveedor_de_prueba(ProveedorRoto())
    r = client.post(f"{URL}/analizar", json=CUERPO, headers=HDR)
    assert r.status_code == 502
    _sin_nombres(r.text, (MODELO, "vertex", "gemini"))


def test_proveedor_no_disponible_es_neutro(monkeypatch: pytest.MonkeyPatch) -> None:
    for v in VARIABLES:
        monkeypatch.delenv(v, raising=False)
    restablecer_proveedor_entorno()

    ctx = ControlContexto(**{k: v for k, v in CUERPO.items() if k != "fragmentos"})
    with pytest.raises(ProveedorNoDisponible) as exc:
        asyncio.run(analizar_control(ctx, [Fragmento(**CUERPO["fragmentos"][0])]))
    _sin_nombres(str(exc.value), ("vertex", "gemini"))
    assert exc.value.__class__ is ProveedorNoDisponible
    inyectar_proveedor_de_prueba(None)
