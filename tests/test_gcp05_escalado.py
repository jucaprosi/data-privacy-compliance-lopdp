"""GCP-05 · Escalado verificable en Cloud Run: límites explícitos, presupuesto de conexiones y prueba de carga.

`¤cloud-run-perf` `¤arbitro`
"""
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from tests._lector_yaml import leer_yaml

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

import prueba_carga as pc  # noqa: E402

BACKEND = RAIZ / "governance/operaciones/cloudrun_service.yaml"
FRONTEND = RAIZ / "governance/operaciones/cloudrun_frontend_service.yaml"
MINIMO, MAXIMO = "autoscaling.knative.dev/minScale", "autoscaling.knative.dev/maxScale"


def _servicios(ruta: Path) -> list[dict]:
    docs = leer_yaml(ruta.read_text(encoding="utf-8"))
    docs = docs if isinstance(docs, list) and docs and isinstance(docs[0], dict) and "kind" in docs[0] else [docs]
    return [d for d in docs if isinstance(d, dict) and d.get("kind") == "Service"]


def _limites(servicio: dict) -> dict:
    plantilla = servicio["spec"]["template"]
    notas = plantilla["metadata"]["annotations"]
    return {
        "nombre": servicio["metadata"]["name"],
        "min": int(notas[MINIMO]),
        "max": int(notas[MAXIMO]),
        "concurrencia": int(plantilla["spec"]["containerConcurrency"]),
    }


def presupuesto_conexiones(max_instancias: int, pool: int, desborde: int) -> int:
    """Conexiones que puede abrir el backend a plena escala."""
    return max_instancias * (pool + desborde)


def test_manifiestos_con_limites_explicitos():
    servicios = _servicios(BACKEND) + _servicios(FRONTEND)
    assert len(servicios) == 4  # backend + frontend de producción, pruebas y demo
    for servicio in servicios:
        limites = _limites(servicio)  # KeyError si falta mínimo, máximo o concurrencia
        assert limites["min"] >= 0 and limites["max"] >= max(1, limites["min"]), limites
        assert limites["concurrencia"] > 0, limites


def test_valores_de_la_tabla_de_la_ficha():
    backend = _limites(_servicios(BACKEND)[0])
    assert (backend["min"], backend["max"], backend["concurrencia"]) == (1, 10, 80)
    produccion, *otros = [_limites(s) for s in _servicios(FRONTEND)]
    assert (produccion["min"], produccion["max"], produccion["concurrencia"]) == (0, 5, 80)
    assert all(o["max"] <= 5 and o["min"] == 0 for o in otros)


def test_presupuesto_de_conexiones():
    servicio = _servicios(BACKEND)[0]
    notas = servicio["metadata"]["annotations"]
    pool, desborde = int(notas["evydentia.com/pool-size"]), int(notas["evydentia.com/max-overflow"])
    base = int(notas["evydentia.com/conexiones-base"])
    total = presupuesto_conexiones(_limites(servicio)["max"], pool, desborde)
    assert total <= base, f"{total} conexiones posibles superan las {base} que admite la base"


def test_el_ejemplo_de_la_ficha_no_cabe():
    """10 instancias × (5 + 5) = 100 supera 80: la regla debe rechazarlo."""
    assert presupuesto_conexiones(10, 5, 5) == 100 > 80


def test_prueba_carga_rechaza_produccion(monkeypatch, capsys):
    def no_debe_llamarse(*_a, **_k):
        raise AssertionError("se envió una petición al destino de producción")

    monkeypatch.setattr(pc, "_get", no_debe_llamarse)
    for destino in ("https://app.evydentia.com", "https://app.evydentia.com/api", "https://evydentia-production.example.invalid"):
        assert pc.main(["--entorno", "pruebas", "--url", destino, "--duracion", "1"]) == 2
    assert "producción" in capsys.readouterr().err


def test_percentiles_y_resumen():
    valores = [float(n) for n in range(1, 101)]
    assert pc.percentil(valores, 50) == 50.0 and pc.percentil(valores, 95) == 95.0 and pc.percentil(valores, 99) == 99.0
    assert pc.percentil([], 95) == 0.0
    sano = pc.resumir([100.0] * 10, pc.Counter({200: 10}))
    assert sano["meta_cumplida"] is True
    assert pc.resumir([900.0] * 10, pc.Counter({200: 10}))["meta_cumplida"] is False   # p95 sobre 800 ms
    con_5xx = pc.resumir([10.0] * 10, pc.Counter({200: 9, 503: 1}))
    assert con_5xx["meta_cumplida"] is False and con_5xx["5xx"] == 1


@pytest.fixture
def servidor():
    """Entorno simulado en 127.0.0.1: responde lo que se le indique, sin credenciales ni datos reales."""
    estado = {"entorno": "pruebas", "ruta_fallida": None, "visitas": 0}

    class Manejador(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            estado["visitas"] += 1
            if self.path == estado["ruta_fallida"]:
                self.send_response(503)
                self.end_headers()
                return
            cuerpo = json.dumps({"entorno": estado["entorno"]} if self.path == "/api/v1/entorno" else {"ok": True}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(cuerpo)))
            self.end_headers()
            self.wfile.write(cuerpo)

        def log_message(self, *_):
            pass

    srv = ThreadingHTTPServer(("127.0.0.1", 0), Manejador)
    hilo = threading.Thread(target=srv.serve_forever, daemon=True)
    hilo.start()
    estado["url"] = f"http://127.0.0.1:{srv.server_address[1]}"
    yield estado
    srv.shutdown()
    srv.server_close()


def test_corrida_local_cumple_la_meta(servidor, capsys):
    assert pc.main(["--entorno", "pruebas", "--url", servidor["url"], "--usuarios", "8", "--duracion", "1"]) == 0
    informe = json.loads(capsys.readouterr().out.split("\nMETA")[0])
    assert informe["usuarios"] == 8 and informe["5xx"] == 0 and informe["peticiones"] > 0
    assert set(informe) >= {"p50_ms", "p95_ms", "p99_ms", "codigos"}


def test_un_5xx_no_cumple_la_meta(servidor):
    servidor["ruta_fallida"] = "/api/v1/health"
    assert pc.main(["--entorno", "pruebas", "--url", servidor["url"], "--usuarios", "4", "--duracion", "1"]) == 1


def test_exige_que_el_entorno_reportado_coincida(servidor):
    servidor["entorno"] = "produccion"
    antes = servidor["visitas"]
    assert pc.main(["--entorno", "pruebas", "--url", servidor["url"], "--usuarios", "4", "--duracion", "1"]) == 2
    assert servidor["visitas"] - antes == 1  # solo la consulta de identidad, ninguna carga
