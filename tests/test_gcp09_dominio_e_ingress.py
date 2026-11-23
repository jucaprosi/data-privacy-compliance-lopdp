# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
"""GCP-09 · app.evydentia.com, ingress interno con el balanceador y opción 1 (sin IAM).

`¤ci-cd` `¤arbitro`
"""
from __future__ import annotations

import json
import os
import secrets
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

import pytest

from app_core.config import REGLA_CONFIGURACION, exigir_configuracion_en_la_nube
from tests._lector_yaml import leer_yaml

RAIZ = Path(__file__).resolve().parents[1]
OPS = RAIZ / "governance/operaciones"
BACKEND = OPS / "cloudrun_service.yaml"
FRONTEND = OPS / "cloudrun_frontend_service.yaml"
BALANCEADOR = OPS / "cloud_load_balancer.yaml"

INGRESS = "internal-and-cloud-load-balancing"


def _cargar(ruta: Path):
    return leer_yaml(ruta.read_text(encoding="utf-8"))


def _servicios(ruta: Path) -> list[dict]:
    docs = _cargar(ruta)
    lista = docs if isinstance(docs, list) else [docs]
    return [d for d in lista if isinstance(d, dict) and d.get("kind") == "Service"]


def _todos() -> list[dict]:
    return _servicios(BACKEND) + _servicios(FRONTEND)


def _anotacion_servicio(doc: dict, clave: str) -> str | None:
    return (doc.get("metadata", {}).get("annotations") or {}).get(clave)


def _anotacion_plantilla(doc: dict, clave: str) -> str | None:
    return (doc.get("spec", {}).get("template", {}).get("metadata", {}).get("annotations") or {}).get(clave)


def _env(doc: dict, nombre: str) -> str | None:
    contenedor = doc["spec"]["template"]["spec"]["containers"][0]
    for entry in contenedor.get("env", []):
        if entry.get("name") == nombre:
            return entry.get("value")
    return None


def test_01_ingress_interno_con_balanceador():
    servicios = _todos()
    assert len(servicios) >= 2
    for doc in servicios:
        nombre = doc["metadata"]["name"]
        assert _anotacion_servicio(doc, "run.googleapis.com/ingress") == INGRESS, nombre


def test_02_frontend_sin_token_de_servicio():
    for doc in _servicios(FRONTEND):
        assert _env(doc, "PROXY_AUTH_CLOUD_RUN") == "ninguna", doc["metadata"]["name"]


def test_04_cors_solo_https():
    entorno_base = {
        "K_SERVICE": "evydentia-backend",
        "DATABASE_URL": "postgresql+psycopg://lopdp_app:clave-prueba@db.ejemplo.invalid:5432/evydentia",
    }
    exigir_configuracion_en_la_nube({**entorno_base, "CORS_ORIGINS": "https://app.evydentia.com"})
    for origen_invalido in ("http://app.evydentia.com", "*", "https://app.evydentia.com/ruta"):
        with pytest.raises(RuntimeError) as exc:
            exigir_configuracion_en_la_nube({**entorno_base, "CORS_ORIGINS": origen_invalido})
        assert REGLA_CONFIGURACION in str(exc.value) and "CORS_ORIGINS" in str(exc.value)

    env = {k: v for k, v in os.environ.items() if "DATABASE_URL" not in k}
    env.update(
        K_SERVICE="evydentia-backend",
        AUTH_MODE="oidc",
        DATABASE_URL=entorno_base["DATABASE_URL"],
        CORS_ORIGINS="https://app.evydentia.com",
        JWT_SECRET=secrets.token_urlsafe(32),
        SESSION_SECRET=secrets.token_urlsafe(32),
        PROXIES_CONFIABLES="1",
        PYTHONIOENCODING="utf-8",
    )
    codigo = (
        "import json; from fastapi.testclient import TestClient; from main import app; "
        "c = TestClient(app); "
        "ok = c.options('/health', headers={'Origin': 'https://app.evydentia.com', 'Access-Control-Request-Method': 'GET'}); "
        "bad = c.options('/health', headers={'Origin': 'http://app.evydentia.com', 'Access-Control-Request-Method': 'GET'}); "
        "print(json.dumps({'ok': ok.headers.get('access-control-allow-origin'), 'bad': bad.headers.get('access-control-allow-origin')}))"
    )
    res = subprocess.run([sys.executable, "-c", codigo], cwd=RAIZ, env=env, capture_output=True, text=True, timeout=180)
    assert res.returncode == 0, res.stderr[-2000:]
    datos = json.loads(res.stdout.strip().splitlines()[-1])
    assert datos["ok"] == "https://app.evydentia.com"
    assert datos["bad"] is None


