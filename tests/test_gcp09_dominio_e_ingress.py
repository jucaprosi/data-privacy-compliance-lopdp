"""GCP-09 · app.evydentia.com, ingress interno con el balanceador y opción 1 (sin IAM).

`¤ci-cd` `¤arbitro`
"""

import re
from pathlib import Path
from urllib.parse import urlparse

RAIZ = Path(__file__).resolve().parents[1]
OPS = RAIZ / "governance/operaciones"
BACKEND = OPS / "cloudrun_service.yaml"
FRONTEND = OPS / "cloudrun_frontend_service.yaml"
BALANCEADOR = OPS / "cloud_load_balancer.yaml"
BRIEF = RAIZ / "governance/apoyo/BRIEF_PROPIETARIO_GCP_2026-11-08.md"

INGRESS = "internal-and-cloud-load-balancing"


def _leer(ruta: Path) -> str:
    return ruta.read_text(encoding="utf-8")


def _servicios(ruta: Path) -> list[str]:
    """Documentos Knative del manifiesto (sin PyYAML: el repositorio no lo trae)."""
    return [d for d in re.split(r"^---\s*$", _leer(ruta), flags=re.M) if "kind: Service" in d]


def _anotacion(doc: str, clave: str) -> list[str]:
    return [v.strip().strip('"') for v in re.findall(rf"^\s*{re.escape(clave)}:\s*(\S+)", doc, flags=re.M)]


def _env(doc: str, nombre: str) -> str | None:
    m = re.search(rf"-\s*name:\s*{re.escape(nombre)}\b[^\n]*\n\s*value:\s*(\S+)", doc)
    return m.group(1).strip('"') if m else None


def _todos() -> list[str]:
    return _servicios(BACKEND) + _servicios(FRONTEND)


def test_01_ingress_interno_con_balanceador():
    servicios = _todos()
    assert len(servicios) >= 2
    for doc in servicios:
        assert _anotacion(doc, "run.googleapis.com/ingress") == [INGRESS], doc[:80]


def test_02_frontend_sin_token_de_servicio():
    for doc in _servicios(FRONTEND):
        assert _env(doc, "PROXY_AUTH_CLOUD_RUN") == "ninguna"


def test_03_sin_marcadores_de_ejemplo():
    for ruta in (BACKEND, FRONTEND, BALANCEADOR, BRIEF):
        texto = _leer(ruta)
        assert not re.search(r"\bDOMINIO\b", texto), ruta.name
        assert not re.search(r"\.example\b|example\.(com|org)", texto), ruta.name


def _cors() -> list[str]:
    origenes = re.findall(r"CORS_ORIGINS=(\S+?)`", _leer(BRIEF))
    assert origenes
    return [o for valor in origenes for o in valor.split(",")]


def test_04_cors_solo_https():
    for origen in _cors():
        assert origen.startswith("https://") and not origen.startswith("http://")


def test_05_brief_pide_ingress_en_el_workflow():
    texto = _leer(BRIEF)
    parrafo = next(p for p in texto.split("\n") if "deploy-gcp.yml" in p and "--ingress" in p)
    assert f"--ingress {INGRESS}" in parrafo
    assert "backend" in parrafo and "frontend" in parrafo


def test_06_backend_url_no_es_run_app_sin_egress_total():
    backend_interno = all(_anotacion(d, "run.googleapis.com/ingress") == [INGRESS] for d in _servicios(BACKEND))
    for doc in _servicios(FRONTEND):
        url = _env(doc, "BACKEND_URL") or ""
        host = urlparse(url).hostname or ""
        if backend_interno and host.endswith(".run.app"):
            assert _anotacion(doc, "run.googleapis.com/vpc-access-egress") == ["all-traffic"], url


def test_07_sin_exigir_invoker():
    for doc in _todos():
        assert _anotacion(doc, "run.googleapis.com/invoker-iam-disabled") == ["true"]


def test_08_certificado_y_cors_mismo_host():
    texto = _leer(BALANCEADOR)
    dominios = re.search(r"certificado_administrado:\s*\n(?:\s+.*\n)*?\s+dominios:\s*\[([^\]]+)\]", texto)
    assert dominios
    hosts_cert = {d.strip() for d in dominios.group(1).split(",")}
    hosts_cors = {urlparse(o).hostname for o in _cors()}
    assert hosts_cert == hosts_cors == {"app.evydentia.com"}
    produccion = _servicios(FRONTEND)[0]
    assert urlparse(_env(produccion, "BACKEND_URL") or "").hostname in hosts_cert


def _reglas_backend() -> list[str]:
    texto = _leer(BALANCEADOR)
    reglas = re.findall(r"paths:\s*\[([^\]]+)\]\s*\n\s*service:\s*(\S+)", texto)
    return [p.strip().strip('"') for paths, svc in reglas if svc == "evydentia-backend-bs" for p in paths.split(",")]


def _coincide(regla: str, ruta: str) -> bool:
    """Semántica de pathRules: «/x/*» casa con «/x/» y todo lo que siga; sin «*», ruta exacta."""
    if regla.endswith("/*"):
        return ruta.startswith(regla[:-1]) or ruta == regla[:-2]
    return ruta == regla


def test_09_backend_solo_api_v1_y_rutas_del_frontend_fuera():
    assert _reglas_backend() == ["/api/v1/*"]
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
        for regla in _reglas_backend():
            assert not _coincide(regla, ruta) and not _coincide(regla, ruta + "/"), (regla, ruta)
