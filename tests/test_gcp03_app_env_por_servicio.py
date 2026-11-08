"""GCP-03 · Una sola imagen del frontend; APP_ENV por servicio y al ejecutar (§5.5, EP-02).

`¤cloud-run-perf` `¤seguridad`

La prueba de la imagen real corre si existe `GCP03_IMAGEN` (etiqueta local construida con
`frontend/Dockerfile.cloudrun`) y Docker está disponible; si no, se omite.
"""

import os
import re
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path

import pytest

from app_core.entorno import guardias

RAIZ = Path(__file__).resolve().parents[1]
DOCKERFILE = RAIZ / "frontend/Dockerfile.cloudrun"
SERVICIO = RAIZ / "governance/operaciones/cloudrun_frontend_service.yaml"
DEPLOY_BACKEND = RAIZ / ".github/workflows/deploy-gcp.yml"


def _app_env_frontend() -> dict[str, str]:
    salida = {}
    for doc in re.split(r"^---\s*$", SERVICIO.read_text(encoding="utf-8"), flags=re.M):
        if "kind: Service" not in doc:
            continue
        entorno = re.search(r"^\s+entorno:\s*(\S+)", doc, flags=re.M).group(1)
        valor = re.search(r"name:\s*APP_ENV\s+value:\s*(\S+)", doc).group(1)
        salida[entorno] = valor
    return salida


def test_dockerfile_sin_entorno_al_compilar():
    texto = DOCKERFILE.read_text(encoding="utf-8")
    assert "NEXT_PUBLIC_APP_ENV" not in texto
    assert not re.search(r"^\s*ARG\b", texto, flags=re.M)
    assert not re.search(r"^\s*ENV\b[^\n]*APP_ENV", texto, flags=re.M)


def test_app_env_por_servicio_igual_al_backend():
    frontend = _app_env_frontend()
    assert set(frontend) == {"production", "pruebas", "demo"}
    for entorno, valor in frontend.items():
        assert valor == entorno and valor in guardias.ENTORNOS_VALIDOS
    # El backend de producción declara su APP_ENV en el despliegue a Cloud Run.
    backend = DEPLOY_BACKEND.read_text(encoding="utf-8")
    assert re.search(r"APP_ENV=production\b", backend)


@pytest.mark.skipif(
    not os.environ.get("GCP03_IMAGEN") or not shutil.which("docker"),
    reason="sin GCP03_IMAGEN o sin Docker",
)
def test_imagen_produccion_sirve_robots_allow():
    imagen = os.environ["GCP03_IMAGEN"]

    def robots(app_env: str | None) -> str:
        args = ["docker", "run", "-d", "--rm", "-p", "127.0.0.1::3000"]
        if app_env:
            args += ["-e", f"APP_ENV={app_env}"]
        cid = subprocess.run(args + [imagen], capture_output=True, text=True, check=True).stdout.strip()
        try:
            puerto = subprocess.run(
                ["docker", "port", cid, "3000"], capture_output=True, text=True, check=True
            ).stdout.strip().splitlines()[0].rsplit(":", 1)[1]
            for _ in range(60):
                try:
                    with urllib.request.urlopen(f"http://127.0.0.1:{puerto}/robots.txt", timeout=2) as r:
                        return r.read().decode()
                except OSError:
                    time.sleep(1)
            raise AssertionError("el contenedor no respondió")
        finally:
            subprocess.run(["docker", "stop", cid], capture_output=True)

    assert "Allow: /" in robots("production")
    assert "Disallow: /" in robots("pruebas")
    assert "Disallow: /" in robots(None)