def test_06_backend_url_no_es_run_app_sin_egress_total():
    backend_interno = all(_anotacion_servicio(d, "run.googleapis.com/ingress") == INGRESS for d in _servicios(BACKEND))
    for doc in _servicios(FRONTEND):
        url = _env(doc, "BACKEND_URL") or ""
        host = urlparse(url).hostname or ""
        if backend_interno and host.endswith(".run.app"):
            assert _anotacion_plantilla(doc, "run.googleapis.com/vpc-access-egress") == "all-traffic", url


def test_07_sin_exigir_invoker():
    for doc in _todos():
        assert _anotacion_servicio(doc, "run.googleapis.com/invoker-iam-disabled") == "true"


def test_08_certificado_y_cors_mismo_host():
    balanceador = _cargar(BALANCEADOR)
    hosts_cert = set(balanceador["certificado_administrado"]["dominios"])
    assert hosts_cert == {"app.evydentia.com"}
    produccion = _servicios(FRONTEND)[0]
    url_backend = _env(produccion, "BACKEND_URL") or ""
    partes = urlparse(url_backend)
    assert partes.scheme == "https" and partes.hostname in hosts_cert
    exigir_configuracion_en_la_nube({
        "K_SERVICE": "evydentia-backend",
        "DATABASE_URL": "postgresql+psycopg://lopdp_app:clave-prueba@db.ejemplo.invalid:5432/evydentia",
        "CORS_ORIGINS": f"https://{partes.hostname}",
    })


def _coincide(regla: str, ruta: str) -> bool:
    """Semántica de pathRules: «/x/*» casa con «/x/» y todo lo que siga; sin «*», ruta exacta."""
    if regla.endswith("/*"):
        return ruta.startswith(regla[:-1]) or ruta == regla[:-2]
    return ruta == regla


def test_09_backend_solo_api_v1_y_rutas_del_frontend_fuera():
    balanceador = _cargar(BALANCEADOR)
    reglas_matcher = [r for m in balanceador["url_map"]["pathMatchers"] for r in m["pathRules"]]
    reglas_backend = [p for r in reglas_matcher if r["service"] == "evydentia-backend-bs" for p in r["paths"]]
    assert reglas_backend == ["/api/v1/*"]
    raiz_api = RAIZ / "frontend/src/app/api"
    rutas = []
    for handler in raiz_api.rglob("route.ts"):
        partes = handler.relative_to(raiz_api).parent.parts
        if partes and partes[0] == "v1":
            continue  # el proxy de GCP-08: el navegador va directo al backend
        segmentos = [("x" if p.startswith("[") else p) for p in partes]
        rutas.append("/api/" + "/".join(segmentos))
    assert rutas, "no se encontraron rutas propias del frontend bajo /api"
    for ruta in rutas:
        for regla in reglas_backend:
            assert not _coincide(regla, ruta) and not _coincide(regla, ruta + "/"), (regla, ruta)


def test_10_neg_del_balanceador_coincide_con_servicios():
    nombres = {doc["metadata"]["name"] for doc in _todos()}
    balanceador = _cargar(BALANCEADOR)
    negs = [s["neg_serverless"] for s in balanceador["servicios_backend"]]
    assert negs and set(negs) <= nombres, (negs, nombres)
