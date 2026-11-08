"""GCP-08 · Proxy de /api/v1 en tiempo de ejecución, /health e imagen de menos de 120 MB.

`¤arbitro` — contrato: governance/tareas/GCP-08.md (Arquitecto y Seguridad, 2026-11-08).

Las pruebas arrancan la imagen real de `frontend/Dockerfile.cloudrun` contra backends simulados
en este proceso. Usan `GCP08_IMAGEN` si existe; si no, construyen la imagen una vez. Sin Docker se
omiten, salvo en el CI (`CI` definido), donde son obligatorias.
"""

from __future__ import annotations

import http.client
import json
import os
import re
import shutil
import subprocess
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
FRONTEND = RAIZ / "frontend"
SERVICIO = RAIZ / "governance/operaciones/cloudrun_frontend_service.yaml"
LIMITE_BYTES = 120 * 1000 * 1000
BINARIO = bytes(range(256)) * 4  # 1024 bytes, con bytes que no son UTF-8 válido


def _docker_disponible() -> bool:
    if not shutil.which("docker"):
        return False
    return subprocess.run(["docker", "info"], capture_output=True).returncode == 0


if not _docker_disponible():
    if os.environ.get("CI"):
        raise RuntimeError("GCP-08: el CI exige Docker para medir y arrancar la imagen")
    pytest.skip("sin Docker", allow_module_level=True)


# ----------------------------------------------------------------------------- backend simulado

class _Backend:
    def __init__(self, nombre: str):
        self.nombre = nombre
        self.peticiones: list[dict] = []
        backend = self

        class Manejador(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *args):  # silencio
                pass

            def _responder(self, estado: int, cuerpo: bytes, cabeceras: dict[str, str]):
                self.send_response(estado)
                for k, v in cabeceras.items():
                    self.send_header(k, v)
                self.send_header("Content-Length", str(len(cuerpo)))
                self.end_headers()
                if self.command != "HEAD":
                    self.wfile.write(cuerpo)

            def _atender(self):
                largo = int(self.headers.get("Content-Length") or 0)
                if self.headers.get("Transfer-Encoding", "").lower() == "chunked":
                    cuerpo = b""
                    while True:
                        tam = int(self.rfile.readline().strip() or b"0", 16)
                        if tam == 0:
                            self.rfile.readline()
                            break
                        cuerpo += self.rfile.read(tam)
                        self.rfile.readline()
                else:
                    cuerpo = self.rfile.read(largo) if largo else b""
                backend.peticiones.append({
                    "metodo": self.command,
                    "ruta": self.path,
                    "cabeceras": {k.lower(): v for k, v in self.headers.items()},
                    "cuerpo": cuerpo,
                })
                ruta = self.path.split("?", 1)[0]
                if ruta == "/api/v1/binario":
                    self._responder(200, BINARIO, {
                        "Content-Type": "application/octet-stream",
                        "Content-Disposition": 'attachment; filename="informe.bin"',
                        "Cache-Control": "no-store, private",
                        "X-Content-SHA256": "abc123",
                    })
                elif ruta == "/api/v1/limite":
                    self._responder(429, b'{"detail":"demasiadas"}', {"Content-Type": "application/json", "Retry-After": "7"})
                elif ruta == "/api/v1/parcial":
                    m = re.fullmatch(r"bytes=(\d+)-(\d+)", self.headers.get("Range", ""))
                    if m:
                        a, b = int(m.group(1)), int(m.group(2))
                        self._responder(206, BINARIO[a:b + 1], {
                            "Content-Type": "application/octet-stream",
                            "Content-Range": f"bytes {a}-{b}/{len(BINARIO)}",
                            "Accept-Ranges": "bytes",
                        })
                    else:
                        self._responder(200, BINARIO, {"Content-Type": "application/octet-stream", "Accept-Ranges": "bytes"})
                elif ruta == "/api/v1/redirige":
                    self._responder(302, b"", {"Location": "/api/v1/destino"})
                else:
                    self._responder(200, json.dumps({"backend": backend.nombre}).encode(), {
                        "Content-Type": "application/json",
                        "X-Request-ID": self.headers.get("X-Request-ID", ""),
                        "Set-Cookie": "sesion=filtrada",
                        "X-Interna": "no-debe-salir",
                    })

            do_GET = do_HEAD = do_POST = do_PUT = do_PATCH = do_DELETE = _atender

        self.servidor = ThreadingHTTPServer(("0.0.0.0", 0), Manejador)
        self.puerto = self.servidor.server_address[1]
        threading.Thread(target=self.servidor.serve_forever, daemon=True).start()

    def url(self) -> str:
        return f"http://host.docker.internal:{self.puerto}"

    def cerrar(self):
        self.servidor.shutdown()


# ----------------------------------------------------------------------------- imagen y contenedores

