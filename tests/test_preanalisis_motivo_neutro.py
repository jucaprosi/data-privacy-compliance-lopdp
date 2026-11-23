# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
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

# === DIAG-07 ===
# R6: pide la propuesta quien responde (aquí el administrador, que responde en todas las dimensiones) y solo
# sobre una pregunta con evidencia vinculada por el DPO. Cambian la petición y sus cabeceras, no las aserciones.
HDR_PEDIR = {**HDR, "X-User-ID": "admin-preanalisis", "X-Role": "admin_organizacion"}


def _vincular_evidencia(tenant: str, pregunta_id: int) -> None:
    """El DPO subió y vinculó un documento a la pregunta (catálogo en memoria, subida firmada apagada)."""
    import uuid

    from features.evidencias.domain.models import EvidenciaRegistro
    from features.evidencias.services.evidencias_engine import registrar_evidencia

    registrar_evidencia(EvidenciaRegistro(
        tenant_id=tenant, nombre_archivo="designacion.pdf", sha256_hash=uuid.uuid4().hex * 2,
        controles_vinculados=[pregunta_id],
    ))
# === fin DIAG-07 ===
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
    _vincular_evidencia(HDR["X-Tenant-ID"], CUERPO["control_id"])  # DIAG-07 R6
    # La membresía la valida get_context contra la base (ORG); aquí el contexto es el de un administrador ya
    # validado, como en test_dlp01_sampling_discovery.py. R6 se comprueba igual en exigir_puede_pedir_propuesta.
    from api.rbac import get_context

    app.dependency_overrides[get_context] = lambda: {
        "tenant_id": HDR["X-Tenant-ID"], "user_id": HDR_PEDIR["X-User-ID"], "role": HDR_PEDIR["X-Role"],
    }
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.pop(get_context, None)  # DIAG-07: no se filtra a otras suites
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
    r = client.post(f"{URL}/analizar", json={**CUERPO, "dimension": "D01"}, headers=HDR_PEDIR)
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
    r = client.post(f"{URL}/analizar", json={**CUERPO, "dimension": "D01"}, headers=HDR_PEDIR)
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


# === IA-04 ===
# La sala depende, para la IA, solo del pasillo de inferencia (y este de google-genai): ningún SDK ni cliente HTTP
# propio, ninguna importación directa de la sala `inferencia`. Mutación: `import openai` o
# `from features.inferencia import inferencia_service` en cualquier archivo de features/preanalisis.
def test_preanalisis_depende_solo_del_pasillo_de_inferencia() -> None:
    import ast
    from pathlib import Path

    sala = Path(__file__).resolve().parents[1] / "features" / "preanalisis"
    prohibidos = ("openai", "anthropic", "google", "vertexai", "httpx", "requests", "aiohttp", "features.inferencia")
    pasillos: set[str] = set()
    for archivo in sala.rglob("*.py"):
        for nodo in ast.walk(ast.parse(archivo.read_text(encoding="utf-8"))):
            if isinstance(nodo, ast.Import):
                modulos = [a.name for a in nodo.names]
            elif isinstance(nodo, ast.ImportFrom):
                modulos = [nodo.module or ""]
                if nodo.module == "app_core.pasillo":
                    pasillos.update(a.name for a in nodo.names)
            else:
                continue
            for m in modulos:
                assert not m.startswith(prohibidos), f"{archivo.name} importa {m}"
                assert not (m.startswith("app_core.pasillo.") and m != "app_core.pasillo.inferencia"), m
    assert pasillos <= {"inferencia"}, pasillos
# === fin IA-04 ===
