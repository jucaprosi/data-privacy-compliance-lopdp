# ¤evidencias ¤arbitro
"""EVI-01: las rutas que la pantalla usa hoy no cambian de forma, y las nuevas nacen apagadas (sin base).

`tests/snapshots/openapi_evidencias_antiguas.json` es el OpenAPI de las tres rutas antiguas de /evidencias
tomado de `main` antes de EVI-01, con los esquemas ya resueltos. Se regenera solo a propósito, desde una copia
de `main`, nunca desde esta rama.

Mutación ejecutada (dejó en rojo test_las_rutas_nuevas_responden_404_con_la_bandera_apagada y
test_el_estado_dice_subida_firmada_falso_por_defecto; se restauró): en `subida_firmada_activa`, devolver True
cuando la variable no está definida (bandera encendida por defecto).
"""
import json
import os
from pathlib import Path

import pytest

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://sin-base:sin-base@localhost:1/sin-base")

from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402

SNAPSHOT = Path(__file__).parent / "snapshots" / "openapi_evidencias_antiguas.json"
RUTAS_ANTIGUAS = (
    "/api/v1/evidencias",
    "/api/v1/evidencias/verificar/{sha256}",
    "/api/v1/evidencias/{evidencia_id}/vinculos",
)
RUTAS_NUEVAS = (
    ("post", "/api/v1/evidencias/subidas"),
    ("post", "/api/v1/evidencias/subidas/confirmar"),
    ("get", "/api/v1/evidencias/documentos"),
    ("put", "/api/v1/evidencias/documentos/x/vinculos/1"),
    ("delete", "/api/v1/evidencias/documentos/x/vinculos/1"),
)
CABECERAS = {"X-User-ID": "u", "X-Tenant-ID": "t", "X-Role": "dpo"}


def _resolver(nodo, esquema):
    if isinstance(nodo, dict):
        if "$ref" in nodo:
            return _resolver(esquema["components"]["schemas"][nodo["$ref"].rsplit("/", 1)[1]], esquema)
        return {k: _resolver(v, esquema) for k, v in nodo.items()}
    if isinstance(nodo, list):
        return [_resolver(x, esquema) for x in nodo]
    return nodo


def test_las_rutas_antiguas_conservan_exactamente_su_forma_en_openapi():
    esquema = app.openapi()
    actual = {ruta: _resolver(esquema["paths"][ruta], esquema) for ruta in RUTAS_ANTIGUAS}
    guardado = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert set(guardado) == set(RUTAS_ANTIGUAS)
    assert json.loads(json.dumps(actual)) == guardado


def test_las_rutas_nuevas_responden_404_con_la_bandera_apagada(monkeypatch):
    monkeypatch.delenv("EVIDENCIAS_SUBIDA_FIRMADA", raising=False)
    cliente = TestClient(app)
    for metodo, ruta in RUTAS_NUEVAS:
        r = getattr(cliente, metodo)(ruta, headers=CABECERAS, **({"json": {}} if metodo == "post" else {}))
        assert r.status_code == 404, f"{metodo.upper()} {ruta} -> {r.status_code}"


def test_el_estado_dice_subida_firmada_falso_por_defecto(monkeypatch):
    monkeypatch.delenv("EVIDENCIAS_SUBIDA_FIRMADA", raising=False)
    r = TestClient(app).get("/api/v1/evidencias/estado", headers=CABECERAS)
    assert r.status_code == 200 and r.json() == {"subida_firmada": False}


@pytest.mark.parametrize("valor", ["", "0", "false", "no", "apagada"])
def test_cualquier_valor_que_no_encienda_deja_la_bandera_apagada(monkeypatch, valor):
    monkeypatch.setenv("EVIDENCIAS_SUBIDA_FIRMADA", valor)
    r = TestClient(app).get("/api/v1/evidencias/estado", headers=CABECERAS)
    assert r.json() == {"subida_firmada": False}


def test_la_bandera_se_lee_solo_en_el_backend():
    raiz = Path(__file__).resolve().parent.parent
    for carpeta in ("frontend/src", "frontend/app"):
        base = raiz / carpeta
        if base.exists():
            for ruta in base.rglob("*"):
                if ruta.suffix in {".ts", ".tsx", ".js"}:
                    assert "EVIDENCIAS_SUBIDA_FIRMADA" not in ruta.read_text(encoding="utf-8", errors="ignore")
