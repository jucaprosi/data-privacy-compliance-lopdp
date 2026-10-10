"""/health informa qué routers cargaron y cuáles fallaron (Aporte 91)."""
from types import SimpleNamespace

from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient

import main


def _importador(falla: dict[str, Exception]):
    def importar(path: str):
        if path in falla:
            raise falla[path]
        router = APIRouter()

        @router.get(f"/{path.rsplit('.', 1)[-1]}")
        def ruta() -> dict:
            return {"ok": True}

        return SimpleNamespace(router=router)

    return importar


def test_registrar_routers_separa_cargados_y_fallidos():
    app = FastAPI()
    mapa = [("a.uno", "uno"), ("a.dos", "dos"), ("a.tres", "tres")]
    falla = {"a.dos": ModuleNotFoundError("No module named 'secreto_interno'")}

    cargados, fallidos = main.registrar_routers(app, mapa, importar=_importador(falla))

    assert cargados == ["uno", "tres"]
    assert fallidos == [{"router": "dos", "error": "ModuleNotFoundError"}]
    paths = TestClient(app).get("/openapi.json").json()["paths"]
    assert "/api/v1/uno" in paths and "/api/v1/tres" in paths
    assert "/api/v1/dos" not in paths


def test_fallidos_no_exponen_el_mensaje_del_error():
    _, fallidos = main.registrar_routers(
        FastAPI(),
        [("a.uno", "uno")],
        importar=_importador({"a.uno": RuntimeError("postgresql://usuario:clave@host/db")}),
    )
    assert "clave" not in str(fallidos) and fallidos[0]["error"] == "RuntimeError"


def test_health_informa_routers_y_estado_coherente():
    r = TestClient(main.app).get("/health")
    cuerpo = r.json()
    routers = cuerpo["routers"]
    assert routers["total"] == len(main.ROUTERS_MAP)
    assert len(routers["cargados"]) + len(routers["fallidos"]) == routers["total"]
    sano = not routers["fallidos"]
    assert cuerpo["status"] == ("OPERATIONAL" if sano else "DEGRADED")
    assert r.status_code == (200 if sano else 503)


def test_health_devuelve_503_si_hay_routers_fallidos(monkeypatch):
    monkeypatch.setattr(main, "ROUTERS_FALLIDOS", [{"router": "roadmaps", "error": "ModuleNotFoundError"}])
    for ruta in ("/health", "/api/v1/health", "/"):
        r = TestClient(main.app).get(ruta)
        assert r.status_code == 503
        assert r.json()["status"] == "DEGRADED"
        assert r.json()["routers"]["total"] == len(main.ROUTERS_MAP)


def test_health_de_emergencia_devuelve_503_sin_exponer_detalle(monkeypatch, caplog):
    """Si toda la app falla al importarse, api/index.py sirve un /health en 503.

    El cuerpo es público: solo lleva el tipo de la excepción; el mensaje y el
    traceback van al log.
    """
    import importlib.util
    import logging
    import sys

    monkeypatch.setitem(sys.modules, "main", None)  # `from main import app` lanza ImportError
    spec = importlib.util.spec_from_file_location("index_emergencia", "api/index.py")
    modulo = importlib.util.module_from_spec(spec)
    with caplog.at_level(logging.ERROR, logger="jubys.arranque"):
        spec.loader.exec_module(modulo)

    r = TestClient(modulo.app).get("/health")
    assert r.status_code == 503
    cuerpo = r.json()
    assert cuerpo["status"] == "STARTUP_ERROR"
    assert cuerpo["error"] in ("ImportError", "ModuleNotFoundError")
    assert "traceback" not in cuerpo and "error_detail" not in cuerpo
    assert "Traceback" not in r.text and "api/index.py" not in r.text
    assert "Traceback" in caplog.text  # el detalle queda en el log
