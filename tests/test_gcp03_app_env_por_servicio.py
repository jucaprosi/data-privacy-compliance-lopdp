"""GCP-03 · Una sola imagen del frontend; APP_ENV por servicio y al ejecutar (§5.5, EP-02).

`¤cloud-run-perf` `¤seguridad`

La prueba de la imagen real corre si existe `GCP03_IMAGEN` (etiqueta local construida con
`frontend/Dockerfile.cloudrun`) y Docker está disponible; si no, se omite.
"""

import os
import shutil
import subprocess
import time
import urllib.request

import pytest


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
