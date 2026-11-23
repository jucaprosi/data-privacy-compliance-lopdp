# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤arbitro
"""IA-04: el preanálisis usa la compuerta de inferencia sobre Vertex AI. Cliente simulado, sin red ni clave de API.

Mutaciones (cada una pone en rojo al menos una prueba de este archivo):
  M1. `estado_proveedor` devuelve `PROVEEDOR_NOMBRE = "OpenAI"` o el nombre de una variable de entorno
      -> test_estado_con_compuerta_nombra_vertex_y_modelo_cerrado.
  M2. `estado_proveedor` devuelve proveedor/modelo aunque la compuerta no esté disponible
      -> test_estado_sin_compuerta_es_null_y_neutro.
  M3. `ProveedorVertex.proponer` elude `app_core.pasillo.inferencia` (llama a otro cliente o devuelve una propuesta fija)
      -> test_proponer_pasa_por_la_compuerta_con_el_modelo_y_la_org y test_fuente_solo_usa_el_pasillo_de_inferencia.
  M4. El adaptador propaga el texto de la excepción del cliente (`raise ProveedorFallo(str(exc.__cause__))`)
      -> test_fallo_neutro_del_proveedor_nuevo y test_respuesta_invalida_del_modelo_es_fallo_neutro.
  M5. Importar `features.inferencia` o `openai` en `proveedor.py`
      -> test_fuente_solo_usa_el_pasillo_de_inferencia.
"""
from __future__ import annotations

import ast
import asyncio
from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from features.inferencia import inferencia_service as svc
from features.inferencia.domain.modelos_permitidos import MODELOS_PERMITIDOS
from features.preanalisis.domain.models import PropuestaModelo, ProveedorFallo, ProveedorNoDisponible
from features.preanalisis.preanalisis_service import restablecer_proveedor_entorno
from features.preanalisis.services import proveedor as mod
from main import app
from app_core.pasillo.inferencia import MODELO_GENERACION

URL = "/api/v1/preanalisis"
HDR = {"X-Tenant-ID": "tenant-ia04"}
RAIZ = Path(__file__).resolve().parents[1]
FUENTE = RAIZ / "features" / "preanalisis" / "services" / "proveedor.py"
PROYECTO = "proyecto-simulado-ia04-no-real"
SECRETO = "secreto-simulado-ia04"
VARIABLES = ("GOOGLE_CLOUD_PROJECT", "VERTEX_LOCATION")
PROHIBIDOS = (*VARIABLES, "API_KEY", "BASE_URL", "OPENAI", "DEEPSEEK", PROYECTO, SECRETO, "us-central1")
PROPUESTA = '{"estado": "Conforme", "citas": [], "razonamiento": "ok"}'
ORG = "11111111-2222-3333-4444-555555555555"


class _Modelos:
    """Imita `cliente.aio.models` de google-genai: registra la llamada y devuelve texto o lanza."""

    def __init__(self, texto: str | None = PROPUESTA, error: Exception | None = None) -> None:
        self.texto, self.error, self.llamadas = texto, error, []

    async def generate_content(self, **kw):  # noqa: ANN003
        self.llamadas.append(kw)
        if self.error:
            raise self.error
        return SimpleNamespace(text=self.texto)


def _cliente(modelos: _Modelos) -> SimpleNamespace:
    return SimpleNamespace(aio=SimpleNamespace(models=modelos))


def _sin_filtraciones(texto: str) -> None:
    bajo = texto.lower()
    for t in PROHIBIDOS:
        assert t.lower() not in bajo, f"{t!r} aparece en: {texto}"


@pytest.fixture()
def consumos(monkeypatch: pytest.MonkeyPatch) -> Iterator[list[str]]:
    """Compuerta sin configurar, tope simulado en memoria y proveedor de la plataforma (sin inyectar)."""
    vistos: list[str] = []

    async def consumir(org_id: str) -> None:
        vistos.append(org_id)

    for v in VARIABLES:
        monkeypatch.delenv(v, raising=False)
    svc.inyectar_cliente_de_prueba(None)
    svc.inyectar_consumidor_de_prueba(consumir)
    restablecer_proveedor_entorno()
    try:
        yield vistos
    finally:
        svc.inyectar_cliente_de_prueba(None)
        svc.inyectar_consumidor_de_prueba(None)
        restablecer_proveedor_entorno()


