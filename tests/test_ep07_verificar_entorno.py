# ¤entorno-pruebas ¤arbitro
"""EP-07: el verificador del entorno de pruebas, contra un servidor HTTP falso en localhost.

Cada comprobación falla por su propia causa, y ni el token ni la URL aparecen en la salida.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))
import verificar_entorno_pruebas as vep  # noqa: E402

from tests._lector_yaml import leer_yaml  # noqa: E402

TOKEN = f"tok-ep07-{uuid.uuid4().hex}"
DIGEST = "sha256:" + "a" * 64
SANO = {"status": "OPERATIONAL", "routers": {"cargados": ["salud"], "fallidos": [], "total": 1}}
CHEQUEOS = ["salud", "entorno", "sin_headers", "iap", "robots", "digest"]


class Falso:
    """Comportamiento del entorno falso; cada prueba rompe una sola pieza."""

    def __init__(self):
        self.health = (200, SANO)
        self.entorno = (200, {"entorno": "pruebas", "datos_ficticios": True})
        self.x_entorno = "pruebas"
        self.datos_org = 401
        self.front_sin_iap = (302, "https://accounts.google.com/o/oauth2/v2/auth")
        self.robots = "User-agent: *\nDisallow: /\n"
        self.vistas: list[dict] = []


@pytest.fixture
def entorno():
    falso = Falso()

    class Manejador(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _responder(self, estado, cuerpo="", cabeceras=None):
            self.send_response(estado)
            for k, v in (cabeceras or {}).items():
                self.send_header(k, v)
            datos = cuerpo.encode() if isinstance(cuerpo, str) else json.dumps(cuerpo).encode()
            self.send_header("Content-Length", str(len(datos)))
            self.end_headers()
            self.wfile.write(datos)

        def do_GET(self):
            cab = {k.lower(): v for k, v in self.headers.items()}
            falso.vistas.append({"ruta": self.path, **cab})
            iap = cab.get("proxy-authorization") == f"Bearer {TOKEN}"
            run = cab.get("x-serverless-authorization") == f"Bearer {TOKEN}"
            if self.path.startswith("/api/"):
                if not run:
                    return self._responder(403, "sin invocador")
                if self.path == "/api/v1/health":
                    return self._responder(*falso.health)
                if self.path == "/api/v1/entorno":
                    return self._responder(falso.entorno[0], falso.entorno[1], {"X-Entorno": falso.x_entorno})
                if self.path == vep.RUTA_DATOS_ORGANIZACION:
                    return self._responder(falso.datos_org, {"detail": "x"})
                return self._responder(404)
            if not iap:
                estado, ubicacion = falso.front_sin_iap
                return self._responder(estado, "", {"Location": ubicacion} if ubicacion else {})
            if self.path == "/robots.txt":
                return self._responder(200, falso.robots)
            return self._responder(200, "<html></html>")

    servidor = ThreadingHTTPServer(("127.0.0.1", 0), Manejador)
    hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()
    falso.url = f"http://127.0.0.1:{servidor.server_address[1]}"
    yield falso
    servidor.shutdown()


def _correr(falso, digest=DIGEST, token=lambda aud: TOKEN):
    def obtener_digest():
        if isinstance(digest, Exception):
            raise digest
        return digest

    resultados, d = vep.verificar(falso.url, falso.url, "aud-iap-ep07", obtener_token=token,
                                  obtener_digest=obtener_digest)
    salida = vep.formatear(resultados, d)
    assert TOKEN not in salida and falso.url not in salida and "127.0.0.1" not in salida
    return {r.nombre: r.ok for r in resultados}, salida


def _solo_falla(estado: dict, nombre: str):
    assert estado == {c: c != nombre for c in CHEQUEOS}, estado


def test_entorno_sano_pasa_e_imprime_el_digest(entorno):
    estado, salida = _correr(entorno)
    assert all(estado.values()) and list(estado) == CHEQUEOS
    assert f"DIGEST {DIGEST}" in salida


def test_salud_falla_por_su_causa(entorno):
    entorno.health = (200, {**SANO, "status": "DEGRADED"})
    _solo_falla(_correr(entorno)[0], "salud")


@pytest.mark.parametrize("cambio", ["entorno", "ficticios", "cabecera", "estado"])
def test_entorno_falla_por_su_causa(entorno, cambio):
    if cambio == "entorno":
        entorno.entorno = (200, {"entorno": "production", "datos_ficticios": True})
    elif cambio == "ficticios":
        entorno.entorno = (200, {"entorno": "pruebas", "datos_ficticios": False})
    elif cambio == "cabecera":
        entorno.x_entorno = "production"
    else:
        entorno.entorno = (404, {})
    _solo_falla(_correr(entorno)[0], "entorno")


@pytest.mark.parametrize("estado_http", [200, 403])
def test_modo_headers_activo_falla(entorno, estado_http):
    entorno.datos_org = estado_http
    _solo_falla(_correr(entorno)[0], "sin_headers")


def test_la_identidad_inventada_va_sin_token_de_la_aplicacion(entorno):
    _correr(entorno)
    vista = next(v for v in entorno.vistas if v["ruta"] == vep.RUTA_DATOS_ORGANIZACION)
    assert vista["x-tenant-id"] and vista["x-user-id"].endswith(".invalid")
    assert "authorization" not in vista


@pytest.mark.parametrize("sin_iap", [(200, ""), (302, "https://otro.invalid/entrar")])
def test_frontend_abierto_sin_iap_falla(entorno, sin_iap):
    entorno.front_sin_iap = sin_iap
    _solo_falla(_correr(entorno)[0], "iap")


@pytest.mark.parametrize("sin_iap", [(401, ""), (403, "")])
def test_iap_que_rechaza_con_401_o_403_pasa(entorno, sin_iap):
    entorno.front_sin_iap = sin_iap
    assert all(_correr(entorno)[0].values())


@pytest.mark.parametrize("robots", ["User-agent: *\nAllow: /\n", "User-agent: *\nDisallow: /privado\n"])
def test_robots_falla_por_su_causa(entorno, robots):
    entorno.robots = robots
    _solo_falla(_correr(entorno)[0], "robots")


@pytest.mark.parametrize("digest", ["", "sha256:corto", RuntimeError("el tráfico no está al 100 %")])
def test_digest_falla_por_su_causa(entorno, digest):
    estado, salida = _correr(entorno, digest=digest)
    _solo_falla(estado, "digest")
    assert "DIGEST" not in salida


def test_sin_token_de_identidad_no_verifica_nada(entorno):
    def sin_token(aud):
        raise RuntimeError(f"fallo con {TOKEN}")

    estado, salida = _correr(entorno, token=sin_token)
    assert estado == {"credenciales": False}


def test_backend_caido_falla_sin_mostrar_la_url():
    url = "http://127.0.0.1:9"
    resultados, d = vep.verificar(url, url, "aud", obtener_token=lambda a: TOKEN, obtener_digest=lambda: DIGEST)
    salida = vep.formatear(resultados, d)
    assert not all(r.ok for r in resultados)
    assert url not in salida and TOKEN not in salida


def test_main_rechaza_el_proyecto_de_produccion(monkeypatch, capsys):
    monkeypatch.setenv("HUELLA_PROYECTO_PRODUCCION", "huella-ep07-prod")
    monkeypatch.delenv("PROYECTO_PRUEBAS", raising=False)
    assert vep.main(["https://frontend.invalid", "--proyecto", "huella-ep07-prod-x"]) == 2
    assert vep.main(["https://frontend.invalid"]) == 2
    assert "frontend.invalid" not in capsys.readouterr().err


def test_digest_que_sirve_lee_la_revision_al_100(monkeypatch):
    llamadas = []

    def falso_run(cmd, **k):
        llamadas.append(cmd)
        if cmd[2] == "services":
            salida = {"status": {"traffic": [{"revisionName": "rev-1", "percent": 100}]}}
        else:
            salida = {"status": {"imageDigest": DIGEST}}
        return subprocess.CompletedProcess(cmd, 0, json.dumps(salida), "")

    monkeypatch.setattr(vep.subprocess, "run", falso_run)
    assert vep.digest_que_sirve("proy-pruebas", "us-central1", "evydentia-backend") == DIGEST
    assert all("--project" in c and "proy-pruebas" in c for c in llamadas)
    assert all(c[:3] in (["gcloud", "run", "services"], ["gcloud", "run", "revisions"]) for c in llamadas)


def test_reutiliza_verificar_despliegue_sin_copiarlo():
    codigo = (RAIZ / "scripts" / "verificar_entorno_pruebas.py").read_text(encoding="utf-8")
    assert "import verificar_despliegue" in codigo and "def verificar_health" not in codigo


# --- Brief del workflow (gobernanza reservada) -----------------------------------------------------

BRIEF = RAIZ / "governance" / "apoyo" / "BRIEF_PROPIETARIO_EP07_WORKFLOW.md"


def _yaml_del_brief() -> dict:
    texto = BRIEF.read_text(encoding="utf-8")
    bloques = re.findall(r"```yaml\n(.*?)```", texto, re.S)
    assert len(bloques) == 1, "el brief debe tener un único bloque yaml con el workflow completo"
    return leer_yaml(bloques[0])


def test_el_brief_trae_el_workflow_completo():
    wf = _yaml_del_brief()
    disparadores = wf["on"]
    assert "workflow_dispatch" in disparadores and "repository_dispatch" in disparadores
    trabajo = wf["jobs"]["verificar-entorno-pruebas"]
    pasos = " ".join(str(p.get("run", "")) + str(p.get("uses", "")) for p in trabajo["steps"])
    assert "scripts/verificar_entorno_pruebas.py" in pasos
    assert "google-github-actions/auth" in pasos and "workload_identity_provider" in json.dumps(trabajo)
    assert wf["permissions"]["id-token"] == "write"
    assert "credentials_json" not in json.dumps(wf)
    assert not re.search(r"https?://", json.dumps(wf)), "las direcciones salen de variables del repositorio"
    assert "${{ vars." in BRIEF.read_text(encoding="utf-8")


def test_el_brief_dice_que_no_es_check_obligatorio_y_lo_aplica_el_propietario():
    texto = BRIEF.read_text(encoding="utf-8")
    assert "no es un check obligatorio" in texto.lower()
    assert ".github/workflows/entorno-pruebas.yml" in texto
    assert "propietario" in texto.lower()