@pytest.fixture(scope="module")
def imagen():
    etiqueta = os.environ.get("GCP08_IMAGEN")
    if not etiqueta:
        etiqueta = "gcp08-web:prueba"
        subprocess.run(["docker", "build", "-q", "-f", "Dockerfile.cloudrun", "-t", etiqueta, "."],
                       cwd=FRONTEND, check=True, capture_output=True, timeout=1200)
    return etiqueta


class _Frontend:
    def __init__(self, imagen: str, entorno: dict[str, str]):
        args = ["docker", "run", "-d", "--rm", "-p", "127.0.0.1::3000", "--add-host", "host.docker.internal:host-gateway"]
        for k, v in entorno.items():
            args += ["-e", f"{k}={v}"]
        self.id = subprocess.run(args + [imagen], capture_output=True, text=True, check=True).stdout.strip()
        salida = subprocess.run(["docker", "port", self.id, "3000"], capture_output=True, text=True, check=True).stdout
        self.puerto = int(salida.strip().splitlines()[0].rsplit(":", 1)[1])
        for _ in range(60):
            try:
                if self.pedir("GET", "/health")[0] == 200:
                    return
            except OSError:
                pass
            time.sleep(1)
        raise AssertionError("el frontend no arrancó")

    def pedir(self, metodo: str, ruta: str, cuerpo: bytes | None = None, cabeceras: dict | None = None):
        conexion = http.client.HTTPConnection("127.0.0.1", self.puerto, timeout=30)
        try:
            conexion.request(metodo, ruta, body=cuerpo, headers=cabeceras or {})
            r = conexion.getresponse()
            return r.status, {k.lower(): v for k, v in r.getheaders()}, r.read()
        finally:
            conexion.close()

    def cerrar(self):
        subprocess.run(["docker", "stop", "-t", "1", self.id], capture_output=True)


@pytest.fixture(scope="module")
def backends():
    a, b = _Backend("A"), _Backend("B")
    yield a, b
    a.cerrar()
    b.cerrar()


@pytest.fixture(scope="module")
def nube(imagen, backends):
    """Frontend como en Cloud Run (K_SERVICE), apuntando al backend A."""
    f = _Frontend(imagen, {"K_SERVICE": "evydentia-web", "APP_ENV": "pruebas", "BACKEND_URL": backends[0].url()})
    yield f
    f.cerrar()


@pytest.fixture(scope="module")
def local(imagen, backends):
    """La MISMA imagen, sin K_SERVICE, apuntando al backend B."""
    f = _Frontend(imagen, {"APP_ENV": "pruebas", "BACKEND_URL": backends[1].url()})
    yield f
    f.cerrar()


def _ultima(backend: _Backend, ruta: str) -> dict:
    return [p for p in backend.peticiones if p["ruta"].startswith(ruta)][-1]


# ----------------------------------------------------------------------------- pruebas 1 a 14

def test_01_la_misma_imagen_reenvia_al_backend_de_cada_servicio(nube, local):
    assert json.loads(nube.pedir("GET", "/api/v1/eco")[2]) == {"backend": "A"}
    assert json.loads(local.pedir("GET", "/api/v1/eco")[2]) == {"backend": "B"}


def test_02_reenvia_identidad_y_no_reenvia_host(nube, backends):
    marca = uuid.uuid4().hex
    nube.pedir("GET", f"/api/v1/eco?m={marca}", cabeceras={
        "Authorization": "Bearer generado", "X-Tenant-ID": "t-1", "X-Role": "dpo",
        "Host": "atacante.example", "Cookie": "c=1", "X-Forwarded-For": "1.2.3.4", "X-Otra": "x",
    })
    p = _ultima(backends[0], f"/api/v1/eco?m={marca}")
    c = p["cabeceras"]
    assert c["authorization"] == "Bearer generado" and c["x-tenant-id"] == "t-1" and c["x-role"] == "dpo"
    assert c["host"] == f"host.docker.internal:{backends[0].puerto}"
    assert "cookie" not in c and "x-forwarded-for" not in c and "x-otra" not in c


def test_03_sin_backend_url_en_la_nube_responde_503(imagen):
    f = _Frontend(imagen, {"K_SERVICE": "evydentia-web", "APP_ENV": "pruebas"})
    try:
        estado, cabeceras, cuerpo = f.pedir("GET", "/api/v1/eco")
        assert estado == 503 and b"http" not in cuerpo
        # BACKEND_URL http hacia un host público, en la nube: también 503.
    finally:
        f.cerrar()
    g = _Frontend(imagen, {"K_SERVICE": "evydentia-web", "APP_ENV": "pruebas", "BACKEND_URL": "http://backend.example.com"})
    try:
        assert g.pedir("GET", "/api/v1/eco")[0] == 503
        assert g.pedir("OPTIONS", "/api/v1/eco")[0] == 405
    finally:
        g.cerrar()


def test_04_health_responde_sin_tocar_el_backend(nube, backends):
    antes = len(backends[0].peticiones)
    estado, _, cuerpo = nube.pedir("GET", "/health")
    assert estado == 200 and json.loads(cuerpo) == {"estado": "ok"}
    assert len(backends[0].peticiones) == antes


