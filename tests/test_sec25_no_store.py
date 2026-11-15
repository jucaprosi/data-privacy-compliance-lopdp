"""SEC-25: Cache-Control no-store por defecto en /api/v1. Sin base de datos."""
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app_core.cache import CABECERA_NO_STORE
from app_core.seguridad.no_store import NoStoreMiddleware

NO_STORE = CABECERA_NO_STORE["Cache-Control"]


def _cliente(con_middleware: bool = True) -> TestClient:
    app = FastAPI()

    @app.get("/api/v1/datos")
    def datos():
        return {"ok": True}

    @app.get("/api/v1/descarga")
    def descarga():
        return JSONResponse({"ok": True}, headers={"Cache-Control": "private, max-age=60"})

    @app.get("/api/v1/prohibido")
    def prohibido():
        raise HTTPException(status_code=401, detail="no")

    @app.get("/health")
    def health():
        return {"ok": True}

    @app.get("/api/v10/x")
    def otra():
        return {"ok": True}

    if con_middleware:
        app.add_middleware(NoStoreMiddleware)
    return TestClient(app)


def test_api_sin_cabecera_recibe_no_store():
    assert _cliente().get("/api/v1/datos").headers["cache-control"] == NO_STORE
    # Mutación: sin el middleware la cabecera no aparece.
    assert "cache-control" not in _cliente(con_middleware=False).get("/api/v1/datos").headers


def test_errores_con_no_store():
    c = _cliente()
    assert c.get("/api/v1/prohibido").headers["cache-control"] == NO_STORE
    r = c.get("/api/v1/no-existe")
    assert r.status_code == 404 and r.headers["cache-control"] == NO_STORE


def test_cabecera_propia_se_respeta():
    r = _cliente().get("/api/v1/descarga")
    assert r.headers["cache-control"] == "private, max-age=60"
    assert r.headers.get_list("cache-control") == ["private, max-age=60"]


def test_solo_el_prefijo_api_v1():
    c = _cliente()
    assert "cache-control" not in c.get("/health").headers
    assert "cache-control" not in c.get("/api/v10/x").headers


def test_usa_la_constante_comun():
    fuente = (Path(__file__).resolve().parent.parent / "app_core" / "seguridad" / "no_store.py").read_text(encoding="utf-8")
    assert NO_STORE not in fuente
