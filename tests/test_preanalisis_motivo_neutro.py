"""IA-01: el estado del preanálisis y sus errores de proveedor nunca nombran variables, claves ni modelos. Sin red."""
from __future__ import annotations

import json
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from features.preanalisis.domain.models import ProveedorFallo, ProveedorNoDisponible
from features.preanalisis.preanalisis_service import (
    inyectar_proveedor_de_prueba,
    restablecer_proveedor_entorno,
)
from features.preanalisis.services import proveedor as mod_proveedor
from main import app

URL = "/api/v1/preanalisis"
HDR = {"X-Tenant-ID": "tenant-pre-neutro"}
MODELO = "modelo-simulado-ia01"
CLAVE = "valor-simulado-ia01-no-real"
PROHIBIDOS = ("API_KEY", "PREANALISIS_", "OPENAI_", "DEEPSEEK_", "BASE_URL")
VARIABLES = (
    "PREANALISIS_API_KEY", "OPENAI_API_KEY", "PREANALISIS_BASE_URL", "PREANALISIS_MODEL",
    "DEEPSEEK_API_KEY", "DEEPSEEK_BASE_URL", "DEEPSEEK_MODEL",
)
CUERPO = {
    "control_id": 5,
    "control": "Delegado de Protección de Datos",
    "enunciado": "Se ha designado un Delegado de Protección de Datos",
    "evidencia_esperada": "Resolución de designación",
    "referencia_normativa": "LOPDP art. 48",
    "fragmentos": [{"texto": "La organización designó formalmente a un Delegado.", "origen": "p. 1"}],
}


def _sin_nombres(texto: str, modelos: tuple[str, ...] = ()) -> None:
    for t in (*PROHIBIDOS, CLAVE, *modelos, mod_proveedor.MODELO_POR_DEFECTO):
        assert t not in texto, f"{t!r} aparece en: {texto}"


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    for v in VARIABLES:
        monkeypatch.delenv(v, raising=False)
    restablecer_proveedor_entorno()
    with TestClient(app) as c:
        yield c
    restablecer_proveedor_entorno()


def _configurar(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PREANALISIS_API_KEY", CLAVE)
    monkeypatch.setenv("PREANALISIS_BASE_URL", "http://servidor-simulado.invalid/v1")
    monkeypatch.setenv("PREANALISIS_MODEL", MODELO)


def test_estado_sin_proveedor_es_neutro(client: TestClient) -> None:
    r = client.get(f"{URL}/estado", headers=HDR)
    assert r.status_code == 200
    assert r.json()["disponible"] is False
    _sin_nombres(r.text)


def test_propuesta_sin_proveedor_503_es_neutra(client: TestClient) -> None:
    r = client.post(f"{URL}/analizar", json=CUERPO, headers=HDR)
    assert r.status_code == 503
    _sin_nombres(r.text)


def test_estado_con_proveedor_no_filtra_nombres_en_el_motivo(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _configurar(monkeypatch)
    r = client.get(f"{URL}/estado", headers=HDR)
    cuerpo = r.json()
    assert r.status_code == 200 and cuerpo["disponible"] is True
    # `modelo` es un campo del contrato público; el resto del cuerpo no nombra nada interno.
    resto = {k: v for k, v in cuerpo.items() if k != "modelo"}
    _sin_nombres(json.dumps(resto), (MODELO,))


def test_propuesta_con_proveedor_que_falla_502_es_neutra(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _configurar(monkeypatch)

    class ClienteRoto:
        def __init__(self, *a: object, **k: object) -> None:
            raise RuntimeError(f"fallo con {CLAVE} {MODELO} PREANALISIS_API_KEY BASE_URL")

    monkeypatch.setattr("openai.AsyncOpenAI", ClienteRoto)
    r = client.post(f"{URL}/analizar", json=CUERPO, headers=HDR)
    assert r.status_code == 502
    _sin_nombres(r.text, (MODELO,))


@pytest.mark.anyio
async def test_proveedor_fallo_real_es_neutro(monkeypatch: pytest.MonkeyPatch) -> None:
    class ClienteRoto:
        def __init__(self, *a: object, **k: object) -> None:
            raise RuntimeError(f"fallo con {CLAVE} {MODELO} OPENAI_API_KEY DEEPSEEK_BASE_URL")

    monkeypatch.setattr("openai.AsyncOpenAI", ClienteRoto)
    p = mod_proveedor.ProveedorOpenAICompatible(CLAVE, "http://servidor-simulado.invalid/v1", MODELO)
    with pytest.raises(ProveedorFallo) as exc:
        await p.proponer("s", "u")
    _sin_nombres(str(exc.value), (MODELO,))


def test_proveedor_no_disponible_es_neutro(monkeypatch: pytest.MonkeyPatch) -> None:
    for v in VARIABLES:
        monkeypatch.delenv(v, raising=False)
    restablecer_proveedor_entorno()
    from features.preanalisis.preanalisis_service import analizar_control
    from features.preanalisis.domain.models import ControlContexto, Fragmento
    import asyncio

    ctx = ControlContexto(**{k: v for k, v in CUERPO.items() if k != "fragmentos"})
    with pytest.raises(ProveedorNoDisponible) as exc:
        asyncio.run(analizar_control(ctx, [Fragmento(**CUERPO["fragmentos"][0])]))
    _sin_nombres(str(exc.value))
    assert exc.value.__class__ is ProveedorNoDisponible
    inyectar_proveedor_de_prueba(None)