def test_05_la_imagen_pesa_menos_de_120_mb(imagen):
    """Suma de las capas sin comprimir (`docker history`): el tamaño real en cualquier almacén.

    Con el almacén containerd, `docker image inspect` suma además los blobs comprimidos.
    """
    salida = subprocess.run(["docker", "history", "--no-trunc", "--human=false", "--format", "{{.Size}}", imagen],
                            capture_output=True, text=True, check=True).stdout
    total = sum(int(x) for x in salida.split() if x.isdigit())
    assert 0 < total < LIMITE_BYTES, f"{total / 1e6:.1f} MB"


def test_06_las_sondas_usan_health():
    texto = SERVICIO.read_text(encoding="utf-8")
    assert "/robots.txt" not in texto
    for sonda in ("startupProbe", "livenessProbe"):
        bloques = re.findall(sonda + r":\s*\n\s*httpGet:\s*\n\s*path:\s*(\S+)", texto)
        assert bloques and set(bloques) == {"/health"}


def test_07_un_binario_llega_identico_con_su_content_disposition(nube):
    estado, cabeceras, cuerpo = nube.pedir("GET", "/api/v1/binario")
    assert estado == 200 and cuerpo == BINARIO
    assert cabeceras["content-disposition"] == 'attachment; filename="informe.bin"'
    assert cabeceras["x-content-sha256"] == "abc123"


def test_08_x_request_id_de_ida_y_vuelta(nube, backends):
    rid = uuid.uuid4().hex
    _, cabeceras, _ = nube.pedir("GET", "/api/v1/eco?rid=1", cabeceras={"X-Request-ID": rid})
    assert _ultima(backends[0], "/api/v1/eco?rid=1")["cabeceras"]["x-request-id"] == rid
    assert cabeceras["x-request-id"] == rid
    assert "set-cookie" not in cabeceras and "x-interna" not in cabeceras


def test_09_en_la_nube_x_user_id_no_llega_al_backend(nube, local, backends):
    nube.pedir("GET", "/api/v1/eco?u=nube", cabeceras={"X-User-ID": "suplantado"})
    assert "x-user-id" not in _ultima(backends[0], "/api/v1/eco?u=nube")["cabeceras"]
    local.pedir("GET", "/api/v1/eco?u=local", cabeceras={"X-User-ID": "dev"})
    assert _ultima(backends[1], "/api/v1/eco?u=local")["cabeceras"]["x-user-id"] == "dev"


def test_10_post_json_y_429_con_retry_after(nube, backends):
    cuerpo = json.dumps({"nombre": "Área ñ", "n": 1}).encode()
    nube.pedir("POST", "/api/v1/eco?post=1", cuerpo, {"Content-Type": "application/json"})
    p = _ultima(backends[0], "/api/v1/eco?post=1")
    assert p["metodo"] == "POST" and p["cuerpo"] == cuerpo
    assert p["cabeceras"]["content-type"] == "application/json"
    estado, cabeceras, _ = nube.pedir("GET", "/api/v1/limite")
    assert estado == 429 and cabeceras["retry-after"] == "7"


def test_11_range_devuelve_206_con_content_range(nube):
    estado, cabeceras, cuerpo = nube.pedir("GET", "/api/v1/parcial", cabeceras={"Range": "bytes=100-299"})
    assert estado == 206
    assert cabeceras["content-range"] == "bytes 100-299/1024" and cabeceras["accept-ranges"] == "bytes"
    assert cuerpo == BINARIO[100:300]


def test_12_la_ruta_no_sale_del_backend(nube, backends):
    antes = len(backends[0].peticiones)
    for ruta in ("/api/v1/..%2f..%2fadmin", "/api/v1/%2e%2e/%2e%2e/admin", "/api/v1//otro.host", "/api/v1/a%2fb"):
        estado, _, _ = nube.pedir("GET", ruta)
        assert estado in (400, 404, 308), (ruta, estado)
    nuevas = backends[0].peticiones[antes:]
    assert all(p["ruta"].startswith("/api/v1/") and ".." not in p["ruta"] for p in nuevas)
    assert not any("admin" in p["ruta"] or "otro.host" in p["ruta"] for p in nuevas)


def test_13_no_sigue_redirecciones(nube, backends):
    estado, cabeceras, _ = nube.pedir("GET", "/api/v1/redirige")
    assert estado == 302 and cabeceras["location"] == "/api/v1/destino"
    assert not any(p["ruta"] == "/api/v1/destino" for p in backends[0].peticiones)


def test_14_cache_control_se_conserva_y_no_store_por_defecto(nube):
    assert nube.pedir("GET", "/api/v1/binario")[1]["cache-control"] == "no-store, private"
    assert nube.pedir("GET", "/api/v1/eco?cc=1")[1]["cache-control"] == "no-store"
