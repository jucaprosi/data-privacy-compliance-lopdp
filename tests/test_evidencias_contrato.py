"""Contrato de la Bóveda de Evidencias: integridad SHA-256, vínculos y aislamiento."""
from __future__ import annotations

import hashlib
from collections.abc import Iterator
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from features.evidencias.evidencias_service import reiniciar_repositorio_evidencias
from main import app

URL = "/api/v1/evidencias"
TENANT_A = {"X-Tenant-ID": "tenant-evd-a"}
TENANT_B = {"X-Tenant-ID": "tenant-evd-b"}


@pytest.fixture()
def client() -> Iterator[TestClient]:
    reiniciar_repositorio_evidencias()
    with TestClient(app) as c:
        yield c
    reiniciar_repositorio_evidencias()


def _sha(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def _registrar(client: TestClient, headers: dict[str, str], **campos: object) -> dict:
    payload: dict[str, object] = {"nombre_archivo": "politica.pdf"}
    payload.update(campos)
    resp = client.post(URL, json=payload, headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_hash_precalculado_se_guarda_tal_cual(client: TestClient) -> None:
    h = _sha("documento binario simulado")
    data = _registrar(client, TENANT_A, sha256_hash=h.upper(), tamano_bytes=2048, tipo_mime="application/pdf")
    evd = data["evidencia"]
    assert evd["sha256_hash"] == h
    assert evd["sha256_hash"] != _sha(h)
    assert evd["tamano_bytes"] == 2048
    assert evd["tipo_mime"] == "application/pdf"
    assert evd["normativa"] == "LOPDP"
    assert data["duplicada"] is False


def test_texto_se_hashea_como_hashlib(client: TestClient) -> None:
    texto = "Política de privacidad — versión 1"
    evd = _registrar(client, TENANT_A, contenido_texto=texto)["evidencia"]
    assert evd["sha256_hash"] == hashlib.sha256(texto.encode("utf-8")).hexdigest()
    assert evd["tamano_bytes"] == len(texto.encode("utf-8"))


def test_hash_y_texto_coincidentes_se_aceptan(client: TestClient) -> None:
    texto = "contenido coherente"
    evd = _registrar(client, TENANT_A, contenido_texto=texto, sha256_hash=_sha(texto))["evidencia"]
    assert evd["sha256_hash"] == _sha(texto)


def test_conflicto_hash_texto_devuelve_422(client: TestClient) -> None:
    resp = client.post(
        URL,
        json={"nombre_archivo": "x.pdf", "sha256_hash": _sha("A"), "contenido_texto": "B"},
        headers=TENANT_A,
    )
    assert resp.status_code == 422


@pytest.mark.parametrize("invalido", ["abc", "z" * 64, "a" * 63, "a" * 65, ""])
def test_hash_invalido_devuelve_422(client: TestClient, invalido: str) -> None:
    resp = client.post(URL, json={"nombre_archivo": "x.pdf", "sha256_hash": invalido}, headers=TENANT_A)
    assert resp.status_code == 422


def test_sin_hash_ni_texto_devuelve_422(client: TestClient) -> None:
    resp = client.post(URL, json={"nombre_archivo": "x.pdf"}, headers=TENANT_A)
    assert resp.status_code == 422


def test_campo_obsoleto_distingue_hash_de_texto(client: TestClient) -> None:
    h = _sha("archivo")
    evd_hash = _registrar(client, TENANT_A, contenido_texto_o_hash=h)["evidencia"]
    assert evd_hash["sha256_hash"] == h
    evd_texto = _registrar(client, TENANT_A, nombre_archivo="b.txt", contenido_texto_o_hash="texto libre")["evidencia"]
    assert evd_texto["sha256_hash"] == _sha("texto libre")


def test_duplicado_incorpora_los_controles_pedidos(client: TestClient) -> None:
    h = _sha("documento vinculado dos veces")
    primera = _registrar(client, TENANT_A, sha256_hash=h, controles_vinculados=[9])["evidencia"]
    segunda = _registrar(client, TENANT_A, sha256_hash=h, controles_vinculados=[12, 9])
    assert segunda["duplicada"] is True
    assert segunda["evidencia"]["id"] == primera["id"]
    assert segunda["evidencia"]["controles_vinculados"] == [9, 12]


def test_duplicado_devuelve_existente(client: TestClient) -> None:
    h = _sha("mismo documento")
    primera = _registrar(client, TENANT_A, sha256_hash=h, controles_vinculados=[3])
    segunda = _registrar(client, TENANT_A, sha256_hash=h, nombre_archivo="copia.pdf")
    assert segunda["duplicada"] is True
    assert segunda["evidencia"]["id"] == primera["evidencia"]["id"]
    assert client.get(URL, headers=TENANT_A).json()["total"] == 1
    otra_norma = _registrar(client, TENANT_A, sha256_hash=h, normativa="ISO27001")
    assert otra_norma["duplicada"] is False
    assert otra_norma["evidencia"]["id"] != primera["evidencia"]["id"]


def test_listar_filtra_por_normativa(client: TestClient) -> None:
    _registrar(client, TENANT_A, sha256_hash=_sha("1"))
    _registrar(client, TENANT_A, sha256_hash=_sha("2"), normativa="ISO27001")
    todas = client.get(URL, headers=TENANT_A).json()
    assert todas["total"] == 2
    iso = client.get(URL, params={"normativa": "ISO27001"}, headers=TENANT_A).json()
    assert iso["total"] == 1
    assert iso["evidencias"][0]["normativa"] == "ISO27001"


def test_vincular_y_desvincular_controles(client: TestClient) -> None:
    evd = _registrar(client, TENANT_A, sha256_hash=_sha("v"), controles_vinculados=[5, 1, 5])["evidencia"]
    assert evd["controles_vinculados"] == [1, 5]
    url = f"{URL}/{evd['id']}/vinculos"
    resp = client.patch(url, json={"agregar": [80, 12]}, headers=TENANT_A)
    assert resp.status_code == 200
    assert resp.json()["evidencia"]["controles_vinculados"] == [1, 5, 12, 80]
    resp = client.patch(url, json={"quitar": [5, 40]}, headers=TENANT_A)
    assert resp.json()["evidencia"]["controles_vinculados"] == [1, 12, 80]


@pytest.mark.parametrize("fuera", [0, 81, -1])
def test_controles_fuera_de_rango_422(client: TestClient, fuera: int) -> None:
    resp = client.post(
        URL, json={"nombre_archivo": "x.pdf", "sha256_hash": _sha("r"), "controles_vinculados": [fuera]}, headers=TENANT_A
    )
    assert resp.status_code == 422
    evd = _registrar(client, TENANT_A, sha256_hash=_sha("r"))["evidencia"]
    resp = client.patch(f"{URL}/{evd['id']}/vinculos", json={"agregar": [fuera]}, headers=TENANT_A)
    assert resp.status_code == 422


def test_vinculos_evidencia_inexistente_404(client: TestClient) -> None:
    resp = client.patch(f"{URL}/no-existe/vinculos", json={"agregar": [1]}, headers=TENANT_A)
    assert resp.status_code == 404


def test_verificar_por_hash(client: TestClient) -> None:
    h = _sha("verificable")
    evd = _registrar(client, TENANT_A, sha256_hash=h)["evidencia"]
    ok = client.get(f"{URL}/verificar/{h.upper()}", headers=TENANT_A).json()
    assert ok["coincide"] is True
    assert ok["evidencia"]["id"] == evd["id"]
    no = client.get(f"{URL}/verificar/{_sha('otro')}", headers=TENANT_A).json()
    assert no == {"sha256_hash": _sha("otro"), "coincide": False, "evidencia": None}
    assert client.get(f"{URL}/verificar/no-es-hash", headers=TENANT_A).status_code == 422


def test_aislamiento_entre_tenants(client: TestClient) -> None:
    h = _sha("confidencial")
    evd = _registrar(client, TENANT_A, sha256_hash=h)["evidencia"]
    assert client.get(URL, headers=TENANT_B).json()["total"] == 0
    assert client.get(f"{URL}/verificar/{h}", headers=TENANT_B).json()["coincide"] is False
    resp = client.patch(f"{URL}/{evd['id']}/vinculos", json={"agregar": [2]}, headers=TENANT_B)
    assert resp.status_code == 404
    propia_b = _registrar(client, TENANT_B, sha256_hash=h)
    assert propia_b["duplicada"] is False
    assert propia_b["evidencia"]["id"] != evd["id"]
    assert client.get(URL, headers=TENANT_A).json()["evidencias"][0]["controles_vinculados"] == []


def test_codigo_correlativo_no_se_repite(client: TestClient) -> None:
    anio = datetime.now(timezone.utc).year
    _registrar(client, TENANT_A, sha256_hash=_sha("c1"))
    _registrar(client, TENANT_A, sha256_hash=_sha("c2"), codigo=f"EVD-{anio}-0007")
    tercera = _registrar(client, TENANT_A, sha256_hash=_sha("c3"))["evidencia"]
    assert tercera["codigo"] == f"EVD-{anio}-0008"
    codigos = [e["codigo"] for e in client.get(URL, headers=TENANT_A).json()["evidencias"]]
    assert len(codigos) == len(set(codigos))
    # Otro tenant arranca su propia secuencia
    assert _registrar(client, TENANT_B, sha256_hash=_sha("c1"))["evidencia"]["codigo"] == f"EVD-{anio}-0001"


def test_codigo_correlativo_usa_maximo_tras_borrado(client: TestClient) -> None:
    from features.evidencias.services.evidencias_engine import repo_evidencias

    anio = datetime.now(timezone.utc).year
    e1 = _registrar(client, TENANT_A, sha256_hash=_sha("d1"))["evidencia"]
    _registrar(client, TENANT_A, sha256_hash=_sha("d2"))
    del repo_evidencias._store[e1["id"]]  # simula borrado de la primera
    nueva = _registrar(client, TENANT_A, sha256_hash=_sha("d3"))["evidencia"]
    assert nueva["codigo"] == f"EVD-{anio}-0003"


def test_codigo_explicito_repetido_409(client: TestClient) -> None:
    _registrar(client, TENANT_A, sha256_hash=_sha("k1"), codigo="EVD-MANUAL-1")
    resp = client.post(
        URL, json={"nombre_archivo": "y.pdf", "sha256_hash": _sha("k2"), "codigo": "EVD-MANUAL-1"}, headers=TENANT_A
    )
    assert resp.status_code == 409