def _disponible(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", PROYECTO)
    monkeypatch.setenv("VERTEX_LOCATION", "us-central1")


def test_estado_con_compuerta_nombra_vertex_y_modelo_cerrado(consumos, monkeypatch) -> None:
    _disponible(monkeypatch)
    with TestClient(app) as c:
        r = c.get(f"{URL}/estado", headers=HDR)
    j = r.json()
    assert r.status_code == 200 and j["disponible"] is True and j["motivo"] is None
    assert j["proveedor"] == "Google Vertex AI"
    assert j["modelo"] == MODELO_GENERACION and j["modelo"] in MODELOS_PERMITIDOS
    _sin_filtraciones(r.text)


def test_estado_sin_compuerta_es_null_y_neutro(consumos) -> None:
    with TestClient(app) as c:
        r = c.get(f"{URL}/estado", headers=HDR)
    j = r.json()
    assert r.status_code == 200 and j["disponible"] is False
    assert j["proveedor"] is None and j["modelo"] is None
    assert j["motivo"] == mod.MOTIVO_NO_DISPONIBLE
    _sin_filtraciones(r.text)
    assert "vertex" not in r.text.lower() and "gemini" not in r.text.lower()


def test_sin_compuerta_no_hay_proveedor(consumos) -> None:
    assert mod.obtener_proveedor() is None


def test_proponer_pasa_por_la_compuerta_con_el_modelo_y_la_org(consumos, monkeypatch) -> None:
    _disponible(monkeypatch)
    modelos = _Modelos()
    svc.inyectar_cliente_de_prueba(_cliente(modelos))
    proveedor = mod.obtener_proveedor()
    assert isinstance(proveedor, mod.ProveedorVertex)
    p = asyncio.run(proveedor.proponer("sis", "usu", org_id=ORG))
    assert isinstance(p, PropuestaModelo) and p.estado == "Conforme"
    assert len(modelos.llamadas) == 1 and modelos.llamadas[0]["model"] == MODELO_GENERACION
    assert consumos == [ORG]


def test_fallo_neutro_del_proveedor_nuevo(consumos, monkeypatch) -> None:
    """El cliente de la sala `inferencia` falla con un texto sensible: el preanálisis responde neutro."""
    _disponible(monkeypatch)
    error = RuntimeError(f"{SECRETO} {PROYECTO} GOOGLE_CLOUD_PROJECT API_KEY")
    svc.inyectar_cliente_de_prueba(_cliente(_Modelos(error=error)))
    with pytest.raises(ProveedorFallo) as exc:
        asyncio.run(mod.ProveedorVertex().proponer("sis", "usu", org_id=ORG))
    _sin_filtraciones(str(exc.value))


def test_respuesta_invalida_del_modelo_es_fallo_neutro(consumos, monkeypatch) -> None:
    _disponible(monkeypatch)
    svc.inyectar_cliente_de_prueba(_cliente(_Modelos(texto=f"no es json {SECRETO}")))
    with pytest.raises(ProveedorFallo) as exc:
        asyncio.run(mod.ProveedorVertex().proponer("sis", "usu", org_id=ORG))
    _sin_filtraciones(str(exc.value))


def test_compuerta_caida_entre_estado_y_llamada_es_no_disponible_neutro(consumos, monkeypatch) -> None:
    """Sin configuración la compuerta falla cerrada; el adaptador lo traduce a no disponible, sin nombres."""
    proveedor = mod.ProveedorVertex()
    with pytest.raises(ProveedorNoDisponible) as exc:
        asyncio.run(proveedor.proponer("sis", "usu", org_id=ORG))
    assert str(exc.value) == mod.MOTIVO_NO_DISPONIBLE
    _sin_filtraciones(str(exc.value))


@pytest.mark.parametrize("org_id", ["", "   "])
def test_org_vacia_falla_cerrado_sin_llamar_a_la_compuerta(consumos, monkeypatch, org_id) -> None:
    _disponible(monkeypatch)
    modelos = _Modelos()
    svc.inyectar_cliente_de_prueba(_cliente(modelos))
    with pytest.raises(ProveedorNoDisponible):
        asyncio.run(mod.ProveedorVertex().proponer("sis", "usu", org_id=org_id))
    assert modelos.llamadas == [] and consumos == []


def test_la_org_explicita_y_el_modelo_llegan_tal_cual_al_pasillo(monkeypatch) -> None:
    vistos: list[tuple[str, str]] = []

    async def espia(sistema, usuario, esquema, *, modelo, org_id):  # noqa: ANN001
        assert esquema is PropuestaModelo
        vistos.append((modelo, org_id))
        return PropuestaModelo(estado="Conforme", citas=[], razonamiento="ok")

    monkeypatch.setattr(mod.pasillo_inferencia, "generar_estructurado", espia)
    asyncio.run(mod.ProveedorVertex().proponer("sis", "usu", org_id=ORG))
    assert vistos == [(MODELO_GENERACION, ORG)]


def test_fuente_solo_usa_el_pasillo_de_inferencia() -> None:
    texto = FUENTE.read_text(encoding="utf-8")
    for prohibido in ("openai", "deepseek", "api_key", "os.environ", "getenv"):
        assert prohibido not in texto.lower(), prohibido
    modulos: set[str] = set()
    for nodo in ast.walk(ast.parse(texto)):
        if isinstance(nodo, ast.ImportFrom):
            modulos.add(nodo.module or "")
            if nodo.module == "app_core.pasillo":
                assert [a.name for a in nodo.names] == ["inferencia"]
        elif isinstance(nodo, ast.Import):
            modulos.update(a.name for a in nodo.names)
    assert "app_core.pasillo" in modulos
    assert not any(m.startswith("features.inferencia") for m in modulos)
    assert not any(m.startswith(("google", "httpx", "requests")) for m in modulos)
